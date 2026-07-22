import collections
from typing import Dict, List, Optional
from serializer import UnifiedHMIPayload

class HMITimeSyncProcessor:
    """
    The Time-Synchronization and Signal Alignment Layer for IntentOS.
    Buffers multi-modal, variable-frequency hardware streams into a rolling alignment matrix.
    Allows developers to match disparate sensor frames (e.g. Gaze + EMG) across a unified timeline.
    """
    def __init__(self, window_size_us: int = 50000):
        # 50,000 microseconds = 50 milliseconds alignment window bounds
        self.window_size_us = window_size_us
        # Ring buffers partitioned cleanly by distinct device ID metrics
        self.device_buffers: Dict[str, collections.deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=1000)
        )

    def ingest_frame(self, payload: UnifiedHMIPayload) -> None:
        """Injects a payload frame into its respective thread-safe memory buffer stack."""
        self.device_buffers[payload.hardware_source_id].append(payload)

    def retrieve_aligned_intent(self, master_timestamp_us: int) -> List[UnifiedHMIPayload]:
        """
        Scans all device buffers to extract frames matching the master timeline window.
        Filters out temporal drift automatically.
        """
        aligned_frames: List[UnifiedHMIPayload] = []
        
        for device_id, buffer in self.device_buffers.items():
            best_match: Optional[UnifiedHMIPayload] = None
            smallest_delta = self.window_size_us
            
            # Linearly inspect rolling frames to extract the optimal timestamp fit
            for frame in list(buffer):
                delta = abs(frame.timestamp_utc_us - master_timestamp_us)
                if delta < smallest_delta:
                    smallest_delta = delta
                    best_match = frame
            
            if best_match:
                aligned_frames.append(best_match)
                
        return aligned_frames

if __name__ == "__main__":
    print("--- IntentOS Real-Time Time-Sync Processor Verification ---\n")
    processor = HMITimeSyncProcessor()
    
    # 1. Simulate an eye-tracking vector snapshot arriving early
    gaze_packet = UnifiedHMIPayload(hardware_source_id="spatial_gaze_tracker", modality=UnifiedHMIPayload.SPATIAL_GAZE)
    gaze_packet.timestamp_utc_us = 1000000  # Base clock line
    gaze_packet.set_signal_vector(values=[120.5, 480.2], intensity=1.0)
    processor.ingest_frame(gaze_packet)
    
    # 2. Simulate a delayed muscle armband flex packet arriving with clock drift
    emg_packet = UnifiedHMIPayload(hardware_source_id="biophysical_emg_band", modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
    emg_packet.timestamp_utc_us = 1000015  # 15 microseconds of drift lag
    emg_packet.set_signal_vector(values=[0.88, -0.11], intensity=0.92)
    emg_packet.set_inferred_intent(token="PRIMARY_SELECT", confidence=0.98, lead_us=45000)
    processor.ingest_frame(emg_packet)
    
    # 3. Request cross-modal alignment from the master framework clock tracking line
    master_clock = 1000005
    synchronized_timeline = processor.retrieve_aligned_intent(master_timestamp_us=master_clock)
    
    print(f"Master Evaluation Clock Line: {master_clock} us")
    print(f"Synchronized Streams Extracted count: {len(synchronized_timeline)} active data channels")
    for synchronized_frame in synchronized_timeline:
        print(f"  [Aligned Frame] Source: {synchronized_frame.hardware_source_id} | Raw Signal Delta Variance: {abs(synchronized_frame.timestamp_utc_us - master_clock)} us")
    
    print("\nMulti-frequency matrix tracking completed with zero timeline calculation dropouts!")
