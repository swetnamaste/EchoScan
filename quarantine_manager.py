"""
Quarantine Manager - Auto-capture edge cases for EchoScan
Automatically quarantines symbolic anomalies, drift > 0.02, unclassified glyphs
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class QuarantineManager:
    """Manages quarantine operations for edge cases and anomalies."""
    
    def __init__(self, quarantine_dir: str = "quarantine"):
        """Initialize quarantine manager.
        
        Args:
            quarantine_dir: Directory to store quarantined inputs
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of anomalies
        self.drift_dir = self.quarantine_dir / "drift_anomalies"
        self.glyph_dir = self.quarantine_dir / "unclassified_glyphs"
        self.symbolic_dir = self.quarantine_dir / "symbolic_anomalies" 
        self.general_dir = self.quarantine_dir / "general_edge_cases"
        
        for dir_path in [self.drift_dir, self.glyph_dir, self.symbolic_dir, self.general_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def should_quarantine(self, result: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if a result should be quarantined and why.
        
        Args:
            result: EchoVerifier result dictionary
            
        Returns:
            Tuple of (should_quarantine, reason)
        """
        reasons = []
        
        # Check for drift > 0.02
        delta_s = result.get("delta_s", 0.0)
        if delta_s > 0.02:
            reasons.append(f"High drift detected: {delta_s:.4f}")
        
        # Check for unclassified glyphs
        glyph_id = result.get("glyph_id", "")
        if glyph_id == "unclassified" or not glyph_id:
            reasons.append("Unclassified glyph detected")
        
        # Check for symbolic anomalies from SBSM
        if "metadata" in result:
            sbsm_result = result.get("metadata", {}).get("sbsm", {})
            if isinstance(sbsm_result, dict):
                source_class = sbsm_result.get("source_classification", "")
                if source_class in ["AI-Generated", "Questionable"]:
                    reasons.append(f"Symbolic anomaly: {source_class}")
                
                # Check for extreme drift in SBSM
                drift_score = sbsm_result.get("drift_score", 0.0)
                if drift_score > 0.02:
                    reasons.append(f"SBSM drift anomaly: {drift_score:.4f}")
        
        # Check verdict for edge cases
        verdict = result.get("verdict", "")
        if verdict == "Hallucination":
            reasons.append("Hallucination verdict")
        
        # Check echo_sense for anomalous scores
        echo_sense = result.get("echo_sense", 0.0)
        if echo_sense < 0.1:  # Very low authenticity score
            reasons.append(f"Low authenticity score: {echo_sense:.4f}")
        
        should_quarantine = len(reasons) > 0
        reason = "; ".join(reasons) if reasons else "No quarantine needed"
        
        return should_quarantine, reason
    
    def quarantine_input(self, input_data: str, result: Dict[str, Any], reason: str) -> str:
        """Quarantine an input with structured metadata.
        
        Args:
            input_data: Original input data
            result: EchoVerifier result
            reason: Reason for quarantine
            
        Returns:
            Path to quarantined file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Determine subdirectory based on reason
        if "drift" in reason.lower():
            subdir = self.drift_dir
            prefix = "drift"
        elif "glyph" in reason.lower():
            subdir = self.glyph_dir
            prefix = "glyph"
        elif "symbolic" in reason.lower() or "ai-generated" in reason.lower():
            subdir = self.symbolic_dir
            prefix = "symbolic"
        else:
            subdir = self.general_dir
            prefix = "general"
        
        filename = f"{prefix}_{timestamp}.json"
        filepath = subdir / filename
        
        quarantine_entry = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "input_data": input_data[:1000] + "..." if len(input_data) > 1000 else input_data,
            "input_length": len(input_data),
            "input_hash": hash(input_data),
            "result": result,
            "quarantine_metadata": {
                "category": prefix,
                "filepath": str(filepath),
                "auto_captured": True
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(quarantine_entry, f, indent=2)
        
        return str(filepath)
    
    def get_quarantine_stats(self) -> Dict[str, Any]:
        """Get statistics about quarantined items.
        
        Returns:
            Dictionary with quarantine statistics
        """
        stats = {
            "total_quarantined": 0,
            "by_category": {},
            "recent_entries": []
        }
        
        for subdir in [self.drift_dir, self.glyph_dir, self.symbolic_dir, self.general_dir]:
            category = subdir.name
            files = list(subdir.glob("*.json"))
            count = len(files)
            stats["by_category"][category] = count
            stats["total_quarantined"] += count
            
            # Get recent entries (last 5)
            if files:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for file in files[:5]:
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            entry = json.load(f)
                        stats["recent_entries"].append({
                            "category": category,
                            "timestamp": entry.get("timestamp"),
                            "reason": entry.get("reason"),
                            "filepath": str(file)
                        })
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # Sort recent entries by timestamp
        stats["recent_entries"].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        stats["recent_entries"] = stats["recent_entries"][:10]  # Keep only top 10
        
        return stats
    
    def process_result(self, input_data: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process a result for potential quarantine.
        
        Args:
            input_data: Original input data  
            result: EchoVerifier result
            
        Returns:
            Updated result with quarantine information
        """
        should_quarantine, reason = self.should_quarantine(result)
        
        quarantine_info = {
            "quarantined": should_quarantine,
            "reason": reason if should_quarantine else None,
            "filepath": None
        }
        
        if should_quarantine:
            try:
                filepath = self.quarantine_input(input_data, result, reason)
                quarantine_info["filepath"] = filepath
                print(f"[QUARANTINE] Auto-captured edge case: {reason}")
                print(f"[QUARANTINE] Saved to: {filepath}")
            except Exception as e:
                print(f"[QUARANTINE ERROR] Failed to quarantine input: {e}")
                quarantine_info["error"] = str(e)
        
        # Add quarantine info to result
        result["quarantine"] = quarantine_info
        return result


# Global quarantine manager instance
quarantine_manager = QuarantineManager()