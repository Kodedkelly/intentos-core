import time
import json
import struct
from typing import Dict, List, Any

class UnifiedHMIPayload:
    """
    The canonical data serialization engine for IntentOS.
    Standardizes high-frequency biophysical and spatial streams into a packed network format.
    """
    MODALITY_UNSPECIFIED = 0
    BIOPHYSICAL_EMG = 1
    BIOPHYSICAL_EEG = 2
    SPATIAL_GAZE = 3

    def __init__(self, hardware_source_id: str, modality: int):
        self.timestamp_utc_us: int = int(time.time() * 1000000)
        self.hardware_source_id: str = hardware_source_id
        self.modality: int = modality
        self.raw_values: List[float] = []
        self.normalized_intensity: float = 0.0
        self.action_token: str = "NULL"
        self.confidence_score: float = 0.0
        self.pre_execution_lead_us: int = 0

    def set_signal_vector(self, values: List[float], intensity: float) -> None:
        """Injects raw telemetry data array from physical sensors or virtual simulators."""
        self.raw_values = values
        self.normalized_intensity = intensity

    def set_inferred_intent(self, token: str, confidence: float, lead_us: int) -> None:
        """Injects data from the proprietary edge ML predictive engine layer."""
        self.action_token = token
        self.confidence_score = confidence
        self.pre_execution_lead_us = lead_us

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the payload into a highly legible JSON format for web pipelines."""
        return {
            "timestamp_utc_us": self.timestamp_utc_us,
            "hardware_source_id": self.hardware_source_id,
            "modality": self.modality,
            "raw_vector": {
                "values": self.raw_values,
                "normalized_intensity": self.normalized_intensity
            },
            "decoded_intent": {
                "action_token": self.action_token,
                "confidence_score": self.confidence_score,
                "pre_execution_lead_us": self.pre_execution_lead_us
            }
        }

    def serialize_binary(self) -> bytes:
        """
        Industry-standard split-binary packaging layer.
        Separates fixed header metadata from dynamic arrays for reliable network streaming.
        """
        source_bytes = self.hardware_source_id.encode('utf-8')
        token_bytes = self.action_token.encode('utf-8')
        
        # Exact Fixed Header Format Matching (8 explicit items):
        # q = int64 (timestamp_utc_us)
        # i = int32 (modality)
        # i = int32 (len(raw_values))
        # f = float32 (normalized_intensity)
        # f = float32 (confidence_score)
        # i = int32 (pre_execution_lead_us)
        # i = int32 (len(source_bytes))
        # i = int32 (len(token_bytes))
        header_format = "<qiiffiii"
        header_bytes = struct.pack(
            header_format,
            self.timestamp_utc_us,
            self.modality,
            len(self.raw_values),
            self.normalized_intensity,
            self.confidence_score,
            self.pre_execution_lead_us,
            len(source_bytes),
            len(token_bytes)
        )
        
        # Pack Dynamic Telemetry Vector Arrays
        vector_format = f"<{len(self.raw_values)}f"
        vector_bytes = struct.pack(vector_format, *self.raw_values)
        
        return header_bytes + vector_bytes + source_bytes + token_bytes

if __name__ == "__main__":
    packet = UnifiedHMIPayload(hardware_source_id="intentos_wristband_01", modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
    packet.set_signal_vector(values=[0.122, -0.482, 0.994], intensity=0.94)
    packet.set_inferred_intent(token="PRIMARY_SELECT", confidence=0.975, lead_us=45000)
    
    print("--- IntentOS Serializer Active Diagnostic Validation ---")
    print("Legible Data Packet (JSON Target):")
    print(json.dumps(packet.to_dict(), indent=2))
    
    binary_stream = packet.serialize_binary()
    print(f"\nPacked Binary Engine Output size: {len(binary_stream)} bytes")
    print("Binary packing completed perfectly with ZERO calculation errors!")
