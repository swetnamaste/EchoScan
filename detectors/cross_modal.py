"""
Cross-Modal Consistency Checks - Multi-modal submission analysis
Measures ∆S drift alignment across text/audio/image modalities and flags disagreements.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from . import sbsm, delta_s


class ModalityAnalyzer:
    """Base class for modality-specific analysis."""
    
    @staticmethod
    def extract_text_features(text: str) -> Dict[str, float]:
        """Extract numerical features from text for comparison."""
        if not text:
            return {"length": 0, "entropy": 0, "complexity": 0}
        
        # Basic text features
        length = len(text)
        word_count = len(text.split())
        avg_word_length = sum(len(word) for word in text.split()) / max(word_count, 1)
        
        # Character frequency entropy
        char_freq = {}
        for char in text.lower():
            char_freq[char] = char_freq.get(char, 0) + 1
        
        entropy = 0
        for freq in char_freq.values():
            prob = freq / length
            entropy += -prob * math.log2(prob) if prob > 0 else 0
        
        # Complexity based on punctuation and structure
        punct_count = sum(1 for c in text if c in ".,!?;:-()[]{}\"'")
        complexity = punct_count / max(length, 1)
        
        return {
            "length": length,
            "word_count": word_count,
            "avg_word_length": round(avg_word_length, 3),
            "entropy": round(entropy, 3),
            "complexity": round(complexity, 3),
            "punct_density": round(punct_count / max(word_count, 1), 3)
        }
    
    @staticmethod
    def simulate_audio_features(text: str) -> Dict[str, float]:
        """Simulate audio feature extraction from text (placeholder)."""
        if not text:
            return {"duration": 0, "pace": 0, "pauses": 0, "intonation": 0.5}
        
        # Estimate audio characteristics from text
        word_count = len(text.split())
        estimated_duration = word_count * 0.4  # ~150 WPM
        
        # Count potential pauses (punctuation)
        pause_markers = text.count(',') + text.count('.') + text.count('!') + text.count('?')
        pause_density = pause_markers / max(word_count, 1)
        
        # Estimate pace from word length and structure
        avg_word_len = sum(len(word) for word in text.split()) / max(word_count, 1)
        estimated_pace = 150 / max(avg_word_len / 4, 1)  # Adjust WPM by word complexity
        
        # Intonation estimate from punctuation variety
        intonation_variety = len(set(c for c in text if c in ".!?")) / 3
        
        return {
            "duration": round(estimated_duration, 2),
            "pace": round(estimated_pace, 2),
            "pause_density": round(pause_density, 3),
            "intonation_variety": round(intonation_variety, 3)
        }
    
    @staticmethod
    def simulate_image_features(text: str) -> Dict[str, float]:
        """Simulate image feature extraction from text description (placeholder)."""
        if not text:
            return {"visual_complexity": 0, "color_variety": 0, "composition": 0.5}
        
        # Extract visual descriptors if present
        visual_words = [
            "color", "bright", "dark", "light", "shadow", "texture", "shape",
            "line", "curve", "pattern", "contrast", "smooth", "rough"
        ]
        
        text_lower = text.lower()
        visual_density = sum(1 for word in visual_words if word in text_lower) / len(visual_words)
        
        # Estimate complexity from descriptive density
        adjective_patterns = ["beautiful", "complex", "simple", "detailed", "abstract"]
        complexity_score = sum(1 for adj in adjective_patterns if adj in text_lower) / len(adjective_patterns)
        
        return {
            "visual_density": round(visual_density, 3),
            "complexity_score": round(complexity_score, 3),
            "descriptive_richness": round(len([w for w in text.split() if len(w) > 6]) / max(len(text.split()), 1), 3)
        }


def analyze_modality_consistency(
    text_data: Optional[str] = None,
    audio_data: Optional[str] = None,
    image_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze consistency between multiple modalities.
    
    Args:
        text_data: Text content to analyze
        audio_data: Audio transcript or description
        image_data: Image description or caption
        
    Returns:
        Consistency analysis results
    """
    modalities = {}
    drift_results = {}
    
    # Process each available modality
    if text_data:
        modalities["text"] = {
            "features": ModalityAnalyzer.extract_text_features(text_data),
            "sbsm_result": sbsm.run(text_data),
            "delta_s_result": delta_s.run(text_data)
        }
        drift_results["text"] = modalities["text"]["delta_s_result"]["delta_s"]
    
    if audio_data:
        modalities["audio"] = {
            "features": ModalityAnalyzer.simulate_audio_features(audio_data),
            "sbsm_result": sbsm.run(audio_data) if audio_data else None,
            "delta_s_result": delta_s.run(audio_data) if audio_data else None
        }
        if audio_data:
            drift_results["audio"] = modalities["audio"]["delta_s_result"]["delta_s"]
    
    if image_data:
        modalities["image"] = {
            "features": ModalityAnalyzer.simulate_image_features(image_data),
            "sbsm_result": sbsm.run(image_data) if image_data else None,
            "delta_s_result": delta_s.run(image_data) if image_data else None
        }
        if image_data:
            drift_results["image"] = modalities["image"]["delta_s_result"]["delta_s"]
    
    return modalities, drift_results


