#!/usr/bin/env python3
"""
EchoScan CLI - Command Line Interface

Provides CLI access to EchoScan detection engines including SBSH symbolic hash, EchoVerifier, and pipeline operations.
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import monitoring modules
from monitoring import log_user_anomaly

# SBSH module imports
try:
    from sbsh_module import sbsh_hash, validate_sbsh_output
except ImportError:
    sbsh_hash = None
    validate_sbsh_output = None

import main

# EchoVerifier module import
try:
    import echoverifier
except ImportError:
    echoverifier = None

def handle_symbolic_hash(text, glyph_digest=None):
    """Handle --symbolic-hash flag"""
    if sbsh_hash:
        result = sbsh_hash(text, glyph_digest)
        return json.dumps(result, indent=2)
    else:
        return json.dumps({"error": "sbsh_hash not available"}, indent=2)

def handle_rehydrate(hash_data):
    """Handle --rehydrate flag - placeholder for rehydration logic"""
    return {"status": "rehydration not implemented", "input": hash_data}

def handle_compare_sbsh(hash1, hash2):
    """Handle --compare-sbsh flag - compare two SBSH hashes"""
    try:
        if isinstance(hash1, str):
            hash1 = json.loads(hash1)
        if isinstance(hash2, str):
            hash2 = json.loads(hash2)
        
        delta_match = hash1.get("delta_hash") == hash2.get("delta_hash")
        fold_match = hash1.get("fold_hash") == hash2.get("fold_hash")
        glyph_match = hash1.get("glyph_hash") == hash2.get("glyph_hash")
        
        return {
            "delta_match": delta_match,
            "fold_match": fold_match,
            "glyph_match": glyph_match,
            "overall_match": delta_match and fold_match and glyph_match
        }
    except Exception as e:
        return {"error": f"Comparison failed: {str(e)}"}

def handle_export_sbsh(text, format_type="json"):
    """Handle --export-sbsh flag"""
    if sbsh_hash:
        result = sbsh_hash(text)
    else:
        result = {"error": "sbsh_hash not available"}
    
    if format_type.lower() == "json":
        return json.dumps(result, indent=2)
    elif format_type.lower() == "csv":
        return f"delta_hash,fold_hash,glyph_hash,status\n{result.get('delta_hash')},{result.get('fold_hash')},{result.get('glyph_hash')},{result.get('status')}"
    else:
        return str(result)

def handle_sbsh_chain_link(text, previous_hash=None):
    """Handle --sbsh-chain-link flag - create chained hash"""
    if sbsh_hash:
        if previous_hash:
            combined_input = f"{text}::{previous_hash}"
            result = sbsh_hash(combined_input)
            result["chain_previous"] = previous_hash
            return result
        else:
            return sbsh_hash(text)
    else:
        return {"error": "sbsh_hash not available"}

def create_parser():
    """Create argument parser for CLI"""
    parser = argparse.ArgumentParser(
        description="EchoScan - Math-Anchored Symbolic Detection Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbolic-hash "Some text"
  python cli.py --compare-sbsh hash1.json hash2.json
  python cli.py --export-sbsh "text" --format json
  python cli.py --sbsh-chain-link "text" --previous-hash "hash_string"
  python cli.py --verify "Some text"
  python cli.py --unlock "Some hash"
  python cli.py --ancestry "Some text"
  python cli.py --export-verifier "Some text"
  python cli.py --full-scan filename.txt
Integration hooks available: TraceView, EchoVault, CollapseGlyph, EchoCradle, EchoSense, PulseAdapt
        """
    )
    # SBSH-related flags
    parser.add_argument("--symbolic-hash", type=str, help="Generate SBSH symbolic hash for input text")
    parser.add_argument("--glyph-digest", type=str, help="Optional glyph digest for symbolic hash")
    parser.add_argument("--rehydrate", type=str, help="Rehydrate from SBSH hash (placeholder)")
    parser.add_argument("--compare-sbsh", nargs=2, metavar=("HASH1", "HASH2"), help="Compare two SBSH hashes")
    parser.add_argument("--export-sbsh", type=str, help="Export SBSH hash for input text")
    parser.add_argument("--format", choices=["json", "csv", "raw"], default="json", help="Output format for export (default: json)")
    parser.add_argument("--sbsh-chain-link", type=str, help="Create chained SBSH hash")
    parser.add_argument("--previous-hash", type=str, help="Previous hash for chain linking")
    # Other CLI flags
    parser.add_argument("--encode-dna", type=str, help="Encode text using DNA-style encoding (placeholder)")
    parser.add_argument("--paradox", type=str, help="Generate paradox synthesis (placeholder)")
    # Full pipeline flag
    parser.add_argument("--full-scan", type=str, help="Run full EchoScan pipeline on input file")
    parser.add_argument("--input-type", choices=["text", "image", "audio", "video"], default="text", help="Input type for full scan (default: text)")
    # EchoVerifier flags
    parser.add_argument('--verify', type=str, help='Run EchoVerifier authenticity validation')
    parser.add_argument('--unlock', type=str, help='Run EchoLock unlock procedure')
    parser.add_argument('--ancestry', type=str, help='Perform ancestry depth analysis')
    parser.add_argument('--export-verifier', type=str, help='Export verifier data in structured format')
    # Additional options
    parser.add_argument('--input-file', type=str, help='Read input from file')
    parser.add_argument('--output-file', type=str, help='Write output to file')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--pipeline', action='store_true', help='Run full detection pipeline')
    # Edge case monitoring flags
    parser.add_argument('--feedback-log', type=str, help='Log user-reported anomaly to edge_cases.log')
    parser.add_argument('--verbose', action='store_true', help='Verbose output with detailed logging')
    parser.add_argument('--drill', choices=['provenance'], help='Drill down into specific analysis areas')

    return parser

