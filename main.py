import os
import sys
import json
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Module imports
try:
    import echoverifier
except ImportError:
    echoverifier = None

try:
    from sbsh_module import sbsh_hash
except ImportError:
    sbsh_hash = None


def run_pipeline(input_file_or_text, input_type="text"):
    """
    Run the complete EchoScan detection pipeline on input data.
    
    Args:
        input_file_or_text: Path to input file or direct text input
        input_type: Type of input ('text', 'image', 'audio', 'video')
    
    Returns:
        dict: Complete pipeline results including EchoScore and analysis
    """
    # Read input data
    if os.path.isfile(input_file_or_text):
        with open(input_file_or_text, 'r', encoding='utf-8') as f:
            input_data = f.read()
    else:
        input_data = input_file_or_text
    
    results = {}
    
    # Run EchoVerifier analysis
    if echoverifier:
        try:
            ev_result = echoverifier.run(input_data, mode="verify")
            results["echoverifier"] = ev_result
        except Exception as e:
            results["echoverifier"] = {"error": str(e)}
    
    # Run SBSH symbolic hash
    if sbsh_hash:
        try:
            sbsh_result = sbsh_hash(input_data)
            results["sbsh"] = sbsh_result
        except Exception as e:
            results["sbsh"] = {"error": str(e)}
    
    # Calculate overall EchoScore based on results
    echo_score = calculate_echo_score(results)
    
    # Compute advisory flags
    advisory_flags = compute_advisory_flags(results)
    
    # Determine decision label
    decision_label = determine_decision_label(echo_score, results)
    
    return {
        "EchoScore": echo_score,
        "Decision Label": decision_label,
        "Advisory Flags": advisory_flags,
        "FullResults": results,
        "Timestamp": datetime.now().isoformat(),
        "InputType": input_type
    }


def calculate_echo_score(results):
    """Calculate overall EchoScore from module results."""
    base_score = 50  # Neutral baseline
    
    # EchoVerifier contribution
    if "echoverifier" in results and isinstance(results["echoverifier"], dict):
        ev = results["echoverifier"]
        if "echo_sense" in ev:
            base_score += (ev["echo_sense"] - 0.5) * 30  # Scale echo_sense to influence score
        if ev.get("verdict") == "Authentic":
            base_score += 20
        elif ev.get("verdict") == "Hallucination":
            base_score -= 30
    
    # SBSH contribution (if available)
    if "sbsh" in results and isinstance(results["sbsh"], dict):
        if "delta_s" in results["sbsh"]:
            # Lower delta_s indicates more authentic content
            delta_s = results["sbsh"]["delta_s"]
            if delta_s < 0.01:
                base_score += 10
            elif delta_s > 0.1:
                base_score -= 10
    
    # Ensure score is within 0-100 range
    return max(0, min(100, base_score))


def determine_decision_label(echo_score, results):
    """Determine the overall decision label based on EchoScore and results."""
    if echo_score >= 80:
        return "Authentic"
    elif echo_score >= 60:
        return "Likely Authentic"
    elif echo_score >= 40:
        return "Uncertain"
    elif echo_score >= 20:
        return "Likely Synthetic"
    else:
        return "Synthetic"


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