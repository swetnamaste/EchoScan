#!/usr/bin/env python3
"""
Test suite for SBSH module integration with EchoScan
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sbsh_module import (
    sbsh_hash, 
    validate_sbsh_output, 
    z_score_normalize, 
    calculate_delta_s, 
    echo_fold_dct,
    sha256_fold_hash,
    digit_sum_base
)


class TestSBSHModule:
    """Test the SBSH module functions"""
    
    def test_sbsh_hash_basic(self):
        """Test basic SBSH hash functionality"""
        result = sbsh_hash("test input")
        
        # Validate structure
        assert validate_sbsh_output(result)
        assert "delta_hash" in result
        assert "fold_hash" in result
        assert "glyph_hash" in result
        assert "status" in result
        assert result["status"] == "LOCKED"
        
        # Validate delta_hash format (5 decimal places)
        assert "." in result["delta_hash"]
        delta_val = float(result["delta_hash"])
        assert 0 <= delta_val <= 1.0  # Should be in reasonable range
        
        # Validate fold_hash is hex
        assert len(result["fold_hash"]) == 32
        int(result["fold_hash"], 16)  # Should not raise ValueError
    
    def test_sbsh_hash_with_glyph(self):
        """Test SBSH hash with glyph digest"""
        result = sbsh_hash("test input", "glyph_data")
        
        assert validate_sbsh_output(result)
        assert result["glyph_hash"] is not None
        assert len(result["glyph_hash"]) == 32
    
    def test_delta_s_calculation(self):
        """Test digit-sum drift calculation"""
        # Test with known input
        delta_s = calculate_delta_s("ABC")
        assert isinstance(delta_s, float)
        assert delta_s >= 0  # Should be non-negative
        
        # Test empty string
        assert calculate_delta_s("") == 0.0
        
        # Test single character
        single_delta = calculate_delta_s("A")
        assert isinstance(single_delta, float)
    
    def test_z_score_normalization(self):
        """Test Z-score normalization"""
        data = [1, 2, 3, 4, 5]
        normalized = z_score_normalize(data)
        
        # Should have same length
        assert len(normalized) == len(data)
        
        # Mean should be approximately 0
        assert abs(sum(normalized) / len(normalized)) < 1e-10
        
        # Test edge cases
        assert z_score_normalize([]) == []
        assert z_score_normalize([5]) == [5]
        assert z_score_normalize([1, 1, 1]) == [0.0, 0.0, 0.0]
    
    def test_digit_sum_bases(self):
        """Test digit sum calculation in different bases"""
        # Test base 6
        assert digit_sum_base(10, 6) == 1 + 4  # 10 = 14 in base 6
        assert digit_sum_base(0, 6) == 0
        
        # Test base 8
        assert digit_sum_base(8, 8) == 1 + 0  # 8 = 10 in base 8
        
        # Test with negative (should use absolute value)
        assert digit_sum_base(-10, 6) == digit_sum_base(10, 6)
    
    def test_echo_fold_dct(self):
        """Test DCT fold compression"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        folded = echo_fold_dct(data, 8)
        
        # Should be compressed (less than original)
        assert len(folded) <= len(data)
        
        # Test empty input
        assert echo_fold_dct([]) == []
        
        # Test small input
        small_folded = echo_fold_dct([1, 2, 3])
        assert len(small_folded) == 3  # Should return as-is if too small
    
    def test_sha256_fold_hash(self):
        """Test SHA-256 fold hash"""
        hash1 = sha256_fold_hash("test")
        hash2 = sha256_fold_hash("test")
        hash3 = sha256_fold_hash("different")
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Different input should produce different hash
        assert hash1 != hash3
        
        # Should be hex string of appropriate length
        assert len(hash1) == 64
        int(hash1, 16)  # Should not raise ValueError
    
    def test_consistency(self):
        """Test that same input produces same output"""
        text = "consistent test input"
        
        result1 = sbsh_hash(text)
        result2 = sbsh_hash(text)
        
        assert result1["delta_hash"] == result2["delta_hash"]
        assert result1["fold_hash"] == result2["fold_hash"]
        assert result1["status"] == result2["status"]
    
    def test_mathematical_accuracy(self):
        """Test mathematical accuracy of the implementation"""
        # Test with specific known values
        test_cases = [
            "A",          # Single character
            "ABC",        # Simple sequence  
            "Hello",      # Common word
            "12345",      # Numbers
            "!@#$%",      # Symbols
            "",           # Empty (edge case)
        ]
        
        for test_input in test_cases:
            result = sbsh_hash(test_input)
            
            # All should be valid format
            assert validate_sbsh_output(result)
            
            # Delta hash should be mathematically consistent
            recalc_delta = calculate_delta_s(test_input)
            expected_delta = f"{recalc_delta:.5f}"
            assert result["delta_hash"] == expected_delta


class TestSBSHIntegration:
    """Test SBSH integration with EchoScan"""
    
    def test_output_format_matches_spec(self):
        """Test that output matches the specification format"""
        result = sbsh_hash("Some text")
        
        # Should match example format from problem statement
        expected_keys = {"delta_hash", "fold_hash", "glyph_hash", "status"}
        assert set(result.keys()) == expected_keys
        
        # Status should be LOCKED
        assert result["status"] == "LOCKED"
        
        # Glyph hash should be null when not provided
        assert result["glyph_hash"] is None
        
        # Format should match example: 0.08421 format for delta
        assert len(result["delta_hash"].split(".")[1]) == 5  # 5 decimal places
        
        # Fold hash should be hex string (example shows e11c6fa3e39...)
        assert all(c in "0123456789abcdef" for c in result["fold_hash"])
    
    def test_spoof_resistance(self):
        """Test spoof resistance - similar inputs should produce different hashes"""
        inputs = [
            "Hello world",
            "Hello world!",
            "Hello World",
            "hello world",
            "Hello  world"  # Extra space
        ]
        
        results = [sbsh_hash(inp) for inp in inputs]
        fold_hashes = [r["fold_hash"] for r in results]
        
        # All fold hashes should be different
        assert len(set(fold_hashes)) == len(fold_hashes), "Fold hashes should be unique for different inputs"
        
        # Delta hashes should also vary
        delta_hashes = [r["delta_hash"] for r in results]
        # Allow some to be the same but not all
        assert len(set(delta_hashes)) > 1, "Delta hashes should show variation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])