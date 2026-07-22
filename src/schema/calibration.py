import os
import sys
import numpy as np
from typing import List, Dict, Any

# Ensure absolute structural path tracking
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

class HMIDeviceCalibrator:
    """
    The Adaptive Baseline Calibration Engine for IntentOS.
    Captures raw rest and peak exertion states to dynamically compute 
    customized ML threshold targets tailored to an individual user's biology.
    """
    def __init__(self):
        self.rest_samples: List[float] = []
        self.peak_samples: List[float] = []
        self.is_calibrated = False
        self.computed_thresholds: Dict[str, float] = {"noise_floor": 0.15, "activation_trigger": 0.65}

    def collect_calibration_sample(self, raw_values: List[float], state_mode: str) -> None:
        """
        Ingests high-frequency metrics into matching calibration buffer slots.
        state_mode options: 'REST' or 'PEAK'
        """
        # Compress the incoming multi-channel matrix frame using its Root Mean Square (RMS) power profile
        frame_power = float(np.sqrt(np.mean(np.square(raw_values)))) if raw_values else 0.0
        
        if state_mode.upper() == "REST":
            self.rest_samples.append(frame_power)
        elif state_mode.upper() == "PEAK":
            self.peak_samples.append(frame_power)

    def finalize_user_profile(self) -> Dict[str, float]:
        """
        Processes collected biological signals and calculates tailored ML activation thresholds.
        """
        if not self.rest_samples or not self.peak_samples:
            print("[IntentOS Calibration Warning] Insufficient sample sizes. Falling back to platform defaults.")
            return self.computed_thresholds

        # Calculate absolute statistics using numpy array blocks
        noise_floor = float(np.percentile(self.rest_samples, 95)) # 95th percentile filters out baseline noise
        max_exertion = float(np.percentile(self.peak_samples, 90)) # 90th percentile maps true continuous muscle flexes

        # Stanford/Industry standard trigger calibration: set activation halfway between rest and peak
        activation_trigger = noise_floor + ((max_exertion - noise_floor) * 0.5)

        # Enforce technical bounds constraints
        self.computed_thresholds = {
            "noise_floor": round(max(0.05, noise_floor), 4),
            "activation_trigger": round(min(0.95, max(0.20, activation_trigger)), 4)
        }
        self.is_calibrated = True
        return self.computed_thresholds

if __name__ == "__main__":
    print("--- IntentOS Personalization Calibration Engine Verification ---")
    calibrator = HMIDeviceCalibrator()

    print("\n1. Simulating 3 seconds of a user resting their arm (Baseline Noise Input)...")
    for _ in range(50):
        # Small chaotic micro-voltages representing ambient muscle noise
        calibrator.collect_calibration_sample([0.02, -0.04, 0.09], state_mode="REST")

    print("2. Simulating 3 seconds of a user intentionally clenching their fist (Peak Input)...")
    for _ in range(50):
        # Heavy voltage bursts representing absolute intentional physical action
        calibrator.collect_calibration_sample([0.65, -0.88, 0.94], state_mode="PEAK")

    profile = calibrator.finalize_user_profile()
    print("\n=========================================================")
    print("          CALIBRATION PROFILE COMPILATION COMPLETE       ")
    print("=========================================================")
    print(f"Computed Custom User Noise Floor  : {profile['noise_floor']} RMS")
    print(f"Computed Custom ML Trigger Target : \033[92m{profile['activation_trigger']}\033[0m RMS")
    print("=========================================================\n")
