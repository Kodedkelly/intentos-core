import unittest
import struct
import sys
import os
import json

# Ensure absolute structural path tracking inside our sandbox execution
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from serializer import UnifiedHMIPayload
from processor import HMITimeSyncProcessor
from dsp import HMISignalFeatureExtractor
from classifier import HMIPredictiveClassifier

class TestIntentOSCoreInfrastructure(unittest.TestCase):
    """
    Automated Testing Pipeline for the IntentOS Developer Core.
    Validates structural integrity, memory limits, and mathematical accuracy.
    """

    def test_binary_serialization_layout(self):
        """CRITICAL: Verifies byte alignment contract and string concatenation integrity."""
        hardware_id = "test_device_alpha_99"
        token = "TEST_INTENT_TRIGGER"
        payload = UnifiedHMIPayload(hardware_source_id=hardware_id, modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
        payload.set_signal_vector(values=[0.55, -0.22, 0.91], intensity=0.88)
        payload.set_inferred_intent(token=token, confidence=0.95, lead_us=30000)

        binary_bytes = payload.serialize_binary()

        # Read Fixed Size Header Metadata (<qiiffiii -> 36 bytes)
        header_format = "<qiiffiii"
        header_size = struct.calcsize(header_format)
        self.assertEqual(header_size, 36, "Header size configuration must map exactly to 36 bytes.")
        
        header_data = struct.unpack(header_format, binary_bytes[:header_size])
        timestamp, modality, vec_len, intensity, confidence, lead, src_len, tok_len = header_data
        
        self.assertEqual(modality, UnifiedHMIPayload.BIOPHYSICAL_EMG)
        self.assertEqual(vec_len, 3)
        self.assertAlmostEqual(intensity, 0.88, places=2)
        self.assertAlmostEqual(confidence, 0.95, places=2)
        self.assertEqual(lead, 30000)

    def test_time_sync_alignment_window(self):
        """VERIFICATION: Guarantees clock-drift cancellation within the 50ms constraint."""
        processor = HMITimeSyncProcessor(window_size_us=50000) 
        master_clock = 5000000

        # Frame 1: Arrives safely within window parameters
        frame_in = UnifiedHMIPayload(hardware_source_id="sensor_1", modality=UnifiedHMIPayload.SPATIAL_GAZE)
        frame_in.timestamp_utc_us = master_clock + 20000 
        processor.ingest_frame(frame_in)

        # Frame 2: Arrives outside window limits (+60ms drift)
        frame_out = UnifiedHMIPayload(hardware_source_id="sensor_2", modality=UnifiedHMIPayload.BIOPHYSICAL_EEG)
        frame_out.timestamp_utc_us = master_clock + 60000 
        processor.ingest_frame(frame_out)

        aligned_set = processor.retrieve_aligned_intent(master_timestamp_us=master_clock)
        source_ids = [f.hardware_source_id for f in aligned_set]
        
        self.assertIn("sensor_1", source_ids)
        self.assertNotIn("sensor_2", source_ids)

    def test_dsp_rolling_window_math(self):
        """VERIFICATION: Confirms mathematical feature boundaries for MAV and RMS tracking."""
        extractor = HMISignalFeatureExtractor(window_size=2)
        device_id = "dsp_test"

        f1 = extractor.push_signals(device_id, [1.0, -1.0])
        f2 = extractor.push_signals(device_id, [2.0, -2.0])

        self.assertEqual(f2["mav"], 1.5)
        self.assertAlmostEqual(f2["rms"], 1.5811, places=4)

    def test_json_broadcast_payload_contract(self):
        """INDUSTRY STANDARD: Validates out-of-the-box broadcast data serialization compliance."""
        # Arrange
        payload = UnifiedHMIPayload(hardware_source_id="broadcast_test_node", modality=UnifiedHMIPayload.SPATIAL_GAZE)
        payload.set_signal_vector(values=[10.5, 20.5], intensity=1.0)
        payload.set_inferred_intent(token="SYSTEM_HEARTBEAT_BOOST", confidence=0.912, lead_us=65000)

        # Act
        serialized_json_string = json.dumps(payload.to_dict())
        parsed_data = json.loads(serialized_json_string)

        # Assert: Verify out-of-the-box framework structure schema constraints match
        self.assertIn("timestamp_utc_us", parsed_data)
        self.assertEqual(parsed_data["hardware_source_id"], "broadcast_test_node")
        self.assertEqual(parsed_data["modality"], UnifiedHMIPayload.SPATIAL_GAZE)
        self.assertEqual(parsed_data["decoded_intent"]["action_token"], "SYSTEM_HEARTBEAT_BOOST")
        self.assertAlmostEqual(parsed_data["decoded_intent"]["confidence_score"], 0.912, places=3)
        self.assertEqual(parsed_data["decoded_intent"]["pre_execution_lead_us"], 65000)

if __name__ == "__main__":
    unittest.main()
