#!/usr/bin/env python3
"""
Test suite for EchoScan enhanced features
Tests the new confidence bands, consensus voting, enhanced detectors, and CLI features.
"""

import pytest
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import echoverifier
from detectors import motif, echoarc, delta_s


class TestEnhancedEchoVerifier:
    """Test enhanced EchoVerifier features."""
    
    def test_confidence_band_present(self):
        """Test that confidence_band is included in results."""
        result = echoverifier.run("test input for confidence band")
        
        assert "confidence_band" in result
        assert isinstance(result["confidence_band"], float)
        assert 0.0 <= result["confidence_band"] <= 1.0
    
    def test_consensus_voting(self):
        """Test consensus voting mechanism."""
        result = echoverifier.run("test input for consensus voting")
        
        assert "consensus" in result
        assert result["consensus"] in ["Strong", "Weak", "Ambiguous"]
    
    def test_intermediate_metrics(self):
        """Test intermediate metrics transparency."""
        result = echoverifier.run("test input for intermediate metrics")
        
        assert "intermediate_metrics" in result
        metrics = result["intermediate_metrics"]
        
        expected_keys = ["delta_s_variance", "fold_cosine", "ancestry_depth", "quirk_count", "consensus_status"]
        for key in expected_keys:
            assert key in metrics
    
    def test_drift_metrics(self):
        """Test drift metrics in API output."""
        result = echoverifier.run("test input for drift metrics")
        
        assert "drift_metrics" in result
        drift = result["drift_metrics"]
        
        assert "delta_s" in drift
        assert "variance" in drift
        assert "fold_similarity" in drift
    
    def test_quirk_score(self):
        """Test quirk score calculation."""
        result = echoverifier.run("test input with special chars: !@#$%")
        
        assert "quirk_score" in result
        assert isinstance(result["quirk_score"], float)
        assert result["quirk_score"] >= 0.0
    
    def test_provenance_chain(self):
        """Test provenance chain generation."""
        result = echoverifier.run("test input for provenance")
        
        assert "provenance" in result
        provenance = result["provenance"]
        
        assert "timestamp" in provenance
        assert "sha256_signature" in provenance
        assert "audit_bundle" in provenance
        assert "decision_trace" in provenance
    
    def test_ambiguous_verdict(self):
        """Test ambiguous verdict detection."""
        # Test with different inputs to see consensus behavior
        result1 = echoverifier.run("a" * 10)  # Very repetitive content
        result2 = echoverifier.run("test input")  # Regular content
        
        # At least one should either be Ambiguous or have mixed consensus
        has_ambiguous = (result1["verdict"] == "Ambiguous" or 
                        result2["verdict"] == "Ambiguous" or
                        result1["consensus"] in ["Weak", "Ambiguous"] or
                        result2["consensus"] in ["Weak", "Ambiguous"])
        
        assert has_ambiguous, "Should detect some ambiguity in consensus voting system"
    
    def test_export_verifier_enhanced(self):
        """Test enhanced export functionality."""
        export_result = echoverifier.echoverifier.export_verifier("test export")
        export_data = json.loads(export_result)
        
        assert export_data["verifier_version"] == "2.0.0-enhanced"
        assert "export_timestamp" in export_data
        assert "sha256_signature" in export_data
        assert "audit_bundle" in export_data


class TestEnhancedMotifDetector:
    """Test enhanced motif detector."""
    
    def test_enhanced_motif_structure(self):
        """Test enhanced motif detector output structure."""
        result = motif.run("test input with patterns ABC ABC ABC")
        
        assert result["detector"] == "motif_enhanced"
        assert "loop_recursion" in result
        assert "missing_closures" in result
        assert "parasite_glyphs" in result
        assert "sds1_dna_arcs" in result
        assert "pattern_complexity" in result
    
    def test_loop_recursion_detection(self):
        """Test loop recursion detection."""
        result = motif.run("ABCABC" * 10)  # Highly repetitive pattern
        
        loop_info = result["loop_recursion"]
        assert "loop_detected" in loop_info
        assert "recursion_depth" in loop_info
        assert isinstance(loop_info["loop_detected"], bool)
        assert isinstance(loop_info["recursion_depth"], int)
    
    def test_closure_detection(self):
        """Test missing closures detection."""
        result = motif.run("text with brackets ((( and some missing closures")
        
        closure_info = result["missing_closures"]
        assert "missing_closures" in closure_info
        assert "unmatched_opens" in closure_info
        assert closure_info["unmatched_opens"] > 0  # Should detect missing closures
    
    def test_parasite_glyph_detection(self):
        """Test parasite glyph detection."""
        result = motif.run("normal text")  # Should not detect parasites
        
        parasite_info = result["parasite_glyphs"]
        assert "parasite_detected" in parasite_info
        assert "parasite_count" in parasite_info
        assert parasite_info["parasite_count"] >= 0
    
    def test_sds1_dna_arcs(self):
        """Test SDS-1 DNA arc analysis."""
        result = motif.run("test input for DNA analysis")
        
        dna_info = result["sds1_dna_arcs"]
        assert "dna_sequence" in dna_info
        assert "arc_count" in dna_info
        assert "complementarity_score" in dna_info
        assert 0.0 <= dna_info["complementarity_score"] <= 1.0


