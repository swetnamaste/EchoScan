from detectors import sbsm, delta_s, motif, echoarc, nsnl, echocradle, echostamp, glyph, foldback, obelisk, stuttergate, mimetic_drift, voicecradle, ecc_core, ai_drift, collapseglyph
from vault.vault import vault
from vault.traceview import traceview
import echoverifier

def normalize_input(input_file, input_type):
    # Placeholder: Add file reading and normalization logic per modality
    with open(input_file, "r", encoding="utf-8") as f:
        return f.read()

def run_pipeline(input_file, input_type, **flags):
    S = normalize_input(input_file, input_type)
    # SBSM is the central stem
    sbsm_result = sbsm.run(S)
    delta_s_result = delta_s.run(S)
    motif_result = motif.run(S)

    # Pass SBSM and motif results to downstream modules
    echoarc_result = echoarc.run(sbsm_result, delta_s_result, motif_result)
    nsnl_result = nsnl.run(S, motif_result, echoarc_result)
    cradle_result = echocradle.run(S, echoarc_result)
    stamp_result = echostamp.run(S, motif_result, sbsm_result, flags.get("time_metadata"))
    glyph_result = glyph.run(S, input_type)
    foldback_result = foldback.run(motif_result)
    obelisk_result = obelisk.run(S, sbsm_result, delta_s_result)
    stuttergate_result = stuttergate.run(S, sbsm_result, delta_s_result)
    mimetic_drift_result = mimetic_drift.run(flags.get("entity_series"))
    voicecradle_result = voicecradle.run(S, input_type)
    ecc_result = ecc_core.run(S, delta_s_result, echoarc_result, sbsm_result)
    ai_drift_result = ai_drift.run(S, delta_s_result, sbsm_result)
    collapseglyph_result = collapseglyph.run(S, delta_s_result, sbsm_result)

    # EchoVerifier firewall validation
    echoverifier_result = echoverifier.run(S, mode="verify")

    # Aggregate scoring, decision, advisory, output
    results = {
        "sbsm": sbsm_result,
        "delta_s": delta_s_result,
        "motif": motif_result,
        "echoarc": echoarc_result,
        "nsnl": nsnl_result,
        "cradle": cradle_result,
        "stamp": stamp_result,
        "glyph": glyph_result,
        "foldback": foldback_result,
        "obelisk": obelisk_result,
        "stuttergate": stuttergate_result,
        "mimetic_drift": mimetic_drift_result,
        "voicecradle": voicecradle_result,
        "ecc": ecc_result,
        "ai_drift": ai_drift_result,
        "collapseglyph": collapseglyph_result,
        "echoverifier": echoverifier_result,
    }

    echo_score = compute_echo_score(results)
    decision_label = compute_decision_label(results, echo_score)
    advisory_flags = compute_advisory_flags(results)
    arcfit = echoarc_result.get("arc_fit", 0)
    ahy = echoarc_result.get("ahy", 0)
    glyphs = glyph_result.get("glyphs", [])
    traceview.write(results)
    vault.log(results)

    output = {
        "EchoScore": echo_score,
        "Decision Label": decision_label,
        "Advisory Flags": advisory_flags,
        "ArcFit": arcfit,
        "AHY": ahy,
        "Glyphs": glyphs,
        "TraceView": traceview.summary(results),
        "VaultRef": vault.last_entry_ref(),
        "FullResults": results
    }
    return output

def compute_echo_score(results):
    # Placeholder: aggregate module scores and penalties
    score = 0.0
    for mod in results:
        mod_res = results[mod]
        if isinstance(mod_res, dict) and "echo_score_penalty" in mod_res:
            score += mod_res["echo_score_penalty"]
        if isinstance(mod_res, dict) and "echo_score_modifier" in mod_res:
            score += mod_res["echo_score_modifier"]
    # Normalize score to range 0.0-5.0
    score = max(0.0, min(5.0, 2.5 + score / 50.0))
    return round(score, 2)

