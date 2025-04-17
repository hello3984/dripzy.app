"""
Modules package for the modular monolith architecture.
Each module encapsulates a specific business domain with its own routes, services, and dependencies.
"""

from app.core.module_registry import registry

__all__ = ['registry'] 