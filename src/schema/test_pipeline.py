import unittest
import struct
import sys
import os

# Ensure the parent directory is in the path for flat imports
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from serializer import UnifiedHMIPayload
from processor import HMITimeSyncProcessor
from dsp import HMISignalFeatureExtractor

class TestIntentOSCoreInfrastructure(unittest.TestCase):
    """
    Automated Test Pipeline for the IntentOS Developer Core.
    Validates structural integrity, memory limits, and mathematical accuracy.
    """

    def test_binary_serialization_layout(self):
        """CRITICAL: Verifies byte alignment contract and string concatenation integrity."""
        # Arrange
        hardware_id = "test_device_alpha_99"
        token = "TEST_INTENT_TRIGGER"
        payload = UnifiedHMIPayload(hardware_source_id=hardware_id, modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
        payload.set_signal_vector(values=[0.55, -0.22, 0.91], intensity=0.88)
        payload.set_inferred_intent(token=token, confidence=0.95, lead_us=30000)

        # Act
        binary_bytes = payload.serialize_binary()

        # Assert: Read Fixed Size Header Metadata (<qiiffiii -> 36 bytes)
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
        self.assertEqual(src_len, len(hardware_id.encode('utf-8')))
        self.assertEqual(tok_len, len(token.encode('utf-8')))

    def test_time_sync_alignment_window(self):
        """VERIFICATION: Guarantees clock-drift cancellation within the 50ms constraint."""
        # Arrange
        processor = HMITimeSyncProcessor(window_size_us=50000) # 50 milliseconds
        master_clock = 5000000

        # Frame 1: Arrives safely within window parameters
        frame_in = UnifiedHMIPayload(hardware_source_id="sensor_1", modality=UnifiedHMIPayload.SPATIAL_GAZE)
        frame_in.timestamp_utc_us = master_clock + 20000 # +20ms drift
        processor.ingest_frame(frame_in)

        # Frame 2: Arrives outside window limits (60ms out)
        frame_out = UnifiedHMIPayload(hardware_source_id="sensor_2", modality=UnifiedHMIPayload.BIOPHYSICAL_EEG)
        frame_out.timestamp_utc_us = master_clock + 60000 # +60ms drift
        processor.ingest_frame(frame_out)

        # Act
        aligned_set = processor.retrieve_aligned_intent(master_timestamp_us=master_clock)

        # Assert
        source_ids = [f.hardware_source_id for f in aligned_set]
        self.assertIn("sensor_1", source_ids, "Sensor 1 must clear the 50ms alignment window threshold.")
        self.assertNotIn("sensor_2", source_ids, "Sensor 2 metrics must be filtered due to extreme latency drift.")

    def test_dsp_rolling_window_math(self):
        """VERIFICATION: Confirms mathematical feature boundaries for MAV and RMS tracking."""
        # Arrange
        extractor = HMISignalFeatureExtractor(window_size=2)
        device_id = "dsp_test"

        # Act
        f1 = extractor.push_signals(device_id, [1.0, -1.0])
        f2 = extractor.push_signals(device_id, [2.0, -2.0])

        # Assert: Combined history matrix = [1.0, -1.0, 2.0, -2.0]
        # MAV = (1 + 1 + 2 + 2) / 4 = 1.5
        # RMS = sqrt((1 + 1 + 4 + 4) / 4) = sqrt(2.5) = 1.5811
        self.assertEqual(f2["mav"], 1.5)
        self.assertAlmostEqual(f2["rms"], 1.5811, places=4)

if __name__ == "__main__":
    unittest.main()
