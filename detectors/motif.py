"""Motif detector module for EchoScan."""

import numpy as np

def run(stream):
    if len(stream) == 0:
        return {
            "detector": "motif",
            "top_motif": "",
            "repeat_score": 0.0,
            "delta_s": 0.0,
            "echo_score_modifier": 0.0
        }
    
    # Convert to ASCII
    ascii_vals = np.array([ord(c) for c in stream])
    # Detect repeating motifs (3-char substrings)
    motifs = {}
    for i in range(len(stream)-2):
        motif = stream[i:i+3]
        motifs[motif] = motifs.get(motif, 0) + 1
    top_motif = max(motifs, key=motifs.get) if motifs else ""
    repeat_score = motifs[top_motif] / len(stream) if motifs and len(stream) > 0 else 0.0
    # Drift stability (∆S across bases 6–9)
    def digit_sum(n, base): return sum(int(d) for d in np.base_repr(n, base))
    drift_vals = []
    for b in [6,7,8,9]:
        digit_sums = [digit_sum(v, b) for v in ascii_vals]
        if len(digit_sums) > 1:
            drift_vals.append(np.mean(np.abs(np.diff(digit_sums))))
        else:
            drift_vals.append(0.0)
    delta_s = float(np.mean(drift_vals)) if drift_vals else 0.0
    return {
        "detector": "motif",
        "top_motif": top_motif,
        "repeat_score": round(repeat_score, 3),
        "delta_s": round(delta_s, 6),
        "echo_score_modifier": max(0.1, 1 - delta_s) * repeat_score
    }
