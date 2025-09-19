"""
Adaptive SBSM Module - ML/AI Gap Bridge
Implements adaptive refresh of SBSM reference vectors and contextual scoring modifiers
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
import logging
from collections import deque

logger = logging.getLogger(__name__)

class AdaptiveSBSMConfig:
    """Configuration for adaptive SBSM functionality"""
    
    def __init__(self):
        self.adaptive_refresh = os.getenv('SBSM_ADAPTIVE_REFRESH', 'true').lower() == 'true'
        self.confidence_threshold = float(os.getenv('SBSM_CONFIDENCE_THRESHOLD', '0.8'))
        self.update_frequency = int(os.getenv('SBSM_UPDATE_FREQUENCY', '100'))
        self.reference_vector_file = os.getenv('SBSM_REFERENCE_FILE', 'vault/sbsm_references.json')
        self.history_size = int(os.getenv('SBSM_HISTORY_SIZE', '1000'))

class ReferenceVectorManager:
    """Manages and updates SBSM reference vectors adaptively"""
    
    def __init__(self):
        self.config = AdaptiveSBSMConfig()
        self.reference_vectors = self._load_reference_vectors()
        self.detection_history = deque(maxlen=self.config.history_size)
        self.update_counter = 0
        
    def _load_reference_vectors(self) -> Dict[str, Any]:
        """Load reference vectors from storage"""
        try:
            if os.path.exists(self.config.reference_vector_file):
                with open(self.config.reference_vector_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load reference vectors: {e}")
        
        # Default reference vectors
        return {
            'human_generated': {
                'mean_vector': [0.5] * 16,
                'std_vector': [0.1] * 16,
                'sample_count': 0,
                'last_updated': datetime.now(timezone.utc).isoformat()
            },
            'ai_generated': {
                'mean_vector': [0.3] * 16,
                'std_vector': [0.15] * 16,
                'sample_count': 0,
                'last_updated': datetime.now(timezone.utc).isoformat()
            },
            'questionable': {
                'mean_vector': [0.4] * 16,
                'std_vector': [0.2] * 16,
                'sample_count': 0,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _save_reference_vectors(self):
        """Save reference vectors to storage"""
        try:
            os.makedirs(os.path.dirname(self.config.reference_vector_file), exist_ok=True)
            with open(self.config.reference_vector_file, 'w') as f:
                json.dump(self.reference_vectors, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save reference vectors: {e}")
    
    def update_reference_vector(self, classification: str, fold_vector: List[float], confidence: float):
        """Update reference vector with new field data"""
        if not self.config.adaptive_refresh:
            return
        
        if classification not in self.reference_vectors:
            logger.warning(f"Unknown classification: {classification}")
            return
        
        # Only update if we have reasonable confidence
        if confidence < self.config.confidence_threshold:
            return
        
        ref_data = self.reference_vectors[classification]
        
        # Convert to numpy for easier math
        fold_array = np.array(fold_vector)
        mean_array = np.array(ref_data['mean_vector'])
        std_array = np.array(ref_data['std_vector'])
        
        # Update sample count
        n = ref_data['sample_count']
        ref_data['sample_count'] = n + 1
        
        # Online update of mean and standard deviation
        if n == 0:
            # First sample
            ref_data['mean_vector'] = fold_vector
            ref_data['std_vector'] = [0.1] * len(fold_vector)  # Initial std
        else:
            # Incremental update using Welford's algorithm
            delta = fold_array - mean_array
            mean_array += delta / (n + 1)
            
            # Update variance estimate
            if n > 1:
                delta2 = fold_array - mean_array
                variance = (std_array ** 2 * (n - 1) + delta * delta2) / n
                std_array = np.sqrt(variance)
            
            ref_data['mean_vector'] = mean_array.tolist()
            ref_data['std_vector'] = std_array.tolist()
        
        ref_data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save periodically
        self.update_counter += 1
        if self.update_counter % 10 == 0:  # Save every 10 updates
            self._save_reference_vectors()
            logger.info(f"Updated {classification} reference vector (sample #{ref_data['sample_count']})")
    
    def get_adaptive_confidence(self, fold_vector: List[float]) -> Dict[str, float]:
        """Calculate confidence scores against adaptive reference vectors"""
        confidences = {}
        
        fold_array = np.array(fold_vector)
        
        for classification, ref_data in self.reference_vectors.items():
            mean_array = np.array(ref_data['mean_vector'])
            std_array = np.array(ref_data['std_vector'])
            
            # Calculate normalized distance (like z-score but multivariate)
            normalized_distances = np.abs((fold_array - mean_array) / (std_array + 1e-8))
            
            # Average normalized distance
            avg_distance = np.mean(normalized_distances)
            
            # Convert to confidence (lower distance = higher confidence)
            confidence = max(0.0, 1.0 - (avg_distance / 3.0))  # 3-sigma rule
            confidences[classification] = confidence
        
        return confidences

class ContextualScoringModifier:
    """Implements contextual scoring modifiers for detector disagreement"""
    
    def __init__(self):
        self.disagreement_threshold = 0.3  # Threshold for significant disagreement
        
    def calculate_detector_agreement(self, detector_results: Dict[str, Any]) -> float:
        """Calculate agreement level between detectors"""
        
        # Extract scores/modifiers from different detectors
        scores = []
        modifiers = []
        
        for detector_name, result in detector_results.items():
            if isinstance(result, dict):
                if 'echo_score_modifier' in result:
                    modifiers.append(result['echo_score_modifier'])
                if 'echo_score_penalty' in result:
                    modifiers.append(-abs(result['echo_score_penalty']))
                
                # Extract other relevant scores
                for key in ['confidence', 'authenticity_score', 'drift_score']:
                    if key in result:
                        scores.append(result[key])
        
        if not scores and not modifiers:
            return 0.5  # Neutral when no scores available
        
        # Combine scores and modifiers
        all_values = scores + modifiers
        
        if len(all_values) < 2:
            return 0.8  # High agreement when only one detector
        
        # Calculate coefficient of variation as disagreement measure
        mean_val = np.mean(all_values)
        std_val = np.std(all_values)
        
        if abs(mean_val) < 1e-8:  # Avoid division by zero
            agreement = 0.9 if std_val < 0.1 else 0.5
        else:
            cv = std_val / abs(mean_val)
            agreement = max(0.1, 1.0 - cv)  # Higher CV = lower agreement
        
        return min(1.0, agreement)
    
    def get_confidence_modifier(self, detector_results: Dict[str, Any], base_confidence: float) -> Tuple[float, str]:
        """Get confidence band modifier based on detector agreement"""
        
        agreement = self.calculate_detector_agreement(detector_results)
        
        if agreement < self.disagreement_threshold:
            # Significant disagreement - widen confidence band
            modifier = 0.3  # Reduce confidence by 30%
            reason = f"Detectors disagree (agreement: {agreement:.2f})"
        elif agreement > 0.8:
            # High agreement - maintain or slightly boost confidence
            modifier = 0.05  # Small boost
            reason = f"High detector agreement ({agreement:.2f})"
        else:
            # Moderate agreement - neutral
            modifier = 0.0
            reason = f"Moderate detector agreement ({agreement:.2f})"
        
        # Apply modifier
        adjusted_confidence = base_confidence * (1 - modifier) if modifier > 0 else base_confidence + modifier
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        return adjusted_confidence, reason

class ParadoxHooks:
    """RPS-1 Paradox Hooks for forward/backward symbolic binding (stubbed for now)"""
    
    def __init__(self):
        self.paradox_cache = {}
        self.binding_history = deque(maxlen=100)
    
    def forward_symbolic_binding(self, input_data: str, fold_vector: List[float]) -> Dict[str, Any]:
        """Forward symbolic binding hook (stubbed implementation)"""
        
        # Generate a simple paradox ID based on input
        paradox_id = f"FSB_{hash(input_data) % 10000:04X}"
        
        # Simple forward binding logic (placeholder)
        binding_strength = sum(fold_vector) / len(fold_vector) if fold_vector else 0.5
        
        result = {
            'paradox_id': paradox_id,
            'binding_type': 'forward',
            'binding_strength': binding_strength,
            'symbolic_anchor': input_data[:20],  # First 20 chars as anchor
            'temporal_index': len(self.binding_history),
            'status': 'bound' if binding_strength > 0.5 else 'unbound'
        }
        
        self.binding_history.append(result)
        self.paradox_cache[paradox_id] = result
        
        return result
    
    def backward_symbolic_binding(self, paradox_id: str, reference_vector: List[float]) -> Dict[str, Any]:
        """Backward symbolic binding hook (stubbed implementation)"""
        
        if paradox_id in self.paradox_cache:
            forward_result = self.paradox_cache[paradox_id]
            
            # Calculate binding coherence
            coherence = 0.8 if forward_result['status'] == 'bound' else 0.3
            
            result = {
                'paradox_id': paradox_id,
                'binding_type': 'backward',
                'coherence': coherence,
                'reference_match': sum(reference_vector) / len(reference_vector) if reference_vector else 0.5,
                'temporal_consistency': True,
                'resolution_state': 'resolved' if coherence > 0.5 else 'unresolved'
            }
        else:
            result = {
                'paradox_id': paradox_id,
                'binding_type': 'backward',
                'error': 'paradox_not_found',
                'resolution_state': 'failed'
            }
        
        return result
    
    def paradox_synthesis(self, input_data: str, fold_vector: List[float]) -> Dict[str, Any]:
        """Synthesize paradox analysis combining forward and backward binding"""
        
        forward = self.forward_symbolic_binding(input_data, fold_vector)
        backward = self.backward_symbolic_binding(forward['paradox_id'], fold_vector)
        
        synthesis = {
            'forward_binding': forward,
            'backward_binding': backward,
            'synthesis_score': (forward['binding_strength'] + backward.get('coherence', 0)) / 2,
            'paradox_resolved': forward['status'] == 'bound' and backward['resolution_state'] == 'resolved'
        }
        
        return synthesis

# Global instances
reference_manager = ReferenceVectorManager()
contextual_modifier = ContextualScoringModifier()
paradox_hooks = ParadoxHooks()

def adaptive_sbsm_analysis(sbsm_result: Dict[str, Any], detector_results: Dict[str, Any]) -> Dict[str, Any]:
    """Main adaptive SBSM analysis function"""
    
    # Extract relevant data
    fold_vector = sbsm_result.get('fold_vector', [0.5] * 16)
    classification = sbsm_result.get('source_classification', 'Unknown')
    base_confidence = sbsm_result.get('confidence', 0.5)
    
    # Get adaptive confidence scores
    adaptive_confidences = reference_manager.get_adaptive_confidence(fold_vector)
    
    # Get contextual modifier
    adjusted_confidence, modifier_reason = contextual_modifier.get_confidence_modifier(
        detector_results, base_confidence
    )
    
    # Update reference vectors if we have a valid classification
    if classification != 'Unknown' and classification.lower().replace('-', '_') in reference_manager.reference_vectors:
        reference_manager.update_reference_vector(
            classification.lower().replace('-', '_'), 
            fold_vector, 
            adjusted_confidence
        )
    
    # Paradox synthesis
    input_data = sbsm_result.get('input', '')
    paradox_analysis = paradox_hooks.paradox_synthesis(input_data, fold_vector)
    
    return {
        'adaptive_confidences': adaptive_confidences,
        'original_confidence': base_confidence,
        'adjusted_confidence': adjusted_confidence,
        'confidence_modifier_reason': modifier_reason,
        'detector_agreement': contextual_modifier.calculate_detector_agreement(detector_results),
        'paradox_analysis': paradox_analysis,
        'ml_drift_immunity': {
            'adaptive_vectors': True,
            'reference_stability': len(reference_manager.detection_history),
            'update_frequency': reference_manager.update_counter
        }
    }

def get_ml_drift_immunity_status() -> Dict[str, Any]:
    """Get current ML drift immunity status"""
    return {
        'adaptive_refresh_enabled': reference_manager.config.adaptive_refresh,
        'reference_vectors_loaded': len(reference_manager.reference_vectors),
        'total_updates': reference_manager.update_counter,
        'history_size': len(reference_manager.detection_history),
        'last_vector_update': max([
            ref['last_updated'] for ref in reference_manager.reference_vectors.values()
        ]) if reference_manager.reference_vectors else None,
        'immunity_level': 'HIGH' if reference_manager.update_counter > 50 else 'MODERATE'
    }