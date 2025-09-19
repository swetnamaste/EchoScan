# EchoScan — Math-Anchored Symbolic Detection Engine

EchoScan is an advanced authenticity and anomaly detection toolkit for text, images, audio, and video streams.  
It combines symbolic hash, DNA-style encoding, paradox synthesis, and trust ancestry with operational hardening and monitoring capabilities.

## 🚀 Features

### Core Detection Engines
- **SBSH (Symbolic Hash)** - Mathematical fingerprinting with drift detection
- **EchoVerifier** - Multi-tier authenticity validation with confidence scoring
- **EchoLock** - Trust stack with ancestry depth analysis
- **EchoSeal** - Drift trace monitoring with anomaly detection
- **SDS-1** - Symbolic DNA Sequencer for genetic-style encoding
- **RPS-1** - Recursive Paradox Synthesizer for complex pattern analysis

### Operational Hardening
- **Edge Case Monitoring** - Automated quarantine for drift anomalies (ΔS > 0.02)
- **User Feedback System** - Community-driven anomaly reporting with `edge_cases.log`
- **Performance Monitoring** - Request latency tracking with spike detection
- **Vault Failsafe** - Retry mechanism with secure fallback storage
- **Enhanced Output** - Confidence bands, trust chains, and detailed explanations

### API & Interfaces
- **REST API** - FastAPI-based with interactive documentation
- **CLI Interface** - Comprehensive command-line tools
- **Batch Processing** - Optimized multi-input verification
- **Signature Verification** - Cryptographic authenticity validation

## 📋 Enhanced Output Fields

EchoVerifier now returns comprehensive analysis including:

### Standard Fields
- `verdict` - Authentication result ("Authentic", "Plausible", "Hallucination")
- `delta_s` - Drift analysis score (anomaly threshold: > 0.02)
- `glyph_id` - Symbolic classification identifier
- `ancestry_depth` - Trust chain depth verification
- `echo_sense` - Mathematical trust scoring (0.0 - 1.0)
- `vault_permission` - Secure storage qualification

### Enhanced Fields
- **`confidence_band`** - Multi-factor confidence scoring with breakdown
  - `score` - Overall confidence (0.0 - 1.0)
  - `level` - Classification ("high", "medium", "low", "very_low")
  - `factors` - Contributing elements (echo_sense, drift_penalty, ancestry_bonus)

- **`trust_chain`** - Detailed verification pathway
  - `chain_links` - Step-by-step validation process
  - `chain_integrity` - Overall chain validation status
  - `trust_score` - Normalized trust based on chain depth

- **`explanation`** - Human-readable analysis
  - `summary` - Primary verdict explanation
  - `detailed_factors` - Contributing analysis elements
  - `recommendation` - Usage guidance based on results
  - `explanation_confidence` - Confidence in the explanation itself

## 🛠 Usage

### CLI Interface

#### Basic Verification
```bash
# Single input verification with enhanced output
python cli.py --verify "Your text here" --json

# Verbose mode with detailed logging
python cli.py --verify "Your text here" --verbose

# User feedback for anomaly reporting
python cli.py --feedback-log "Suspicious text here"
# (Interactive prompt for anomaly description)

# Provenance drill-down analysis
python cli.py --verify "Your text here" --drill provenance
```

#### Advanced CLI Options
```bash
# SBSH symbolic hash generation
python cli.py --symbolic-hash "Some text"

# Ancestry depth analysis
python cli.py --ancestry "Some text"

# EchoLock unlock procedure
python cli.py --unlock "Some text"

# Structured data export
python cli.py --export-verifier "Some text"

# Full detection pipeline
python cli.py --full-scan filename.txt --input-type text
```

### REST API

Start the API server:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### API Endpoints

**Single Verification**
```bash
curl -X POST "http://localhost:8000/verify" \
  -H "Content-Type: application/json" \
  -d '{"input_data": "Your text here", "verbose": true}'
```

**Batch Processing**
```bash
curl -X POST "http://localhost:8000/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": ["Text 1", "Text 2", "Text 3"],
    "enable_downstream": true
  }'
```

**Signature Verification**
```bash
curl -X POST "http://localhost:8000/verify-signature" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": "Your text here",
    "signature": "your_signature_here",
    "public_key": "optional_public_key"
  }'
```

**Anomaly Feedback**
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": "Anomalous text",
    "anomaly_description": "Unexpected behavior description"
  }'
