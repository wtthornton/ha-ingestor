"""API package"""

from .health import router as health_router
from .data_router import router as data_router
from .pattern_router import router as pattern_router
from .suggestion_router import router as suggestion_router
from .analysis_router import router as analysis_router
from .suggestion_management_router import router as suggestion_management_router
from .deployment_router import router as deployment_router
from .nl_generation_router import router as nl_generation_router
from .conversational_router import router as conversational_router  # Story AI1.23

__all__ = [
    'health_router',
    'data_router',
    'pattern_router',
    'suggestion_router',
    'analysis_router',
    'suggestion_management_router',
    'deployment_router',
    'nl_generation_router',
    'conversational_router'  # Story AI1.23: Conversational Refinement
]

