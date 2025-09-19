"""Enhanced EchoArc detector module with EchoFold + SDS-1 DNA arcs integration."""

import numpy as np
import math
from typing import Dict, List, Any, Optional


def generate_echofold_vector(input_data: str, context_hash: str = "") -> List[float]:
    """Generate EchoFold vector from input and optional context hash."""
    vec = []
    combined = input_data + context_hash
    for i in range(16):  # 16-dimensional vector
        val = sum(ord(c) * (i + 1) for c in combined[i::16]) / max(1, len(combined))
        vec.append(round(val / 255.0, 6))  # Normalize to [0,1]
    return vec


def calculate_arc_trajectories(vector: List[float]) -> Dict[str, Any]:
    """Calculate arc trajectories from EchoFold vector."""
    if len(vector) < 4:
        return {"trajectory_valid": False, "arc_strength": 0.0}
    
    # Calculate trajectory curvature using sequential triplets
    curvatures = []
    for i in range(len(vector) - 2):
        p1, p2, p3 = vector[i], vector[i+1], vector[i+2]
        
        # Calculate curvature approximation
        if p1 != p3:  # Avoid division by zero
            curvature = abs(2 * (p2 - (p1 + p3) / 2)) / max(0.001, abs(p3 - p1))
            curvatures.append(curvature)
    
    avg_curvature = np.mean(curvatures) if curvatures else 0.0
    arc_strength = min(1.0, avg_curvature * 2)  # Normalize to [0,1]
    
    # Detect arc patterns (valleys and peaks)
    valleys = []
    peaks = []
    for i in range(1, len(vector) - 1):
        if vector[i] < vector[i-1] and vector[i] < vector[i+1]:
            valleys.append(i)
        elif vector[i] > vector[i-1] and vector[i] > vector[i+1]:
            peaks.append(i)
    
    return {
        "trajectory_valid": len(curvatures) > 0,
        "arc_strength": round(arc_strength, 6),
        "average_curvature": round(avg_curvature, 6),
        "valley_count": len(valleys),
        "peak_count": len(peaks),
        "symmetry_score": round(abs(len(valleys) - len(peaks)) / max(1, len(valleys) + len(peaks)), 3)
    }


def analyze_sds1_dna_compatibility(input_data: str, echofold_vector: List[float]) -> Dict[str, Any]:
    """Analyze SDS-1 DNA sequence compatibility with EchoFold patterns."""
    
    # DNA mapping based on character properties
    dna_map = {'A': 0.0, 'T': 0.33, 'G': 0.67, 'C': 1.0}
    dna_sequence = ""
    dna_vector = []
    
    for char in input_data.lower():
        if char in 'aeiou':
            dna_sequence += 'A'
            dna_vector.append(0.0)
        elif char.isalpha():
            dna_sequence += 'T'
            dna_vector.append(0.33)
        elif char.isdigit():
            dna_sequence += 'G'
            dna_vector.append(0.67)
        else:
            dna_sequence += 'C'
            dna_vector.append(1.0)
    
    # Resample DNA vector to match EchoFold dimensions
    if len(dna_vector) > 16:
        # Downsample by averaging chunks
        chunk_size = len(dna_vector) // 16
        resampled_dna = []
        for i in range(16):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < 15 else len(dna_vector)
            chunk_avg = np.mean(dna_vector[start_idx:end_idx])
            resampled_dna.append(chunk_avg)
        dna_vector = resampled_dna
    elif len(dna_vector) < 16:
        # Upsample by interpolation
        dna_vector = np.interp(np.linspace(0, 1, 16), 
                              np.linspace(0, 1, len(dna_vector)), 
                              dna_vector).tolist()
    
    # Calculate compatibility metrics
    compatibility_score = 0.0
    if len(echofold_vector) == len(dna_vector):
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(echofold_vector, dna_vector))
        norm1 = math.sqrt(sum(a * a for a in echofold_vector))
        norm2 = math.sqrt(sum(b * b for b in dna_vector))
        
        if norm1 > 0 and norm2 > 0:
            compatibility_score = dot_product / (norm1 * norm2)
    
    # Analyze base composition
    base_counts = {base: dna_sequence.count(base) for base in 'ATGC'}
    total_bases = len(dna_sequence)
    base_ratios = {base: count / max(1, total_bases) for base, count in base_counts.items()}
    
    # Calculate GC content (important metric in genetics)
    gc_content = (base_counts['G'] + base_counts['C']) / max(1, total_bases)
    
    return {
        "dna_sequence_length": len(dna_sequence),
        "compatibility_score": round(compatibility_score, 6),
        "base_composition": base_ratios,
        "gc_content": round(gc_content, 3),
        "dominant_base": max(base_counts, key=base_counts.get) if dna_sequence else 'A',
        "sequence_entropy": round(-sum(ratio * math.log2(ratio) if ratio > 0 else 0 
                                     for ratio in base_ratios.values()), 3)
    }


