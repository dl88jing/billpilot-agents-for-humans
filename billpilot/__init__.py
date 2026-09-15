"""BillPilot — multi-agent Everyday Agent for household bill management."""

__version__ = "0.2.0"

from billpilot.orchestrator import build_swarm, run_pipeline

__all__ = ["build_swarm", "run_pipeline", "__version__"]
