import os
import sys
import time
import threading
from client import IntentOSStreamClient
from simulator import HMIVirtualSimulator

# Maintain strict lookups across directory structures
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

class HMIInfrastructureStressTester:
    """
    High-Throughput Concurrency Stress Tester for IntentOS.
    Spins up multiple independent threads to simulate concurrent hardware devices
    spamming the ingestion server, benchmarking throughput limits and package drops.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8888, concurrency_level: int = 5):
        self.host = host
        self.port = port
        self.concurrency_level = concurrency_level
        self.is_running = False
        self.total_frames_sent = 0
        self.counter_lock = threading.Lock()

    def _worker_stream_loop(self, worker_id: int):
        """Simulates a highly reactive, standalone biometric device stream over sockets."""
        client = IntentOSStreamClient(host=self.host, port=self.port)
        if not client.connect():
            print(f"[Stress Tester] Worker-{worker_id} connection link failed.")
            return

        simulator = HMIVirtualSimulator(simulation_device_id=f"stress_peripheral_0{worker_id}")
        local_sent = 0

        while self.is_running:
            try:
                # Toggle fast across heavy muscle contractions and neural signals
                if local_sent % 2 == 0:
                    payload = simulator.generate_mock_emg_flex(intensity_modifier=0.90)
                else:
                    payload = simulator.generate_mock_eeg_focus(concentration_score=0.85)

                # Send raw bytes down socket structures
                client.send_payload(payload)
                local_sent += 1
                
                # Low interval delay to mimic blistering 50Hz streaming rates per device
                time.sleep(0.02)
                
            except Exception:
                break

        client.close()
        with self.counter_lock:
            self.total_frames_sent += local_sent

    def run_benchmark(self, test_duration_seconds: int = 5):
        """Orchestrates concurrent worker threads and computes total processing performance metrics."""
        print(f"🚀 Initializing Concurrency Stress Test Engine...")
        print(f"  ├─ Simulating {self.concurrency_level} Concurrent Hardware Accessories")
        print(f"  └─ Target Execution Window: {test_duration_seconds} Seconds\n")
        
        self.is_running = True
        threads = []

        # Boot up individual thread layers
        for i in range(self.concurrency_level):
            t = threading.Thread(target=self._worker_stream_loop, args=(i+1,), daemon=True)
            threads.append(t)
            t.start()

        # Run benchmark timeline capture window
        start_time = time.time()
        time.sleep(test_duration_seconds)
        self.is_running = False

        # Wait briefly for worker cleanup pipelines to cycle off
        for t in threads:
            t.join(timeout=1.0)

        elapsed_time = time.time() - start_time
        
        print("\n=========================================================")
        print("          INTENTOS INGESTION PERFORMANCE REPORT          ")
        print("=========================================================")
        print(f"Total Stream Processing Time : {elapsed_time:.2f} seconds")
        print(f"Aggregated Telemetry Packets : {self.total_frames_sent} frames successfully sent")
        print(f"System Throughput Performance: {int(self.total_frames_sent / elapsed_time)} frames/second")
        print("=========================================================\n")

if __name__ == "__main__":
    # Expects main.py or server.py to be active on port 8888
    tester = HMIInfrastructureStressTester(concurrency_level=5)
    tester.run_benchmark(test_duration_seconds=5)
