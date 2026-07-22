import os

class IntentOSConfig:
    """
    The Single Source of Truth Configuration Blueprint for IntentOS.
    Consolidates network layers, data constraints, ML weights, and pipeline paths
    to ensure predictable enterprise infrastructure operations.
    """
    # Network Layer Settings
    GATEWAY_HOST: str = os.getenv("INTENTOS_HOST", "127.0.0.1")
    GATEWAY_PORT: int = int(os.getenv("INTENTOS_PORT", 8888))
    
    # Timing & Alignment Constraints
    TIME_SYNC_WINDOW_US: int = int(os.getenv("INTENTOS_SYNC_WINDOW_US", 50000)) # 50ms
    BUFFER_MAX_LEN: int = int(os.getenv("INTENTOS_BUFFER_MAX_LEN", 1000))
    
    # Digital Signal Processing Properties
    DSP_SLIDING_WINDOW_SIZE: int = int(os.getenv("INTENTOS_DSP_WINDOW", 10))
    
    # Core Machine Learning Classifications
    DEFAULT_EMG_ACTIVATION_THRESHOLD: float = float(os.getenv("INTENTOS_EMG_THRESH", 0.65))
    DEFAULT_EEG_ACTIVATION_THRESHOLD: float = float(os.getenv("INTENTOS_EEG_THRESH", 0.70))
    AI_CONFIDENCE_PASS_FLOOR: float = float(os.getenv("INTENTOS_CONF_FLOOR", 0.85))
    
    # Cold Storage Properties
    DATA_MOAT_DIR: str = os.getenv("INTENTOS_STORAGE_DIR", "data_moat")
    STREAM_FILE_EXTENSION: str = ".ihmi"

    @classmethod
    def print_runtime_profile(cls) -> None:
        """Outputs an institutional diagnostic breakdown of active engine configurations."""
        print("--- IntentOS Active System Runtime Configuration Profile ---")
        print(f"  ├─ Network Target      : {cls.GATEWAY_HOST}:{cls.GATEWAY_PORT}")
        print(f"  ├─ Alignment Constraint: {cls.TIME_SYNC_WINDOW_US / 1000} ms Max Drift")
        print(f"  ├─ DSP Processing Depth: Rolling {cls.DSP_SLIDING_WINDOW_SIZE} Sample Frames")
        print(f"  ├─ Edge ML Sensitivity : EMG={cls.DEFAULT_EMG_ACTIVATION_THRESHOLD} | EEG={cls.DEFAULT_EEG_ACTIVATION_THRESHOLD}")
        print(f"  └─ Cold Ledger Directory: {cls.DATA_MOAT_DIR}/")

if __name__ == "__main__":
    IntentOSConfig.print_runtime_profile()