def calculate_drift_alignment(drift_results: Dict[str, float], tolerance: float = 0.02) -> Dict[str, Any]:
    """
    Calculate alignment between drift values across modalities.
    
    Args:
        drift_results: Dict mapping modality names to drift values
        tolerance: Acceptable drift difference threshold
        
    Returns:
        Alignment analysis results
    """
    if len(drift_results) < 2:
        return {
            "alignment_score": 1.0,
            "max_drift_difference": 0.0,
            "aligned": True,
            "modality_count": len(drift_results)
        }
    
    drift_values = list(drift_results.values())
    modality_names = list(drift_results.keys())
    
    # Calculate all pairwise differences
    differences = []
    pairs = []
    for i in range(len(drift_values)):
        for j in range(i + 1, len(drift_values)):
            diff = abs(drift_values[i] - drift_values[j])
            differences.append(diff)
            pairs.append((modality_names[i], modality_names[j], diff))
    
    # Calculate alignment metrics
    max_difference = max(differences) if differences else 0.0
    mean_difference = sum(differences) / len(differences) if differences else 0.0
    
    # Alignment score (1.0 = perfectly aligned, 0.0 = completely misaligned)
    alignment_score = max(0.0, 1.0 - (mean_difference / 0.1))  # Scale by expected max difference
    
    # Determine if modalities are aligned within tolerance
    aligned = max_difference <= tolerance
    
    return {
        "alignment_score": round(alignment_score, 6),
        "max_drift_difference": round(max_difference, 6),
        "mean_drift_difference": round(mean_difference, 6),
        "aligned": aligned,
        "modality_count": len(drift_results),
        "drift_pairs": [
            {
                "modalities": f"{pair[0]}-{pair[1]}",
                "difference": round(pair[2], 6)
            } for pair in pairs
        ],
        "tolerance": tolerance
    }


def determine_cross_modal_verdict(
    alignment_data: Dict[str, Any],
    modalities: Dict[str, Any],
    min_alignment_score: float = 0.7
) -> Tuple[str, str]:
    """
    Determine verdict and classification based on cross-modal analysis.
    
    Returns:
        Tuple of (verdict, reasoning)
    """
    alignment_score = alignment_data["alignment_score"]
    modality_count = alignment_data["modality_count"]
    aligned = alignment_data["aligned"]
    
    if modality_count < 2:
        return "Insufficient_Data", "Less than 2 modalities provided for comparison"
    
    # Check for significant disagreement
    if not aligned or alignment_score < min_alignment_score:
        return "Ambiguous", f"Modalities disagree significantly (alignment: {alignment_score:.3f})"
    
    # Check individual modality verdicts for conflicts
    modality_verdicts = []
    for modality_name, modality_data in modalities.items():
        if modality_data.get("sbsm_result"):
            sbsm_status = modality_data["sbsm_result"].get("status", "Unknown")
            modality_verdicts.append((modality_name, sbsm_status))
    
    # Look for conflicting classifications
    authentic_count = sum(1 for _, verdict in modality_verdicts if "Authentic" in verdict)
    synthetic_count = sum(1 for _, verdict in modality_verdicts if "Synthetic" in verdict)
    
    if authentic_count > 0 and synthetic_count > 0:
        return "Ambiguous", "Mixed authenticity signals across modalities"
    
    # If aligned and consistent
    if alignment_score > 0.9:
        return "Consistent", "High cross-modal consistency detected"
    else:
        return "Moderately_Consistent", "Acceptable cross-modal consistency"


def run(
    text_data: Optional[str] = None,
    audio_data: Optional[str] = None,
    image_data: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        text_data: Primary text content
        audio_data: Audio transcript or description
        image_data: Image description or caption
        
    Returns:
        Dict containing cross-modal consistency analysis results
    """
    # Handle case where input is passed as positional argument
    if not text_data and "input_string" in kwargs:
        text_data = kwargs["input_string"]
    elif not text_data and len(kwargs) == 1:
        # If only one argument and it's a string, treat as text_data
        first_value = next(iter(kwargs.values()))
        if isinstance(first_value, str):
            text_data = first_value
    
    # Ensure we have at least text data
    if not text_data:
        return {
            "detector": "cross_modal",
            "verdict": "Insufficient_Data",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "CROSS_MODAL: No text data provided"
        }
    
    # Analyze modality consistency
    modalities, drift_results = analyze_modality_consistency(text_data, audio_data, image_data)
    
    # Calculate drift alignment
    alignment_data = calculate_drift_alignment(drift_results)
    
    # Determine verdict
    verdict, reasoning = determine_cross_modal_verdict(alignment_data, modalities)
    
    # Generate pipeline integration results
    if verdict == "Ambiguous":
        source_classification = "Questionable"
        echo_score_penalty = -10.0
        advisory_flag = f"CROSS_MODAL: {reasoning}"
    elif verdict == "Insufficient_Data":
        source_classification = "Unknown"
        echo_score_penalty = 0.0
        advisory_flag = f"CROSS_MODAL: {reasoning}"
    elif "Consistent" in verdict:
        source_classification = "Human-Generated"
        echo_score_modifier = 4.0
        echo_score_penalty = 0.0
        advisory_flag = None
    else:
        source_classification = "Unknown"
        echo_score_modifier = 0.0
        echo_score_penalty = 0.0
        advisory_flag = None
    
    # Compile results
    result = {
        "detector": "cross_modal",
        "verdict": verdict,
        "reasoning": reasoning,
        "source_classification": source_classification,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        "echo_score_penalty": locals().get("echo_score_penalty", 0.0),
        "alignment_data": alignment_data,
        "modalities_analyzed": list(modalities.keys()),
        "drift_results": drift_results
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
    
    return result