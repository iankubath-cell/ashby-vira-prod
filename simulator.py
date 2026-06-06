"""
simulator.py — Timeline Simulator (Safe Key Access)
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StateSnapshot:
    timestamp: str
    metrics: Dict[str, float]
    intervention_applied: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "metrics": self.metrics, "intervention_applied": self.intervention_applied}

@dataclass
class SimulationResult:
    initial_state: StateSnapshot
    final_state: StateSnapshot
    timeline: List[StateSnapshot]
    feedback_loops_detected: List[str]
    stability_score: float
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_state": self.initial_state.to_dict(),
            "final_state": self.final_state.to_dict(),
            "timeline": [s.to_dict() for s in self.timeline],
            "feedback_loops_detected": self.feedback_loops_detected,
            "stability_score": self.stability_score,
            "warnings": self.warnings
        }

class TimelineSimulator:
    def __init__(self, graph):
        self.graph = graph
        self._simulation_history: List[SimulationResult] = []

    def simulate_path_execution(self, path: List[str], initial_state: Dict[str, float], duration_seconds: int = 300, step_interval: int = 30):
        logger.info(f"Starting simulation: path={path}")
        current_time = datetime.now()
        current_metrics = initial_state.copy()
        timeline: List[StateSnapshot] = []
        warnings: List[str] = []
        
        # Initial Snapshot
        timeline.append(StateSnapshot(timestamp=current_time.isoformat(), metrics=current_metrics.copy()))
        
        steps = duration_seconds // step_interval
        
        for i, action in enumerate(path):
            if i >= steps: break
            
            effect = self._apply_action_effect(action, current_metrics)
            current_metrics.update(effect)
            
            alert = self._check_thresholds(current_metrics, action)
            if alert: warnings.append(alert)
            
            snap_time = current_time + timedelta(seconds=(i+1)*step_interval)
            timeline.append(StateSnapshot(timestamp=snap_time.isoformat(), metrics=current_metrics.copy(), intervention_applied=action))
        
        # Stability Calculation
        stability_score = self._calculate_stability(current_metrics)
        
        return SimulationResult(
            initial_state=timeline[0],
            final_state=StateSnapshot(timestamp=(current_time + timedelta(seconds=duration_seconds)).isoformat(), metrics=current_metrics),
            timeline=timeline,
            feedback_loops_detected=[],
            stability_score=stability_score,
            warnings=warnings
        )

    def _apply_action_effect(self, action: str, state: Dict[str, float]) -> Dict[str, float]:
        effects = {}
        action_upper = action.upper()
        
        if "SCALE" in action_upper:
            effects["CPU_Usage"] = max(0, state.get("CPU_Usage", 50) * 0.7)
            effects["Cost_Per_Hour"] = state.get("Cost_Per_Hour", 15) * 1.5
            effects["Throughput"] = state.get("Throughput", 1000) * 1.3
        elif "RESTART" in action_upper:
            effects["Error_Rate"] = 0.1
            effects["Latency"] = state.get("Latency", 200) * 1.2
        elif "CACHE" in action_upper:
            effects["Latency"] = max(10, state.get("Latency", 200) * 0.5)
            effects["Throughput"] = state.get("Throughput", 1000) * 1.2
        
        return effects

    def _check_thresholds(self, metrics: Dict[str, float], action: str) -> Optional[str]:
        thresholds = {"CPU_Usage": 95, "Memory_Usage": 95, "Error_Rate": 10.0}
        alerts = []
        for m, t in thresholds.items():
            val = metrics.get(m, 0)
            if val > t: alerts.append(f"{m} > {t}")
        return "; ".join(alerts) if alerts else None

    def _calculate_stability(self, metrics: Dict[str, float]) -> float:
        score = 100.0
        penalties = {
            "CPU_Usage": lambda v: max(0, (v - 70) * 0.5) if v > 70 else 0,
            "Error_Rate": lambda v: v * 2,
        }
        for m, fn in penalties.items():
            score -= fn(metrics.get(m, 0))
        return max(0, min(100, score))
