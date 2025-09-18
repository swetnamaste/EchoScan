# EchoScan — Math-Anchored Symbolic Detection Engine

EchoScan is an authenticity and anomaly detection toolkit for text, images, audio, and video streams.  
It combines symbolic hash, DNA-style encoding, paradox synthesis, and trust ancestry.

## Features

- SBSH (Symbolic Hash)
- EchoLock trust stack
- EchoVerifier firewall
- EchoSeal drift trace
- SDS-1 Symbolic DNA Sequencer
- RPS-1 Recursive Paradox Synthesizer
- CLI and API

## Usage

### CLI
```bash
python cli.py --symbolic-hash "Some text"
python cli.py --encode-dna "Some text"
python cli.py --paradox "Some phrase"
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

## Vault
All signatures, ancestry, DNA strands, and paradox locks are stored in `/vault/`.

## Extend
Add logic to any detector module in `detectors/`.

## License
MIT