import socket
import struct
import threading
from serializer import UnifiedHMIPayload
from sdk import IntentOSEventSDK
from dsp import HMISignalFeatureExtractor
from classifier import HMIPredictiveClassifier
from config import IntentOSConfig
from broadcast import IntentOSBroadcastHub

class IntentOSStreamingServer:
    """
    The High-Performance Ingestion & Inference Server for IntentOS.
    Binds a local port to receive packed raw binary telemetry over sockets,
    extracting features and running predictive ML inferences live on the data stream.
    """
    def __init__(self, host: str = IntentOSConfig.GATEWAY_HOST, port: int = IntentOSConfig.GATEWAY_PORT):
        self.host = host
        self.port = port
        self.sdk = IntentOSEventSDK()
        self.dsp_extractor = HMISignalFeatureExtractor(window_size=IntentOSConfig.DSP_SLIDING_WINDOW_SIZE)
        self.ml_classifier = HMIPredictiveClassifier()
        self.broadcast_hub = IntentOSBroadcastHub(host="127.0.0.1", port=8889)
        self.is_running = False

    def start(self) -> None:
        self.is_running = True
        self.broadcast_hub.start()
        
        self.sdk.on_intent("PRIMARY_SELECT", self.broadcast_hub.broadcast_intent)
        self.sdk.on_intent("SYSTEM_HEARTBEAT_BOOST", self.broadcast_hub.broadcast_intent)
        
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
                    
                    # FIXED: Extracting index [0] safely converts tuple parameters to pure integers
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
                    sim_action_token = packet_bytes[cursor:cursor+tok_len].decode('utf-8')

                    features = self.dsp_extractor.push_signals(hardware_source_id, raw_values)
                    inference = self.ml_classifier.evaluate_intent(modality, features)

                    payload = UnifiedHMIPayload(hardware_source_id=hardware_source_id, modality=modality)
                    payload.timestamp_utc_us = timestamp
                    payload.set_signal_vector(values=raw_values, intensity=intensity)
                    payload.set_inferred_intent(
                        token=inference["action_token"], 
                        confidence=inference["confidence_score"], 
                        lead_us=45000 if inference["action_token"] != "NULL_REST_STATE" else 0
                    )
                    payload.dsp_features = features
                    self.sdk.process_incoming_sensor_stream(payload)
                except Exception as e:
                    break
