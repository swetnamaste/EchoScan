"""
Rolling Reference Updates and Drift Tracking - Periodic vector refresh system
Implements domain-specific anchors, reference drift tracking, and baseline updates.
"""

import json
import os
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import statistics
import math


class DomainAnchor:
    """Represents a domain-specific reference anchor."""
    
    def __init__(self, domain: str, reference_vector: List[float], 
                 confidence: float = 1.0, timestamp: float = None):
        self.domain = domain
        self.reference_vector = reference_vector
        self.confidence = confidence
        self.timestamp = timestamp or time.time()
        self.usage_count = 0
        self.drift_history = deque(maxlen=100)
    
    def update_vector(self, new_vector: List[float], confidence: float = 1.0):
        """Update the reference vector with exponential smoothing."""
        alpha = 0.1 * confidence  # Learning rate based on confidence
        
        for i in range(len(self.reference_vector)):
            if i < len(new_vector):
                self.reference_vector[i] = (
                    (1 - alpha) * self.reference_vector[i] + 
                    alpha * new_vector[i]
                )
        
        self.timestamp = time.time()
        self.usage_count += 1
    
    def calculate_drift(self, test_vector: List[float]) -> float:
        """Calculate drift from this anchor."""
        if len(test_vector) != len(self.reference_vector):
            return 1.0  # Maximum drift for incompatible vectors
        
        # Cosine distance
        dot_product = sum(a * b for a, b in zip(self.reference_vector, test_vector))
        norm_ref = math.sqrt(sum(a * a for a in self.reference_vector))
        norm_test = math.sqrt(sum(b * b for b in test_vector))
        
        if norm_ref == 0 or norm_test == 0:
            return 1.0
        
        cosine_sim = dot_product / (norm_ref * norm_test)
        drift = 1.0 - max(0, cosine_sim)  # Convert similarity to drift
        
        self.drift_history.append(drift)
        return drift
    
    def get_stability_metric(self) -> float:
        """Calculate how stable this anchor has been over time."""
        if len(self.drift_history) < 3:
            return 0.5
        
        recent_drifts = list(self.drift_history)[-10:]  # Last 10 measurements
        drift_variance = statistics.variance(recent_drifts)
        
        # Lower variance means more stability
        stability = max(0.0, 1.0 - (drift_variance * 10))
        return stability
    
    def needs_refresh(self, max_age_days: float = 30.0) -> bool:
        """Check if anchor needs refreshing based on age and stability."""
        age_days = (time.time() - self.timestamp) / (24 * 3600)
        
        # Refresh if too old or if drift patterns suggest instability
        if age_days > max_age_days:
            return True
        
        stability = self.get_stability_metric()
        if stability < 0.3 and self.usage_count > 10:
            return True
        
        return False


