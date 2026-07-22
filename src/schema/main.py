import os
import sys
import time

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from server import IntentOSStreamingServer
from client import IntentOSStreamClient
from simulator import HMIVirtualSimulator

def main():
    print("=========================================================")
    print("      INTENTOS ENTERPRISE ORCHESTRATION ENGINE           ")
    print("=========================================================\n")

    server = IntentOSStreamingServer(host="127.0.0.1", port=8888)
    
    def on_predicted_intent_received(event):
        # Extract features injected by our background streaming network server
        dsp_features = getattr(event, 'dsp_features', {"mav": 0.0, "rms": 0.0})
        
        print(f"⚡ [ORCHESTRATOR ALERT — INTENT ROUTED SUCCESSFULLY]")
        print(f"  ├─ Origin Peripheral ID: {event.hardware_source_id}")
        print(f"  ├─ Decoded Action Token: \033[92m{event.action_token}\033[0m")
        print(f"  ├─ Live Feature Extraction: MAV={dsp_features['mav']} | RMS={dsp_features['rms']}")
        print(f"  └─ Lead Execution Buffer: {event.pre_execution_lead_us / 1000} ms ahead of physical completion")
        print("-" * 57)

    server.sdk.on_intent("PRIMARY_SELECT", on_predicted_intent_received)
    server.sdk.on_intent("SYSTEM_HEARTBEAT_BOOST", on_predicted_intent_received)
    
    server.start()
    time.sleep(1)

    client = IntentOSStreamClient(host="127.0.0.1", port=8888)
    if not client.connect():
        print("[Critical Error] Master orchestrator stream link deployment aborted.")
        server.is_running = False
        sys.exit(1)

    simulator = HMIVirtualSimulator(simulation_device_id="intentos_macbook_pro_dev")
    
    print("\n🚀 [SYSTEM RUNTIME READY] Beginning live cross-process simulation pipeline loops.\n")
    
    frame_counter = 0
    try:
        while True:
            frame_counter += 1
            
            if frame_counter % 2 == 0:
                payload = simulator.generate_mock_emg_flex(intensity_modifier=0.92)
            else:
                payload = simulator.generate_mock_eeg_focus(concentration_score=0.88)
            
            client.send_payload(payload)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Keyboard Interrupt caught. Starting graceful runtime teardown protocols...")
    finally:
        client.close()
        server.is_running = False
        print("[IntentOS System Engine] Teardown operations completed cleanly. Execution terminated.")

if __name__ == "__main__":
    main()
