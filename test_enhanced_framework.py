"""
Test script for the enhanced EchoScan framework modules.
Tests all 6 framework enhancements and integration.
"""

import sys
import traceback
import json


def test_context_drift():
    """Test Context Drift Vectors module."""
    print("Testing Context Drift Vectors...")
    try:
        from detectors import context_drift
        
        # Test with varied text blocks
        test_text = """
        This is the first paragraph discussing technical implementation details and algorithmic approaches.
        
        This second paragraph shifts to a more conversational tone, you know, with informal language patterns.
        
        The third paragraph returns to formal discourse regarding methodological considerations and analytical frameworks.
        """
        
        result = context_drift.run(test_text)
        assert result["detector"] == "context_drift"
        assert "drift_variance" in result
        assert "block_count" in result
        assert result["block_count"] >= 3
        
        print(f"  ✅ Context Drift: {result['block_count']} blocks, variance: {result['drift_variance']:.6f}")
        return True
        
    except Exception as e:
        print(f"  ❌ Context Drift failed: {e}")
        traceback.print_exc()
        return False


def test_quirk_injection():
    """Test Quirk Injection Layer module."""
    print("Testing Quirk Injection Layer...")
    try:
        from detectors import quirk_injection
        
        # Test with quirky text
        quirky_text = "Well, um, this is like a test... you know? I mean, it has hesitations and, uh, filler words. By the way, this should score high on quirk detection!"
        
        result = quirk_injection.run(quirky_text)
        assert result["detector"] == "quirk_injection"
        assert "quirk_score" in result
        assert result["quirk_score"] > 0.2  # Should detect quirks
        
        print(f"  ✅ Quirk Injection: score {result['quirk_score']:.3f}, classification: {result['source_classification']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Quirk Injection failed: {e}")
        traceback.print_exc()
        return False


def test_cross_modal():
    """Test Cross-Modal Consistency Checks."""
    print("Testing Cross-Modal Consistency...")
    try:
        from detectors import cross_modal
        
        # Test with text only
        result = cross_modal.run(
            text_data="This is a descriptive text with visual elements like bright colors and complex patterns.",
            audio_data=None,
            image_data=None
        )
        assert result["detector"] == "cross_modal"
        assert "verdict" in result
        
        print(f"  ✅ Cross-Modal: verdict {result['verdict']}, modalities: {len(result['modalities_analyzed'])}")
        return True
        
    except Exception as e:
        print(f"  ❌ Cross-Modal failed: {e}")
        traceback.print_exc()
        return False


def test_dynamic_threshold():
    """Test Dynamic Thresholding module."""
    print("Testing Dynamic Thresholding...")
    try:
        from detectors import dynamic_threshold
        
        # Create mock pipeline results
        mock_results = {
            "echoverifier": {"delta_s": 0.005, "echo_sense": 0.75},
            "sbsm": {"global_drift": 2.5}
        }
        
        result = dynamic_threshold.run("test input", mock_results)
        assert result["detector"] == "dynamic_threshold"
        assert "overall_confidence" in result
        assert "classification_results" in result
        
        print(f"  ✅ Dynamic Threshold: confidence {result['overall_confidence']:.3f}, verdict: {result['verdict']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Dynamic Threshold failed: {e}")
        traceback.print_exc()
        return False


def test_consensus_voting():
    """Test Consensus Voting module."""
    print("Testing Consensus Voting...")
    try:
        import consensus_voting
        
        # Create mock pipeline results with diverse verdicts
        mock_results = {
            "echoverifier": {"verdict": "Authentic", "echo_sense": 0.85},
            "sbsm": {"source_classification": "Human-Generated"},
            "downstream": {
                "echoseal": {"trace_status": "active"},
                "sds1": {"sequence_integrity": "stable", "genetic_markers": 4}
            }
        }
        
        result = consensus_voting.run("test", mock_results)
        assert result["detector"] == "consensus_voting"
        assert "consensus_verdict" in result
        assert "module_verdicts" in result
        
        print(f"  ✅ Consensus Voting: {result['consensus_verdict']}, {len(result['module_verdicts'])} modules")
        return True
        
    except Exception as e:
        print(f"  ❌ Consensus Voting failed: {e}")
        traceback.print_exc()
        return False


def test_rolling_reference():
    """Test Rolling Reference Updates module."""
    print("Testing Rolling Reference Updates...")
    try:
        from detectors import rolling_reference
        
        # Test with fold vector
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        
        result = rolling_reference.run(
            "This is academic research text discussing methodological approaches and analytical frameworks.",
            test_vector,
            {"source_type": "academic"}
        )
        
        assert result["detector"] == "rolling_reference"
        assert "drift_analysis" in result
        assert "domain_anchors_count" in result
        
        print(f"  ✅ Rolling Reference: {result['verdict']}, {result['domain_anchors_count']} anchors")
        return True
        
    except Exception as e:
        print(f"  ❌ Rolling Reference failed: {e}")
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test complete pipeline integration."""
    print("Testing Full Pipeline Integration...")
    try:
        import main
        
        test_text = """
        This comprehensive test demonstrates various writing patterns and characteristics.
        Um, it includes hesitation markers and, you know, informal language elements.
        
        The text also shifts between different domains - technical, conversational, and formal.
        Actually, let me clarify that point... I mean, adjust the phrasing for better clarity.
        
        By the way, this should trigger multiple detection systems simultaneously.
        """
        
        result = main.run_pipeline(test_text, "text")
        
        assert "EchoScore" in result
        assert "Decision Label" in result
        assert "FullResults" in result
        
        # Check that all enhanced modules ran
        full_results = result["FullResults"]
        expected_modules = ["echoverifier", "context_drift", "quirk_injection", "cross_modal", 
                          "rolling_reference", "dynamic_threshold", "consensus_voting"]
        
        modules_present = [module for module in expected_modules if module in full_results]
        
        print(f"  ✅ Full Pipeline: Score {result['EchoScore']}, Decision: {result['Decision Label']}")
        print(f"     Modules executed: {len(modules_present)}/{len(expected_modules)}")
        
        return len(modules_present) >= 6  # At least 6 modules should run
        
    except Exception as e:
        print(f"  ❌ Full Pipeline failed: {e}")
        traceback.print_exc()
        return False


def test_cli_functionality():
    """Test CLI enhancements."""
    print("Testing CLI Enhancements...")
    try:
        import subprocess
        
        # Test enhanced pipeline CLI
        result = subprocess.run([
            sys.executable, "cli.py", 
            "--enhanced-pipeline", 
            "--input-file", "test_enhanced.txt",
            "--json"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            output_data = json.loads(result.stdout)
            assert "EchoScore" in output_data
            assert "FullResults" in output_data
            print("  ✅ Enhanced CLI: JSON output successful")
            return True
        else:
            print(f"  ❌ CLI failed with return code {result.returncode}")
            print(f"     Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ CLI test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 ENHANCED ECHOSCAN FRAMEWORK TESTING")
    print("=" * 50)
    
    tests = [
        test_context_drift,
        test_quirk_injection,
        test_cross_modal,
        test_dynamic_threshold,
        test_consensus_voting,
        test_rolling_reference,
        test_full_pipeline,
        test_cli_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced framework is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())