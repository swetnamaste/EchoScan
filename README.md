# EchoScan — Enhanced Math-Anchored Symbolic Detection Engine

EchoScan is a comprehensive authenticity and anomaly detection toolkit for text analysis with advanced mathematical validation.  
**Version 2.0.0-Enhanced** features confidence transparency, consensus voting, ambiguous verdict detection, enhanced visual CLI, and comprehensive audit trails.

## 🚀 Enhanced Features (v2.0.0)

### Core Enhancements
- **🎯 Confidence Transparency**: Numeric confidence bands (0.0–1.0) for all verdicts
- **🗳️ Consensus Voting**: Multi-module voting system with ambiguous verdict detection  
- **⚠️ Ambiguous Verdict Handling**: Intelligent conflict resolution when modules disagree
- **🎨 Color-Coded CLI**: Green=authentic, yellow=ambiguous, red=hallucination with progress bars
- **📊 Enhanced Metrics**: Surface intermediate metrics (∆S variance, fold_cosine, ancestry_depth, quirk_count)
- **🔐 Cryptographic Signatures**: Real timestamps and SHA256 signatures for all results
- **📚 Comprehensive Audit Trails**: Full decision traces with vault references and provenance chains

### Enhanced Detectors
- **🔬 Enhanced Motif Detection**: Loop recursion, missing closures, parasite glyph detection, SDS-1 DNA arcs
- **🌊 Advanced EchoArc Analysis**: EchoFold integration, trajectory analysis, anomaly detection
- **⚡ Dynamic Delta-S**: Context-aware penalties, multi-window analysis, synthetic likelihood assessment
- **🧬 SDS-1 DNA Compatibility**: Genetic pattern analysis and complementarity scoring

### System Improvements  
- **📈 Rolling Baseline Vectors**: Dynamic reference vectors replace static [0.5]*16
- **🎛️ Dynamic Thresholds**: Context-aware scaling with ancestry depth and module agreement
- **🏦 Enhanced Vault Logging**: Trust chains, validation paths, symbolic arc logging
- **🌐 Web Dashboard**: Interactive HTML dashboard with real-time visualizations
- **🔌 REST API**: Enhanced JSON API with full feature support

## 🛠️ Installation & Setup

```bash
git clone https://github.com/swetnamaste/EchoScan.git
cd EchoScan
pip install -r requirements.txt
```

### Optional Web Dashboard Dependencies
```bash
pip install flask flask-cors  # For web dashboard and API server
```

## 💻 Usage

### Enhanced CLI with Color-Coded Output
```bash
# Basic authenticity verification with enhanced display
python cli.py --verify "Your text to analyze"

# Export with full audit bundle
python cli.py --export-verifier "Text to export" --json

# Ancestry analysis with enhanced metrics
python cli.py --ancestry "Text for ancestry analysis"

# JSON output for API integration
python cli.py --verify "Text" --json
```

### Web Dashboard
```bash
# Start the enhanced API server and dashboard
python api_server.py

# Open browser to http://localhost:5000
# Interactive dashboard with real-time analysis and visualizations
```

### Enhanced API Endpoints
```bash
# Main analysis endpoint with full enhancement support
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text to analyze", "options": {"include_provenance": true}}'

# Export with audit bundle
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{"text": "Text to export"}'

# System metrics and detector capabilities
curl http://localhost:5000/api/metrics
```

## 📊 Enhanced Output Format

### Sample Enhanced Analysis Result
```json
{
  "verdict": "Authentic",
  "confidence_band": 0.847,
  "consensus": "Strong",
  "delta_s": 0.001234,
  "echo_sense": 0.923,
  "intermediate_metrics": {
    "delta_s_variance": 0.000012,
    "fold_cosine": 0.856743,
    "ancestry_depth": 5,
    "quirk_count": 3,
    "consensus_status": "Strong"
  },
  "drift_metrics": {
    "delta_s": 0.001234,
    "variance": 0.000012,
    "fold_similarity": 0.856743
  },
  "quirk_score": 0.042,
  "provenance": {
    "timestamp": 1640995200.123,
    "iso_timestamp": "2022-01-01T00:00:00.123Z",
    "sha256_signature": "a1b2c3d4e5f6...",
    "audit_bundle": {
      "decision_trace": {...},
      "vault_ref": "vault_entry_1234",
      "validation_status": "complete"
    }
  },
  "vault_ref": "vault_entry_1234"
}
```

