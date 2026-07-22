import socket
import struct
from serializer import UnifiedHMIPayload
from config import IntentOSConfig

class IntentOSStreamClient:
    """
    The High-Performance Client Transport Wrapper for IntentOS.
    Handles network telemetry shipping and control packet orchestration over local sockets.
    """
    def __init__(self, host: str = IntentOSConfig.GATEWAY_HOST, port: int = IntentOSConfig.GATEWAY_PORT):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"[IntentOS Client] Connection established toward {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[IntentOS Client Error] Gateway destination unreachable: {e}")
            return False

    def send_payload(self, payload: UnifiedHMIPayload) -> None:
        if not self.socket:
            raise RuntimeError("Cannot execute socket stream. No active server link configured.")
        binary_data = payload.serialize_binary()
        packet_size = len(binary_data)
        size_header = struct.pack("<I", packet_size)
        try:
            self.socket.sendall(size_header + binary_data)
        except Exception as e:
            print(f"[IntentOS Client Transport Failure] Stream connection lost: {e}")

    def trigger_remote_calibration(self, mode: str) -> None:
        """
        Pumps an isolated system control framing packet over the socket layer.
        Modes allowed: 'START_REST', 'START_PEAK', 'FINALIZE'
        """
        control_packet = UnifiedHMIPayload(hardware_source_id="hardware_client_sync", modality=0)
        
        if mode.upper() == "START_REST":
            token = "START_CALIBRATION_REST"
        elif mode.upper() == "START_PEAK":
            token = "START_CALIBRATION_PEAK"
        else:
            token = "FINALIZE_CALIBRATION"
            
        control_packet.set_inferred_intent(token=token, confidence=1.0, lead_us=0)
        self.send_payload(control_packet)
        print(f"[IntentOS Client] Dispatched Remote Control Command: {token}")

    def close(self) -> None:
        if self.socket:
            self.socket.close()
            print("[IntentOS Client] Connection pool closed cleanly.")
