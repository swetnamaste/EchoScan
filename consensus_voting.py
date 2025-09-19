"""
Consensus Voting - Module aggregation and disagreement handling
Aggregates verdicts from EchoVerifier, EchoSeal, and SDS-1 with disagreement detection.
"""

from typing import Dict, List, Any, Tuple, Optional
import statistics
from collections import Counter


class VerdictAggregator:
    """Handles consensus voting and disagreement resolution."""
    
    VERDICT_RANKINGS = {
        # Higher scores indicate stronger authenticity signals
        "Authentic": 1.0,
        "High_Confidence_Authentic": 1.2,
        "Plausible": 0.8,
        "Normal": 0.7,
        "Moderately_Consistent": 0.6,
        "Consistent": 0.9,
        "Unknown": 0.5,
        "Low_Confidence": 0.3,
        "Questionable": 0.2,
        "Suspicious": 0.1,
        "Anomalous": 0.0,
        "AI-Generated": -0.2,
        "Hallucination": -0.5,
        "Synthetic": -0.8
    }
    
    @staticmethod
    def normalize_verdict(verdict: str) -> str:
        """Normalize verdict strings to standard format."""
        if not verdict:
            return "Unknown"
        
        verdict = str(verdict).strip()
        verdict_lower = verdict.lower()
        
        # Map various verdict formats to standard ones
        if any(term in verdict_lower for term in ["authentic", "genuine", "human"]):
            if "high" in verdict_lower or "confident" in verdict_lower:
                return "High_Confidence_Authentic"
            return "Authentic"
        elif any(term in verdict_lower for term in ["plausible", "likely", "probable"]):
            return "Plausible"
        elif any(term in verdict_lower for term in ["synthetic", "artificial", "ai", "generated"]):
            return "Synthetic"
        elif any(term in verdict_lower for term in ["hallucination", "fabricated"]):
            return "Hallucination"
        elif any(term in verdict_lower for term in ["suspicious", "flagged"]):
            return "Suspicious"
        elif any(term in verdict_lower for term in ["anomalous", "anomaly"]):
            return "Anomalous"
        elif any(term in verdict_lower for term in ["questionable", "uncertain"]):
            return "Questionable"
        elif any(term in verdict_lower for term in ["normal", "standard"]):
            return "Normal"
        elif any(term in verdict_lower for term in ["consistent"]):
            if "moderate" in verdict_lower:
                return "Moderately_Consistent"
            return "Consistent"
        else:
            return "Unknown"
    
    @staticmethod
    def extract_module_verdicts(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract verdicts and confidence scores from pipeline results."""
        module_verdicts = {}
        
        # EchoVerifier
        if "echoverifier" in results:
            ev_result = results["echoverifier"]
            if isinstance(ev_result, dict):
                module_verdicts["echoverifier"] = {
                    "verdict": VerdictAggregator.normalize_verdict(ev_result.get("verdict", "Unknown")),
                    "confidence": VerdictAggregator._extract_confidence(ev_result),
                    "echo_sense": ev_result.get("echo_sense", 0.5),
                    "raw_verdict": ev_result.get("verdict", "Unknown")
                }
        
        # EchoSeal (from downstream hooks)
        if "downstream" in results and "echoseal" in results["downstream"]:
            seal_result = results["downstream"]["echoseal"]
            # EchoSeal primarily provides drift trace, infer verdict from trace status
            trace_status = seal_result.get("trace_status", "inactive")
            seal_verdict = "Authentic" if trace_status == "active" else "Questionable"
            
            module_verdicts["echoseal"] = {
                "verdict": seal_verdict,
                "confidence": 0.8 if trace_status == "active" else 0.4,
                "trace_status": trace_status,
                "raw_verdict": trace_status
            }
        
        # SDS-1 (from downstream hooks)
        if "downstream" in results and "sds1" in results["downstream"]:
            sds1_result = results["downstream"]["sds1"]
            # SDS-1 provides genetic markers and sequence integrity
            integrity = sds1_result.get("sequence_integrity", "unknown")
            markers = sds1_result.get("genetic_markers", 0)
            
            if integrity == "stable" and markers >= 3:
                sds1_verdict = "Authentic"
                sds1_confidence = 0.7
            elif integrity == "stable":
                sds1_verdict = "Plausible"
                sds1_confidence = 0.6
            else:
                sds1_verdict = "Questionable"
                sds1_confidence = 0.3
                
            module_verdicts["sds1"] = {
                "verdict": sds1_verdict,
                "confidence": sds1_confidence,
                "integrity": integrity,
                "markers": markers,
                "raw_verdict": integrity
            }
        
        # Dynamic Threshold results
        if "dynamic_threshold" in results:
            dt_result = results["dynamic_threshold"]
            if isinstance(dt_result, dict):
                module_verdicts["dynamic_threshold"] = {
                    "verdict": VerdictAggregator.normalize_verdict(dt_result.get("verdict", "Unknown")),
                    "confidence": dt_result.get("overall_confidence", 0.5),
                    "raw_verdict": dt_result.get("verdict", "Unknown")
                }
        
        # Context Drift results
        if "context_drift" in results:
            cd_result = results["context_drift"]
            if isinstance(cd_result, dict):
                source_class = cd_result.get("source_classification", "Unknown")
                cd_verdict = VerdictAggregator._source_class_to_verdict(source_class)
                
                module_verdicts["context_drift"] = {
                    "verdict": cd_verdict,
                    "confidence": 1.0 - cd_result.get("anomaly_score", 0.5),
                    "anomaly_score": cd_result.get("anomaly_score", 0.5),
                    "raw_verdict": source_class
                }
        
        # Quirk Injection results
        if "quirk_injection" in results:
            qi_result = results["quirk_injection"]
            if isinstance(qi_result, dict):
                source_class = qi_result.get("source_classification", "Unknown")
                qi_verdict = VerdictAggregator._source_class_to_verdict(source_class)
                
                module_verdicts["quirk_injection"] = {
                    "verdict": qi_verdict,
                    "confidence": qi_result.get("quirk_score", 0.5),
                    "quirk_score": qi_result.get("quirk_score", 0.5),
                    "raw_verdict": source_class
                }
        
        return module_verdicts
    
    @staticmethod
    def _extract_confidence(result: Dict[str, Any]) -> float:
        """Extract confidence score from module results."""
        # Look for various confidence indicators
        if "confidence" in result:
            return result["confidence"]
        elif "echo_sense" in result:
            return result["echo_sense"]
        elif "overall_confidence" in result:
            return result["overall_confidence"]
        else:
            return 0.5  # Default confidence
    
    @staticmethod
    def _source_class_to_verdict(source_class: str) -> str:
        """Convert source classification to normalized verdict."""
        if source_class == "Human-Generated":
            return "Authentic"
        elif source_class == "AI-Generated":
            return "Synthetic"
        elif source_class == "Questionable":
            return "Questionable"
        else:
            return "Unknown"


def calculate_consensus(module_verdicts: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate consensus from module verdicts.
    
    Args:
        module_verdicts: Dict of module names to verdict data
        
    Returns:
        Consensus analysis results
    """
    if not module_verdicts:
        return {
            "consensus_verdict": "Unknown",
            "consensus_confidence": 0.0,
            "agreement_level": 0.0,
            "participating_modules": [],
            "disagreements": []
        }
    
    # Extract verdicts and confidences
    verdicts = []
    confidences = []
    module_names = []
    
    for module_name, verdict_data in module_verdicts.items():
        verdicts.append(verdict_data["verdict"])
        confidences.append(verdict_data["confidence"])
        module_names.append(module_name)
    
    # Calculate verdict scores using ranking system
    verdict_scores = []
    for verdict in verdicts:
        score = VerdictAggregator.VERDICT_RANKINGS.get(verdict, 0.5)
        verdict_scores.append(score)
    
    # Weighted average based on confidence
    if confidences and sum(confidences) > 0:
        weighted_score = sum(score * conf for score, conf in zip(verdict_scores, confidences)) / sum(confidences)
    else:
        weighted_score = statistics.mean(verdict_scores) if verdict_scores else 0.5
    
    # Convert weighted score back to verdict
    consensus_verdict = VerdictAggregator._score_to_verdict(weighted_score)
    
    # Calculate agreement level
    unique_verdicts = set(verdicts)
    if len(unique_verdicts) == 1:
        agreement_level = 1.0  # Perfect agreement
    else:
        # Calculate how close verdicts are to each other
        score_variance = statistics.variance(verdict_scores) if len(verdict_scores) > 1 else 0
        agreement_level = max(0.0, 1.0 - (score_variance / 0.5))  # Normalize by expected max variance
    
    # Identify disagreements
    disagreements = VerdictAggregator._identify_disagreements(module_verdicts)
    
    # Calculate consensus confidence
    if agreement_level > 0.8:
        consensus_confidence = statistics.mean(confidences) if confidences else 0.5
    else:
        # Reduce confidence when there's disagreement
        consensus_confidence = statistics.mean(confidences) * agreement_level if confidences else 0.5
    
    return {
        "consensus_verdict": consensus_verdict,
        "consensus_confidence": round(consensus_confidence, 3),
        "agreement_level": round(agreement_level, 3),
        "participating_modules": module_names,
        "disagreements": disagreements,
        "weighted_score": round(weighted_score, 3),
        "verdict_distribution": dict(Counter(verdicts))
    }
    
    @staticmethod
    def _score_to_verdict(score: float) -> str:
        """Convert consensus score back to verdict."""
        if score >= 1.0:
            return "High_Confidence_Authentic"
        elif score >= 0.8:
            return "Authentic"
        elif score >= 0.6:
            return "Plausible"
        elif score >= 0.4:
            return "Unknown"
        elif score >= 0.2:
            return "Questionable"
        elif score >= 0.0:
            return "Suspicious"
        else:
            return "Synthetic"
    
    @staticmethod
    def _identify_disagreements(module_verdicts: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify and categorize disagreements between modules."""
        disagreements = []
        
        # Get verdict rankings for comparison
        module_rankings = {}
        for module_name, verdict_data in module_verdicts.items():
            verdict = verdict_data["verdict"]
            ranking = VerdictAggregator.VERDICT_RANKINGS.get(verdict, 0.5)
            module_rankings[module_name] = {
                "verdict": verdict,
                "ranking": ranking,
                "confidence": verdict_data["confidence"]
            }
        
        # Find pairs with significant disagreements
        modules = list(module_rankings.keys())
        for i in range(len(modules)):
            for j in range(i + 1, len(modules)):
                module1, module2 = modules[i], modules[j]
                
                ranking1 = module_rankings[module1]["ranking"]
                ranking2 = module_rankings[module2]["ranking"]
                
                # Significant disagreement threshold
                if abs(ranking1 - ranking2) > 0.4:
                    disagreement_type = "Major"
                elif abs(ranking1 - ranking2) > 0.2:
                    disagreement_type = "Minor"
                else:
                    continue
                
                disagreements.append({
                    "modules": [module1, module2],
                    "verdicts": [
                        module_rankings[module1]["verdict"],
                        module_rankings[module2]["verdict"]
                    ],
                    "ranking_difference": round(abs(ranking1 - ranking2), 3),
                    "disagreement_type": disagreement_type,
                    "confidence_difference": round(
                        abs(module_rankings[module1]["confidence"] - module_rankings[module2]["confidence"]), 3
                    )
                })
        
        return disagreements


# Fix the indentation issue
VerdictAggregator._score_to_verdict = lambda score: (
    "High_Confidence_Authentic" if score >= 1.0
    else "Authentic" if score >= 0.8
    else "Plausible" if score >= 0.6
    else "Unknown" if score >= 0.4
    else "Questionable" if score >= 0.2
    else "Suspicious" if score >= 0.0
    else "Synthetic"
)

VerdictAggregator._identify_disagreements = lambda module_verdicts: [
    {
        "modules": [module1, module2],
        "verdicts": [
            module_verdicts[module1]["verdict"],
            module_verdicts[module2]["verdict"]
        ],
        "ranking_difference": round(abs(
            VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module1]["verdict"], 0.5) -
            VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module2]["verdict"], 0.5)
        ), 3),
        "disagreement_type": (
            "Major" if abs(
                VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module1]["verdict"], 0.5) -
                VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module2]["verdict"], 0.5)
            ) > 0.4 else "Minor"
        ),
        "confidence_difference": round(abs(
            module_verdicts[module1]["confidence"] - module_verdicts[module2]["confidence"]
        ), 3)
    }
    for module1 in module_verdicts
    for module2 in module_verdicts
    if module1 < module2 and abs(
        VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module1]["verdict"], 0.5) -
        VerdictAggregator.VERDICT_RANKINGS.get(module_verdicts[module2]["verdict"], 0.5)
    ) > 0.2
]


def run(input_string: str, pipeline_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input string (for interface compatibility)
        pipeline_results: Complete results from pipeline modules
        
    Returns:
        Dict containing consensus voting results
    """
    if not pipeline_results:
        return {
            "detector": "consensus_voting",
            "consensus_verdict": "Insufficient_Data",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "CONSENSUS_VOTING: No pipeline results provided"
        }
    
    # Extract module verdicts
    module_verdicts = VerdictAggregator.extract_module_verdicts(pipeline_results)
    
    if not module_verdicts:
        return {
            "detector": "consensus_voting",
            "consensus_verdict": "No_Modules",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "CONSENSUS_VOTING: No compatible module verdicts found"
        }
    
    # Calculate consensus
    consensus_results = calculate_consensus(module_verdicts)
    
    # Determine final classification and modifiers
    consensus_verdict = consensus_results["consensus_verdict"]
    agreement_level = consensus_results["agreement_level"]
    disagreements = consensus_results["disagreements"]
    
    # Handle disagreement cases
    if len(disagreements) > 0 and agreement_level < 0.6:
        # Significant disagreements detected
        final_verdict = "Ambiguous"
        source_classification = "Questionable"
        echo_score_penalty = -5.0
        advisory_flag = f"CONSENSUS_VOTING: {len(disagreements)} major disagreement(s) between modules"
    elif agreement_level < 0.8:
        # Minor disagreements
        final_verdict = consensus_verdict
        source_classification = VerdictAggregator._verdict_to_source_class(consensus_verdict)
        echo_score_penalty = -2.0
        advisory_flag = "CONSENSUS_VOTING: Minor disagreements detected between modules"
    else:
        # Good consensus
        final_verdict = consensus_verdict
        source_classification = VerdictAggregator._verdict_to_source_class(consensus_verdict)
        
        if consensus_verdict in ["High_Confidence_Authentic", "Authentic"]:
            echo_score_modifier = 5.0
            echo_score_penalty = 0.0
            advisory_flag = None
        elif consensus_verdict in ["Synthetic", "Suspicious"]:
            echo_score_modifier = 0.0
            echo_score_penalty = -10.0
            advisory_flag = None
        else:
            echo_score_modifier = 1.0
            echo_score_penalty = 0.0
            advisory_flag = None
    
    # Compile results
    result = {
        "detector": "consensus_voting",
        "consensus_verdict": final_verdict,
        "source_classification": source_classification,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        "echo_score_penalty": locals().get("echo_score_penalty", 0.0),
        "consensus_results": consensus_results,
        "module_verdicts": module_verdicts,
        "disagreement_count": len(disagreements)
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
    
    return result


# Helper method for VerdictAggregator
VerdictAggregator._verdict_to_source_class = lambda verdict: (
    "Human-Generated" if verdict in ["Authentic", "High_Confidence_Authentic", "Plausible", "Normal", "Consistent"]
    else "AI-Generated" if verdict in ["Synthetic", "Suspicious", "Anomalous"]
    else "Questionable" if verdict in ["Questionable", "Ambiguous"]
    else "Unknown"
)