def compute_decision_label(results, echo_score):
    # Placeholder: logic for label based on score and module verdicts
    if echo_score >= 4.2:
        return "Real"
    elif echo_score >= 3.4:
        return "Edited-Real"
    elif echo_score >= 2.2:
        return "Borderline"
    else:
        synth_mods = [m for m in results if results[m] and isinstance(results[m], dict) and results[m].get("source_classification")=="AI-Generated"]
        return "Synthetic" if synth_mods else "Synthetic (Obfuscated or Obvious)"

def compute_advisory_flags(results):
    # Placeholder: collect flags from modules
    flags = []
    for mod in results:
        mod_res = results[mod]
        if isinstance(mod_res, dict) and "advisory_flag" in mod_res:
            flags.append(mod_res["advisory_flag"])
    return flags

def run_echo_verifier(metrics):
    """
    Refines EchoVerifier to produce Authentic / Plausible / Synthetic verdicts 
    based on strict thresholds and mathematical consistency.
    Uses delta_s, echo_fold_sim, glyph_match, and ancestry_depth from metrics for decision logic.
    
    Args:
        metrics (dict): Dictionary containing delta_s, echo_fold_sim, glyph_match, ancestry_depth
        
    Returns:
        str: Verdict - "Authentic", "Plausible", or "Synthetic"
    """
    delta_s = metrics.get('delta_s', 0.0)
    echo_fold_sim = metrics.get('echo_fold_sim', 0.0)
    glyph_match = metrics.get('glyph_match', '')
    ancestry_depth = metrics.get('ancestry_depth', 0)
    
    # Mathematical consistency check - ensure all values are within expected ranges
    if not (0.0 <= delta_s <= 1.0):
        delta_s = max(0.0, min(1.0, delta_s))
    if not (0.0 <= echo_fold_sim <= 1.0):
        echo_fold_sim = max(0.0, min(1.0, echo_fold_sim))
    if ancestry_depth < 0:
        ancestry_depth = 0
        
    # Determine glyph family based on glyph_match pattern
    glyph_family = "standard"
    if isinstance(glyph_match, str):
        if "synthetic" in glyph_match.lower() or "ai" in glyph_match.lower():
            glyph_family = "synthetic"
        elif "hybrid" in glyph_match.lower():
            glyph_family = "hybrid"
    
    # Strict thresholds for authenticity verification (based on EchoVerifier._determine_verdict)
    # Authentic criteria (highest confidence, zero false positives)
    if (delta_s < 0.01 and 
        echo_fold_sim > 0.85 and 
        glyph_family == "standard" and
        ancestry_depth >= 3):
        return "Authentic"
    
    # Synthetic criteria (clear indicators of synthetic content) 
    elif (delta_s > 0.05 or 
          echo_fold_sim < 0.3 or
          glyph_family == "synthetic" or
          ancestry_depth < 2):
        return "Synthetic"
    
    # Plausible (middle ground with mathematical consistency)
    else:
        return "Plausible"

