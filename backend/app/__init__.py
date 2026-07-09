"""
后端应用包初始化
"""
from .config_loader import ConfigLoader
from .mcp_client import MCPServiceManager, LocationData
from .scoring_engine import ScoringEngine, ScoreResult
from .location_agent import LocationAnalysisAgent

__version__ = "1.0.0"
__all__ = [
    "ConfigLoader",
    "MCPServiceManager",
    "LocationData",
    "ScoringEngine",
    "ScoreResult",
    "LocationAnalysisAgent"
]
