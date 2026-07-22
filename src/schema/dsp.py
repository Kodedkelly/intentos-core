import math
from collections import deque
from typing import List, Dict

class HMISignalFeatureExtractor:
    """
    The Digital Signal Processing (DSP) Engine for IntentOS.
    Maintains a rolling sliding window over incoming raw sensor vectors to extract
    mathematical features (MAV, RMS) needed to drive predictive machine learning inferences.
    """
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        # Dictionary of rolling windows partitioned cleanly by device ID
        self.signal_history: Dict[str, deque] = {}

    def push_signals(self, hardware_source_id: str, raw_values: List[float]) -> Dict[str, float]:
        """
        Pushes new raw signal floats into the device window and computes rolling DSP features.
        Returns a dictionary of calculated features (Mean Absolute Value and Root Mean Square).
        """
        if hardware_source_id not in self.signal_history:
            self.signal_history[hardware_source_id] = deque(maxlen=self.window_size)
            
        # Append the latest multichannel hardware vector to our history block
        self.signal_history[hardware_source_id].append(raw_values)
        
        # Pull history state to execute window calculations
        history_snapshot = list(self.signal_history[hardware_source_id])
        
        # Flatten all values currently inside the active window matrix to calculate features
        all_window_samples = [val for sample in history_snapshot for val in sample]
        
        if not all_window_samples:
            return {"mav": 0.0, "rms": 0.0}
            
        # 1. Compute Mean Absolute Value (MAV)
        absolute_sum = sum(abs(x) for x in all_window_samples)
        mav = absolute_sum / len(all_window_samples)
        
        # 2. Compute Root Mean Square (RMS)
        squared_sum = sum(x ** 2 for x in all_window_samples)
        rms = math.sqrt(squared_sum / len(all_window_samples))
        
        return {
            "mav": round(mav, 4),
            "rms": round(rms, 4)
        }

if __name__ == "__main__":
    print("--- IntentOS DSP Feature Extractor Standalone Verification ---")
    extractor = HMISignalFeatureExtractor(window_size=5)
    
    # Simulate a stream of 3 raw chaotic muscular electrode pulses
    device_id = "test_armband_sensor"
    simulated_frames = [
        [0.12, -0.45, 0.78],
        [0.22, -0.31, 0.91],
        [-0.05, 0.15, 0.64]
    ]
    
    for idx, raw_frame in enumerate(simulated_frames):
        features = extractor.push_signals(device_id, raw_frame)
        print(f"\n[DSP Frame Window Update #{idx + 1}]")
        print(f"  Ingested Raw Signals: {raw_frame}")
        print(f"  Extracted Features   : MAV={features['mav']} | RMS={features['rms']}")
