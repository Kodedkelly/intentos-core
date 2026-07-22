import socket
import sys
import os
import json

# Ensure absolute structural tracking handles match cleanly
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

class IntentOSCommandLineListener:
    """
    The Native Command Line Ingestion Client for IntentOS.
    Demonstrates how a third-party developer script can hook directly into the 
    IntentOS Broadcast Hub (Port 8889) to pipeline human intent JSON packets natively.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8889):
        self.host = host
        self.port = port
        self.socket = None
        self.is_running = False

    def start_ingestion_loop(self) -> None:
        """Opens a raw TCP network socket handle and processes incoming intent packets."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_running = True
            print(f"🔊 [NATIVE LISTENER] Pipeline connection hooked cleanly onto port {self.port}")
            print("Piping live human intents down standard output stream... (Ctrl+C to exit)\n")
        except Exception as e:
            print(f"[Listener Error] Ingestion hub unreachable: {e}")
            return

        network_buffer = ""
        try:
            while self.is_running:
                raw_bytes = self.socket.recv(4096)
                if not raw_bytes:
                    print("\n⚠️ [LISTENER ALERT] Stream pipeline dropped by server core.")
                    break
                
                # Accumulate and decode continuous byte streams over clean string splits
                network_buffer += raw_bytes.decode('utf-8')
                while "\n" in network_buffer:
                    json_line, network_buffer = network_buffer.split("\n", 1)
                    if json_line.strip():
                        self._process_streamed_intent(json_line)
                        
        except KeyboardInterrupt:
            print("\n⚠️ [LISTENER] Detaching cleanly from network ingestion stream...")
        finally:
            self.socket.close()

    def _process_streamed_intent(self, json_payload_string: str) -> None:
        """Parses the telemetry string and demonstrates piping output loops natively."""
        try:
            payload_data = json.loads(json_payload_string)
            decoded_intent = payload_data.get("decoded_intent", {})
            
            action_token = decoded_intent.get("action_token", "NULL")
            confidence = decoded_intent.get("confidence_score", 0.0)
            lead_time_ms = decoded_intent.get("pre_execution_lead_us", 0) / 1000
            
            # Output a crisp, functional terminal telemetry frame log block
            print(f"⚙️  [PIPE RUNTIME] Intent Isolated: {action_token} | Confidence: {confidence*100:.1f}% | Lead: -{lead_time_ms}ms")
            
        except Exception as e:
            print(f"[Stream Defect] Dropped fragmented network frame: {e}")

if __name__ == "__main__":
    listener = IntentOSCommandLineListener()
    listener.start_ingestion_loop()
