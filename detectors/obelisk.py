"""Obelisk detector module for EchoScan."""

import numpy as np

def run(stream, sbsm_result=None, delta_s_result=None):
    # Symmetry check (mirror about center)
    half = len(stream) // 2
    left, right = stream[:half], stream[-half:][::-1]
    if half > 0:
        symmetry_score = sum(1 for i in range(half) if left[i] == right[i]) / half
    else:
        symmetry_score = 0.0
    # Entropy calculation
    ascii_vals = np.array([ord(c) for c in stream])
    unique_chars = set(stream)
    probs = [list(stream).count(ch)/len(stream) for ch in unique_chars if len(stream) > 0]
    entropy = float(-sum([p * np.log2(p) for p in probs if p > 0])) if probs else 0.0
    return {
        "detector": "obelisk",
        "symmetry_score": round(symmetry_score, 3),
        "entropy": round(entropy, 3),
        "echo_score_modifier": (symmetry_score * 0.7) + (1 / (1 + entropy)) * 0.3
    }