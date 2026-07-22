import sqlite3
import os
import sys
import json
from config import IntentOSConfig
from serializer import UnifiedHMIPayload

# Ensure absolute structural tracking layout is preserved
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

class IntentOSDataStore:
    """
    The Relational Data Moat Engine for IntentOS.
    Binds to the core platform pipeline to write multi-modal human intent telemetry
    straight into an indexed local datastore file, locking in the enterprise data moat.
    """
    def __init__(self, database_name: str = "intentos_data_moat.db"):
        self.db_path = os.path.join(IntentOSConfig.DATA_MOAT_DIR, database_name)
        
        # Ensure the cold storage target directory physically exists on disk
        if not os.path.exists(IntentOSConfig.DATA_MOAT_DIR):
            os.makedirs(IntentOSConfig.DATA_MOAT_DIR)
            
        self._initialize_relational_tables()

    def _initialize_relational_tables(self) -> None:
        """Creates the canonical telemetry mapping table structures with accelerated index keys."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hmi_telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc_us INTEGER NOT NULL,
                    hardware_source_id TEXT NOT NULL,
                    modality INTEGER NOT NULL,
                    action_token TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    pre_execution_lead_us INTEGER NOT NULL,
                    dsp_features_json TEXT
                )
            """)
            # Generate accelerated database index filters for timeline matrix querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON hmi_telemetry_logs(timestamp_utc_us)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_action ON hmi_telemetry_logs(action_token)")
            conn.commit()

    def commit_telemetry_payload(self, payload: UnifiedHMIPayload) -> None:
        """Serializes and logs an incoming multi-modal data frame directly to deep relational storage."""
        dsp_features = getattr(payload, 'dsp_features', {"mav": 0.0, "rms": 0.0})
        features_serialized = json.dumps(dsp_features)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hmi_telemetry_logs (
                    timestamp_utc_us, hardware_source_id, modality, 
                    action_token, confidence_score, pre_execution_lead_us, dsp_features_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                payload.timestamp_utc_us,
                payload.hardware_source_id,
                payload.modality,
                payload.action_token,
                payload.confidence_score,
                payload.pre_execution_lead_us,
                features_serialized
            ))
            conn.commit()

    def extract_metrics_summary(self) -> None:
        """Diagnostic helper that executes a statistical lookup query across historical records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), AVG(confidence_score) FROM hmi_telemetry_logs")
            total_records, avg_confidence = cursor.fetchone()
            print("\n=========================================================")
            # Bold visual text output to format our local ledger tracking
            print("         INTENTOS SECURE DATASTORE LOG LEDGER            ")
            print("=========================================================")
            print(f"Stored Telemetry Database File: {self.db_path}")
            print(f"Total Logged Interaction Rows : {total_records or 0} frames successfully saved")
            print(f"Aggregated Intent Precision   : {((avg_confidence or 0.0) * 100):.2f}% mean match score")
            print("=========================================================\n")

if __name__ == "__main__":
    print("--- IntentOS Relational Datastore Diagnostics ---")
    store = IntentOSDataStore()
    
    # Mock up a sample intent payload structure to verify transaction loops pass
    packet = UnifiedHMIPayload(hardware_source_id="test_periph_datastore", modality=UnifiedHMIPayload.BIOPHYSICAL_EMG)
    packet.set_inferred_intent(token="PRIMARY_SELECT", confidence=0.942, lead_us=45000)
    packet.dsp_features = {"mav": 0.612, "rms": 0.741}
    
    store.commit_telemetry_payload(packet)
    store.extract_metrics_summary()