def main_cli():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Handle input
    input_data = None
    input_file = None
    if args.input_file:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_data = f.read()
        input_file = args.input_file

    result = None

    try:
        # SBSH Flags
        if args.symbolic_hash:
            result = handle_symbolic_hash(args.symbolic_hash, args.glyph_digest)
            print(result)
            return

        if args.rehydrate:
            result = handle_rehydrate(args.rehydrate)
            print(json.dumps(result, indent=2))
            return

        if args.compare_sbsh:
            hash1, hash2 = args.compare_sbsh
            if os.path.isfile(hash1):
                with open(hash1, 'r') as f:
                    hash1 = f.read()
            if os.path.isfile(hash2):
                with open(hash2, 'r') as f:
                    hash2 = f.read()
            result = handle_compare_sbsh(hash1, hash2)
            print(json.dumps(result, indent=2))
            return

        if args.export_sbsh:
            result = handle_export_sbsh(args.export_sbsh, args.format)
            print(result)
            return

        if args.sbsh_chain_link:
            result = handle_sbsh_chain_link(args.sbsh_chain_link, args.previous_hash)
            print(json.dumps(result, indent=2))
            return

        # Edge case monitoring flags
        if args.feedback_log:
            target_input = args.feedback_log
            anomaly_description = input("Enter anomaly description: ").strip()
            
            if not anomaly_description:
                print("Error: Anomaly description is required for feedback logging.")
                return
            
            feedback_result = log_user_anomaly(target_input, anomaly_description)
            
            if args.json:
                print(json.dumps(feedback_result, indent=2))
            else:
                print(f"📝 Feedback logged successfully:")
                print(f"   Input: {target_input[:50]}...")
                print(f"   Description: {anomaly_description}")
                print(f"   Timestamp: {feedback_result['timestamp']}")
            return

        # EchoVerifier flags
        if echoverifier:
            if args.verify:
                target = input_data if input_data else args.verify
                result = echoverifier.run(target, mode="verify")
                if not args.json:
                    print(f"EchoVerifier Analysis for: {target[:50]}...")
                    print(f"Verdict: {result['verdict']}")
                    print(f"Delta S: {result['delta_s']}")
                    print(f"Glyph ID: {result['glyph_id']}")
                    print(f"Ancestry Depth: {result['ancestry_depth']}")
                    print(f"EchoSense Score: {result['echo_sense']}")
                    print(f"Vault Permission: {result['vault_permission']}")
                    if 'downstream' in result:
                        print(f"EchoSeal Status: {result['downstream']['echoseal']['trace_status']}")
                        print(f"EchoVault Access: {result['downstream']['echovault']['access_granted']}")
                        print(f"SDS-1 Sequence: {result['downstream']['sds1']['dna_sequence'][:10]}...")
                        print(f"RPS-1 State: {result['downstream']['rps1']['synthesis_state']}")
                else:
                    print(json.dumps(result, indent=2))
                return

            if args.unlock:
                target = input_data if input_data else args.unlock
                result = echoverifier.run(target, mode="unlock")
                if not args.json:
                    print(f"EchoLock Unlock for: {target[:50]}...")
                    print(f"Unlocked: {result['unlocked']}")
                    print(f"Unlock Level: {result['unlock_level']}")
                    print(f"EchoSense Score: {result['echo_sense']}")
                else:
                    print(json.dumps(result, indent=2))
                return

            if args.ancestry:
                target = input_data if input_data else args.ancestry
                result = echoverifier.run(target, mode="ancestry")
                if not args.json:
                    print(f"Ancestry Analysis for: {target[:50]}...")
                    print(f"Ancestry Depth: {result['ancestry_depth']}")
                    print(f"Trust Chain: {result['ancestry_trace']['trust_chain']}")
                    print(f"Validation Path: {result['ancestry_trace']['validation_path']}")
                else:
                    print(json.dumps(result, indent=2))
                return

            if args.export_verifier:
                target = input_data if input_data else args.export_verifier
                result = echoverifier.run(target, mode="export")
                if not args.json:
                    print("Exported Verifier Data:")
                    print(result['export_data'])
                else:
                    result = json.loads(result['export_data'])
                    print(json.dumps(result, indent=2))
                return

        # Other flags (placeholders)
        if args.encode_dna:
            print(f"DNA encoding for '{args.encode_dna}' - not implemented")
            return

        if args.paradox:
            print(f"Paradox synthesis for '{args.paradox}' - not implemented")
            return

        if args.full_scan:
            if not os.path.isfile(args.full_scan):
                print(f"Error: File '{args.full_scan}' not found")
                sys.exit(1)
            result = main.run_pipeline(args.full_scan, args.input_type)
            print(json.dumps(result, indent=2, default=str))
            return

        # Full pipeline (new logic)
        if args.pipeline and input_file:
            result = main.run_pipeline(input_file, "text")
            if not args.json:
                print("Full Pipeline Results:")
                print(f"Echo Score: {result['EchoScore']}")
                print(f"Decision: {result['Decision Label']}")
                if 'echoverifier' in result.get('FullResults', {}):
                    ev_result = result['FullResults']['echoverifier']
                    print(f"EchoVerifier Verdict: {ev_result['verdict']}")
            else:
                print(json.dumps(result, indent=2))
            return

        # Output to file if specified
        if args.json and result:
            json_output = json.dumps(result, indent=2)
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    f.write(json_output)
            else:
                print(json_output)
            return

        if args.output_file and result and not args.json:
            with open(args.output_file, 'w') as f:
                f.write(str(result))
            return

        # If no specific flag provided, show help
        parser.print_help()

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main_cli()