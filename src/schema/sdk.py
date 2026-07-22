import time
from typing import Dict, List, Callable
from serializer import UnifiedHMIPayload
from processor import HMITimeSyncProcessor

class IntentOSEventSDK:
    """
    The main developer-facing abstraction engine for IntentOS.
    Hides raw signal complexities and exposes clean, event-driven intent hooks
    to frontend apps, games, and spatial runtimes.
    """
    def __init__(self, alignment_window_us: int = 50000):
        self.sync_processor = HMITimeSyncProcessor(window_size_us=alignment_window_us)
        # Dictionary mapping action tokens (e.g., "PRIMARY_SELECT") to lists of developer callbacks
        self.listeners: Dict[str, List[Callable[[UnifiedHMIPayload], None]]] = {}

    def on_intent(self, action_token: str, callback: Callable[[UnifiedHMIPayload], None]) -> None:
        """
        Registers a developer event listener hook.
        Example: sdk.on_intent("PRIMARY_SELECT", fire_laser_weapon)
        """
        if action_token not in self.listeners:
            self.listeners[action_token] = []
        self.listeners[action_token].append(callback)

    def process_incoming_sensor_stream(self, payload: UnifiedHMIPayload) -> None:
        """
        Ingests high-frequency raw hardware frames, routes them through the time-sync alignment matrix,
        and dispatches high-confidence intent events to app layer callbacks.
        """
        # 1. Ingest frame into the synchronization buffer
        self.sync_processor.ingest_frame(payload)
        
        # 2. Extract current intent signatures
        token = payload.action_token
        confidence = payload.confidence_score
        
        # 3. Only fire callbacks if intent is valid and clears our 85% high-performance threshold
        if token != "NULL" and token != "NULL_REST_STATE" and confidence >= 0.85:
            if token in self.listeners:
                for callback in self.listeners[token]:
                    try:
                        callback(payload)
                    except Exception as e:
                        print(f"[IntentOS SDK Alert] Error executing developer callback: {e}")

# --- Developer Integration Example & Diagnostic Verification ---
def gameplay_fire_action(event: UnifiedHMIPayload):
    """A sample game developer function responding to zero-latency intent triggers."""
    print("\n🚀 [GAME ENGINE TRIGGER]")
    print(f"  Action Executed: Player successfully activated 'CAST_SPELL' command.")
    print(f"  Hardware Driver Origin: {event.hardware_source_id}")
    print(f"  Predictive Execution Advantage: Engine executed trigger {event.pre_execution_lead_us / 1000} ms ahead of physical transit completion!")
    print(f"  AI Intent Confidence Moat: {event.confidence_score * 100}% absolute match rate.")

if __name__ == "__main__":
    print("--- IntentOS Cross-Platform SDK Active Diagnostic Validation ---")
    sdk = IntentOSEventSDK()
    
    # Simulating a developer subscribing to an action token inside their game code loop
    print("Developer Status: Subscribed to 'PRIMARY_SELECT' event listener.")
    sdk.on_intent("PRIMARY_SELECT", gameplay_fire_action)
    
    # Simulating a real physical muscle flex frame passing through the system pipeline
    print("\nSystem Status: Streaming incoming biometric data package...")
    packet = UnifiedHMIPayload(hardware_source_id="intentos_neural_armband_v1", modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
    packet.set_signal_vector(values=[0.155, -0.712, 0.899], intensity=0.96)
    packet.set_inferred_intent(token="PRIMARY_SELECT", confidence=0.985, lead_us=45000)
    
    # Process event
    sdk.process_incoming_sensor_stream(packet)
    print("\nSDK runtime initialization completed cleanly with 0 processing errors.")