class ReferenceManager:
    """Manages rolling reference updates and domain anchors."""
    
    def __init__(self, storage_file: str = "reference_anchors.json"):
        self.storage_file = storage_file
        self.domain_anchors: Dict[str, DomainAnchor] = {}
        self.global_drift_history = deque(maxlen=1000)
        self.last_baseline_update = 0.0
        self.trusted_sources = set()  # SBSH/EchoLock archive sources
        self._load_anchors()
    
    def _get_storage_path(self) -> str:
        """Get full path for reference storage."""
        vault_dir = os.path.join(os.path.dirname(__file__), "..", "vault")
        if os.path.exists(vault_dir):
            return os.path.join(vault_dir, self.storage_file)
        return self.storage_file
    
    def _load_anchors(self):
        """Load existing reference anchors from storage."""
        try:
            filepath = self._get_storage_path()
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct domain anchors
                for domain_name, anchor_data in data.get("anchors", {}).items():
                    anchor = DomainAnchor(
                        domain=domain_name,
                        reference_vector=anchor_data["reference_vector"],
                        confidence=anchor_data.get("confidence", 1.0),
                        timestamp=anchor_data.get("timestamp", time.time())
                    )
                    anchor.usage_count = anchor_data.get("usage_count", 0)
                    anchor.drift_history = deque(
                        anchor_data.get("drift_history", [])[-100:], 
                        maxlen=100
                    )
                    self.domain_anchors[domain_name] = anchor
                
                self.last_baseline_update = data.get("last_baseline_update", 0.0)
                self.trusted_sources = set(data.get("trusted_sources", []))
                
        except Exception as e:
            # Start with empty state if loading fails
            pass
    
    def _save_anchors(self):
        """Save current anchors to storage."""
        try:
            data = {
                "anchors": {},
                "last_baseline_update": self.last_baseline_update,
                "trusted_sources": list(self.trusted_sources),
                "metadata": {
                    "total_anchors": len(self.domain_anchors),
                    "last_saved": time.time()
                }
            }
            
            for domain_name, anchor in self.domain_anchors.items():
                data["anchors"][domain_name] = {
                    "reference_vector": anchor.reference_vector,
                    "confidence": anchor.confidence,
                    "timestamp": anchor.timestamp,
                    "usage_count": anchor.usage_count,
                    "drift_history": list(anchor.drift_history)
                }
            
            filepath = self._get_storage_path()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            # Silently handle save errors
            pass
    
    def determine_domain(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Determine the appropriate domain for the text."""
        text_lower = text.lower()
        
        # Define domain keywords
        domain_keywords = {
            "academic": ["research", "study", "paper", "journal", "analysis", "methodology"],
            "business": ["company", "revenue", "market", "sales", "strategy", "profit"],
            "technical": ["algorithm", "implementation", "code", "system", "protocol", "api"],
            "creative": ["story", "character", "narrative", "creative", "imagine", "fiction"],
            "news": ["reported", "according", "statement", "breaking", "update", "source"],
            "conversational": ["i think", "you know", "like", "um", "actually", "personally"],
            "formal": ["furthermore", "therefore", "consequently", "moreover", "however"]
        }
        
        # Score each domain
        domain_scores = defaultdict(int)
        word_count = len(text.split())
        
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight by keyword frequency and text length
                    occurrences = text_lower.count(keyword)
                    domain_scores[domain] += occurrences
        
        # Normalize scores
        for domain in domain_scores:
            domain_scores[domain] /= max(word_count, 1)
        
        # Additional heuristics from metadata
        if metadata:
            source_type = metadata.get("source_type", "").lower()
            if source_type in domain_keywords:
                domain_scores[source_type] += 0.5
        
        # Return domain with highest score, or "general" if no clear match
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0.01:  # Minimum threshold
                return best_domain
        
        return "general"
    
    def get_reference_vector(self, text: str, fold_vector: List[float], 
                           metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[float], float, str]:
        """
        Get appropriate reference vector for comparison.
        
        Returns:
            Tuple of (reference_vector, confidence, domain)
        """
        domain = self.determine_domain(text, metadata)
        
        # Get or create domain anchor
        if domain not in self.domain_anchors:
            # Create new anchor with current vector as initial reference
            self.domain_anchors[domain] = DomainAnchor(
                domain=domain,
                reference_vector=fold_vector.copy(),
                confidence=0.5  # Lower confidence for new anchors
            )
            self._save_anchors()
        
        anchor = self.domain_anchors[domain]
        
        # Check if anchor needs refreshing
        if anchor.needs_refresh():
            self._refresh_anchor(domain, fold_vector)
        
        return anchor.reference_vector.copy(), anchor.confidence, domain
    
    def _refresh_anchor(self, domain: str, new_vector: List[float]):
        """Refresh a domain anchor with new trusted data."""
        if domain in self.domain_anchors:
            anchor = self.domain_anchors[domain]
            
            # Calculate refresh confidence based on stability history
            stability = anchor.get_stability_metric()
            refresh_confidence = min(0.9, 0.5 + stability)
            
            anchor.update_vector(new_vector, refresh_confidence)
            self._save_anchors()
    
    def update_from_trusted_source(self, text: str, fold_vector: List[float], 
                                 source_id: str, metadata: Optional[Dict[str, Any]] = None):
        """Update anchors from trusted SBSH/EchoLock archive."""
        if source_id not in self.trusted_sources:
            # Verify source trustworthiness (placeholder logic)
            if self._verify_trusted_source(source_id, metadata):
                self.trusted_sources.add(source_id)
            else:
                return
        
        domain = self.determine_domain(text, metadata)
        
        if domain not in self.domain_anchors:
            # Create new anchor from trusted source
            self.domain_anchors[domain] = DomainAnchor(
                domain=domain,
                reference_vector=fold_vector.copy(),
                confidence=0.9  # High confidence for trusted sources
            )
        else:
            # Update existing anchor
            self.domain_anchors[domain].update_vector(fold_vector, confidence=0.8)
        
        self.last_baseline_update = time.time()
        self._save_anchors()
    
    def _verify_trusted_source(self, source_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Verify if a source should be trusted."""
        # Placeholder implementation - in practice, this would verify against
        # SBSH/EchoLock signatures, check source reputation, etc.
        
        if metadata and metadata.get("sbsh_verified", False):
            return True
        
        # Check source ID format (simplified verification)
        if source_id.startswith(("SBSH_", "EchoLock_")) and len(source_id) > 10:
            return True
        
        return False
    
    def track_drift_patterns(self, drift_measurements: Dict[str, float]):
        """Track global drift patterns and detect persistent deviations."""
        # Calculate aggregate drift
        if drift_measurements:
            avg_drift = statistics.mean(drift_measurements.values())
            self.global_drift_history.append({
                "timestamp": time.time(),
                "average_drift": avg_drift,
                "measurements": drift_measurements.copy()
            })
        
        # Check for persistent deviation
        if len(self.global_drift_history) >= 20:
            recent_drifts = [entry["average_drift"] for entry in list(self.global_drift_history)[-20:]]
            recent_mean = statistics.mean(recent_drifts)
            
            # Compare with longer-term baseline
            if len(self.global_drift_history) >= 100:
                baseline_drifts = [entry["average_drift"] for entry in list(self.global_drift_history)[-100:-20]]
                baseline_mean = statistics.mean(baseline_drifts)
                
                # Trigger update if persistent deviation detected
                if abs(recent_mean - baseline_mean) > 0.05:  # 5% drift threshold
                    return True  # Suggest baseline update
        
        return False
    
    def get_drift_analysis(self, test_vector: List[float], domain: str = None) -> Dict[str, Any]:
        """Analyze drift against appropriate domain anchors."""
        if not domain:
            # Use general domain or find best match
            domain = "general"
        
        results = {
            "domain": domain,
            "drift_measurements": {},
            "best_match": None,
            "confidence": 0.0
        }
        
        if domain in self.domain_anchors:
            anchor = self.domain_anchors[domain]
            drift = anchor.calculate_drift(test_vector)
            
            results["drift_measurements"][domain] = drift
            results["best_match"] = {
                "domain": domain,
                "drift": drift,
                "anchor_age_days": (time.time() - anchor.timestamp) / (24 * 3600),
                "anchor_stability": anchor.get_stability_metric(),
                "usage_count": anchor.usage_count
            }
            results["confidence"] = anchor.confidence
        else:
            # Try to find closest domain anchor
            if self.domain_anchors:
                best_drift = float('inf')
                best_domain = None
                
                for anchor_domain, anchor in self.domain_anchors.items():
                    drift = anchor.calculate_drift(test_vector)
                    results["drift_measurements"][anchor_domain] = drift
                    
                    if drift < best_drift:
                        best_drift = drift
                        best_domain = anchor_domain
                
                if best_domain:
                    anchor = self.domain_anchors[best_domain]
                    results["best_match"] = {
                        "domain": best_domain,
                        "drift": best_drift,
                        "anchor_age_days": (time.time() - anchor.timestamp) / (24 * 3600),
                        "anchor_stability": anchor.get_stability_metric(),
                        "usage_count": anchor.usage_count
                    }
                    results["confidence"] = anchor.confidence * 0.8  # Reduced for cross-domain match
        
        return results


# Global reference manager instance
reference_manager = ReferenceManager()


def run(input_string: str, fold_vector: Optional[List[float]] = None, 
        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input text to analyze
        fold_vector: EchoFold vector from input
        metadata: Additional metadata about the input
        
    Returns:
        Dict containing rolling reference analysis results
    """
    if not fold_vector:
        # Try to generate basic vector if not provided
        from echoverifier import EchoFold
        fold_vector = EchoFold.generate_vector(input_string, "")
    
    if not fold_vector or len(fold_vector) == 0:
        return {
            "detector": "rolling_reference",
            "verdict": "Insufficient_Data",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "ROLLING_REFERENCE: No fold vector provided"
        }
    
    # Get domain-specific reference vector
    ref_vector, ref_confidence, domain = reference_manager.get_reference_vector(
        input_string, fold_vector, metadata
    )
    
    # Analyze drift against references
    drift_analysis = reference_manager.get_drift_analysis(fold_vector, domain)
    
    # Track drift patterns for baseline updates
    drift_measurements = drift_analysis["drift_measurements"]
    needs_baseline_update = reference_manager.track_drift_patterns(drift_measurements)
    
    # Determine authenticity implications
    best_match = drift_analysis.get("best_match")
    if best_match:
        drift_value = best_match["drift"]
        anchor_stability = best_match["anchor_stability"]
        anchor_age_days = best_match["anchor_age_days"]
        
        # Classification logic
        if drift_value < 0.1 and anchor_stability > 0.8:
            source_classification = "Human-Generated"
            echo_score_modifier = 4.0
            verdict = "Low_Drift_Authentic"
            advisory_flag = None
        elif drift_value < 0.2 and anchor_stability > 0.6:
            source_classification = "Human-Generated"
            echo_score_modifier = 2.0
            verdict = "Acceptable_Drift"
            advisory_flag = None
        elif drift_value > 0.7 or anchor_stability < 0.3:
            source_classification = "AI-Generated"
            echo_score_penalty = -12.0
            verdict = "High_Drift_Suspicious"
            advisory_flag = "ROLLING_REFERENCE: High drift from domain baseline"
        elif anchor_age_days > 60:  # Very old anchor
            source_classification = "Questionable"
            echo_score_penalty = -3.0
            verdict = "Stale_Reference"
            advisory_flag = "ROLLING_REFERENCE: Reference baseline may be outdated"
        else:
            source_classification = "Unknown"
            echo_score_modifier = 0.0
            verdict = "Moderate_Drift"
            advisory_flag = None
    else:
        source_classification = "Unknown"
        echo_score_modifier = 0.0
        verdict = "No_Reference"
        advisory_flag = "ROLLING_REFERENCE: No suitable reference found"
    
    # Compile results
    result = {
        "detector": "rolling_reference",
        "verdict": verdict,
        "source_classification": source_classification,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        "echo_score_penalty": locals().get("echo_score_penalty", 0.0),
        "drift_analysis": drift_analysis,
        "reference_confidence": ref_confidence,
        "needs_baseline_update": needs_baseline_update,
        "domain_anchors_count": len(reference_manager.domain_anchors),
        "trusted_sources_count": len(reference_manager.trusted_sources)
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
    
    return result