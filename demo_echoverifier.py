"""
EchoVerifier Demonstration Script
Shows the mathematical authenticity validation in action.
"""

import json
import echoverifier

def demo_echoverifier():
    """Demonstrate EchoVerifier functionality."""
    print("🔍 EchoScan EchoVerifier Demonstration")
    print("=" * 50)
    
    # Sample inputs with different characteristics
    test_cases = [
        {
            "name": "Clean Authentic Text",
            "input": "This is a simple, clean message for verification.",
            "description": "Should score high on authenticity metrics"
        },
        {
            "name": "Complex Mixed Content", 
            "input": "Mixed content with various patterns, symbols, and generated-like artificial textual constructs.",
            "description": "Should fall into Plausible category"
        },
        {
            "name": "Synthetic-looking Pattern",
            "input": "AI-generated synthetic artificial automated machine-produced content with repetitive algorithmic patterns and structures.",
            "description": "Should be detected as potential Hallucination"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['name']}")
        print(f"Input: {case['input']}")
        print(f"Expected: {case['description']}")
        print("-" * 40)
        
        # Run EchoVerifier
        result = echoverifier.run(case["input"], mode="verify")
        
        # Display results
        print(f"🎯 Verdict: {result['verdict']}")
        print(f"📊 Delta S Drift: {result['delta_s']:.6f}")
        print(f"🏷️  Glyph ID: {result['glyph_id']}")
        print(f"🌳 Ancestry Depth: {result['ancestry_depth']}")
        print(f"🧠 EchoSense Score: {result['echo_sense']:.6f}")
        print(f"🔐 Vault Permission: {'✅' if result['vault_permission'] else '❌'}")
        
        if 'downstream' in result:
            print(f"🔗 EchoSeal: {result['downstream']['echoseal']['trace_status']}")
            print(f"🏛️  EchoVault: {'✅' if result['downstream']['echovault']['access_granted'] else '❌'}")
            print(f"🧬 SDS-1 DNA: {result['downstream']['sds1']['dna_sequence'][:15]}...")
            print(f"🌀 RPS-1 Paradox: {result['downstream']['rps1']['synthesis_state']}")
    
    print("\n" + "=" * 50)
    print("✨ EchoVerifier Demo Complete!")
    print("\nCLI Usage Examples:")
    print("python cli.py --verify 'Your text here'")
    print("python cli.py --verify 'Your text here' --json")
    print("python cli.py --unlock 'Your text here'")
    print("python cli.py --ancestry 'Your text here'")
    print("python cli.py --export-verifier 'Your text here'")

if __name__ == "__main__":
    demo_echoverifier()