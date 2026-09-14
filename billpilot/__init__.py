"""BillPilot — autonomous everyday agent for household bill management."""

__version__ = "0.1.0"

from billpilot.agent import build_agent, run_offline_pipeline

__all__ = ["build_agent", "run_offline_pipeline", "__version__"]
