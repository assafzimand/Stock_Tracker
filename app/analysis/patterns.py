from dataclasses import dataclass

@dataclass
class CupAndHandleConfig:
    min_cup_duration: int = 20        # number of data points
    max_cup_duration: int = 120
    max_handle_duration: int = 20
    max_handle_depth: float = 0.1     # 10% drop from right rim
    symmetry_tolerance: float = 0.2   # max difference ratio between left/right sides
    min_recovery_ratio: float = 0.9   # must recover to 90% of left peak
    min_depth_ratio: float = 0.05     # minimum depth of cup vs peaks


CUP_AND_HANDLE_CONFIG = CupAndHandleConfig()