```

### Example Output

```json
{
  "input": "This is a test message",
  "verdict": "Plausible",
  "delta_s": 0.0017,
  "confidence_band": {
    "score": 0.9746,
    "level": "high",
    "factors": {
      "base_echo_sense": 0.8916,
      "drift_penalty": 0.017,
      "ancestry_bonus": 0.1
    }
  },
  "trust_chain": {
    "total_levels": 8,
    "chain_integrity": "valid",
    "trust_score": 0.4
  },
  "explanation": {
    "summary": "Content shows mixed signals - could be authentic or generated",
    "recommendation": "Content requires additional verification - use caution in high-stakes applications",
    "explanation_confidence": "high"
  }
}
```

## 📝 Example Walkthroughs

### Text Analysis Example

**Input:** "This is a natural human-written message with normal characteristics."

**Expected Analysis:**
- High confidence score (> 0.8)
- "Authentic" verdict
- Low drift value (< 0.01)
- Detailed trust chain showing validation steps
- Clear explanation recommending high-trust usage

### Synthetic Content Detection

**Input:** "AI-generated synthetic artificial automated machine-produced content with repetitive algorithmic patterns."

**Expected Analysis:**
- "Hallucination" verdict
- Elevated drift score
- Quarantine trigger if ΔS > 0.02
- Detailed explanation of AI-generation indicators

### Image Processing Example

```bash
python cli.py --full-scan image.jpg --input-type image --json
```

**Expected Output:**
- Visual authenticity analysis
- Metadata extraction results
- Manipulation detection scores
- Provenance chain verification

### Audio Analysis Example

```bash
python cli.py --full-scan audio.wav --input-type audio --verbose
```

**Expected Output:**
- Acoustic authenticity validation
- Deepfake detection results
- Audio fingerprint analysis
- Voice synthesis indicators

## 🔍 Monitoring & Logging

### Edge Case Monitoring

The system automatically monitors for:
- **Drift Anomalies**: Inputs with ΔS > 0.02 → quarantined to `quarantine/`
- **Glyph Anomalies**: Unclassified glyph patterns → quarantined
- **User Reports**: Community feedback → logged to `edge_cases.log`

### Performance Monitoring

Request latency tracking with alerts:
- **Single Input**: Alert if > 500ms
- **Batch Processing**: Alert if > 5s
- **Logs**: Performance data in `perf.log`

### Logging Files

- `edge_cases.log` - Anomaly reports and quarantine events
- `perf.log` - Performance metrics and spike detection
- `quarantine/` - Suspicious inputs requiring review
- `vault_fallback/` - Backup storage for vault failures

## 🛡 Security & Reliability

### Vault Failsafe System
- Automatic retry (3 attempts) for vault logging failures
- Exponential backoff between retry attempts
- Secure fallback storage for critical data
- Comprehensive error logging and recovery

### Data Integrity
- Hash-based input verification
- Cryptographic signature validation
- Chain of custody tracking
- Audit trail maintenance

## 🚀 Deployment

### Local Development
```bash
git clone https://github.com/swetnamaste/EchoScan.git
cd EchoScan
pip install -r requirements.txt

# CLI usage
python cli.py --verify "test input"

# API server
uvicorn api:app --reload
```

### Docker Deployment
```bash
docker build -t echoscan .
docker run -p 8000:8000 echoscan
```

### DigitalOcean App Platform
1. Fork this repository
2. Connect to DigitalOcean App Platform
3. Configure environment variables if needed
4. Deploy with auto-scaling enabled

## 🔧 System Requirements

- Python 3.8+
- FastAPI for API functionality
- NumPy/SciPy for mathematical operations
- Storage space for quarantine and logging

## 📖 API Documentation

When running the API server, visit:
- **Interactive Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`
- **System Stats**: `http://localhost:8000/stats`

## 🏛 Vault Storage

All verification results, ancestry chains, DNA sequences, and paradox locks are securely stored in the `/vault/` directory with failsafe mechanisms for data integrity.

## 🔧 Extending EchoScan

Add custom detection logic to any module in `detectors/`:
- Create new detector following existing patterns
- Implement required methods for integration
- Add to downstream hooks for pipeline inclusion

## 📄 License

MIT License - See LICENSE file for details

---

**Integration Hooks Available:**
TraceView, EchoVault, CollapseGlyph, EchoCradle, EchoSense, PulseAdapt

**Enterprise Support:**
Contact for enterprise-scale deployment, custom integrations, and SLA support.