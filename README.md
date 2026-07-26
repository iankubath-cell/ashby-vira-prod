Ashby-Vira Semantic Engine



Causal Validation Engine for Autonomous Systems



Production-grade FastAPI backend that validates proposed interventions using semantic causal graphs. Prevents dangerous actions while approving safe ones, backed by causal reasoning rather than simple rules.

Overview



Ashby-Vira operates at Rung 2 (Intervention) of Pearl's Ladder of Causation. It performs deterministic validation of proposed interventions against a domain-specific semantic causal graph, answering:



&#x20;   "If I perform this action, will it achieve my goal without causing catastrophes?"



Key Capabilities

Feature 	Description

Path Existence Check 	Does a valid causal path exist from intervention to goal?

Safety Analysis 	Will this intervention cause cascading failures?

Precondition Validation 	Are all prerequisites satisfied?

Empirical Evidence 	Does historical data support this action?

Auto-Repair 	Proposes fixes when validation fails

System Health Monitoring 	Tracks drift and stability over time

Architecture Response:



┌─────────────────────────────────────────────────────────┐ │ API Server │ │ (FastAPI, Port 8000) │ └────────────┬───────────────────────┬────────────────────┘ │ │ ┌────────▼────────┐ ┌───────▼────────┐ │ Validator │ │ Immune │ │ (Vira) │ │ System │ │ - Graph Traversal │ - Health Score │ │ - 6-Check Logic │ - Drift Detect │ │ - Decision Output │ - Stability │ └─────────────────┘ └────────────────┘

Components

Module 	Purpose

api\_server.py 	FastAPI backend with REST endpoints

validator.py 	ViraValidator with 6-check deterministic validation

semantic\_graph.py 	Domain-specific causal graph creation (infrastructure, healthcare)

semantic\_immune\_system.py 	Health monitoring (score 0–100), drift detection, auto-calibration

ashby\_repair.py 	Proposes parameter adjustments when errors detected

simulator.py 	Timeline/path execution simulation

Installation

Prerequisites



&#x20;   Python 3.9+

&#x20;   Virtual environment (recommended)

&#x20;   Setup



bash Clone repository



git clone https://github.com/YOUR\_USERNAME/ashby-vira-prod.git cd ashby-vira-prod Create virtual environment



python -m venv venv venv\\Scripts\\activate # Windows source venv/bin/activate # macOS/Linux Install dependencies



pip install fastapi uvicorn pydantic networkx Run server



python api\_server.py



Server starts at: http://localhost:8000

API Endpoints

Endpoint 	Method 	Description

/validate 	POST 	Validate an intervention

/repair 	POST 	Get repair recommendations

/simulate 	POST 	Simulate timeline execution

/health 	GET 	System health status

/state 	GET 	Validator state/stats

/immune/diagnostic 	POST 	Run drift diagnostic

/immune/dashboard 	GET 	Health dashboard data

/decay\_cycle 	POST 	Apply decay cycle manually

/docs 	GET 	Swagger UI documentation

Usage Examples

Validate an Intervention



bash curl -X POST http://localhost:8000/validate -H "Content-Type: application/json" -d '{ "intervention": "SCALE\_UP\_REPLICAS", "current\_state": {"cpu\_percent": 50}, "goal\_property": "Value" }'



Response:



json { "status": "APPROVED", "reason": "Intervention validated: Safe path exists, no catastrophes detected", "intervention": "SCALE\_UP\_REPLICAS", "path": \["SCALE\_UP\_REPLICAS", "system\_stability"], "predicted\_effect": 0.95, "conflicts": \[], "risk\_flags": \[], "empirical\_success\_rate": 0.92 }

Check System Health



bash curl http://localhost:8000/health



Response:



json { "status": "ok", "engine": "Ashby-Vira Semantic", "version": "3.2", "domain": "infrastructure", "graph\_nodes": 3, "graph\_edges": 1, "health\_score": 100.0, "severity": "HEALTHY", "uptime\_seconds": 3600.5 }

Validation Status Types

Status 	Meaning 	Action Required

