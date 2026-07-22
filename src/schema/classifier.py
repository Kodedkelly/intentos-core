import os
import sys
from typing import Dict, Any

# Ensure absolute structural tracking maps cleanly
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

class HMIPredictiveClassifier:
    """
    The Machine Learning Inference Engine for IntentOS.
    Consumes real-time streaming sliding-window features (MAV, RMS)
    and maps them to predictive structural human intent action states.
    """
    def __init__(self, emg_threshold: float = 0.65, eeg_threshold: float = 0.70):
        self.emg_threshold = emg_threshold
        self.eeg_threshold = eeg_threshold

    def evaluate_intent(self, modality: int, dsp_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes a real-time linear classifier evaluation over incoming feature maps.
        Returns a dictionary carrying the inferred action token and absolute confidence metrics.
        """
        mav = dsp_features.get("mav", 0.0)
        rms = dsp_features.get("rms", 0.0)
        
        action_token = "NULL_REST_STATE"
        confidence_score = 1.0

        # Modality 1: Biophysical EMG (Muscle tracking)
        if modality == 1: 
            # Using an industry-standard linear combination of energy (MAV) and absolute power (RMS)
            combined_activation = (mav * 0.4) + (rms * 0.6)
            if combined_activation > self.emg_threshold:
                action_token = "PRIMARY_SELECT"
                # Normalize confidence based on over-threshold scaling profiles
                confidence_score = min(0.99, 0.85 + (combined_activation - self.emg_threshold) * 0.2)
            else:
                confidence_score = max(0.50, 1.0 - (combined_activation / self.emg_threshold) * 0.5)

        # Modality 2: Biophysical EEG (Neural focus state)
        elif modality == 2:
            # Neural patterns heavily weigh sudden power distribution spikes (RMS)
            if rms > self.eeg_threshold:
                action_token = "SYSTEM_HEARTBEAT_BOOST"
                confidence_score = min(0.98, 0.80 + (rms - self.eeg_threshold) * 0.3)
            else:
                confidence_score = max(0.50, 1.0 - (rms / self.eeg_threshold) * 0.4)

        return {
            "action_token": action_token,
            "confidence_score": round(confidence_score, 4)
        }

if __name__ == "__main__":
    print("--- IntentOS Predictive Machine Learning Classifier Standalone Verification ---")
    classifier = HMIPredictiveClassifier()
    
    # 1. Simulate a heavy incoming muscle flexion feature set
    mock_emg_features = {"mav": 0.72, "rms": 0.85}
    result_emg = classifier.evaluate_intent(modality=1, dsp_features=mock_emg_features)
    print(f"\n[EMG Evaluation Frame]")
    print(f"  Input Features: {mock_emg_features}")
    print(f"  Predicted Target Intent : \033[92m{result_emg['action_token']}\033[0m (Confidence: {result_emg['confidence_score'] * 100}%)")
    
    # 2. Simulate a calm neural rest state feature set
    mock_eeg_features = {"mav": 0.11, "rms": 0.18}
    result_eeg = classifier.evaluate_intent(modality=2, dsp_features=mock_eeg_features)
    print(f"\n[EEG Evaluation Frame]")
    print(f"  Input Features: {mock_eeg_features}")
    print(f"  Predicted Target Intent : \033[94m{result_eeg['action_token']}\033[0m (Confidence: {result_eeg['confidence_score'] * 100}%)")
