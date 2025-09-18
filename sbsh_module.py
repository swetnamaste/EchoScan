"""
Swetnam Base Symbolic Hash (SBSH) Module

This module implements Z-score normalization, digit-sum drift (∆S) across bases 6–9,
discrete cosine transform (DCT) fold compression (EchoFold), and SHA-256 fold hash.

Features:
- Z-score normalization
- Digit-sum drift calculation across bases 6-9
- DCT fold compression (EchoFold)
- SHA-256 fold hash
- Mathematical accuracy and spoof-resistance
"""

import hashlib
import math
import numpy as np
from scipy.fft import dct
import statistics


def z_score_normalize(data):
    """
    Apply Z-score normalization to input data.
    
    Args:
        data: List of numeric values
        
    Returns:
        List of z-score normalized values
    """
    if not data or len(data) < 2:
        return data
    
    mean_val = statistics.mean(data)
    std_val = statistics.stdev(data)
    
    if std_val == 0:
        return [0.0] * len(data)
    
    return [(x - mean_val) / std_val for x in data]


def digit_sum_base(number, base):
    """
    Calculate digit sum of a number in given base.
    
    Args:
        number: Integer to convert
        base: Base for conversion (6-9)
        
    Returns:
        Sum of digits in the specified base
    """
    if number == 0:
        return 0
    
    digit_sum = 0
    num = abs(number)
    
    while num > 0:
        digit_sum += num % base
        num //= base
    
    return digit_sum


def calculate_delta_s(input_string):
    """
    Calculate digit-sum drift (∆S) across bases 6–9.
    
    Args:
        input_string: Input text to process
        
    Returns:
        Float representing delta S value
    """
    # Convert string to numeric representation
    char_values = [ord(c) for c in input_string]
    
    # Calculate digit sums for each base
    base_sums = []
    for base in range(6, 10):  # bases 6, 7, 8, 9
        total_sum = sum(digit_sum_base(val, base) for val in char_values)
        base_sums.append(total_sum)
    
    # Calculate drift (difference between max and min normalized by length)
    if not base_sums:
        return 0.0
    
    max_sum = max(base_sums)
    min_sum = min(base_sums)
    length_norm = len(input_string) if input_string else 1
    
    delta_s = (max_sum - min_sum) / (length_norm * 10.0)  # Normalize to reasonable range
    return round(delta_s, 5)


def echo_fold_dct(input_data, fold_factor=8):
    """
    Apply DCT fold compression (EchoFold).
    
    Args:
        input_data: List of numeric values
        fold_factor: Compression factor
        
    Returns:
        Compressed data array
    """
    if not input_data or len(input_data) < fold_factor:
        return input_data
    
    # Ensure input is numpy array
    data = np.array(input_data, dtype=float)
    
    # Pad to multiple of fold_factor
    pad_len = (fold_factor - len(data) % fold_factor) % fold_factor
    if pad_len > 0:
        data = np.pad(data, (0, pad_len), mode='constant')
    
    # Reshape and apply DCT
    reshaped = data.reshape(-1, fold_factor)
    dct_result = dct(reshaped, axis=1, norm='ortho')
    
    # Take first half coefficients (compression)
    compressed = dct_result[:, :fold_factor//2]
    
    return compressed.flatten()


def sha256_fold_hash(data):
    """
    Generate SHA-256 fold hash from data.
    
    Args:
        data: Input data to hash
        
    Returns:
        Hexadecimal hash string
    """
    if isinstance(data, (list, np.ndarray)):
        # Convert numeric data to bytes
        data_bytes = b''.join(str(x).encode('utf-8') for x in data)
    else:
        data_bytes = str(data).encode('utf-8')
    
    hash_obj = hashlib.sha256(data_bytes)
    return hash_obj.hexdigest()


def sbsh_hash(input_string, glyph_digest=None):
    """
    Main SBSH hash function that orchestrates all components.
    
    Args:
        input_string: Input text to process
        glyph_digest: Optional glyph digest for additional hashing
        
    Returns:
        Dict with delta_hash, fold_hash, glyph_hash (optional), and status
    """
    try:
        # Step 1: Calculate delta S (digit-sum drift)
        delta_s = calculate_delta_s(input_string)
        
        # Step 2: Convert input to numeric representation for processing
        char_values = [ord(c) for c in input_string]
        
        # Step 3: Apply Z-score normalization
        normalized_values = z_score_normalize(char_values)
        
        # Step 4: Apply DCT fold compression (EchoFold)
        if normalized_values:
            folded_data = echo_fold_dct(normalized_values)
        else:
            folded_data = []
        
        # Step 5: Generate SHA-256 fold hash
        fold_hash = sha256_fold_hash(folded_data)
        
        # Step 6: Process glyph digest if provided
        glyph_hash = None
        if glyph_digest is not None:
            glyph_hash = sha256_fold_hash(glyph_digest)
        
        # Format delta_hash to 5 decimal places as shown in example
        delta_hash = f"{delta_s:.5f}"
        
        return {
            "delta_hash": delta_hash,
            "fold_hash": fold_hash[:32],  # Truncate to match example length
            "glyph_hash": glyph_hash[:32] if glyph_hash else None,
            "status": "LOCKED"
        }
        
    except Exception as e:
        # Return error state but maintain structure
        return {
            "delta_hash": "0.00000",
            "fold_hash": "error_" + hashlib.sha256(str(e).encode()).hexdigest()[:26],
            "glyph_hash": None,
            "status": "ERROR"
        }


def validate_sbsh_output(result):
    """
    Validate SBSH output format matches specification.
    
    Args:
        result: SBSH hash result dict
        
    Returns:
        Boolean indicating if format is valid
    """
    required_keys = {"delta_hash", "fold_hash", "glyph_hash", "status"}
    
    if not isinstance(result, dict):
        return False
    
    if not all(key in result for key in required_keys):
        return False
    
    # Validate delta_hash format (should be numeric string)
    try:
        float(result["delta_hash"])
    except (ValueError, TypeError):
        return False
    
    # Validate fold_hash is hexadecimal string
    if not isinstance(result["fold_hash"], str):
        return False
    
    try:
        int(result["fold_hash"], 16)
    except ValueError:
        return False
    
    # Validate status
    if result["status"] not in ["LOCKED", "ERROR"]:
        return False
    
    return True


if __name__ == "__main__":
    # Test the SBSH module
    test_input = "Some text"
    result = sbsh_hash(test_input)
    print("SBSH Test Result:")
    print(f"Input: {test_input}")
    print(f"Output: {result}")
    print(f"Valid format: {validate_sbsh_output(result)}")