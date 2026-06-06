"""
semantic_graph.py — The Semantic Toolbox (Causal Graph)
Defines nodes (metrics) and edges (causal relationships) for infrastructure and healthcare.
Supports abstract typing (Pressure, Flow, Resistance) for cross-domain analogies.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# External library for graph operations
try:
    import networkx as nx
except ImportError:
    nx = None  # Fallback if networkx not installed (should be in requirements.txt)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AbstractType(Enum):
    """
    Universal physical/logical primitives used for cross-domain analogy matching.
    - PRESSURE: Load, Density, CPU Usage
    - FLOW: Throughput, Traffic Speed, Data Rate
    - RESISTANCE: Latency, Friction, Blockage
    - THRESHOLD: Limits, Caps, Triggers
    - FEEDBACK: Loops, Oscillations
    """
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    RESISTANCE = "RESISTANCE"
    THRESHOLD = "THRESHOLD"
    FEEDBACK = "FEEDBACK"


@dataclass
class EffectSpecification:
    """Mathematical description of how one node affects another."""
    type: str  # "linear", "exponential", "threshold", "inverse"
    coefficient: float = 1.0
    threshold_value: Optional[float] = None
    
    def calculate_effect(self, source_value: float, current_val: float) -> float:
        """Calculate the predicted effect value based on source change."""
        if self.type == "linear":
            return source_value * self.coefficient
        elif self.type == "inverse":
            # e.g., Latency ~ 1/Throughput
            if source_value == 0: return 0
            return self.coefficient / source_value
        elif self.type == "threshold":
            if source_value > (self.threshold_value or 0):
                return self.coefficient
            return 0.0
        else:
            return source_value * self.coefficient


@dataclass
class SemanticNode:
    """Represents a metric or property in the system."""
    name: str
    value: float
    abstract_type: AbstractType
    domain: str
    bounds: Tuple[float, float] = (0.0, 100.0)
    
    def is_valid(self) -> bool:
        return self.bounds[0] <= self.value <= self.bounds[1]


@dataclass
class SemanticEdge:
    """Represents a causal relationship between two nodes."""
    source: str
    target: str
    effect_spec: EffectSpecification
    weight: float = 1.0
    relationship_type: str = "CAUSAL_INCREASE" # or "DAMPENS"


def create_infrastructure_graph() -> 'nx.DiGraph':
    """
    Creates a causal graph for Infrastructure/DevOps systems.
    Nodes: CPU, Memory, Latency, Throughput, Cost, ErrorRate
    Edges: How scaling affects these metrics.
    """
    if nx is None:
        logger.warning("NetworkX not found. Returning mock graph structure.")
        # Return a mock object to prevent crashes if networkx is missing
        class MockGraph:
            def __init__(self):
                self.nodes = ["CPU_Usage", "Memory_Usage", "Latency", "Throughput", "Cost", "Error_Rate"]
                self.edges = [("CPU_Usage", "Latency"), ("Throughput", "Latency")]
            @property
            def nodes(self): return self._nodes
            @property 
            def edges(self): return self._edges
        
        g = MockGraph()
        g._nodes = {"CPU_Usage": {"abstract": "PRESSURE"}, "Latency": {"abstract": "RESISTANCE"}}
        g._edges = [("CPU_Usage", "Latency", {"weight": 0.8})]
        return g

    G = nx.DiGraph()

    # --- ADD NODES ---
    # Pressure Metrics
    G.add_node("CPU_Usage", value=50.0, abstract_type=AbstractType.PRESSURE, domain="infrastructure")
    G.add_node("Memory_Usage", value=40.0, abstract_type=AbstractType.PRESSURE, domain="infrastructure")
    G.add_node("Queue_Depth", value=10.0, abstract_type=AbstractType.PRESSURE, domain="infrastructure")
    
    # Flow Metrics
    G.add_node("Throughput", value=1000.0, abstract_type=AbstractType.FLOW, domain="infrastructure")
    G.add_node("Request_Rate", value=500.0, abstract_type=AbstractType.FLOW, domain="infrastructure")

    # Resistance Metrics
    G.add_node("Latency", value=200.0, abstract_type=AbstractType.RESISTANCE, domain="infrastructure")
    G.add_node("Error_Rate", value=0.5, abstract_type=AbstractType.THRESHOLD, domain="infrastructure")
    
    # Cost Metric
    G.add_node("Cost_Per_Hour", value=15.0, abstract_type=AbstractType.PRESSURE, domain="infrastructure")

    # --- ADD EDGES (Causal Relationships) ---
    # 1. High CPU -> High Latency (Inverse relation? No, usually linear increase until saturation)
    G.add_edge("CPU_Usage", "Latency", 
               effect_spec=EffectSpecification(type="linear", coefficient=0.5), 
               relationship_type="INCREASES")

    # 2. High Throughput -> Low Latency (Usually, up to a point) -> Actually, High Throughput often increases Latency due to queueing
    # Let's model: Request Rate -> Queue Depth -> Latency
    G.add_edge("Request_Rate", "Queue_Depth", 
               effect_spec=EffectSpecification(type="linear", coefficient=0.1),
               relationship_type="INCREASES")
               
    G.add_edge("Queue_Depth", "Latency", 
               effect_spec=EffectSpecification(type="exponential", coefficient=0.2),
               relationship_type="INCREASES")

    # 3. Scaling Up -> Low CPU, High Cost
    G.add_edge("Scale_Up_Action", "CPU_Usage", 
               effect_spec=EffectSpecification(type="inverse", coefficient=100.0),
               relationship_type="DECREASES")
    G.add_edge("Scale_Up_Action", "Cost_Per_Hour", 
               effect_spec=EffectSpecification(type="linear", coefficient=10.0),
               relationship_type="INCREASES")
    
    # 4. High Error Rate -> System Instability (Feedback loop concept)
    G.add_edge("Error_Rate", "System_Stability", 
               effect_spec=EffectSpecification(type="inverse", coefficient=1.0),
               relationship_type="DECREASES")

    logger.info(f"Infrastructure graph created: {len(G.nodes())} nodes, {len(G.edges())} edges")
    return G


def create_healthcare_graph() -> 'nx.DiGraph':
    """
    Creates a causal graph for Healthcare systems.
    Nodes: Staff Levels, Patient Wait Time, Readmission Rate, Cost, Bed Occupancy.
    Used to demonstrate cross-domain analogy (e.g., Patient Flow ~ Network Packet Flow).
    """
    if nx is None:
        logger.warning("NetworkX not found. Returning mock healthcare graph.")
        class MockGraph:
            nodes = ["Staff_Levels", "Wait_Time", "Bed_Occupancy"]
            edges = [("Staff_Levels", "Wait_Time")]
        return MockGraph()

    G = nx.DiGraph()

    # Nodes
    G.add_node("Staff_Levels", value=80.0, abstract_type=AbstractType.FLOW, domain="healthcare")
    G.add_node("Patient_Arrival_Rate", value=10.0, abstract_type=AbstractType.FLOW, domain="healthcare")
    G.add_node("Wait_Time", value=30.0, abstract_type=AbstractType.RESISTANCE, domain="healthcare")
    G.add_node("Bed_Occupancy", value=75.0, abstract_type=AbstractType.PRESSURE, domain="healthcare")
    G.add_node("Readmission_Rate", value=5.0, abstract_type=AbstractType.THRESHOLD, domain="healthcare")

    # Edges
    # More Staff -> Less Wait Time
    G.add_edge("Staff_Levels", "Wait_Time", 
               effect_spec=EffectSpecification(type="inverse", coefficient=100.0),
               relationship_type="DECREASES")
    
    # More Patients -> More Bed Occupancy
    G.add_edge("Patient_Arrival_Rate", "Bed_Occupancy", 
               effect_spec=EffectSpecification(type="linear", coefficient=2.0),
               relationship_type="INCREASES")
    
    # High Occupancy -> Higher Wait Time (Bottleneck)
    G.add_edge("Bed_Occupancy", "Wait_Time", 
               effect_spec=EffectSpecification(type="exponential", coefficient=0.3),
               relationship_type="INCREASES")

    logger.info(f"Healthcare graph created: {len(G.nodes())} nodes, {len(G.edges())} edges")
    return G


# Helper function to get abstract types for analogy matching
def get_abstract_topology(graph: 'nx.DiGraph') -> Dict[str, AbstractType]:
    """Returns a mapping of node names to their abstract types."""
    topo = {}
    for node, data in graph.nodes(data=True):
        topo[node] = data.get('abstract_type', AbstractType.PRESSURE)
    return topo
