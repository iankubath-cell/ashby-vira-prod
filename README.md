# Ashby-Vira Semantic Engine

**Causal Validation Engine for Autonomous Systems**

Production-grade FastAPI backend that validates proposed interventions using semantic causal graphs. Prevents dangerous actions while approving safe ones, backed by causal reasoning rather than simple rules.

---

## Overview

Ashby-Vira operates at **Rung 2 (Intervention)** of Pearl's Ladder of Causation. It performs deterministic validation of proposed interventions against a domain-specific semantic causal graph, answering:

> *"If I perform this action, will it achieve my goal without causing catastrophes?"*

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Path Existence Check** | Does a valid causal path exist from intervention to goal? |
| **Safety Analysis** | Will this intervention cause cascading failures? |
| **Precondition Validation** | Are all prerequisites satisfied? |
| **Empirical Evidence** | Does historical data support this action? |
| **Auto-Repair** | Proposes fixes when validation fails |
| **System Health Monitoring** | Tracks drift and stability over time |

---

## Architecture# Ashby-Vira Semantic Engine

**Causal Validation Engine for Autonomous Systems**

Production-grade FastAPI backend that validates proposed interventions using semantic causal graphs. Prevents dangerous actions while approving safe ones, backed by causal reasoning rather than simple rules.

---

## Overview

Ashby-Vira operates at **Rung 2 (Intervention)** of Pearl's Ladder of Causation. It performs deterministic validation of proposed interventions against a domain-specific semantic causal graph, answering:

> *"If I perform this action, will it achieve my goal without causing catastrophes?"*

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Path Existence Check** | Does a valid causal path exist from intervention to goal? |
| **Safety Analysis** | Will this intervention cause cascading failures? |
| **Precondition Validation** | Are all prerequisites satisfied? |
| **Empirical Evidence** | Does historical data support this action? |
| **Auto-Repair** | Proposes fixes when validation fails |
| **System Health Monitoring** | Tracks drift and stability over time |

---

## Architecture

┌─────────────────────────────┐ │ API Server │ │ (FastAPI, Port 8000) │ └──────────┬──────────────────┘ │ ┌───────▼───────┐ ┌──────────────┐ │ Validator │ │ Immune │ │ (Vira) │ │ System │ │ - Graph Traversal│ │ - Health │ │ - 6-Check Logic│ │ Score │ │ - Decision Out│ │ - Drift Det.│ └───────────────┘ └──────────────┘

### Components

| Module | Purpose |
|--------|---------|
| `api_server.py` | FastAPI backend with REST endpoints |
| `validator.py` | ViraValidator with 6-check deterministic validation |
| `semantic_graph.py` | Domain-specific causal graph creation (infrastructure, healthcare) |
| `semantic_immune_system.py` | Health monitoring (score 0–100), drift detection, auto-calibration |
| `ashby_repair.py` | Proposes parameter adjustments when errors detected |
| `simulator.py` | Timeline/path execution simulation |

---

## Installation

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Setup

bash
Clone repository

git clone https://github.com/iankubath-cell/ashby-vira-prod.git cd ashby-vira-prod
Create virtual environment

python -m venv venv venv\Scripts\activate # Windows source venv/bin/activate # macOS/Linux
Install dependencies

pip install fastapi uvicorn pydantic networkx
Run server

python api_server.py

