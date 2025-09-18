"""
EchoScan CLI with EchoVerifier integration
Supports --verify, --unlock, --ancestry, --export-verifier flags
"""

import argparse
import sys
import json
from pathlib import Path
import echoverifier
import main


def create_temp_file(content: str) -> str:
    """Create a temporary file with content for processing."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        return f.name


def main_cli():
    parser = argparse.ArgumentParser(description='EchoScan - Math-Anchored Symbolic Detection Engine')
    
    # Original CLI flags
    parser.add_argument('--symbolic-hash', type=str, help='Generate symbolic hash for text')
    parser.add_argument('--encode-dna', type=str, help='Encode text as DNA sequence') 
    parser.add_argument('--paradox', type=str, help='Generate paradox synthesis')
    
    # EchoVerifier flags (new)
    parser.add_argument('--verify', type=str, help='Run EchoVerifier authenticity validation')
    parser.add_argument('--unlock', type=str, help='Run EchoLock unlock procedure')
    parser.add_argument('--ancestry', type=str, help='Perform ancestry depth analysis')
    parser.add_argument('--export-verifier', type=str, help='Export verifier data in structured format')
    
    # Additional options
    parser.add_argument('--input-file', type=str, help='Read input from file')
    parser.add_argument('--output-file', type=str, help='Write output to file')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--pipeline', action='store_true', help='Run full detection pipeline')
    
    args = parser.parse_args()
    
    # Handle input
    input_data = None
    input_file = None
    
    if args.input_file:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            input_data = f.read()
        input_file = args.input_file
    
    result = None
    
    # EchoVerifier operations
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
    
    elif args.unlock:
        target = input_data if input_data else args.unlock
        result = echoverifier.run(target, mode="unlock")
        if not args.json:
            print(f"EchoLock Unlock for: {target[:50]}...")
            print(f"Unlocked: {result['unlocked']}")
            print(f"Unlock Level: {result['unlock_level']}")
            print(f"EchoSense Score: {result['echo_sense']}")
    
    elif args.ancestry:
        target = input_data if input_data else args.ancestry
        result = echoverifier.run(target, mode="ancestry")
        if not args.json:
            print(f"Ancestry Analysis for: {target[:50]}...")
            print(f"Ancestry Depth: {result['ancestry_depth']}")
            print(f"Trust Chain: {result['ancestry_trace']['trust_chain']}")
            print(f"Validation Path: {result['ancestry_trace']['validation_path']}")
    
    elif args.export_verifier:
        target = input_data if input_data else args.export_verifier
        result = echoverifier.run(target, mode="export")
        if not args.json:
            print("Exported Verifier Data:")
            print(result['export_data'])
        else:
            result = json.loads(result['export_data'])
    
    # Original operations (stubs)
    elif args.symbolic_hash:
        target = input_data if input_data else args.symbolic_hash
        from detectors import sbsm
        sbsm_result = sbsm.run(target)
        result = {"symbolic_hash": sbsm_result["sbsh_hash"]}
        if not args.json:
            print(f"Symbolic Hash: {sbsm_result['sbsh_hash']}")
    
    elif args.encode_dna:
        target = input_data if input_data else args.encode_dna
        result = {"dna_sequence": f"DNA_{hash(target) % 10000:04X}"}
        if not args.json:
            print(f"DNA Sequence: {result['dna_sequence']}")
    
    elif args.paradox:
        target = input_data if input_data else args.paradox
        result = {"paradox": f"PARADOX_{hash(target) % 10000:04X}"}
        if not args.json:
            print(f"Paradox: {result['paradox']}")
    
    # Full pipeline
    elif args.pipeline and input_file:
        result = main.run_pipeline(input_file, "text")
        if not args.json:
            print("Full Pipeline Results:")
            print(f"Echo Score: {result['EchoScore']}")
            print(f"Decision: {result['Decision Label']}")
            if 'echoverifier' in result.get('FullResults', {}):
                ev_result = result['FullResults']['echoverifier']
                print(f"EchoVerifier Verdict: {ev_result['verdict']}")
    
    # Handle JSON output
    if args.json and result:
        json_output = json.dumps(result, indent=2)
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(json_output)
        else:
            print(json_output)
    
    # Handle regular output file
    elif args.output_file and result and not args.json:
        with open(args.output_file, 'w') as f:
            f.write(str(result))
    
    if not any([args.verify, args.unlock, args.ancestry, args.export_verifier, 
                args.symbolic_hash, args.encode_dna, args.paradox, args.pipeline]):
        parser.print_help()


if __name__ == "__main__":
    main_cli()