#!/usr/bin/env python3
"""
EchoScan CLI - Command Line Interface

Provides CLI access to EchoScan detection engines including SBSH symbolic hash.
"""

import argparse
import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sbsh_module import sbsh_hash, validate_sbsh_output
import main


def handle_symbolic_hash(text, glyph_digest=None):
    """Handle --symbolic-hash flag"""
    result = sbsh_hash(text, glyph_digest)
    return json.dumps(result, indent=2)


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
    result = sbsh_hash(text)
    
    if format_type.lower() == "json":
        return json.dumps(result, indent=2)
    elif format_type.lower() == "csv":
        return f"delta_hash,fold_hash,glyph_hash,status\n{result['delta_hash']},{result['fold_hash']},{result['glyph_hash']},{result['status']}"
    else:
        return str(result)


def handle_sbsh_chain_link(text, previous_hash=None):
    """Handle --sbsh-chain-link flag - create chained hash"""
    if previous_hash:
        # Incorporate previous hash into current calculation
        combined_input = f"{text}::{previous_hash}"
        result = sbsh_hash(combined_input)
        result["chain_previous"] = previous_hash
        return result
    else:
        return sbsh_hash(text)


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
  
Integration hooks available: TraceView, EchoVault, CollapseGlyph, EchoCradle, EchoSense, PulseAdapt
        """
    )
    
    # SBSH-related flags
    parser.add_argument(
        "--symbolic-hash", 
        type=str, 
        help="Generate SBSH symbolic hash for input text"
    )
    
    parser.add_argument(
        "--glyph-digest",
        type=str,
        help="Optional glyph digest for symbolic hash"
    )
    
    parser.add_argument(
        "--rehydrate", 
        type=str, 
        help="Rehydrate from SBSH hash (placeholder)"
    )
    
    parser.add_argument(
        "--compare-sbsh", 
        nargs=2, 
        metavar=("HASH1", "HASH2"),
        help="Compare two SBSH hashes"
    )
    
    parser.add_argument(
        "--export-sbsh", 
        type=str, 
        help="Export SBSH hash for input text"
    )
    
    parser.add_argument(
        "--format", 
        choices=["json", "csv", "raw"], 
        default="json",
        help="Output format for export (default: json)"
    )
    
    parser.add_argument(
        "--sbsh-chain-link", 
        type=str, 
        help="Create chained SBSH hash"
    )
    
    parser.add_argument(
        "--previous-hash", 
        type=str, 
        help="Previous hash for chain linking"
    )
    
    # Other CLI flags mentioned in README
    parser.add_argument(
        "--encode-dna", 
        type=str, 
        help="Encode text using DNA-style encoding (placeholder)"
    )
    
    parser.add_argument(
        "--paradox", 
        type=str, 
        help="Generate paradox synthesis (placeholder)"
    )
    
    # Full pipeline flag
    parser.add_argument(
        "--full-scan",
        type=str,
        help="Run full EchoScan pipeline on input file"
    )
    
    parser.add_argument(
        "--input-type",
        choices=["text", "image", "audio", "video"],
        default="text",
        help="Input type for full scan (default: text)"
    )
    
    return parser


def main_cli():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Handle SBSH flags
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
            # Try to read from files if they exist, otherwise treat as direct hash strings
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
        
        # Handle other flags (placeholders)
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
        
        # If no specific flag provided, show help
        parser.print_help()
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_cli()