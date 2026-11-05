"""CareFlow Process Mining Package.

Provides clinical pathway event-log extraction, normalization, and validation,
along with process discovery algorithms (DFG, Variants, Inductive Miner Petri Nets).
"""

from .event_log import CareFlowEventLogGenerator
from .process_discovery import CareFlowProcessDiscovery

__all__ = ["CareFlowEventLogGenerator", "CareFlowProcessDiscovery"]