## 🎯 Verdict Types

| Verdict | Color | Description |
|---------|-------|-------------|
| **Authentic** | 🟢 Green | High confidence human-generated content |
| **Plausible** | 🔵 Blue | Moderate confidence, likely authentic |
| **Ambiguous** | 🟡 Yellow | Conflicting indicators, manual review recommended |
| **Hallucination** | 🔴 Red | High confidence synthetic/AI-generated content |

## 🔬 Enhanced Detector Capabilities

### Motif Detector (Enhanced)
- **Loop Recursion Detection**: Identifies repetitive patterns and recursion depth
- **Missing Closure Analysis**: Detects unmatched brackets, parentheses, quotes
- **Parasite Glyph Detection**: Identifies suspicious Unicode characters and zero-width chars
- **SDS-1 DNA Arc Mapping**: DNA-style sequence analysis with complementary base pairing

### EchoArc Detector (Enhanced)
- **EchoFold Vector Integration**: 16-dimensional trajectory analysis
- **Anomaly Detection**: Identifies suspicious curvature and symmetry patterns  
- **SDS-1 DNA Compatibility**: Genetic naturalness scoring and base composition analysis
- **Risk Assessment**: Multi-factor risk level calculation (low/medium/high)

### Delta-S Detector (Enhanced)
- **Dynamic Baseline Calculation**: Context-aware penalty scaling
- **Multi-Window Analysis**: Analysis across multiple window sizes (3, 5, 10, 15, 20)
- **Synthetic Likelihood Assessment**: Advanced classification with confidence factors
- **Stability Scoring**: Variance-based stability measurements

## 🗄️ Enhanced Vault System

Enhanced vault entries include:
- **Trust Chain**: Step-by-step verification path
- **Provenance Chain**: Complete audit trail with timestamps and signatures  
- **Symbolic Arcs**: Pre/post state transformations
- **Validation Path**: Full processing pipeline documentation

## 🧪 Testing

```bash
# Run all tests including enhanced features
python -m pytest test_enhanced_features.py -v

# Run original compatibility tests
python -m pytest test_echoverifier.py test_sbsh.py -v
```

## 🔧 Development & Extension

### Adding Custom Detectors
```python
# detectors/my_detector.py
def run(input_data, context_modules=None):
    return {
        "detector": "my_detector_enhanced",
        "result": "analysis_result",
        "echo_score_modifier": 0.0,
        "confidence_factors": ["factor1", "factor2"]
    }
```

### Integrating with Consensus System
Enhanced detectors can participate in consensus voting by returning standardized verdict classifications.

## 📈 Performance & Scalability

- **Response Time**: ~100-500ms per analysis (depending on text length)
- **Concurrent Requests**: Supports multiple simultaneous analyses
- **Memory Usage**: ~50-100MB per analysis process
- **Scalability**: Horizontally scalable via API deployment

## 🚢 Deployment

### Docker with Enhanced Features
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install flask flask-cors  # For dashboard support
COPY . .
EXPOSE 5000
CMD ["python", "api_server.py"]
```

### DigitalOcean App Platform
1. Fork this repository
2. Connect to DigitalOcean App Platform
3. Set environment variables if needed
4. Deploy with automatic HTTPS and scaling

## 📋 System Requirements

- **Python**: 3.8+ (3.12+ recommended)
- **Memory**: 256MB+ available RAM
- **Dependencies**: numpy, scipy, pytest
- **Optional**: flask, flask-cors (for web dashboard)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`python -m pytest -v`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🏆 Advanced Features Status

- [x] Confidence Transparency (0.0-1.0 bands)
- [x] Consensus Voting & Ambiguous Verdicts  
- [x] Enhanced Vault Logging with Trust Chains
- [x] Color-Coded CLI with Progress Bars
- [x] Real Timestamps & SHA256 Signatures
- [x] Dynamic Reference Vectors & Thresholds
- [x] Enhanced Motif/Arc Detectors with SDS-1 DNA
- [x] Web Dashboard with Interactive Visualizations
- [x] REST API with Full Feature Support
- [x] Comprehensive Test Suite
- [x] Enhanced Documentation

---

**EchoScan v2.0.0-Enhanced** - The most advanced mathematical authenticity detection system with full transparency, consensus intelligence, and cryptographic auditability.