#!/usr/bin/env python3
"""
EchoScan API Server - Simple Flask API for the enhanced EchoScan system
Provides REST endpoints for the dashboard and external integrations.
"""

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-cors")

import json
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import echoverifier

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard


@app.route('/')
def dashboard():
    """Serve the dashboard HTML file."""
    return send_from_directory('.', 'dashboard.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint for EchoScan enhanced verification.
    
    Expected JSON payload:
    {
        "text": "Text to analyze",
        "options": {
            "enable_downstream": true,
            "include_provenance": true
        }
    }
    
    Returns enhanced EchoScan analysis results with all new features.
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text',
                'status': 'error'
            }), 400
        
        text = data['text']
        options = data.get('options', {})
        
        if not text.strip():
            return jsonify({
                'error': 'Text cannot be empty',
                'status': 'error'
            }), 400
        
        # Run EchoScan analysis with enhanced features
        result = echoverifier.run(text, mode="verify", **options)
        
        # Add API-specific metadata
        api_result = result.copy()
        api_result.update({
            'api_version': '2.0.0-enhanced',
            'status': 'success',
            'analysis_complete': True,
            'processing_time_ms': 'simulated',  # In real implementation, measure actual time
            'features_enabled': [
                'confidence_transparency',
                'consensus_voting', 
                'enhanced_vault_logging',
                'ambiguous_verdict_detection',
                'real_timestamps',
                'sha256_signatures',
                'dynamic_reference_vectors',
                'context_aware_penalties',
                'enhanced_motif_detection',
                'echofold_integration',
                'sds1_dna_arcs'
            ]
        })
        
        return jsonify(api_result)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'analysis_complete': False
        }), 500


@app.route('/api/export', methods=['POST'])
def export_analysis():
    """
    Export analysis results with full audit bundle.
    
    Expected JSON payload:
    {
        "text": "Text to analyze and export"
    }
    
    Returns enhanced export data with timestamps, signatures, and audit trails.
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text',
                'status': 'error'
            }), 400
        
        text = data['text']
        
        if not text.strip():
            return jsonify({
                'error': 'Text cannot be empty',
                'status': 'error'
            }), 400
        
        # Get export data from enhanced EchoVerifier
        export_data = echoverifier.echoverifier.export_verifier(text)
        
        return jsonify({
            'status': 'success',
            'export_data': json.loads(export_data),
            'format': 'echoscan_v2_enhanced'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0-enhanced',
        'features': {
            'confidence_bands': True,
            'consensus_voting': True,
            'ambiguous_verdicts': True,
            'enhanced_vault_logging': True,
            'real_timestamps': True,
            'sha256_signatures': True,
            'color_coded_cli': True,
            'dynamic_thresholds': True,
            'enhanced_detectors': True,
            'dashboard_available': True
        },
        'endpoints': [
            '/api/analyze',
            '/api/export', 
            '/api/health',
            '/api/metrics'
        ]
    })


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics and detector information."""
    return jsonify({
        'system_metrics': {
            'detectors_available': [
                'sbsm_enhanced',
                'delta_s_enhanced', 
                'motif_enhanced',
                'echoarc_enhanced',
                'echofold_integrated',
                'glyph_classification',
                'ancestry_depth',
                'echosense_trust'
            ],
            'consensus_modules': 5,
            'confidence_calculation': 'multi_factor',
            'reference_vectors': 'rolling_baseline',
            'vault_logging': 'enhanced_with_provenance'
        },
        'detector_capabilities': {
            'motif': [
                'loop_recursion_detection',
                'missing_closure_analysis', 
                'parasite_glyph_detection',
                'sds1_dna_arc_mapping',
                'pattern_complexity_assessment'
            ],
            'echoarc': [
                'echofold_vector_integration',
                'trajectory_analysis',
                'sds1_dna_compatibility',
                'anomaly_detection',
                'genetic_naturalness_scoring'
            ],
            'delta_s': [
                'dynamic_baseline_calculation',
                'context_aware_penalties',
                'multi_window_analysis',
                'synthetic_likelihood_assessment',
                'stability_scoring'
            ]
        },
        'output_enhancements': {
            'confidence_band': 'numeric_0_to_1',
            'consensus_status': ['Strong', 'Weak', 'Ambiguous'],
            'intermediate_metrics': [
                'delta_s_variance',
                'fold_cosine',
                'ancestry_depth', 
                'quirk_count',
                'consensus_status'
            ],
            'provenance_chain': [
                'real_timestamps',
                'sha256_signatures',
                'audit_bundle',
                'decision_trace'
            ]
        }
    })


if __name__ == '__main__':
    if not FLASK_AVAILABLE:
        print("Flask is required to run the API server.")
        print("Install it with: pip install flask flask-cors")
        sys.exit(1)
    
    print("🚀 Starting EchoScan Enhanced API Server...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🔍 API endpoint: http://localhost:5000/api/analyze")
    print("📤 Export endpoint: http://localhost:5000/api/export")
    print("💚 Health check: http://localhost:5000/api/health")
    print("📈 Metrics: http://localhost:5000/api/metrics")
    
    app.run(debug=True, host='0.0.0.0', port=5000)