from detectors import sbsm, delta_s, motif, echoarc, nsnl, echocradle, echostamp, glyph, foldback, obelisk, stuttergate, mimetic_drift, voicecradle, ecc_core, ai_drift, collapseglyph
from vault import vault, traceview

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
