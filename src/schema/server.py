import socket
import struct
import threading
from serializer import UnifiedHMIPayload
from sdk import IntentOSEventSDK
from dsp import HMISignalFeatureExtractor

class IntentOSStreamingServer:
    """
    The High-Performance Ingestion Server for IntentOS.
    Binds a local port to receive packed raw binary telemetry over sockets,
    extracting mathematical DSP features (MAV, RMS) live on the data stream.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.sdk = IntentOSEventSDK()
        # Initialize the industry-standard feature extraction component
        self.dsp_extractor = HMISignalFeatureExtractor(window_size=10)
        self.is_running = False

    def start(self) -> None:
        self.is_running = True
        self.server_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.server_thread.start()
        print(f"[IntentOS Server] Operational. Listening for telemetry on {self.host}:{self.port}")

    def _listen_loop(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            while self.is_running:
                try:
                    client_socket, address = server_socket.accept()
                    client_handler = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                    client_handler.start()
                except Exception as e:
                    if self.is_running:
                        print(f"[IntentOS Server Error] Exception inside execution routing: {e}")

    def _handle_client(self, client_socket: socket.socket) -> None:
        with client_socket:
            while self.is_running:
                try:
                    size_header = client_socket.recv(4)
                    if not size_header or len(size_header) < 4:
                        break
                    packet_size = struct.unpack("<I", size_header)[0]
                    packet_bytes = bytearray()
                    while len(packet_bytes) < packet_size:
                        chunk = client_socket.recv(packet_size - len(packet_bytes))
                        if not chunk:
                            break
                        packet_bytes.extend(chunk)
                    if len(packet_bytes) < packet_size:
                        break

                    header_format = "<qiiffiii"
                    header_size = struct.calcsize(header_format)
                    header_data = struct.unpack(header_format, packet_bytes[:header_size])
                    timestamp, modality, vec_len, intensity, confidence, lead, src_len, tok_len = header_data
                    
                    cursor = header_size
                    vector_format = f"<{vec_len}f"
                    vector_size = struct.calcsize(vector_format)
                    raw_values = list(struct.unpack(vector_format, packet_bytes[cursor:cursor+vector_size]))
                    
                    cursor += vector_size
                    hardware_source_id = packet_bytes[cursor:cursor+src_len].decode('utf-8')
                    cursor += src_len
                    action_token = packet_bytes[cursor:cursor+tok_len].decode('utf-8')

                    # Reconstruct the structured payload object
                    payload = UnifiedHMIPayload(hardware_source_id=hardware_source_id, modality=modality)
                    payload.timestamp_utc_us = timestamp
                    payload.set_signal_vector(values=raw_values, intensity=intensity)
                    payload.set_inferred_intent(token=action_token, confidence=confidence, lead_us=lead)
                    
                    # PRODUCTION INTEGRATION: Extract mathematical rolling features live on the stream thread
                    features = self.dsp_extractor.push_signals(hardware_source_id, raw_values)
                    
                    # Attach the processed feature map to our running payload metadata to preserve the pipeline
                    payload.dsp_features = features
                    
                    self.sdk.process_incoming_sensor_stream(payload)
                except Exception:
                    break
