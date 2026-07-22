import os

class IntentOSConfig:
    """
    The Single Source of Truth Configuration Blueprint for IntentOS (AAC Wedge Edition).
    Consolidates network parameters, assistive thresholds, and pipeline paths
    to protect multi-vendor accessibility interface software loops.
    """
    # Network Layer Settings
    GATEWAY_HOST: str = os.getenv("INTENTOS_HOST", "127.0.0.1")
    GATEWAY_PORT: int = int(os.getenv("INTENTOS_PORT", 8888))
    
    # Timing & Alignment Constraints
    TIME_SYNC_WINDOW_US: int = int(os.getenv("INTENTOS_SYNC_WINDOW_US", 50000)) # 50ms
    BUFFER_MAX_LEN: int = int(os.getenv("INTENTOS_BUFFER_MAX_LEN", 1000))
    
    # Digital Signal Processing Properties
    DSP_SLIDING_WINDOW_SIZE: int = int(os.getenv("INTENTOS_DSP_WINDOW", 15)) # Deep window for noise reduction
    
    # Assistive HMI Intent Mapping Thresholds (Safety Critical Constraints)
    # Higher confidence requirements filter out spastic tremors and false clicks
    DEFAULT_EYE_GAZE_ACTIVATION_THRESHOLD: float = float(os.getenv("INTENTOS_GAZE_THRESH", 0.70))
    DEFAULT_SWITCH_ACTIVATION_THRESHOLD: float = float(os.getenv("INTENTOS_SWITCH_THRESH", 0.60))
    AI_CONFIDENCE_PASS_FLOOR: float = float(os.getenv("INTENTOS_CONF_FLOOR", 0.90)) # Strict 90% floor
    
    # Cold Storage Properties
    DATA_MOAT_DIR: str = os.getenv("INTENTOS_STORAGE_DIR", "data_moat")
    STREAM_FILE_EXTENSION: str = ".ihmi"

    @classmethod
    def print_runtime_profile(cls) -> None:
        """Outputs an institutional diagnostic breakdown of active assistive configurations."""
        print("=========================================================")
        print("     INTENTOS CORE ACCESSIBILITY ACC DESIGN MODULE       ")
        print("=========================================================")
        print(f"  ├─ Active Gateway Network : {cls.GATEWAY_HOST}:{cls.GATEWAY_PORT}")
        print(f"  ├─ Temporal Sync Matrix   : Rolling {cls.TIME_SYNC_WINDOW_US / 1000} ms Max Drift")
        print(f"  ├─ Tremor Filtering Depth : Sliding {cls.DSP_SLIDING_WINDOW_SIZE} Sample Buffer")
        print(f"  └─ Safety Confidence Floor: Strict {cls.AI_CONFIDENCE_PASS_FLOOR * 100}% Verification Gate")
