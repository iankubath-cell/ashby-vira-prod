"""
ashby_repair.py — The Repair Engine
Generates alternative intervention paths when standard fixes fail.
Uses the semantic graph to find "detours" around blocked constraints.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import networkx as nx
except ImportError:
    nx = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RepairRecommendation:
    """A suggested action to resolve a conflict or failure."""

    def __init__(
        self,
        action: str,
        confidence: float,
        reasoning: str,
        estimated_impact: float,
        risk_level: str = "LOW",
        source_domain: Optional[str] = None,
    ):
        self.action = action
        self.confidence = confidence
        self.reasoning = reasoning
        self.estimated_impact = estimated_impact
        self.risk_level = risk_level
        self.source_domain = source_domain
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "estimated_impact": self.estimated_impact,
            "risk_level": self.risk_level,
            "source_domain": self.source_domain,
        }


class RepairEngine:
    """
    Analyzes failures and proposes alternative repair strategies.
    
    Strategies:
    1. Path Rewiring: Find an alternative causal path to the goal.
    2. Analogy Transfer: Borrow a solution from a different domain (e.g., Traffic).
    3. Step-Down: Break a large intervention into smaller, safer steps.
    """

    def __init__(self, graph):
        self.graph = graph
        self._repair_patterns = self._load_default_patterns()

    def _load_default_patterns(self) -> List[Dict[str, Any]]:
        """Load basic repair heuristics."""
        return [
            {
                "trigger": "scaling_failed",
                "pattern": "step_down",
                "description": "If scaling up too fast fails, try smaller increments.",
                "template": "Scale by {amount}% instead of {full_amount}%."
            },
            {
                "trigger": "cost_constraint",
                "pattern": "efficiency_optimization",
                "description": "If cost is too high, optimize resource usage first.",
                "template": "Enable aggressive caching or compression before adding hardware."
            },
            {
                "trigger": "latency_spike",
                "pattern": "traffic_smoothing",
                "description": "Apply traffic shaping if direct capacity increase is blocked.",
                "template": "Implement request queuing or rate limiting."
            }
        ]

    def get_repair_recommendations(
        self,
        failed_intervention: str,
        current_state: Dict[str, float],
        conflict_type: str = "trade_off",
        max_recommendations: int = 3,
    ) -> List[RepairRecommendation]:
        """
        Generate a list of repair recommendations based on the failure context.
        
        Args:
            failed_intervention: The action that failed (e.g., "SCALE_UP_REPLICAS").
            current_state: Current metrics (e.g., {"cpu": 95, "cost": 500}).
            conflict_type: Type of conflict (e.g., "cost_constraint", "performance_degradation").
            max_recommendations: Max number of suggestions to return.
            
        Returns:
            List of RepairRecommendation objects.
        """
        recommendations = []
        
        logger.info(f"Generating repairs for failed: {failed_intervention}, conflict: {conflict_type}")

        # 1. Check for specific known patterns
        for pattern in self._repair_patterns:
            if conflict_type.lower() in pattern["trigger"].lower():
                rec = self._apply_pattern(pattern, failed_intervention, current_state)
                if rec:
                    recommendations.append(rec)

        # 2. Graph-based Path Search (Mock Logic for Stub)
        # In a full implementation, we would use networkx to find alternate paths
        # from the failed node to the goal node.
        alternate_paths = self._find_alternate_paths_graph(failed_intervention)
        
        for path in alternate_paths:
            rec = RepairRecommendation(
                action=path["action"],
                confidence=path["confidence"],
                reasoning=f"Alternative path found via graph traversal: {' -> '.join(path['nodes'])}",
                estimated_impact=0.85,
                risk_level="MEDIUM",
                source_domain="infrastructure"
            )
            recommendations.append(rec)

        # 3. Analogy-Based Suggestions (Stub)
        # If no infrastructure fixes work, suggest cross-domain analogies
        analogy_rec = self._suggest_analogy(failed_intervention)
        if analogy_rec:
            recommendations.append(analogy_rec)

        # Sort by confidence and return top N
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations[:max_recommendations]

    def _apply_pattern(self, pattern: Dict, failed_action: str, state: Dict) -> Optional[RepairRecommendation]:
        """Apply a heuristic pattern to generate a recommendation."""
        template = pattern.get("template", "Try {alternative}.")
        
        # Simple logic to fill template
        if pattern["pattern"] == "step_down":
            amount = 50  # Half the usual step
            reasoning = f"Reduced step size to avoid threshold breach."
            return RepairRecommendation(
                action=f"Scale by {amount}%",
                confidence=0.75,
                reasoning=reasoning,
                estimated_impact=0.6,
                risk_level="LOW"
            )
        
        if pattern["pattern"] == "efficiency_optimization":
            return RepairRecommendation(
                action="Enable Caching / Compression",
                confidence=0.80,
                reasoning="Optimizing existing resources before adding new ones.",
                estimated_impact=0.7,
                risk_level="LOW"
            )

        return None

    def _find_alternate_paths_graph(self, failed_node: str) -> List[Dict[str, Any]]:
        """
        Search the graph for alternate nodes that might achieve the goal.
        (Stub implementation returns mock data).
        """
        if not hasattr(self, 'graph') or self.graph is None:
            return [{"action": "Restart Service", "confidence": 0.6, "nodes": ["System", "Service"]}]
        
        # Mock logic: Return a generic fallback
        return [
            {
                "action": "Rollback to Last Stable State",
                "confidence": 0.70,
                "nodes": ["Failed_Node", "Previous_State"]
            }
        ]

    def _suggest_analogy(self, failed_action: str) -> Optional[RepairRecommendation]:
        """Suggest a solution based on cross-domain analogy (Stub)."""
        # Example: If "Scale Up" failed in Infrastructure, suggest "Traffic Smoothing" from Traffic domain
        return RepairRecommendation(
            action="Implement Request Throttling (Traffic Analogy)",
            confidence=0.65,
            reasoning="Mapped to 'Variable Speed Limits' from Traffic Management domain.",
            estimated_impact=0.60,
            risk_level="MEDIUM",
            source_domain="analogy_traffic"
        )
