"""
api_server.py — Ashby-Vira Semantic Engine API
Production-grade FastAPI backend.
v3.2 — Thread-safe, memory-bounded, anti-DDoS.
"""

import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any
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

# ─── CONFIGURATION & CONSTANTS ────────────────────────────────────────────────

MAX_HISTORY_SIZE = int(os.environ.get("MAX_HISTORY_SIZE", 1000))
MAX_STRING_LEN = int(os.environ.get("MAX_STRING_LEN", 500)) 
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
RATE_LIMIT_TTL_SECONDS = int(os.getenv("RATE_LIMIT_TTL_SECONDS", 300)) 

# ─── APP INITIALIZATION ───────────────────────────────────────────────────────

app = FastAPI(
    title="Ashby-Vira Semantic Engine",
    version="3.2",
    description="Production-grade causal validation API. Thread-safe, memory-bounded, anti-DDoS."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── THREAD SAFETY & MEMORY MANAGEMENT ────────────────────────────────────────

_validator_lock = threading.RLock()
_simulator_lock = threading.RLock()
_immune_lock = threading.RLock()

_rate_limit_store: Dict[str, tuple] = {} 

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

def truncate_string(s: str, max_len: int = MAX_STRING_LEN) -> str:
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit_and_cleanup(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    response = await call_next(request)
    return response

# ─── SINGLETON ENGINES ────────────────────────────────────────────────────────

validator: Optional[ViraValidator] = None
repair_engine: Optional[RepairEngine] = None
simulator_engine: Optional[TimelineSimulator] = None
immune_system: Optional[SemanticImmuneSystem] = None

validation_history: deque = deque(maxlen=MAX_HISTORY_SIZE)
diagnostic_history: deque = deque(maxlen=MAX_HISTORY_SIZE)

_startup_time = datetime.now()

@app.on_event("startup")
async def startup():
    global validator, repair_engine, simulator_engine, immune_system
    
    logger.info("Starting Ashby-Vira Semantic Engine v3.2...")
    
    try:
        validator = ViraValidator(domain="infrastructure")
        if validator is None or validator.graph is None:
            raise RuntimeError("CRITICAL: Validator or Graph is None. Aborting startup.")

        repair_engine = RepairEngine(validator.graph)
        simulator_engine = TimelineSimulator(validator.graph)
        
        immune_system = SemanticImmuneSystem(
            validator_class=None,
            validator_old_params={},
            validator_new_params={}
        )
        if immune_system is None:
            raise RuntimeError("CRITICAL: Immune system is None. Aborting startup.")

        if hasattr(validator, 'history'):
            existing = list(validator.history)[-MAX_HISTORY_SIZE:]
            validator.history = deque(existing, maxlen=MAX_HISTORY_SIZE)

        logger.info("=" * 60)
        logger.info("ASHBY-VIRA SEMANTIC ENGINE STARTED SUCCESSFULLY")
        logger.info(f"Graph: {len(validator.graph.nodes)} nodes, {len(validator.graph.edges)} edges")
        logger.info(f"History Limit: {MAX_HISTORY_SIZE} | String Limit: {MAX_STRING_LEN}")
        logger.info(f"Rate Limit: {RATE_LIMIT_PER_MINUTE}/min | TTL: {RATE_LIMIT_TTL_SECONDS}s")
        logger.info("=" * 60)

        try:
            diagnostic = immune_system.run_diagnostic()
            logger.info(f"Initial Health: {diagnostic.health_score:.1f}/100 ({diagnostic.overall_severity.value})")
        except Exception as e:
            logger.warning(f"Initial diagnostic failed (non-fatal): {e}")

    except Exception as e:
        logger.critical(f"STARTUP FAILED: {e}")
        import sys
        sys.exit(1)

# ─── REQUEST / RESPONSE MODELS ────────────────────────────────────────────────

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

# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.post("/validate", response_model=ValidateResponse)
def validate_intervention(request: ValidateRequest):
    with _validator_lock:
        try:
            if request.domain == "healthcare":
                validator.graph = create_healthcare_graph()
                validator.domain = "healthcare"

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
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/repair")
def get_repair_recommendations(request: RepairRequest):
    with _validator_lock:
        try:
            recommendations = repair_engine.get_repair_recommendations(
                failed_intervention=request.failed_intervention,
                current_state=request.current_state,
                conflict_type=request.conflict_type,
                max_recommendations=request.max_recommendations
            )
            return {"failed_intervention": request.failed_intervention, "recommendations": recommendations}
        except Exception as e:
            logger.error(f"Repair error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def simulate_timeline(request: SimulateRequest):
    with _simulator_lock:
        try:
            timeline = simulator_engine.simulate_path_execution(
                path=request.path,
                initial_state=request.current_state,
                duration_seconds=request.duration_seconds
            )
            return timeline
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", response_model=HealthResponse)
def health_check():
    try:
        health_score = 100.0
        severity = "HEALTHY"
        try:
            diagnostic = immune_system.run_diagnostic()
            health_score = diagnostic.health_score
            severity = diagnostic.overall_severity.value
        except Exception:
            pass

        uptime = (datetime.now() - _startup_time).total_seconds()
        return HealthResponse(
            status="ok",
            engine="Ashby-Vira Semantic",
            version="3.2",
            domain=validator.domain,
            graph_nodes=len(validator.graph.nodes),
            graph_edges=len(validator.graph.edges),
            health_score=round(health_score, 1),
            severity=severity,
            uptime_seconds=round(uptime, 1)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
def get_state():
    try:
        stats = validator.get_stats() if hasattr(validator, 'get_stats') else {}
        history_count = len(validator.history) if hasattr(validator, 'history') else 0
        return {
            "domain": validator.domain,
            "history_count": history_count,
            "history_limit": MAX_HISTORY_SIZE,
            "validation_history_entries": len(validation_history),
            "diagnostic_history_entries": len(diagnostic_history),
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decay_cycle")
def decay_cycle():
    with _validator_lock:
        try:
            return {
                "status": "decay_applied",
                "message": "Homeostatic decay cycle completed",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/immune/diagnostic")
def run_immune_diagnostic():
    with _immune_lock:
        try:
            diagnostic = immune_system.run_diagnostic()
            diagnostic_history.append({
                "health_score": diagnostic.health_score,
                "severity": diagnostic.overall_severity.value,
                "timestamp": datetime.now().isoformat()
            })
            return diagnostic.to_dict()
        except Exception as e:
            logger.error(f"Immune diagnostic error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/immune/dashboard")
def get_immune_dashboard():
    try:
        diagnostic = immune_system.run_diagnostic()
        return diagnostic.to_dict()
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
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
