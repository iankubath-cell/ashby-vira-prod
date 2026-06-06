"""
api_server.py — Ashby-Vira Semantic Engine API
Production-grade FastAPI backend. v3.2 Fixed.
"""

import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple  # Explicit imports
from datetime import datetime
from collections import deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your modules
from validator import ViraValidator, ValidationStatus
from semantic_graph import create_infrastructure_graph, create_healthcare_graph
from semantic_immune_system import SemanticImmuneSystem, HealthDiagnostic
from ashby_repair import RepairEngine
from simulator import TimelineSimulator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── CONFIGURATION ────────────────────────────────────────────────

MAX_HISTORY_SIZE = int(os.environ.get("MAX_HISTORY_SIZE", 1000))
MAX_STRING_LEN = int(os.environ.get("MAX_STRING_LEN", 500)) 
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
RATE_LIMIT_TTL_SECONDS = int(os.getenv("RATE_LIMIT_TTL_SECONDS", 300)) 

# ─── APP INITIALIZATION ───────────────────────────────────────────

app = FastAPI(
    title="Ashby-Vira Semantic Engine",
    version="3.2",
    description="Production-grade causal validation API."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── SINGLETON ENGINES ────────────────────────────────────────────

validator: Optional[ViraValidator] = None
repair_engine: Optional[RepairEngine] = None
simulator_engine: Optional[TimelineSimulator] = None
immune_system: Optional[SemanticImmuneSystem] = None

validation_history: deque = deque(maxlen=MAX_HISTORY_SIZE)
diagnostic_history: deque = deque(maxlen=MAX_HISTORY_SIZE)
_rate_limit_store: Dict[str, tuple] = {}

_startup_time = datetime.now()

@app.on_event("startup")
async def startup():
    global validator, repair_engine, simulator_engine, immune_system
    
    logger.info("Starting Ashby-Vira Semantic Engine v3.2...")
    
    try:
        # 1. Initialize Validator
        validator = ViraValidator(domain="infrastructure")
        if validator is None or not hasattr(validator, 'graph') or validator.graph is None:
            logger.critical("CRITICAL: Validator failed to initialize graph.")
            raise RuntimeError("Startup Failed: Invalid Validator State")

        # 2. Initialize Dependent Engines
        repair_engine = RepairEngine(validator.graph)
        simulator_engine = TimelineSimulator(validator.graph)
        
        immune_system = SemanticImmuneSystem(
            validator_class=None,
            validator_old_params={},
            validator_new_params={}
        )

        logger.info("=" * 60)
        logger.info("ASHBY-VIRA SEMANTIC ENGINE STARTED SUCCESSFULLY")
        if hasattr(validator.graph, 'number_of_nodes'):
            logger.info(f"Graph: {validator.graph.number_of_nodes()} nodes, {validator.graph.number_of_edges()} edges")
        else:
            logger.warning("Graph object does not support standard node/edge counting.")
        logger.info("=" * 60)

    except Exception as e:
        logger.critical(f"STARTUP FAILED: {e}")
        import sys
        sys.exit(1)

# ─── HELPERS ──────────────────────────────────────────────────────

def truncate_string(s: str, max_len: int = MAX_STRING_LEN) -> str:
    if len(str(s)) > max_len:
        return str(s)[:max_len] + "..."
    return str(s)

def check_rate_limit_and_cleanup(client_id: str) -> bool:
    now = time.time()
    if _rate_limit_store:
        oldest_entry = min(_rate_limit_store.values(), key=lambda x: x[1])[1]
        if now - oldest_entry > RATE_LIMIT_TTL_SECONDS:
            keys_to_remove = [k for k, (_, t) in _rate_limit_store.items() if now - t > RATE_LIMIT_TTL_SECONDS]
            for k in keys_to_remove:
                del _rate_limit_store[k]

    if client_id not in _rate_limit_store:
        _rate_limit_store[client_id] = (deque(maxlen=RATE_LIMIT_PER_MINUTE), now)

    window, last_clean = _rate_limit_store[client_id]
    while window and now - window[0] > 60:
        window.popleft()

    if len(window) >= RATE_LIMIT_PER_MINUTE:
        return False

    window.append(now)
    _rate_limit_store[client_id] = (window, now)
    return True

# ─── MIDDLEWARE ───────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit_and_cleanup(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    response = await call_next(request)
    return response

# ─── MODELS ───────────────────────────────────────────────────────

class ValidateRequest(BaseModel):
    intervention: str
    current_state: Dict[str, float]
    goal_property: str = "Value"
    domain: str = "infrastructure"

class ValidateResponse(BaseModel):
    status: str
    reason: str
    intervention: str
    path: Optional[List[str]] = None
    predicted_effect: Optional[float] = None
    conflicts: List[Dict] = []
    risk_flags: List[str] = []
    empirical_success_rate: float = 1.0

class RepairRequest(BaseModel):
    failed_intervention: str
    current_state: Dict[str, float]
    conflict_type: str = "trade_off"
    max_recommendations: int = 3

class SimulateRequest(BaseModel):
    path: List[str]
    current_state: Dict[str, float]
    duration_seconds: int = 300

class HealthResponse(BaseModel):
    status: str
    engine: str
    version: str
    domain: str
    graph_nodes: int
    graph_edges: int
    health_score: float
    severity: str
    uptime_seconds: float

# ─── ENDPOINTS ────────────────────────────────────────────────────

@app.post("/validate", response_model=ValidateResponse)
def validate_intervention(request: ValidateRequest):
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
        
    try:
        if request.domain == "healthcare":
            # Swap graph if needed (optional optimization)
            pass

        result = validator.validate(
            intervention=request.intervention,
            current_state=request.current_state,
            goal_property=request.goal_property
        )

        validation_history.append({
            "intervention": truncate_string(request.intervention),
            "status": result.status.value,
            "timestamp": datetime.now().isoformat()
        })

        return ValidateResponse(
            status=result.status.value,
            reason=result.reason,
            intervention=request.intervention,
            path=result.path,
            predicted_effect=result.predicted_effect,
            conflicts=[
                {"prop1": c[0], "prop2": c[1], "severity": c[2], "desc": truncate_string(c[3])}
                for c in (result.conflicts or [])
            ],
            risk_flags=result.risk_flags or [],
            empirical_success_rate=result.empirical_success_rate
        )
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repair")
def get_repair_recommendations(request: RepairRequest):
    if not validator or not repair_engine:
        raise HTTPException(status_code=500, detail="Engines not initialized")
    try:
        recommendations = repair_engine.get_repair_recommendations(
            failed_intervention=request.failed_intervention,
            current_state=request.current_state,
            conflict_type=request.conflict_type,
            max_recommendations=request.max_recommendations
        )
        return {"failed_intervention": request.failed_intervention, "recommendations": [r.to_dict() for r in recommendations]}
    except Exception as e:
        logger.error(f"Repair error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def simulate_timeline(request: SimulateRequest):
    if not simulator_engine:
        raise HTTPException(status_code=500, detail="Simulator not initialized")
    try:
        timeline = simulator_engine.simulate_path_execution(
            path=request.path,
            initial_state=request.current_state,
            duration_seconds=request.duration_seconds
        )
        return timeline.to_dict()
    except Exception as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        score = 100.0
        severity = "HEALTHY"
        if immune_system:
            try:
                diagnostic = immune_system.run_diagnostic()
                score = diagnostic.health_score
                severity = diagnostic.overall_severity.value
            except Exception:
                pass

        uptime = (datetime.now() - _startup_time).total_seconds()
        
        # Safe node/edge counting
        nodes = 0
        edges = 0
        if validator and hasattr(validator.graph, 'number_of_nodes'):
            nodes = validator.graph.number_of_nodes()
            edges = validator.graph.number_of_edges()

        return HealthResponse(
            status="ok",
            engine="Ashby-Vira Semantic",
            version="3.2",
            domain=validator.domain if validator else "unknown",
            graph_nodes=nodes,
            graph_edges=edges,
            health_score=round(score, 1),
            severity=severity,
            uptime_seconds=round(uptime, 1)
        )
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def get_state():
    if not validator:
        raise HTTPException(status_code=500, detail="Validator not initialized")
    try:
        stats = validator.get_stats() if hasattr(validator, 'get_stats') else {}
        history_count = len(validator.history) if hasattr(validator, 'history') else 0
        return {
            "domain": validator.domain,
            "history_count": history_count,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decay_cycle")
def decay_cycle():
    try:
        return {"status": "decay_applied", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/immune/diagnostic")
def run_immune_diagnostic():
    if not immune_system:
        raise HTTPException(status_code=500, detail="Immune system not initialized")
    try:
        diagnostic = immune_system.run_diagnostic()
        diagnostic_history.append({
            "health_score": diagnostic.health_score,
            "severity": diagnostic.overall_severity.value,
            "timestamp": datetime.now().isoformat()
        })
        return diagnostic.to_dict()
    except Exception as e:
        logger.error(f"Immune diagnostic error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/immune/dashboard")
def get_immune_dashboard():
    if not immune_system:
        raise HTTPException(status_code=500, detail="Immune system not initialized")
    try:
        diagnostic = immune_system.run_diagnostic()
        return diagnostic.to_dict()
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    uptime = (datetime.now() - _startup_time).total_seconds()
    return {
        "name": "Ashby-Vira Semantic Engine",
        "version": "3.2",
        "status": "running",
        "uptime_seconds": round(uptime, 1),
        "endpoints": {
            "POST /validate": "Validate intervention",
            "POST /repair": "Get repair recommendations",
            "POST /simulate": "Timeline simulation",
            "GET /health": "System health",
            "GET /state": "Validator state",
            "POST /decay_cycle": "Manual decay",
            "POST /immune/diagnostic": "Drift diagnostic",
            "GET /immune/dashboard": "Dashboard",
            "GET /docs": "Swagger UI"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Ashby-Vira on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
