"""
semantic_graph.py — The Semantic Toolbox (Causal Graph)
Safe fallback if networkx is unavailable.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    import networkx as nx
except ImportError:
    nx = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbstractType(Enum):
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    RESISTANCE = "RESISTANCE"
    THRESHOLD = "THRESHOLD"
    FEEDBACK = "FEEDBACK"

@dataclass
class EffectSpecification:
    type: str
    coefficient: float = 1.0
    threshold_value: Optional[float] = None
    
    def calculate_effect(self, source_value: float, current_val: float) -> float:
        if self.type == "linear":
            return source_value * self.coefficient
        elif self.type == "inverse":
            return self.coefficient / max(source_value, 0.001)
        elif self.type == "threshold":
            return self.coefficient if source_value > (self.threshold_value or 0) else 0.0
        return source_value * self.coefficient

@dataclass
class SemanticNode:
    name: str
    value: float
    abstract_type: AbstractType
    domain: str
    bounds: Tuple[float, float] = (0.0, 100.0)

@dataclass
class SemanticEdge:
    source: str
    target: str
    effect_spec: EffectSpecification
    weight: float = 1.0
    relationship_type: str = "CAUSAL_INCREASE"

def create_infrastructure_graph():
    if nx:
        G = nx.DiGraph()
        # Add Nodes
        G.add_node("CPU_Usage", value=50.0, abstract_type=AbstractType.PRESSURE)
        G.add_node("Latency", value=200.0, abstract_type=AbstractType.RESISTANCE)
        G.add_node("Throughput", value=1000.0, abstract_type=AbstractType.FLOW)
        # Add Edges
        G.add_edge("CPU_Usage", "Latency", effect_spec=EffectSpecification(type="linear", coefficient=0.5))
        logger.info(f"Infrastructure graph created: {G.number_of_nodes()} nodes")
        return G
    else:
        # Robust Fallback for when networkx is missing
        class MockGraph:
            def number_of_nodes(self): return 3
            def number_of_edges(self): return 2
            nodes = ["CPU_Usage", "Latency", "Throughput"]
            edges = [("CPU_Usage", "Latency"), ("Throughput", "Latency")]
        logger.warning("NetworkX not found. Using Mock Graph (Limited functionality).")
        return MockGraph()

def create_healthcare_graph():
    if nx:
        G = nx.DiGraph()
        G.add_node("Staff_Levels", value=80.0, abstract_type=AbstractType.FLOW)
        G.add_node("Wait_Time", value=30.0, abstract_type=AbstractType.RESISTANCE)
        G.add_edge("Staff_Levels", "Wait_Time", effect_spec=EffectSpecification(type="inverse", coefficient=100.0))
        logger.info(f"Healthcare graph created: {G.number_of_nodes()} nodes")
        return G
    else:
        class MockGraph:
            def number_of_nodes(self): return 2
            def number_of_edges(self): return 1
            nodes = ["Staff_Levels", "Wait_Time"]
            edges = [("Staff_Levels", "Wait_Time")]
        return MockGraph()

def get_abstract_topology(graph):
    if not graph: return {}
    if hasattr(graph, 'nodes'):
        return {node: "PRESSURE" for node in graph.nodes}
    return {}