Server starts at: `http://localhost:8000`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/validate` | POST | Validate an intervention |
| `/repair` | POST | Get repair recommendations |
| `/simulate` | POST | Simulate timeline execution |
| `/health` | GET | System health status |
| `/state` | GET | Validator state/stats |
| `/immune/diagnostic` | POST | Run drift diagnostic |
| `/immune/dashboard` | GET | Health dashboard data |
| `/decay_cycle` | POST | Apply decay cycle manually |
| `/docs` | GET | Swagger UI documentation |

---

## Usage Examples

### Validate an Intervention

bash curl -X POST http://localhost:8000/validate
-H "Content-Type: application/json"
-d '{ "intervention": "SCALE_UP_REPLICAS", "current_state": {"cpu_percent": 50}, "goal_property": "Value" }'

**Response:**

json { "status": "APPROVED", "reason": "Intervention validated: Safe path exists, no catastrophes detected", "intervention": "SCALE_UP_REPLICAS", "path": ["SCALE_UP_REPLICAS", "system_stability"], "predicted_effect": 0.95, "conflicts": [], "risk_flags": [], "empirical_success_rate": 0.92 }

### Check System Health

bash curl http://localhost:8000/health

**Response:**

json { "status": "ok", "engine": "Ashby-Vira Semantic", "version": "3.2", "domain": "infrastructure", "graph_nodes": 3, "graph_edges": 1, "health_score": 100.0, "severity": "HEALTHY", "uptime_seconds": 3600.5 }

---

## Validation Status Types

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `APPROVED` | Validated: Safe path exists, high confidence | Execute intervention |
| `INCONCLUSIVE` | Low confidence: Requires human review | Escalate to operator |
| `FROZEN` | Blocked: Dangerous or catastrophic risk | Manual override required |

---

## Known Interventions

### Safe Interventions

| Intervention | Success Rate |
|--------------|--------------|
| `SCALE_UP_REPLICAS` | 92% |
| `ADD_MEMORY` | 87% |
| `INCREASE_CONNECTION_POOL` | 88% |
| `ENABLE_CACHING` | 85% |
| `RESTART_SERVICE` | 80% |

### Dangerous Interventions (Always Blocked)

- `FORCE_KILL_PODS`
- `DELETE_ALL_DATA`
- `DROP_DATABASE`
- `DISABLE_FIREWALL`
- `REMOVE_ALL_REPLICAS`

---

## Configuration

Environment Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `MAX_HISTORY_SIZE` | 1000 | Validation history window |
| `MAX_STRING_LEN` | 500 | String truncation limit |
| `ALLOWED_ORIGINS` | "*" | CORS origins |
| `RATE_LIMIT_PER_MINUTE` | 60 | Requests per minute |
| `RATE_LIMIT_TTL_SECONDS` | 300 | Rate limit window |

---

## Development

### Add Custom Interventions

python from validator import ViraValidator

validator = ViraValidator(domain="infrastructure")
Add safe intervention

validator.add_custom_intervention("CUSTOM_ACTION", success_rate=0.85)
Add dangerous intervention

validator.add_custom_intervention("DANGEROUS_ACTION", success_rate=0.0, is_dangerous=True)

### Domain Support

| Domain | Graph Type | Use Case |
|--------|------------|----------|
| `infrastructure` | Network/Service topology | DevOps, Kubernetes, cloud |
| `healthcare` | Clinical decision tree | Medical interventions |

To add new domains, extend `semantic_graph.py`.

---

## Shadow Monitoring (Experimental)

The `shadow_fseq_monitor.py` module provides **dual-track validation** research capabilities:

- **Bayesian Track**: Uses system health score as prior (trust-weighted)
- **Popperian Track**: Ignores health, tests evidence severity only

This runs in **shadow mode** — does not affect production decisions, only logs divergence events for calibration analysis.

bash
Standalone test

python shadow_fseq_monitor.py
View calibration report

python -c "from shadow_fseq_monitor import shadow_monitor; shadow_monitor.generate_calibration_report()"

---

## Research Context

This system implements findings from the **F-SEQ v2** paper:

> *"Corroboration as Decision Criterion: Competitive Under Weak Priors, Sample-Inefficient Under Strong Ones"*

Key insight: Different decision strategies work best in different regimes. The hybrid architecture uses Bayesian inference for routine decisions and Popperian corroboration as supervisory monitoring.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure all `.py` files are in the same directory |
| `Graph initialization failed` | Check `semantic_graph.py` for syntax errors |
| `Rate limit exceeded` | Increase `RATE_LIMIT_PER_MINUTE` env var |
| `Validation always APPROVED` | Verify graph has edges (minimal: 1 node, 1 edge) |

---

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT (Code), CC-BY-SA (Paper)

---

## Contact

- **Author:** Ian Kubath
- **Email:** [ViraListen@proton.me](mailto:ViraListen@proton.me)

---

**Version:** 3.2  
**Last Updated:** July 2026
