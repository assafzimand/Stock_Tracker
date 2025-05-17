class CupHandleConfig:
    def __init__(self):
        self.cup_width_min_ratio = 0.07
        self.cup_width_max_ratio = 0.8

        self.handle_width_min_ratio_total = 0.015
        self.handle_width_max_ratio_total = 0.4

        self.min_cup_to_handle_width_ratio = 1.3
        self.max_cup_to_handle_width_ratio = 4.0

        self.handle_depth_ratio_min_vs_cup = 0.05
        self.handle_depth_ratio_max_vs_cup = 0.4

        self.cup_min_position_min = 0.2
        self.cup_min_position_max = 0.8
        self.min_avg_cup_value_vs_ceiling_ratio = 0.025

        self.max_cup_peak_above_rim = 0.025
        self.max_handle_peak_over_ceiling = 0.025

        self.min_cup_depth = 0.075
        self.max_cup_depth = 0.7

        self.min_handle_depth = 0.025

        self.min_left_rim_above_handle_min = 0.0015

        self.max_right_rim_drop_from_left = 0.04
        self.max_right_rim_above_left = 0.06

        self.breakout_tolerance = 0.035
        self.max_breakout_extension_ratio = 0.05
        self.min_handle_recovery_ratio = 0.3

CUP_AND_HANDLE_CONFIG = CupHandleConfig()