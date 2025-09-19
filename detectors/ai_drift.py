"""AI Drift Detector Module"""

import numpy as np

def run(stream, delta_s_result=None, sbsm_result=None):
    if len(stream) == 0:
        return {
            "detector": "ai_drift",
            "drift_variance": 0.0,
            "verdict": "AI-like drift",
            "echo_score_modifier": 1.0
        }
    
    ascii_vals = np.array([ord(c) for c in stream])
    # Drift across bases 6–9
    def digit_sum(n, base): return sum(int(d) for d in np.base_repr(n, base))
    drift_profiles = []
    for b in [6,7,8,9]:
        profile = [digit_sum(v, b) for v in ascii_vals]
        drift_profiles.append(profile)
    
    # Calculate variance of differences, handle cases where there's not enough data
    variances = []
    for profile in drift_profiles:
        if len(profile) > 1:
            diff_profile = np.diff(profile)
            variances.append(np.var(diff_profile))
        else:
            variances.append(0.0)
    
    drift_var = float(np.mean(variances)) if variances else 0.0
    # High variance indicates unstable human-like stream,
    # Low variance (flat drift) indicates synthetic AI filler.
    if drift_var < 0.15:
        verdict = "AI-like drift"
    else:
        verdict = "Human-like drift"
    return {
        "detector": "ai_drift",
        "drift_variance": round(drift_var, 5),
        "verdict": verdict,
        "echo_score_modifier": 1 - drift_var if drift_var < 1 else 0.0
    }