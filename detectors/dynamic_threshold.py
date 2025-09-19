"""
Dynamic Thresholding and Confidence Bands - Adaptive scoring system
Replaces hard-coded cutoffs with adaptive thresholds based on rolling baselines.
"""

import json
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from collections import deque
import statistics


class BaselineManager:
    """Manages rolling baselines and adaptive thresholds."""
    
    def __init__(self, baseline_file: str = "baseline_data.json", max_samples: int = 1000):
        """
        Initialize baseline manager.
        
        Args:
            baseline_file: Path to store baseline data
            max_samples: Maximum number of samples to keep in rolling window
        """
        self.baseline_file = baseline_file
        self.max_samples = max_samples
        self.baselines = {
            "delta_s": deque(maxlen=max_samples),
            "sbsm_drift": deque(maxlen=max_samples),
            "echo_sense": deque(maxlen=max_samples),
            "quirk_score": deque(maxlen=max_samples),
            "timestamps": deque(maxlen=max_samples)
        }
        self._load_baselines()
    
    def _get_baseline_path(self) -> str:
        """Get the full path for baseline storage."""
        # Store in vault directory if it exists, otherwise current directory
        vault_dir = os.path.join(os.path.dirname(__file__), "..", "vault")
        if os.path.exists(vault_dir):
            return os.path.join(vault_dir, self.baseline_file)
        return self.baseline_file
    
    def _load_baselines(self):
        """Load existing baseline data from file."""
        try:
            filepath = self._get_baseline_path()
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                for key, values in data.get("baselines", {}).items():
                    if key in self.baselines and isinstance(values, list):
                        # Load values into deque
                        self.baselines[key] = deque(values[-self.max_samples:], maxlen=self.max_samples)
                        
        except Exception as e:
            # If loading fails, start with empty baselines
            pass
    
    def _save_baselines(self):
        """Save current baseline data to file."""
        try:
            data = {
                "baselines": {key: list(values) for key, values in self.baselines.items()},
                "last_updated": time.time(),
                "max_samples": self.max_samples
            }
            
            filepath = self._get_baseline_path()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            # Silently handle save errors to avoid breaking pipeline
            pass
    
    def add_sample(self, metric_name: str, value: float, authentic: bool = True):
        """
        Add a sample to the baseline if it's from authentic content.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            authentic: Whether this sample is from verified authentic content
        """
        if authentic and metric_name in self.baselines:
            self.baselines[metric_name].append(value)
            self.baselines["timestamps"].append(time.time())
            
            # Periodically save baselines
            if len(self.baselines[metric_name]) % 10 == 0:
                self._save_baselines()
    
    def get_adaptive_threshold(self, metric_name: str, confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate adaptive threshold based on rolling baseline.
        
        Args:
            metric_name: Name of the metric
            confidence_level: Confidence level for threshold calculation
            
        Returns:
            Dict with threshold statistics
        """
        if metric_name not in self.baselines or len(self.baselines[metric_name]) < 5:
            # Fallback to default thresholds
            defaults = {
                "delta_s": {"mean": 0.005, "std": 0.002, "threshold_low": 0.001, "threshold_high": 0.01, "freshness": 0.5},
                "sbsm_drift": {"mean": 2.0, "std": 1.0, "threshold_low": 0.5, "threshold_high": 5.0, "freshness": 0.5},
                "echo_sense": {"mean": 0.8, "std": 0.1, "threshold_low": 0.6, "threshold_high": 0.95, "freshness": 0.5},
                "quirk_score": {"mean": 0.4, "std": 0.2, "threshold_low": 0.1, "threshold_high": 0.8, "freshness": 0.5}
            }
            return defaults.get(metric_name, {"mean": 0.5, "std": 0.1, "threshold_low": 0.3, "threshold_high": 0.7, "freshness": 0.5})
        
        values = list(self.baselines[metric_name])
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.1
        
        # Calculate confidence bands
        z_score = 1.96 if confidence_level >= 0.95 else 1.645  # 95% or 90% confidence
        
        threshold_low = mean_val - (z_score * std_val)
        threshold_high = mean_val + (z_score * std_val)
        
        return {
            "mean": round(mean_val, 6),
            "std": round(std_val, 6),
            "threshold_low": round(threshold_low, 6),
            "threshold_high": round(threshold_high, 6),
            "confidence_level": confidence_level,
            "sample_count": len(values),
            "freshness": self._calculate_freshness()
        }
    
    def _calculate_freshness(self) -> float:
        """Calculate how fresh/recent the baseline data is."""
        if not self.baselines["timestamps"]:
            return 0.0
        
        current_time = time.time()
        timestamps = list(self.baselines["timestamps"])
        
        # Calculate weighted freshness based on recency
        total_weight = 0
        weighted_freshness = 0
        
        for timestamp in timestamps:
            age_days = (current_time - timestamp) / (24 * 3600)
            # Exponential decay: fresh data (0-7 days) = 1.0, older data decays
            freshness = max(0.1, 1.0 * (0.9 ** age_days))
            weight = 1.0 / (1 + age_days)  # More recent data has higher weight
            
            weighted_freshness += freshness * weight
            total_weight += weight
        
        return round(weighted_freshness / max(total_weight, 1), 3)


# Global baseline manager instance
baseline_manager = BaselineManager()


def calculate_confidence_intervals(
    value: float, 
    metric_name: str, 
    confidence_levels: List[float] = [0.68, 0.95, 0.99]
) -> Dict[str, Any]:
    """
    Calculate confidence intervals for a given value and metric.
    
    Args:
        value: The observed value
        metric_name: Name of the metric
        confidence_levels: List of confidence levels to calculate
        
    Returns:
        Confidence interval data
    """
    intervals = {}
    baseline_stats = baseline_manager.get_adaptive_threshold(metric_name, 0.95)
    
    mean_val = baseline_stats["mean"]
    std_val = baseline_stats["std"]
    
    # Calculate z-scores for different confidence levels
    z_scores = {0.68: 1.0, 0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    
    for conf_level in confidence_levels:
        z_score = z_scores.get(conf_level, 1.96)
        
        lower_bound = mean_val - (z_score * std_val)
        upper_bound = mean_val + (z_score * std_val)
        
        # Check if value falls within confidence interval
        within_interval = lower_bound <= value <= upper_bound
        
        # Calculate how many standard deviations away from mean
        z_distance = abs(value - mean_val) / max(std_val, 0.001)
        
        intervals[f"{int(conf_level*100)}%"] = {
            "lower_bound": round(lower_bound, 6),
            "upper_bound": round(upper_bound, 6),
            "within_interval": within_interval,
            "z_distance": round(z_distance, 3)
        }
    
    return {
        "value": value,
        "baseline_mean": mean_val,
        "baseline_std": std_val,
        "intervals": intervals,
        "baseline_freshness": baseline_stats.get("freshness", 0.0)
    }


def adaptive_classification(
    metrics: Dict[str, float],
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    Perform adaptive classification based on dynamic thresholds.
    
    Args:
        metrics: Dictionary of metric values
        strict_mode: Whether to use stricter thresholds
        
    Returns:
        Classification results with confidence bands
    """
    results = {
        "classifications": {},
        "confidence_intervals": {},
        "adaptive_thresholds": {},
        "overall_confidence": 0.0
    }
    
    confidence_scores = []
    
    for metric_name, value in metrics.items():
        # Get adaptive threshold
        threshold_data = baseline_manager.get_adaptive_threshold(metric_name)
        results["adaptive_thresholds"][metric_name] = threshold_data
        
        # Calculate confidence intervals
        conf_intervals = calculate_confidence_intervals(value, metric_name)
        results["confidence_intervals"][metric_name] = conf_intervals
        
        # Classify based on adaptive thresholds
        classification = "Unknown"
        confidence = 0.5
        
        if value < threshold_data["threshold_low"]:
            classification = "Suspicious"
            confidence = 0.2
        elif value > threshold_data["threshold_high"]:
            if metric_name in ["echo_sense", "quirk_score"]:
                classification = "Authentic"
                confidence = 0.9
            else:
                classification = "Anomalous"
                confidence = 0.3
        else:
            # Within normal range
            classification = "Normal"
            # Confidence based on distance from mean
            distance_from_mean = abs(value - threshold_data["mean"])
            max_distance = max(
                threshold_data["threshold_high"] - threshold_data["mean"],
                threshold_data["mean"] - threshold_data["threshold_low"]
            )
            confidence = 1.0 - (distance_from_mean / max(max_distance, 0.001))
            confidence = max(0.5, min(0.9, confidence))
        
        # Adjust confidence based on baseline freshness
        freshness = threshold_data["freshness"]
        confidence *= (0.5 + 0.5 * freshness)  # Reduce confidence for stale baselines
        
        results["classifications"][metric_name] = {
            "value": value,
            "classification": classification,
            "confidence": round(confidence, 3),
            "within_95_ci": conf_intervals["intervals"]["95%"]["within_interval"]
        }
        
        confidence_scores.append(confidence)
    
    # Calculate overall confidence
    if confidence_scores:
        results["overall_confidence"] = round(statistics.mean(confidence_scores), 3)
    
    return results


def update_baselines_from_results(
    results: Dict[str, Any],
    authentic_verdict: bool = True
):
    """
    Update rolling baselines with new authentic results.
    
    Args:
        results: Pipeline results dictionary
        authentic_verdict: Whether the results are from verified authentic content
    """
    # Extract relevant metrics from results
    metrics_to_track = {}
    
    # EchoVerifier results
    if "echoverifier" in results:
        ev_result = results["echoverifier"]
        if "delta_s" in ev_result:
            metrics_to_track["delta_s"] = ev_result["delta_s"]
        if "echo_sense" in ev_result:
            metrics_to_track["echo_sense"] = ev_result["echo_sense"]
    
    # SBSM results
    if "sbsm" in results:
        sbsm_result = results["sbsm"]
        if "global_drift" in sbsm_result:
            metrics_to_track["sbsm_drift"] = sbsm_result["global_drift"]
    
    # Quirk injection results
    if "quirk_injection" in results:
        quirk_result = results["quirk_injection"]
        if "quirk_score" in quirk_result:
            metrics_to_track["quirk_score"] = quirk_result["quirk_score"]
    
    # Add samples to baseline manager
    for metric_name, value in metrics_to_track.items():
        baseline_manager.add_sample(metric_name, value, authentic_verdict)


def run(input_string: str, pipeline_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Interface function for the EchoScan pipeline.
    
    Args:
        input_string: Input string (for interface compatibility)
        pipeline_results: Results from other pipeline modules
        
    Returns:
        Dict containing dynamic threshold analysis results
    """
    if not pipeline_results:
        return {
            "detector": "dynamic_threshold",
            "verdict": "Insufficient_Data",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "DYNAMIC_THRESHOLD: No pipeline results provided"
        }
    
    # Extract metrics from pipeline results
    metrics = {}
    
    # Extract from various modules
    for module_name, module_result in pipeline_results.items():
        if isinstance(module_result, dict):
            if "delta_s" in module_result:
                metrics["delta_s"] = module_result["delta_s"]
            if "global_drift" in module_result:
                metrics["sbsm_drift"] = module_result["global_drift"]
            if "echo_sense" in module_result:
                metrics["echo_sense"] = module_result["echo_sense"]
            if "quirk_score" in module_result:
                metrics["quirk_score"] = module_result["quirk_score"]
    
    if not metrics:
        return {
            "detector": "dynamic_threshold",
            "verdict": "No_Metrics",
            "source_classification": "Unknown",
            "echo_score_modifier": 0.0,
            "advisory_flag": "DYNAMIC_THRESHOLD: No compatible metrics found"
        }
    
    # Perform adaptive classification
    classification_results = adaptive_classification(metrics)
    
    # Determine overall verdict based on classifications
    classifications = classification_results["classifications"]
    overall_confidence = classification_results["overall_confidence"]
    
    suspicious_count = sum(1 for c in classifications.values() if c["classification"] == "Suspicious")
    anomalous_count = sum(1 for c in classifications.values() if c["classification"] == "Anomalous")
    authentic_count = sum(1 for c in classifications.values() if c["classification"] == "Authentic")
    
    # Verdict logic
    if suspicious_count > len(classifications) / 2:
        verdict = "Suspicious"
        source_classification = "AI-Generated"
        echo_score_penalty = -15.0
        advisory_flag = "DYNAMIC_THRESHOLD: Multiple metrics flagged as suspicious"
    elif anomalous_count > 0 and overall_confidence < 0.6:
        verdict = "Anomalous"
        source_classification = "Questionable"
        echo_score_penalty = -8.0
        advisory_flag = "DYNAMIC_THRESHOLD: Anomalous patterns with low confidence"
    elif authentic_count > 0 and overall_confidence > 0.8:
        verdict = "High_Confidence_Authentic"
        source_classification = "Human-Generated"
        echo_score_modifier = 8.0
        echo_score_penalty = 0.0
        advisory_flag = None
    elif overall_confidence > 0.7:
        verdict = "Normal"
        source_classification = "Human-Generated"
        echo_score_modifier = 2.0
        echo_score_penalty = 0.0
        advisory_flag = None
    else:
        verdict = "Low_Confidence"
        source_classification = "Unknown"
        echo_score_modifier = 0.0
        echo_score_penalty = -2.0
        advisory_flag = "DYNAMIC_THRESHOLD: Low confidence in classification"
    
    # Compile results
    result = {
        "detector": "dynamic_threshold",
        "verdict": verdict,
        "source_classification": source_classification,
        "echo_score_modifier": locals().get("echo_score_modifier", 0.0),
        "echo_score_penalty": locals().get("echo_score_penalty", 0.0),
        "overall_confidence": overall_confidence,
        "classification_results": classification_results,
        "baseline_freshness": (
            min(t["freshness"] for t in classification_results["adaptive_thresholds"].values())
            if classification_results["adaptive_thresholds"]
            else 0.0
        )
    }
    
    if advisory_flag:
        result["advisory_flag"] = advisory_flag
    
    return result