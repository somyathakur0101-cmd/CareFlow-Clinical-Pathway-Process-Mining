"""CareFlow Process Mining Package.

Provides clinical pathway event-log extraction, normalization, and validation,
along with process discovery algorithms (DFG, Variants, Inductive Miner Petri Nets),
and comprehensive bottleneck & waiting-time analysis modules.
"""

from .event_log import CareFlowEventLogGenerator
from .process_discovery import CareFlowProcessDiscovery
from .bottleneck_analysis import CareFlowBottleneckAnalysis
from .conformance_checking import CareFlowConformanceChecking

__all__ = [
    "CareFlowEventLogGenerator",
    "CareFlowProcessDiscovery",
    "CareFlowBottleneckAnalysis",
    "CareFlowConformanceChecking",
]