APPROVED 	Validated: Safe path exists, high confidence 	Execute intervention

INCONCLUSIVE 	Low confidence: Requires human review 	Escalate to operator

FROZEN 	Blocked: Dangerous or catastrophic risk 	Manual override required

Known Interventions

Safe Interventions

Intervention 	Success Rate

SCALE\_UP\_REPLICAS 	92%

ADD\_MEMORY 	87%

INCREASE\_CONNECTION\_POOL 	88%

ENABLE\_CACHING 	85%

RESTART\_SERVICE 	80%

Dangerous Interventions (Always Blocked)



&#x20;   FORCE\_KILL\_PODS

&#x20;   DELETE\_ALL\_DATA

&#x20;   DROP\_DATABASE

&#x20;   DISABLE\_FIREWALL

&#x20;   REMOVE\_ALL\_REPLICAS



Configuration



Environment Variables:

Variable 	Default 	Description

PORT 	8000 	Server port

MAX\_HISTORY\_SIZE 	1000 	Validation history window

MAX\_STRING\_LEN 	500 	String truncation limit

ALLOWED\_ORIGINS 	"\*" 	CORS origins

RATE\_LIMIT\_PER\_MINUTE 	60 	Requests per minute

RATE\_LIMIT\_TTL\_SECONDS 	300 	Rate limit window

Development

Add Custom Interventions



python from validator import ViraValidator



validator = ViraValidator(domain="infrastructure") Add safe intervention



validator.add\_custom\_intervention("CUSTOM\_ACTION", success\_rate=0.85) Add dangerous intervention



validator.add\_custom\_intervention("DANGEROUS\_ACTION", success\_rate=0.0, is\_dangerous=True)

Domain Support



Currently supported domains:

Domain 	Graph Type 	Use Case

infrastructure 	Network/Service topology 	DevOps, Kubernetes, cloud

healthcare 	Clinical decision tree 	Medical interventions



To add new domains, extend semantic\_graph.py.

Shadow Monitoring (Experimental)



The shadow\_fseq\_monitor.py module provides dual-track validation research capabilities:



&#x20;   Bayesian Track: Uses system health score as prior (trust-weighted)

&#x20;   Popperian Track: Ignores health, tests evidence severity only



This runs in shadow mode — does not affect production decisions, only logs divergence events for calibration analysis.

Shadow Monitor Commands



bash Standalone test



python shadow\_fseq\_monitor.py View calibration report (after running validations)



python -c "from shadow\_fseq\_monitor import shadow\_monitor; shadow\_monitor.generate\_calibration\_report()"

Research Context



This system implements findings from the F-SEQ v2 paper:



&#x20;   "Corroboration as Decision Criterion: Competitive Under Weak Priors, Sample-Inefficient Under Strong Ones"



Key insight: Different decision strategies work best in different regimes. The hybrid architecture uses Bayesian inference for routine decisions and Popperian corroboration as supervisory monitoring.



Paper: https://arxiv.org/\[REPLACE\_WITH\_ACTUAL\_URL]

Troubleshooting

Common Issues

Issue 	Solution

ModuleNotFoundError 	Ensure all .py files are in the same directory

Graph initialization failed 	Check semantic\_graph.py for syntax errors

Rate limit exceeded 	Increase RATE\_LIMIT\_PER\_MINUTE env var

Validation always APPROVED 	Verify graph has edges (minimal: 1 node, 1 edge)

Enable Debug Logging



python In api\_server.py



import logging logging.basicConfig(level=logging.DEBUG)

Contributing



&#x20;   Fork repository

&#x20;   Create feature branch (git checkout -b feature/amazing-feature)

&#x20;   Commit changes (git commit -m 'Add amazing feature')

&#x20;   Push to branch (git push origin feature/amazing-feature)

&#x20;   Open Pull Request



License



Copyright © 2026 Ashby Project. All rights reserved.

Acknowledgments



Built with:



&#x20;   FastAPI

&#x20;   NetworkX

&#x20;   Pydantic

&#x20;   Uvicorn



Research methodology based on F-SEQ v2 falsification protocol.



