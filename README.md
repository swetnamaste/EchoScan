# EchoScan — Math-Anchored Symbolic Detection Engine

EchoScan is an authenticity and anomaly detection toolkit for text, images, audio, and video streams.  
It combines symbolic hash, DNA-style encoding, paradox synthesis, and trust ancestry.

## Features

- SBSH (Symbolic Hash)
- EchoLock trust stack
- EchoVerifier firewall
- EchoSeal drift trace
- SDS-1 Symbolic DNA Sequencer
- RPS-1 Recursive Paradox Synthesizer (with forward/backward symbolic binding)
- CLI and API
- **NEW: Webhook Integration** - Slack, Teams, AWS Lambda, SIEM, Jira notifications
- **NEW: Adaptive ML/AI** - Self-updating reference vectors with ML drift immunity
- **NEW: UI Excitement Layer** - Confetti, balloons, fireworks for engaging user experience

## Ecosystem & Integrations

EchoScan now supports lightweight webhook notifications and JSON exports for enterprise integration:

### Webhook Support
- **Slack**: Rich message formatting with color-coded alerts
- **Microsoft Teams**: MessageCard format with status indicators  
- **AWS Lambda**: JSON payload for serverless processing
- **SIEM Systems**: CEF-formatted security events
- **Jira**: Auto-create issues for quarantined/critical detections

### Configuration
Copy `.env.example` to `.env` and configure your endpoints:
```bash
cp .env.example .env
# Edit .env with your webhook URLs and credentials
```

### JSON Export
Export EchoScan results in structured JSON format:
```bash
python cli.py --export-json "text to analyze" --output-file results.json
```

## Machine Learning / AI Gap Bridge

EchoScan implements adaptive ML features that provide immunity to black-box drift:

### Adaptive Reference Vectors
- **Auto-updating baselines**: SBSM reference vectors adapt with field data
- **Contextual scoring**: Confidence bands widen when detectors disagree
- **ML Drift Immunity**: Documented resistance to adversarial model attacks

### Paradox Hooks (RPS-1)
- **Forward/Backward Binding**: Symbolic anchoring with temporal consistency
- **Recursive Synthesis**: Multi-dimensional paradox resolution
- **Zero Trust Validation**: Mathematical verification without ML dependencies

Check ML status:
```bash
python cli.py --ml-status
```

## UI Polish (Excitement Layer)

Engaging visual feedback system with production-ready animations:

### Supported Effects
- **Confetti**: High-energy celebration for authentic content
- **Balloons**: Gentle floating animations for plausible results  
- **Fireworks**: Alert celebrations for AI detection
- **Sparkles**: Bonus effects for exceptional scores

### Framework Support
- **React**: Component examples with hooks integration
- **Vanilla JS**: Pure JavaScript implementation
- **Streamlit**: Python web app integration
- **CSS Animations**: Responsive balloon and sparkle effects

Demo the excitement layer:
```bash
python cli.py --excitement-demo "Authentic"
python cli.py --excitement-demo "Hallucination"
```

## Usage

### CLI
```bash
python cli.py --symbolic-hash "Some text"
python cli.py --encode-dna "Some text"
python cli.py --paradox "Some phrase"
python cli.py --verify "Content to analyze"

# New features
python cli.py --webhook-test
python cli.py --ml-status  
python cli.py --excitement-demo "Authentic"
python cli.py --export-json "text" --output-file output.json
```

### API
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Deployment (DigitalOcean)
1. Clone repo & build:
    ```bash
git clone https://github.com/swetnamaste/EchoScan.git
cd EchoScan
docker build -t echoscan .
```
2. Run container:
    ```bash
docker run -p 8000:8000 echoscan
```
3. Set up DigitalOcean App Platform or Droplet with above Docker setup.

## Production Integration

### Webhook Notifications
Configure webhook endpoints in `.env`:
- Set `ENABLE_WEBHOOKS=true` 
- Configure URL endpoints for your services
- Set authentication credentials for Jira/SIEM

### ML Drift Protection
EchoScan's mathematical foundation provides immunity to:
- **Adversarial ML attacks**: Symbolic hash cannot be spoofed by neural networks
- **Model drift**: Reference vectors adapt while maintaining mathematical integrity  
- **Black-box manipulation**: Zero dependency on external AI models
- **Prompt injection**: Symbolic analysis operates below language layer

### UI Integration
Include JavaScript files in your web application:
```html
<link rel="stylesheet" href="static/excitement.css">
<script src="static/excitement.js"></script>
<script>
// Trigger excitement based on EchoScan results
window.echoScanExcitement.trigger(excitementData);
</script>
```

## Vault
All signatures, ancestry, DNA strands, and paradox locks are stored in `/vault/`.

## Extend
Add logic to any detector module in `detectors/`.

## License
MIT