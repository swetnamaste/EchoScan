# EchoScan — Math-Anchored Symbolic Detection Engine

EchoScan is an authenticity and anomaly detection toolkit for text, images, audio, and video streams.  
It combines symbolic hash, DNA-style encoding, paradox synthesis, and trust ancestry with explainable AI and enterprise-grade security.

## Features

- **SBSH (Symbolic Hash)** - Mathematical fingerprinting for content authenticity
- **EchoLock trust stack** - Multi-layered verification system
- **EchoVerifier firewall** - Real-time authenticity validation with explanations
- **EchoSeal drift trace** - Content evolution tracking
- **SDS-1 Symbolic DNA Sequencer** - Genetic-style content encoding
- **RPS-1 Recursive Paradox Synthesizer** - Complex pattern analysis
- **CLI and API** - Full command-line and REST API access
- **Dashboard** - Interactive web interface with analytics
- **Explainability** - Human-readable explanations for all verdicts
- **Module Extensibility** - Plug-and-play detector system
- **Edge Case Hardening** - Ultra-minimal, unicode, and adversarial input support
- **Performance Benchmarking** - Built-in performance testing and optimization
- **Audit Trail** - Comprehensive security and compliance features

## New Fields and Capabilities

### Core Output Fields
- `verdict` - Authentic/Plausible/Hallucination classification
- `explanation` - Human-readable reason for verdict (e.g., "Verdict = Plausible (ΔS drift moderate, EchoSeal-SDS-1 disagreement)")
- `confidence_band` - High/Medium/Low confidence classification
- `trust_chain` - Full provenance path: SBSH→ΔS→Fold→Glyph→Ancestry→EchoSense
- `delta_s` - Mathematical drift measurement
- `echo_sense` - Trust scoring (0.0-1.0)
- `glyph_id` - Content fingerprint identifier
- `ancestry_depth` - Content lineage depth
- `vault_permission` - Secure storage qualification

## Usage

### Enhanced CLI

```bash
# Basic verification with explanation
python cli.py --verify "Your text here"

# Verbose analysis with detailed breakdown
python cli.py --verify "Your text here" --verbose

# Drill down into specific aspects
python cli.py --verify "Your text here" --drill provenance
python cli.py --verify "Your text here" --drill downstream
python cli.py --verify "Your text here" --drill metrics
python cli.py --verify "Your text here" --drill all

# Batch processing
python cli.py --batch "Text 1" "Text 2" "Text 3"

# Export audit trail
python cli.py --export-audit --output-file audit_report.json

# Signature verification
python cli.py --verify-signature "data" "signature_hash"

# JSON output format
python cli.py --verify "Your text here" --json
```

### API Server

```bash
# Start API server
python api.py

# Or with uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### API Endpoints

- `POST /api/verify` - Single text verification
- `POST /api/batch` - Batch processing with concurrent execution
- `GET /api/batch/{batch_id}/status` - Check batch processing status
- `POST /api/verify-signature` - Signature verification with SHA256 + timestamp
- `GET /api/detectors` - List available detectors
- `POST /api/detector/{name}/run` - Run specific detector
- `GET /api/health` - Health check
- `GET /api/stats` - System statistics

#### Example API Usage

```javascript
// Single verification
fetch('/api/verify', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'Your content here'})
})

// Batch processing
fetch('/api/batch', {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        texts: ['Text 1', 'Text 2', 'Text 3'],
        max_workers: 4
    })
})
```

### Interactive Dashboard

Open `http://localhost:8000/` after starting the API server to access the interactive dashboard featuring:

- Real-time drift analysis charts
- Ancestry depth distribution
- EchoSense score timeline
- Verdict distribution pie chart
- Filtering and tooltips
- Audit export functionality
- Batch analysis tools

### Module Extensibility

The detector registry system (`registry.json`) enables plug-and-play modules:

```bash
# List available detectors
python detector_registry.py --list

# Get registry information
python detector_registry.py --info

# Test specific detector
python detector_registry.py --test sbsm
```

#### Adding New Detectors

```json
{
  "detectors": {
    "my_new_detector": {
      "module": "detectors.my_detector",
      "class": "MyDetectorClass",
      "enabled": true,
      "description": "Custom detector description",
      "dependencies": ["existing_detector"]
    }
  }
}
```

### Edge Case Testing

Comprehensive edge case validation with test vectors:

```bash
# Run edge case test suite
python tests/edge_cases/test_edge_cases.py

# Run with pytest
pytest tests/edge_cases/ -v
```

Edge cases covered:
- Ultra-minimal inputs (1 character, empty strings)
- Unicode anomalies and mixed scripts  
- Adversarial symbolic attacks
- Non-English language texts
- Code mixed with natural language

### Performance Benchmarking  

```bash
# Run performance benchmarks
python tests/test_performance.py

# Run specific benchmarks with pytest
pytest tests/test_performance.py --benchmark-only
```

### Legacy Usage Examples

```bash
# Classic functionality still supported
python cli.py --symbolic-hash "Some text"
python cli.py --encode-dna "Some text" 
python cli.py --paradox "Some phrase"
python cli.py --unlock "Some text"
python cli.py --ancestry "Some text"
```

## Deployment

### Local Development
```bash
git clone https://github.com/swetnamaste/EchoScan.git
cd EchoScan
pip install -r requirements.txt
python api.py  # Start API server
```

### Docker Deployment
```bash
docker build -t echoscan .
docker run -p 8000:8000 echoscan
```

### DigitalOcean App Platform
1. Fork this repository
2. Connect to DigitalOcean App Platform
3. Configure build command: `pip install -r requirements.txt`
4. Configure run command: `python api.py`
5. Set port to 8000

## Security & Robustness

- **Signature Verification**: SHA256 + timestamp validation
- **Audit Bundles**: Hashed and signed transaction logs  
- **Chain Verification**: Full provenance validation before vault import
- **Edge Case Hardening**: Handles malformed, adversarial, and minimal inputs
- **Zero Neural Dependencies**: Pure mathematical approach, no external AI models

## Framework Architecture

```
Input → SBSH Hash → ΔS Analysis → EchoFold Vector → Glyph Classification 
  ↓
Ancestry Depth → EchoSense Score → Verdict + Explanation
  ↓  
Downstream Hooks: EchoSeal, EchoVault, SDS-1, RPS-1 → Final Result
```

## Vault

All signatures, ancestry, DNA strands, and paradox locks are stored in `/vault/`.

## Extend

- Add logic to any detector module in `detectors/`
- Register new detectors in `registry.json`
- Modules are automatically discovered and loaded

## Testing

```bash
# Run all tests
pytest

# Run specific test suites  
pytest test_echoverifier.py -v
pytest tests/edge_cases/ -v
pytest tests/test_performance.py --benchmark-only

# Run with coverage
pytest --cov=. --cov-report=html
```

## License

MIT