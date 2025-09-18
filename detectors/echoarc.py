"""EchoArc detector module."""

def run(sbsm_result, delta_s_result, motif_result):
    """Run EchoArc analysis."""
    return {
        "arc_fit": 0.5,
        "ahy": 0.3,
        "echo_score_modifier": 0.0
    }
