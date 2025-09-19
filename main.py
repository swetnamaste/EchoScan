import time

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


def run_pipeline(input_data, input_type="text", **kwargs):
    """
    Run the complete EchoScan pipeline with framework-aligned enhancements.
    
    Args:
        input_data: Input data (file path for files, string for direct input)
        input_type: Type of input ("text", "file", "multimodal")
        **kwargs: Additional parameters for specific modules
        
    Returns:
        Complete pipeline results with enhanced analysis
    """
    import echoverifier
    from detectors import context_drift, quirk_injection, cross_modal, dynamic_threshold, rolling_reference
    import consensus_voting
    
    # Handle file input
    if input_type == "file":
        try:
            with open(input_data, 'r', encoding='utf-8') as f:
                text_content = f.read()
        except Exception as e:
            return {
                "error": f"Failed to read file: {str(e)}",
                "EchoScore": 0,
                "Decision Label": "Error"
            }
    else:
        text_content = str(input_data)
    
    if not text_content.strip():
        return {
            "error": "Empty input provided",
            "EchoScore": 0,
            "Decision Label": "Error"
        }
    
    # Initialize results container
    pipeline_results = {
        "input_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content,
        "input_length": len(text_content),
        "input_type": input_type
    }
    
    try:
        # Phase 1: Core EchoVerifier analysis
        print("Running EchoVerifier...")
        echoverifier_result = echoverifier.run(text_content, mode="verify")
        pipeline_results["echoverifier"] = echoverifier_result
        
        # Phase 2: Enhanced framework detectors
        print("Running Context Drift analysis...")
        context_result = context_drift.run(text_content)
        pipeline_results["context_drift"] = context_result
        
        print("Running Quirk Injection analysis...")
        quirk_result = quirk_injection.run(text_content)
        pipeline_results["quirk_injection"] = quirk_result
        
        # Phase 3: Cross-modal analysis (if applicable)
        print("Running Cross-Modal analysis...")
        cross_modal_kwargs = {
            "text_data": text_content,
            "audio_data": kwargs.get("audio_data"),
            "image_data": kwargs.get("image_data")
        }
        cross_modal_result = cross_modal.run(**cross_modal_kwargs)
        pipeline_results["cross_modal"] = cross_modal_result
        
        # Phase 4: Rolling reference analysis
        print("Running Rolling Reference analysis...")
        fold_vector = echoverifier_result.get("fold_vector", [])
        metadata = kwargs.get("metadata", {})
        rolling_ref_result = rolling_reference.run(text_content, fold_vector, metadata)
        pipeline_results["rolling_reference"] = rolling_ref_result
        
        # Phase 5: Dynamic thresholding
        print("Running Dynamic Thresholding...")
        try:
            dynamic_result = dynamic_threshold.run(text_content, pipeline_results)
            pipeline_results["dynamic_threshold"] = dynamic_result
        except Exception as e:
            print(f"Dynamic thresholding failed: {e}")
            pipeline_results["dynamic_threshold"] = {"error": str(e)}
        
        # Phase 6: Consensus voting
        print("Running Consensus Voting...")
        try:
            consensus_result = consensus_voting.run(text_content, pipeline_results)
            pipeline_results["consensus_voting"] = consensus_result
        except Exception as e:
            print(f"Consensus voting failed: {e}")
            consensus_result = {
                "consensus_verdict": "Unknown",
                "consensus_confidence": 0.5,
                "error": str(e)
            }
            pipeline_results["consensus_voting"] = consensus_result
        
        # Phase 7: Calculate final EchoScore and decision
        echo_score = calculate_echo_score(pipeline_results)
        decision_label = determine_decision_label(echo_score, consensus_result)
        
        # Phase 8: Update rolling baselines (if authentic)
        if decision_label in ["Authentic", "Human"]:
            dynamic_threshold.update_baselines_from_results(pipeline_results, authentic_verdict=True)
        
        # Compile advisory flags
        advisory_flags = compute_advisory_flags(pipeline_results)
        
        # Final result compilation
        final_result = {
            "EchoScore": echo_score,
            "Decision Label": decision_label,
            "Primary Verdict": consensus_result.get("consensus_verdict", "Unknown"),
            "Confidence": consensus_result.get("consensus_confidence", 0.5),
            "Advisory Flags": advisory_flags,
            "FullResults": pipeline_results,
            "Pipeline Metadata": {
                "modules_run": list(pipeline_results.keys()),
                "processing_timestamp": time.time(),
                "framework_version": "Enhanced_v1.0"
            }
        }
        
        return final_result
        
    except Exception as e:
        return {
            "error": f"Pipeline execution failed: {str(e)}",
            "EchoScore": 0,
            "Decision Label": "Error",
            "PartialResults": pipeline_results
        }


def calculate_echo_score(pipeline_results):
    """Calculate final EchoScore from all pipeline modules."""
    base_score = 50.0  # Starting baseline
    
    # Collect score modifiers and penalties
    total_modifier = 0.0
    total_penalty = 0.0
    
    for module_name, result in pipeline_results.items():
        if isinstance(result, dict):
            modifier = result.get("echo_score_modifier", 0.0)
            penalty = result.get("echo_score_penalty", 0.0)
            
            total_modifier += modifier
            total_penalty += penalty
    
    # Apply modifiers and penalties
    final_score = base_score + total_modifier + total_penalty
    
    # Clamp to valid range [0, 100]
    final_score = max(0, min(100, final_score))
    
    return round(final_score, 2)


def determine_decision_label(echo_score, consensus_result):
    """Determine final decision label based on EchoScore and consensus."""
    consensus_verdict = consensus_result.get("consensus_verdict", "Unknown")
    
    # Priority to consensus verdict for ambiguous cases
    if consensus_verdict == "Ambiguous":
        return "Ambiguous"
    elif "Authentic" in consensus_verdict:
        return "Human" if echo_score >= 60 else "Uncertain"
    elif consensus_verdict in ["Synthetic", "Suspicious"]:
        return "AI" if echo_score <= 40 else "Uncertain"
    else:
        # Fallback to EchoScore-based decision
        if echo_score >= 70:
            return "Human"
        elif echo_score <= 30:
            return "AI"
        else:
            return "Uncertain"