def detect_anomalous_arcs(trajectories: Dict[str, Any], compatibility: Dict[str, Any]) -> Dict[str, Any]:
    """Detect anomalous arc patterns that might indicate synthetic content."""
    
    anomaly_flags = []
    anomaly_score = 0.0
    
    # Check for excessive curvature (unnatural patterns)
    if trajectories.get("average_curvature", 0) > 0.8:
        anomaly_flags.append("excessive_curvature")
        anomaly_score += 0.3
    
    # Check for perfect symmetry (suspicious in natural content)
    if trajectories.get("symmetry_score", 1.0) < 0.05:
        anomaly_flags.append("perfect_symmetry")
        anomaly_score += 0.2
    
    # Check for extreme GC content (unusual in natural language)
    gc_content = compatibility.get("gc_content", 0.5)
    if gc_content < 0.1 or gc_content > 0.9:
        anomaly_flags.append("extreme_gc_content")
        anomaly_score += 0.25
    
    # Check for very low sequence entropy
    seq_entropy = compatibility.get("sequence_entropy", 2.0)
    if seq_entropy < 0.5:
        anomaly_flags.append("low_sequence_entropy")
        anomaly_score += 0.35
    
    # Check for compatibility score anomalies
    comp_score = compatibility.get("compatibility_score", 0.5)
    if comp_score > 0.95 or comp_score < 0.05:
        anomaly_flags.append("extreme_compatibility")
        anomaly_score += 0.15
    
    return {
        "anomaly_detected": len(anomaly_flags) > 0,
        "anomaly_score": round(min(1.0, anomaly_score), 3),
        "anomaly_flags": anomaly_flags,
        "risk_level": "high" if anomaly_score > 0.7 else "medium" if anomaly_score > 0.3 else "low"
    }


def run(input_data: str = "", sbsm_result: Optional[Dict] = None, 
        delta_s_result: Optional[Dict] = None, motif_result: Optional[Dict] = None, 
        **kwargs) -> Dict[str, Any]:
    """
    Enhanced EchoArc analysis with EchoFold + SDS-1 DNA arcs integration.
    
    Args:
        input_data: Input string to analyze
        sbsm_result: Results from SBSM module (optional)
        delta_s_result: Results from delta_s module (optional) 
        motif_result: Results from motif module (optional)
        **kwargs: Additional parameters
    
    Returns:
        Dict containing enhanced arc analysis results
    """
    
    if not input_data:
        return {
            "detector": "echoarc_enhanced",
            "arc_fit": 0.0,
            "ahy": 0.0,
            "echo_score_modifier": 0.0,
            "echofold_integration": {"vector_generated": False},
            "sds1_compatibility": {"compatibility_score": 0.0},
            "anomaly_detection": {"anomaly_detected": False}
        }
    
    # Generate EchoFold vector with context from other modules
    context_hash = ""
    if sbsm_result:
        context_hash += str(sbsm_result.get("delta_s", 0))
    if delta_s_result:
        context_hash += str(delta_s_result.get("delta_s", 0))
    
    echofold_vector = generate_echofold_vector(input_data, context_hash)
    
    # Calculate arc trajectories
    trajectories = calculate_arc_trajectories(echofold_vector)
    
    # Analyze SDS-1 DNA compatibility  
    compatibility = analyze_sds1_dna_compatibility(input_data, echofold_vector)
    
    # Detect anomalous patterns
    anomaly_analysis = detect_anomalous_arcs(trajectories, compatibility)
    
    # Calculate enhanced arc fit based on multiple factors
    base_arc_fit = trajectories.get("arc_strength", 0.0)
    compatibility_factor = compatibility.get("compatibility_score", 0.0)
    anomaly_penalty = anomaly_analysis.get("anomaly_score", 0.0)
    
    # Incorporate motif analysis if available
    motif_bonus = 0.0
    if motif_result and "loop_recursion" in motif_result:
        if motif_result["loop_recursion"].get("loop_detected"):
            motif_bonus = -0.2  # Penalty for detected loops
    
    enhanced_arc_fit = max(0.0, base_arc_fit + (compatibility_factor * 0.3) - (anomaly_penalty * 0.5) + motif_bonus)
    
    # Calculate AHY (Arc Harmony Yield) - higher values indicate more natural patterns
    sequence_entropy = compatibility.get("sequence_entropy", 0.0)
    symmetry_score = trajectories.get("symmetry_score", 1.0)
    ahy = (sequence_entropy / 2.0) * (1.0 - symmetry_score) * enhanced_arc_fit
    
    # Calculate echo score modifier
    if anomaly_analysis.get("risk_level") == "high":
        echo_modifier = -0.5
    elif anomaly_analysis.get("risk_level") == "medium":
        echo_modifier = -0.2
    else:
        echo_modifier = enhanced_arc_fit * 0.3
    
    return {
        "detector": "echoarc_enhanced",
        "arc_fit": round(enhanced_arc_fit, 6),
        "ahy": round(ahy, 6),
        "echo_score_modifier": round(echo_modifier, 3),
        "echofold_integration": {
            "vector_generated": True,
            "vector_dimensions": len(echofold_vector),
            "vector_magnitude": round(math.sqrt(sum(v*v for v in echofold_vector)), 6),
            "trajectories": trajectories
        },
        "sds1_compatibility": compatibility,
        "anomaly_detection": anomaly_analysis,
        "arc_metrics": {
            "curvature_complexity": trajectories.get("average_curvature", 0.0),
            "pattern_balance": 1.0 - trajectories.get("symmetry_score", 1.0),
            "genetic_naturalness": 1.0 - anomaly_analysis.get("anomaly_score", 0.0)
        }
    }