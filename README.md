# EchoScan — Math-Anchored Symbolic Detection Engine

EchoScan is an advanced authenticity and anomaly detection toolkit for text, images, audio, and video streams.  
It combines symbolic hash, DNA-style encoding, paradox synthesis, trust ancestry, and comprehensive monitoring.

## Features

### Core Detection
- **SBSH (Symbolic Hash)** - Mathematical authenticity validation
- **EchoVerifier** - Comprehensive authenticity firewall with drift detection
- **EchoLock** - Trust stack for secure authentication
- **EchoSeal** - Drift trace analysis
- **SDS-1 Symbolic DNA Sequencer** - Genetic-style pattern analysis
- **RPS-1 Recursive Paradox Synthesizer** - Paradox detection and resolution

### Hardening & Monitoring
- **Quarantine Manager** - Automatic edge case capture (drift > 0.02, unclassified glyphs, symbolic anomalies)
- **Performance Monitor** - Latency tracking with spike alerts and webhook notifications
- **Vault System** - Robust logging with retry and local backup fallback
- **Continuous Logger** - Field testing and anomaly tracking for rapid patching
- **Enhanced API** - Full metrics dashboard support with JSON export

## Installation

```bash
git clone https://github.com/swetnamaste/EchoScan.git
cd EchoScan
pip install -r requirements.txt
```

## Usage

### CLI Commands

#### Basic Operations
```bash
# Generate symbolic hash
python cli.py --symbolic-hash "Some text"

# Run full verification
python cli.py --verify "Some text"

# Check system status
python cli.py --status

# View quarantine statistics
python cli.py --quarantine-stats

# Show performance metrics
python cli.py --performance-stats
```

#### Advanced Monitoring
```bash
# View recent anomalies
python cli.py --recent-anomalies 20

# Export logs for analysis
python cli.py --export-logs "export.json" --log-type edge_cases --time-window 48

# Run full pipeline scan
python cli.py --full-scan input.txt --pipeline
```

#### EchoVerifier Operations
```bash
# Authenticity verification
python cli.py --verify "suspicious text"

# EchoLock unlock
python cli.py --unlock "locked content"

# Ancestry analysis
python cli.py --ancestry "text to trace"

# Export verification data
python cli.py --export-verifier "text" --json
```

#### SBSH Operations
```bash
# Compare hashes
python cli.py --compare-sbsh hash1.json hash2.json

# Export hash data
python cli.py --export-sbsh "text" --format json

# Chain linking
python cli.py --sbsh-chain-link "new text" --previous-hash "existing_hash"
```

### REST API

Start the API server:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### Endpoints

- `POST /verify` - Verify input data with full metrics
- `GET /status` - System status and statistics  
- `GET /metrics` - Performance metrics and anomaly summary
- `GET /quarantine` - Quarantine information
- `GET /logs` - Log entries and analysis
- `POST /export` - Export data for analysis
- `GET /health` - Health check

#### API Examples

```bash
# Verify content
curl -X POST "http://localhost:8000/verify" \
  -H "Content-Type: application/json" \
  -d '{"input_data": "test content", "mode": "verify"}'

# Get system status
curl "http://localhost:8000/status"

# Export metrics
curl -X POST "http://localhost:8000/export?data_type=metrics&hours=24"
```

### Python API

```python
import echoverifier
from quarantine_manager import quarantine_manager
from performance_monitor import performance_monitor

# Basic verification
result = echoverifier.run("test input", mode="verify")
print(f"Verdict: {result['verdict']}")

# Check quarantine stats
stats = quarantine_manager.get_quarantine_stats()
print(f"Quarantined items: {stats['total_quarantined']}")

# Performance monitoring
with performance_monitor.measure_operation("custom_operation"):
    # Your code here
    pass
```

## Output Fields

### EchoVerifier Results
- `verdict` - Final authenticity verdict (Authentic/Plausible/Hallucination)
- `delta_s` - Drift score (higher = more suspicious)
- `echo_sense` - Trust score (0-1, higher = more trustworthy)
- `glyph_id` - Glyph classification identifier
- `ancestry_depth` - Trust chain depth
- `vault_permission` - Whether result qualifies for vault storage
- `confidence_band` - Confidence assessment (high/medium/low)
- `provenance` - Traceability information
- `advisory_flags` - Warning/alert flags
- `quarantine` - Quarantine status and reason

### Performance Metrics
- `latency` - Operation time in seconds
- `requests_per_second` - Throughput rate
- `average_latency` - Mean response time
- `spike_alerts` - Performance spike notifications

## Edge Case Handling

### Automatic Quarantine Triggers
- **High Drift**: `delta_s > 0.02`
- **Unclassified Glyphs**: Unknown or unidentifiable patterns
- **Symbolic Anomalies**: AI-generated or questionable content
- **Low Authenticity**: `echo_sense < 0.1`
- **Empty/Invalid Input**: Missing or malformed data

### Performance Alerts
- **Absolute Latency**: Exceeds 5 seconds (configurable)
- **Performance Spikes**: 3x average latency (configurable)
- **Webhook Integration**: Slack/Discord notifications support

## Deployment

### Docker
```bash
docker build -t echoscan .
docker run -p 8000:8000 echoscan
```

### DigitalOcean App Platform
1. Connect GitHub repository
2. Configure build settings:
   - Build command: `pip install -r requirements.txt`
   - Run command: `uvicorn api:app --host 0.0.0.0 --port $PORT`

### Environment Variables
- `ECHOSCAN_LATENCY_THRESHOLD` - Performance alert threshold (default: 5.0)
- `ECHOSCAN_LOG_LEVEL` - Logging level (default: INFO)
- `ECHOSCAN_VAULT_BACKUP_DIR` - Backup directory (default: vault_backup)

## Directory Structure

```
EchoScan/
├── echoverifier.py         # Core verification engine
├── quarantine_manager.py   # Edge case quarantine system
├── performance_monitor.py  # Latency and spike monitoring
├── continuous_logger.py    # Field testing and anomaly logging
├── api.py                  # REST API with full metrics
├── cli.py                  # Enhanced command line interface
├── vault/                  # Storage with retry/fallback
│   ├── vault.py           # Enhanced vault system
│   └── echovault.py       # Integration hooks
├── detectors/             # Detection modules
│   ├── sbsm.py           # Symbolic matrix analysis
│   ├── delta_s.py        # Drift detection
│   ├── glyph.py          # Pattern classification
│   └── ...               # Additional detectors
├── logs/                  # Auto-generated log files
│   ├── edge_cases.log    # Anomaly tracking
│   ├── field_test.log    # Continuous testing
│   └── performance.log   # Performance metrics
├── quarantine/           # Auto-captured edge cases
│   ├── drift_anomalies/  # High drift cases
│   ├── symbolic_anomalies/ # AI-generated content
│   └── unclassified_glyphs/ # Unknown patterns
└── exports/              # Data export files
```

## Monitoring Integration

### Metrics Dashboard
- Real-time performance monitoring
- Anomaly detection trending
- Quarantine statistics
- Vault operation status

### Alert Webhooks
Configure webhook URLs for:
- Performance spike alerts
- Critical anomaly detection
- System health notifications

### Field Testing
Continuous logging enables:
- Rapid anomaly response
- Performance optimization
- Edge case improvement
- Production monitoring

## License
MIT