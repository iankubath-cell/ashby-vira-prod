"""
simulator.py — Timeline Simulator
Projects system state forward over time based on intervention paths.
Used for "What-If" analysis before deploying interventions.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

try:
    import networkx as nx
except ImportError:
    nx = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """A point-in-time snapshot of the system state."""
    timestamp: str
    metrics: Dict[str, float]
    intervention_applied: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "intervention_applied": self.intervention_applied
        }


@dataclass
class SimulationResult:
    """Complete results of a simulation run."""
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
    """
    Simulates the execution of an intervention path over time.
    
    Capabilities:
    1. Path Execution: Apply each step in a causal chain.
    2. Feedback Loop Detection: Identify oscillations or runaway conditions.
    3. Stability Scoring: Calculate how stable the end-state will be.
    """

    def __init__(self, graph):
        self.graph = graph
        self._simulation_history: List[SimulationResult] = []

    def simulate_path_execution(
        self,
        path: List[str],
        initial_state: Dict[str, float],
        duration_seconds: int = 300,
        step_interval: int = 30,
    ) -> SimulationResult:
        """
        Simulate executing a sequence of nodes/actions over time.
        
        Args:
            path: Ordered list of node/action names (e.g., ["Scale_Up", "Rebalance_Load"])
            initial_state: Starting values for all monitored metrics.
            duration_seconds: Total simulation time.
            step_interval: Time between state updates (in seconds).
            
        Returns:
            SimulationResult with timeline and stability analysis.
        """
        logger.info(f"Starting simulation: path={path}, duration={duration_seconds}s")
        
        current_time = datetime.now()
        current_metrics = initial_state.copy()
        timeline: List[StateSnapshot] = []
        warnings: List[str] = []
        feedback_loops: List[str] = []
        
        # --- STEP 1: Initialize ---
        initial_snapshot = StateSnapshot(
            timestamp=current_time.isoformat(),
            metrics=current_metrics.copy(),
            intervention_applied=None
        )
        timeline.append(initial_snapshot)
        
        # --- STEP 2: Execute Path Step-by-Step ---
        steps = duration_seconds // step_interval
        
        for i, action in enumerate(path):
            if i >= steps:
                break
            
            # Apply effect of current action
            effect = self._apply_action_effect(action, current_metrics)
            current_metrics.update(effect)
            
            # Check for dangerous thresholds
            alert = self._check_thresholds(current_metrics, action)
            if alert:
                warnings.append(alert)
            
            # Record snapshot
            snap_time = current_time + timedelta(seconds=(i+1)*step_interval)
            snapshot = StateSnapshot(
                timestamp=snap_time.isoformat(),
                metrics=current_metrics.copy(),
                intervention_applied=action
            )
            timeline.append(snapshot)
        
        # --- STEP 3: Detect Feedback Loops ---
        feedback_loops = self._detect_feedback_loops(timeline)
        
        # --- STEP 4: Calculate Final Stability Score ---
        final_metrics = current_metrics
        final_snapshot = StateSnapshot(
            timestamp=(current_time + timedelta(seconds=duration_seconds)).isoformat(),
            metrics=final_metrics,
            intervention_applied=path[-1] if path else None
        )
        
        stability_score = self._calculate_stability(final_metrics)
        
        result = SimulationResult(
            initial_state=initial_snapshot,
            final_state=final_snapshot,
            timeline=timeline,
            feedback_loops_detected=feedback_loops,
            stability_score=stability_score,
            warnings=warnings
        )
        
        self._simulation_history.append(result)
        logger.info(f"Simulation complete: score={stability_score:.1f}, loops={len(feedback_loops)}")
        
        return result

    def _apply_action_effect(self, action: str, state: Dict[str, float]) -> Dict[str, float]:
        """
        Apply the mathematical effect of an action on the current state.
        (Stub implementation - full version would use EffectSpecification from semantic_graph)
        """
        effects = {}
        
        # Mock logic for demonstration
        if action.upper() == "SCALE_UP":
            effects["CPU_Usage"] = max(0, state.get("CPU_Usage", 50) * 0.7)  # Reduce CPU by 30%
            effects["Cost_Per_Hour"] = state.get("Cost_Per_Hour", 15) * 1.5   # Increase cost by 50%
            effects["Throughput"] = state.get("Throughput", 1000) * 1.3       # Increase throughput 30%
        
        elif action.upper() == "RESTART_SERVICE":
            effects["Error_Rate"] = 0.1  # Reset errors
            effects["Latency"] = state.get("Latency", 200) * 1.2  # Slight temp increase
            
        elif action.upper() == "ENABLE_CACHING":
            effects["Latency"] = max(10, state.get("Latency", 200) * 0.5)  # Cut latency in half
            effects["Throughput"] = state.get("Throughput", 1000) * 1.2
            
        else:
            # Unknown action - minimal effect
            effects["System_Stability"] = state.get("System_Stability", 90) - 5
        
        return effects

    def _check_thresholds(self, metrics: Dict[str, float], action: str) -> Optional[str]:
        """Check if any metric has hit a dangerous threshold."""
        alerts = []
        
        critical_thresholds = {
            "CPU_Usage": 95,
            "Memory_Usage": 95,
            "Error_Rate": 10.0,
            "Latency": 1000,  # ms
        }
        
        for metric, threshold in critical_thresholds.items():
            val = metrics.get(metric, 0)
            if val > threshold:
                alerts.append(f"{metric} exceeded threshold ({val}/{threshold}) after {action}")
        
        return "; ".join(alerts) if alerts else None

    def _detect_feedback_loops(self, timeline: List[StateSnapshot]) -> List[str]:
        """
        Detect oscillating patterns that indicate feedback loops.
        (Simple variance detection - stub for complexity)
        """
        loops = []
        
        if len(timeline) < 3:
            return loops
        
        # Check if a metric oscillates more than twice
        metrics = timeline[0].metrics.keys()
        for metric in metrics:
            values = [s.metrics.get(metric, 0) for s in timeline]
            # Count direction changes
            changes = sum(1 for i in range(1, len(values)-1) 
                         if (values[i]-values[i-1]) * (values[i+1]-values[i]) < 0)
            if changes > 2:
                loops.append(f"{metric}: Oscillation detected ({changes} reversals)")
        
        return loops

    def _calculate_stability(self, metrics: Dict[str, float]) -> float:
        """
        Calculate a 0-100 stability score based on metric health.
        Higher = more stable.
        """
        score = 100.0
        
        # Deduct points for unhealthy metrics
        penalties = {
            "CPU_Usage": lambda v: max(0, (v - 70) * 0.5) if v > 70 else 0,
            "Memory_Usage": lambda v: max(0, (v - 70) * 0.5) if v > 70 else 0,
            "Error_Rate": lambda v: v * 2,
            "Latency": lambda v: max(0, (v - 200) * 0.1) if v > 200 else 0,
        }
        
        for metric, penalty_fn in penalties.items():
            val = metrics.get(metric, 0)
            penalty = penalty_fn(val)
            score -= penalty
        
        return max(0, min(100, score))  # Clamp between 0-100

    def get_simulation_history(self) -> List[Dict[str, Any]]:
        """Return all past simulations."""
        return [r.to_dict() for r in self._simulation_history]
