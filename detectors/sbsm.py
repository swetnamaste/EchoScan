"""
Swetnam Base Signature Matrix (SBSM) - Core mathematical detection module

Implements digit-sum sequences across bases 6-9, entropy drift calculations,
base × position matrix, stability vectors, and anomaly detection.
"""

import math
from typing import Dict, List, Any


def digit_sum_base(value: int, base: int) -> int:
    """Calculate digit sum of a number in given base."""
    if value == 0:
        return 0
    
    digit_sum = 0
    while value > 0:
        digit_sum += value % base
        value //= base
    return digit_sum


def string_to_numeric_sequence(input_string: str) -> List[int]:
    """Convert input string to numeric sequence using ASCII values."""
    return [ord(char) for char in input_string]


def calculate_digit_sum_sequences(numeric_sequence: List[int]) -> Dict[int, List[int]]:
    """Calculate digit sum sequences for bases 6-9."""
    sequences = {}
    
    for base in range(6, 10):  # bases 6, 7, 8, 9
        sequences[base] = [digit_sum_base(value, base) for value in numeric_sequence]
    
    return sequences


def calculate_entropy_drift(digit_sums: List[int]) -> float:
    """Calculate entropy drift (ΔS) as mean absolute difference of digit sums."""
    if len(digit_sums) < 2:
        return 0.0
    
    differences = []
    for i in range(1, len(digit_sums)):
        differences.append(abs(digit_sums[i] - digit_sums[i-1]))
    
    return sum(differences) / len(differences) if differences else 0.0


def create_base_position_matrix(digit_sequences: Dict[int, List[int]]) -> List[List[float]]:
    """Create base × position matrix from digit sequences."""
    if not digit_sequences:
        return []
    
    # Get sequence length from first base
    seq_length = len(next(iter(digit_sequences.values())))
    matrix = []
    
    for base in range(6, 10):
        base_row = []
        sequence = digit_sequences[base]
        
        for pos in range(seq_length):
            # Matrix value is (base * position * digit_sum) normalized
            value = (base * (pos + 1) * sequence[pos]) / 1000.0  # Normalize to prevent large values
            base_row.append(value)
        
        matrix.append(base_row)
    
    return matrix


def calculate_stability_vector(matrix: List[List[float]]) -> List[float]:
    """Calculate stability vector from base-position matrix."""
    if not matrix or not matrix[0]:
        return []
    
    stability = []
    num_positions = len(matrix[0])
    
    for pos in range(num_positions):
        # Calculate variance of values at this position across all bases
        position_values = [row[pos] for row in matrix]
        mean_val = sum(position_values) / len(position_values)
        variance = sum((val - mean_val) ** 2 for val in position_values) / len(position_values)
        stability.append(math.sqrt(variance))  # Use standard deviation as stability measure
    
    return stability


def detect_anomaly(global_drift: float, per_base_drifts: Dict[int, float], threshold: float = 0.012) -> str:
    """Detect anomaly based on drift thresholds with improved logic."""
    # Check for extremely low drift (suspicious uniformity - clearly synthetic)
    if global_drift < 0.001:
        return "Synthetic – Suspicious uniformity"
    
    # For natural language, drift typically ranges from 1.0 to 4.0
    # Very high drift suggests artificial patterns or edge cases
    if global_drift > 10.0:
        return "Synthetic – Extreme drift detected"
    
    # Count bases exceeding the threshold (0.012 is quite low for natural text)
    # Adjust threshold dynamically based on global drift
    adaptive_threshold = max(threshold, global_drift * 0.1)  # Use 10% of global drift as minimum
    high_drift_bases = [base for base, drift in per_base_drifts.items() if drift > adaptive_threshold]
    
    # Calculate drift variance across bases (uniformity check)
    drift_values = list(per_base_drifts.values())
    if len(drift_values) >= 4:
        mean_drift = sum(drift_values) / len(drift_values)
        variance = sum((drift - mean_drift) ** 2 for drift in drift_values) / len(drift_values)
        
        # If all bases have very similar drift (low variance), might be synthetic
        if variance < 0.01 and global_drift > 0.5:
            return "Borderline – Uniform cross-base pattern"
    
    # Most natural text will have some bases above threshold due to character distribution
    if len(high_drift_bases) == 0:
        return "Authentic – Stable drift"
    elif len(high_drift_bases) <= 2:
        return "Authentic – Normal variation"
    else:
        return "Borderline – Elevated drift pattern"


def sbsm_matrix(input_string: str) -> Dict[str, Any]:
    """
    Main SBSM calculation function that implements the complete mathematical logic.
    
    Args:
        input_string: Input string to analyze
        
    Returns:
        Dict containing:
        - delta_s: Global entropy drift
        - per_base: Per-base drift values for bases 6-9
        - matrix: Base × position matrix
        - stability_ratio: Average stability measure
        - status: Authentication status based on drift analysis
    """
    if not input_string:
        return {
            "delta_s": 0.0,
            "per_base": {str(base): 0.0 for base in range(6, 10)},
            "matrix": [],
            "stability_ratio": 0.0,
            "status": "Error – Empty input"
        }
    
    # Step 1: Convert string to numeric sequence
    numeric_sequence = string_to_numeric_sequence(input_string)
    
    # Step 2: Calculate digit sum sequences for bases 6-9
    digit_sequences = calculate_digit_sum_sequences(numeric_sequence)
    
    # Step 3: Calculate entropy drift for each base
    per_base_drifts = {}
    for base, sequence in digit_sequences.items():
        per_base_drifts[base] = calculate_entropy_drift(sequence)
    
    # Step 4: Calculate global entropy drift (average of per-base drifts)
    global_drift = sum(per_base_drifts.values()) / len(per_base_drifts)
    
    # Step 5: Create base × position matrix
    matrix = create_base_position_matrix(digit_sequences)
    
    # Step 6: Calculate stability vector and ratio
    stability_vector = calculate_stability_vector(matrix)
    stability_ratio = sum(stability_vector) / len(stability_vector) if stability_vector else 0.0
    
    # Step 7: Anomaly detection
    status = detect_anomaly(global_drift, per_base_drifts)
    
    return {
        "delta_s": round(global_drift, 4),
        "per_base": {str(base): round(drift, 4) for base, drift in per_base_drifts.items()},
        "matrix": [[round(val, 6) for val in row] for row in matrix],
        "stability_ratio": round(stability_ratio, 4),
        "status": status
    }


def run(input_string: str) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input string to analyze
        
    Returns:
        Dict containing SBSM analysis results with additional metadata for pipeline integration
    """
    result = sbsm_matrix(input_string)
    
    # Add pipeline-specific metadata
    result["echo_score_modifier"] = 0.0  # Default neutral score modifier
    result["source_classification"] = "Unknown"  # Will be determined by status
    
    # Set source classification based on status
    if "Synthetic" in result["status"]:
        result["source_classification"] = "AI-Generated"
        result["echo_score_penalty"] = -15.0  # Penalty for synthetic content
    elif "Borderline" in result["status"]:
        result["source_classification"] = "Questionable"
        result["echo_score_penalty"] = -5.0  # Mild penalty
        result["advisory_flag"] = "SBSM: Borderline stability detected"
    else:  # Authentic
        result["source_classification"] = "Human-Generated"
        result["echo_score_modifier"] = 5.0  # Bonus for authentic content
    
    return result