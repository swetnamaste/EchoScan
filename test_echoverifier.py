"""
Comprehensive test script for EchoVerifier implementation.
Validates all requirements from the problem statement.
"""

import json
import echoverifier
from cli import main_cli
import sys

def test_echoverifier_requirements():
    """Test all EchoVerifier requirements."""
    print("=== EchoVerifier Requirements Validation ===\n")
    
    # Test 1: Basic verification with all required fields
    print("Test 1: Basic Verification")
    test_input = "This is a sample text for authenticity verification."
    result = echoverifier.run(test_input, mode="verify")
    
    required_fields = [
        "input", "verdict", "delta_s", "fold_vector", "glyph_id", 
        "ancestry_depth", "echo_sense", "vault_permission"
    ]
    
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
    else:
        print("✅ All required fields present")
    
    # Test 2: Verdict types (Authentic/Plausible/Hallucination)
    print("\nTest 2: Verdict Types")
    verdicts = set()
    test_inputs = [
        "Simple clean text message",  # Should be Authentic
        "Mixed content with some complexity and patterns",  # Should be Plausible  
        "Very complex synthetic looking generated artificial content with unusual patterns",  # Should be Hallucination
    ]
    
    for i, inp in enumerate(test_inputs):
        res = echoverifier.run(inp, mode="verify")
        verdicts.add(res["verdict"])
        print(f"Input {i+1}: {res['verdict']} (Delta S: {res['delta_s']}, EchoSense: {res['echo_sense']})")
    
    expected_verdicts = {"Authentic", "Plausible", "Hallucination"}
    if not verdicts.issubset(expected_verdicts):
        print(f"❌ Invalid verdicts found: {verdicts - expected_verdicts}")
    else:
        print(f"✅ Valid verdict types: {verdicts}")
    
    # Test 3: Mathematical validation components
    print("\nTest 3: Mathematical Components")
    result = echoverifier.run("Test mathematical validation", mode="verify")
    
    # Delta S drift test
    if 0.0 <= result["delta_s"] <= 1.0:
        print("✅ Delta S in valid range [0.0, 1.0]")
    else:
        print(f"❌ Delta S out of range: {result['delta_s']}")
    
    # EchoFold vector
    if len(result["fold_vector"]) == 16 and all(0.0 <= v <= 1.0 for v in result["fold_vector"]):
        print("✅ EchoFold vector valid (16 dimensions, [0,1] range)")
    else:
        print(f"❌ EchoFold vector invalid: length={len(result['fold_vector'])}")
    
    # Glyph ID format
    if result["glyph_id"].startswith("GHX-") and len(result["glyph_id"]) == 8:
        print("✅ Glyph ID format valid (GHX-XXXX)")
    else:
        print(f"❌ Glyph ID format invalid: {result['glyph_id']}")
    
    # Ancestry depth
    if 1 <= result["ancestry_depth"] <= 10:
        print("✅ Ancestry depth in valid range [1, 10]")
    else:
        print(f"❌ Ancestry depth out of range: {result['ancestry_depth']}")
    
    # EchoSense score
    if 0.0 <= result["echo_sense"] <= 1.0:
        print("✅ EchoSense score in valid range [0.0, 1.0]")
    else:
        print(f"❌ EchoSense score out of range: {result['echo_sense']}")
    
    # Test 4: CLI flags
    print("\nTest 4: CLI Flags")
    import subprocess
    import tempfile
    
    cli_tests = [
        (["--verify", "test"], "verify"),
        (["--unlock", "test"], "unlock"), 
        (["--ancestry", "test"], "ancestry"),
        (["--export-verifier", "test"], "export")
    ]
    
    for args, mode in cli_tests:
        try:
            result = subprocess.run(
                ["python", "cli.py"] + args, 
                capture_output=True, text=True, cwd="."
            )
            if result.returncode == 0:
                print(f"✅ CLI flag {args[0]} working")
            else:
                print(f"❌ CLI flag {args[0]} failed: {result.stderr}")
        except Exception as e:
            print(f"❌ CLI flag {args[0]} error: {e}")
    
    # Test 5: Downstream hooks integration
    print("\nTest 5: Downstream Hooks")
    result = echoverifier.run("Test downstream hooks", mode="verify")
    
    if "downstream" in result:
        downstream_modules = ["echoseal", "echoroots", "echovault", "echosense_extended", "sds1", "rps1"]
        present_modules = [mod for mod in downstream_modules if mod in result["downstream"]]
        
        if len(present_modules) == len(downstream_modules):
            print("✅ All downstream hooks integrated")
        else:
            missing = set(downstream_modules) - set(present_modules)
            print(f"❌ Missing downstream hooks: {missing}")
    else:
        print("❌ No downstream hooks found")
    
    # Test 6: JSON output format compliance
    print("\nTest 6: JSON Output Format")
    result = echoverifier.run("JSON format test", mode="verify")
    
    try:
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        print("✅ JSON serialization successful")
        
        # Check sample output format from problem statement
        expected_structure = {
            "input": str, "verdict": str, "delta_s": float, 
            "fold_vector": list, "glyph_id": str, "ancestry_depth": int,
            "echo_sense": float, "vault_permission": bool
        }
        
        structure_valid = True
        for field, expected_type in expected_structure.items():
            if field not in parsed:
                print(f"❌ Missing field: {field}")
                structure_valid = False
            elif not isinstance(parsed[field], expected_type):
                print(f"❌ Wrong type for {field}: expected {expected_type}, got {type(parsed[field])}")
                structure_valid = False
        
        if structure_valid:
            print("✅ Output structure matches specification")
            
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
    
    print("\n=== EchoVerifier Validation Complete ===")

if __name__ == "__main__":
    test_echoverifier_requirements()