def generate_report(stream_id, metrics, verdict, advisory_flags):
    """
    Outputs a full structured report for EchoScan results, ensuring all reporting is math-backed.
    Logs the report to TraceView and stores it in EchoVault.
    
    Args:
        stream_id (str): Unique identifier for the data stream
        metrics (dict): Dictionary containing verification metrics
        verdict (str): The authenticity verdict (Authentic/Plausible/Synthetic)
        advisory_flags (list): List of advisory flags from analysis
        
    Returns:
        dict: Structured report with mathematical backing
    """
    import time
    import json
    
    # Generate mathematical report with full backing
    report = {
        "stream_id": stream_id,
        "timestamp": time.time(),
        "verdict": verdict,
        "confidence_score": _calculate_confidence_score(metrics, verdict),
        "metrics": {
            "delta_s": metrics.get('delta_s', 0.0),
            "echo_fold_similarity": metrics.get('echo_fold_sim', 0.0),
            "glyph_match": metrics.get('glyph_match', ''),
            "ancestry_depth": metrics.get('ancestry_depth', 0),
            "echo_sense": metrics.get('echo_sense', 0.0)
        },
        "mathematical_validation": {
            "delta_s_valid": 0.0 <= metrics.get('delta_s', 0.0) <= 1.0,
            "fold_similarity_valid": 0.0 <= metrics.get('echo_fold_sim', 0.0) <= 1.0,
            "ancestry_depth_valid": metrics.get('ancestry_depth', 0) >= 0,
            "threshold_analysis": _analyze_thresholds(metrics, verdict)
        },
        "advisory_flags": advisory_flags,
        "vault_eligible": _check_vault_eligibility(metrics),
        "report_version": "1.0.0"
    }
    
    # Log to TraceView for result tracking
    traceview.write({
        "echoscan_report": report,
        "metadata": {
            "report_type": "echoverifier_analysis",
            "processing_pipeline": "run_echo_verifier -> generate_report"
        }
    })
    
    # Store in EchoVault for persistent storage
    vault.log({
        "report": report,
        "stream_processing": {
            "stream_id": stream_id,
            "verdict": verdict,
            "mathematical_backing": True
        }
    })
    
    return report

def _calculate_confidence_score(metrics, verdict):
    """Calculate mathematical confidence score for the verdict."""
    delta_s = metrics.get('delta_s', 0.0)
    echo_fold_sim = metrics.get('echo_fold_sim', 0.0)
    ancestry_depth = metrics.get('ancestry_depth', 0)
    
    # Base confidence calculation with mathematical weighting
    if verdict == "Authentic":
        # High confidence for authentic - strict thresholds met
        confidence = min(1.0, (1.0 - delta_s) * 0.3 + echo_fold_sim * 0.4 + min(ancestry_depth / 10.0, 0.3))
    elif verdict == "Synthetic": 
        # High confidence for synthetic - clear indicators present
        confidence = min(1.0, delta_s * 0.4 + (1.0 - echo_fold_sim) * 0.4 + max(0, (5 - ancestry_depth)) / 10.0 * 0.2)
    else:  # Plausible
        # Medium confidence for plausible - mixed signals
        confidence = 0.5 + abs(echo_fold_sim - 0.5) * 0.3 + abs(delta_s - 0.025) * 0.2
    
    return round(min(1.0, max(0.0, confidence)), 4)

def _analyze_thresholds(metrics, verdict):
    """Analyze how metrics compare to decision thresholds."""
    delta_s = metrics.get('delta_s', 0.0)
    echo_fold_sim = metrics.get('echo_fold_sim', 0.0)
    ancestry_depth = metrics.get('ancestry_depth', 0)
    
    return {
        "delta_s_threshold": {
            "value": delta_s,
            "authentic_threshold": 0.01,
            "synthetic_threshold": 0.05,
            "meets_authentic": delta_s < 0.01,
            "meets_synthetic": delta_s > 0.05
        },
        "echo_fold_threshold": {
            "value": echo_fold_sim,
            "authentic_threshold": 0.85,
            "synthetic_threshold": 0.3,
            "meets_authentic": echo_fold_sim > 0.85,
            "meets_synthetic": echo_fold_sim < 0.3
        },
        "ancestry_threshold": {
            "value": ancestry_depth,
            "authentic_threshold": 3,
            "synthetic_threshold": 2,
            "meets_authentic": ancestry_depth >= 3,
            "meets_synthetic": ancestry_depth < 2
        }
    }

def _check_vault_eligibility(metrics):
    """Check if metrics qualify for vault storage based on mathematical criteria."""
    echo_sense = metrics.get('echo_sense', 0.0)
    ancestry_depth = metrics.get('ancestry_depth', 0)
    
    # Based on EchoVerifier._check_vault_permission logic
    return echo_sense > 0.5 and ancestry_depth >= 2