class TestEnhancedEchoArcDetector:
    """Test enhanced EchoArc detector."""
    
    def test_enhanced_echoarc_structure(self):
        """Test enhanced EchoArc detector output structure."""
        result = echoarc.run("test input for arc analysis")
        
        assert result["detector"] == "echoarc_enhanced"
        assert "echofold_integration" in result
        assert "sds1_compatibility" in result
        assert "anomaly_detection" in result
        assert "arc_metrics" in result
    
    def test_echofold_integration(self):
        """Test EchoFold integration."""
        result = echoarc.run("test input")
        
        echofold_info = result["echofold_integration"]
        assert echofold_info["vector_generated"] == True
        assert echofold_info["vector_dimensions"] == 16
        assert "trajectories" in echofold_info
    
    def test_anomaly_detection(self):
        """Test anomaly detection in arc analysis."""
        result = echoarc.run("test input")
        
        anomaly_info = result["anomaly_detection"]
        assert "anomaly_detected" in anomaly_info
        assert "anomaly_score" in anomaly_info
        assert "risk_level" in anomaly_info
        assert anomaly_info["risk_level"] in ["low", "medium", "high"]
    
    def test_sds1_compatibility(self):
        """Test SDS-1 DNA compatibility analysis."""
        result = echoarc.run("test input for DNA compatibility")
        
        compat_info = result["sds1_compatibility"]
        assert "compatibility_score" in compat_info
        assert "base_composition" in compat_info
        assert "gc_content" in compat_info
        assert 0.0 <= compat_info["compatibility_score"] <= 1.0


class TestEnhancedDeltaSDetector:
    """Test enhanced Delta S detector."""
    
    def test_enhanced_delta_s_structure(self):
        """Test enhanced Delta S detector output structure."""
        result = delta_s.run("test input for delta S analysis")
        
        assert result["detector"] == "delta_s_enhanced"
        assert "variance" in result
        assert "stability_score" in result
        assert "synthetic_assessment" in result
        assert "dynamic_baseline" in result
    
    def test_synthetic_assessment(self):
        """Test synthetic content assessment."""
        result = delta_s.run("test input")
        
        assessment = result["synthetic_assessment"]
        assert "synthetic_likelihood" in assessment
        assert "classification" in assessment
        assert 0.0 <= assessment["synthetic_likelihood"] <= 1.0
        assert assessment["classification"] in [
            "highly_synthetic", "possibly_synthetic", "questionable", "likely_authentic"
        ]
    
    def test_dynamic_baseline(self):
        """Test dynamic baseline calculation."""
        result = delta_s.run("test input")
        
        baseline = result["dynamic_baseline"]
        assert "base_penalty" in baseline
        assert "dynamic_penalty" in baseline
        assert "scaling_factor" in baseline
    
    def test_anomaly_flags(self):
        """Test anomaly flag detection."""
        result = delta_s.run("test")  # Very short input
        
        assert "anomaly_flags" in result
        assert isinstance(result["anomaly_flags"], list)


class TestBackwardCompatibility:
    """Test that enhanced features maintain backward compatibility."""
    
    def test_original_fields_present(self):
        """Test that original result fields are still present."""
        result = echoverifier.run("test input")
        
        # Original fields should still be there
        original_fields = ["verdict", "delta_s", "fold_vector", "glyph_id", "ancestry_depth", "echo_sense", "vault_permission"]
        for field in original_fields:
            assert field in result, f"Missing original field: {field}"
    
    def test_legacy_verdict_values(self):
        """Test that verdict values are still valid."""
        result = echoverifier.run("test input")
        
        valid_verdicts = ["Authentic", "Plausible", "Hallucination", "Ambiguous"]
        assert result["verdict"] in valid_verdicts
    
    def test_json_serializable(self):
        """Test that all results are JSON serializable."""
        result = echoverifier.run("test input")
        
        # Should not raise an exception
        json_str = json.dumps(result)
        parsed_back = json.loads(json_str)
        
        assert parsed_back["verdict"] == result["verdict"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])