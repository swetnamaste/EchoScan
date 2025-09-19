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
    """
    Refined decision label computation based on echo_score, module verdicts, and detection patterns.
    
    Uses multi-tier analysis combining:
    - Echo score thresholds
    - Module source classifications
    - EchoVerifier verdict integration
    - Anomaly detection patterns
    """
    # Collect module classifications for analysis
    ai_generated_modules = []
    questionable_modules = []
    human_generated_modules = []
    
    for module_name, module_result in results.items():
        if isinstance(module_result, dict):
            source_class = module_result.get("source_classification")
            if source_class == "AI-Generated":
                ai_generated_modules.append(module_name)
            elif source_class == "Questionable":
                questionable_modules.append(module_name)
            elif source_class == "Human-Generated":
                human_generated_modules.append(module_name)
    
    # Integrate EchoVerifier verdict if available
    echoverifier_verdict = None
    if "echoverifier" in results and isinstance(results["echoverifier"], dict):
        echoverifier_verdict = results["echoverifier"].get("verdict")
    
    # Enhanced decision logic with multi-factor analysis
    # High confidence Real (stringent criteria)
    if (echo_score >= 4.2 and 
        len(ai_generated_modules) == 0 and 
        len(human_generated_modules) >= 2 and
        echoverifier_verdict in ["Authentic", None]):  # None means no contradictory evidence
        return "Real"
    
    # High confidence Synthetic (clear synthetic indicators)
    elif (echo_score <= 1.5 or 
          len(ai_generated_modules) >= 2 or
          echoverifier_verdict == "Hallucination"):
        if len(ai_generated_modules) >= 2:
            return "Synthetic"
        else:
            return "Synthetic (Obfuscated or Obvious)"
    
    # Edited-Real (modified authentic content)
    elif (3.4 <= echo_score < 4.2 and
          len(ai_generated_modules) <= 1 and
          len(questionable_modules) <= 2 and
          echoverifier_verdict in ["Plausible", "Authentic", None]):
        return "Edited-Real"
    
    # Borderline (uncertain classification)
    elif (2.2 <= echo_score < 3.4 or
          len(questionable_modules) >= 2 or
          echoverifier_verdict == "Plausible"):
        return "Borderline"
    
    # Default to Synthetic for remaining low-score cases
    else:
        return "Synthetic" if ai_generated_modules else "Synthetic (Obfuscated or Obvious)"

def compute_advisory_flags(results):
    """
    Refined advisory flag computation with comprehensive flag collection and categorization.
    
    Collects and categorizes flags from all modules into:
    - Critical flags (require immediate attention)
    - Warning flags (suspicious patterns)
    - Info flags (general observations)
    """
    critical_flags = []
    warning_flags = []
    info_flags = []
    
    for module_name, module_result in results.items():
        if isinstance(module_result, dict):
            # Direct advisory flags from modules
            if "advisory_flag" in module_result:
                flag = module_result["advisory_flag"]
                # Categorize flags based on content
                if any(keyword in flag.lower() for keyword in ["synthetic", "extreme", "suspicious", "anomaly"]):
                    critical_flags.append(flag)
                elif any(keyword in flag.lower() for keyword in ["borderline", "elevated", "questionable"]):
                    warning_flags.append(flag)
                else:
                    info_flags.append(flag)
            
            # Generate flags based on module results
            source_class = module_result.get("source_classification")
            if source_class == "AI-Generated":
                critical_flags.append(f"{module_name.upper()}: AI-generated content detected")
            elif source_class == "Questionable":
                warning_flags.append(f"{module_name.upper()}: Content authenticity questioned")
            
            # Check for significant penalties or modifiers
            penalty = module_result.get("echo_score_penalty", 0)
            modifier = module_result.get("echo_score_modifier", 0)
            
            if penalty <= -10:
                critical_flags.append(f"{module_name.upper()}: Severe authenticity penalty applied")
            elif penalty <= -5:
                warning_flags.append(f"{module_name.upper()}: Moderate authenticity penalty applied")
            elif modifier >= 5:
                info_flags.append(f"{module_name.upper()}: Authenticity bonus applied")
    
    # Special handling for EchoVerifier results
    if "echoverifier" in results:
        ev_result = results["echoverifier"]
        if isinstance(ev_result, dict):
            verdict = ev_result.get("verdict")
            if verdict == "Hallucination":
                critical_flags.append("ECHOVERIFIER: Hallucination detected")
            elif verdict == "Plausible":
                warning_flags.append("ECHOVERIFIER: Content classified as plausible")
            elif verdict == "Authentic":
                info_flags.append("ECHOVERIFIER: Content verified as authentic")
            
            # Check vault permission
            vault_perm = ev_result.get("vault_permission", False)
            if not vault_perm:
                warning_flags.append("ECHOVERIFIER: Vault access denied")
    
    # Combine flags in priority order: Critical -> Warning -> Info
    all_flags = critical_flags + warning_flags + info_flags
    
    # Remove duplicates while preserving order
    seen = set()
    unique_flags = []
    for flag in all_flags:
        if flag not in seen:
            unique_flags.append(flag)
            seen.add(flag)
    
    return unique_flags
