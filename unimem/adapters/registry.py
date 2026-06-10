"""Registry for managing and discovering agent adapters."""

from pathlib import Path
from typing import Dict, List, Type
from unimem.adapters.base import BaseAdapter
from unimem.utils.logger import logger

class AdapterRegistry:
    """Registry to map adapter names to their implementing classes."""
    _registry: Dict[str, Type[BaseAdapter]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register an adapter class."""
        def decorator(subclass: Type[BaseAdapter]):
            cls._registry[name.lower()] = subclass
            return subclass
        return decorator

    @classmethod
    def get_adapter(cls, name: str, project_root: Path) -> BaseAdapter:
        """Resolve and instantiate an adapter by name.
        
        Falls back to 'generic' if name is not found.
        """
        adapter_name = name.lower()
        if adapter_name not in cls._registry:
            logger.warning(f"Adapter '{name}' not found. Falling back to 'generic'.")
            adapter_name = "generic"
            
        adapter_cls = cls._registry[adapter_name]
        return adapter_cls(project_root)

    @classmethod
    def list_adapters(cls) -> List[str]:
        """List all registered adapters."""
        return list(cls._registry.keys())

# Import built-in adapters so they register themselves
# Note: We import them after registry setup to avoid circular imports.
def load_builtin_adapters() -> None:
    """Manually import standard adapters to trigger their registry decorators."""
    try:
        import unimem.adapters.generic
        import unimem.adapters.claude
        import unimem.adapters.gemini
        import unimem.adapters.codex
    except ImportError as e:
        logger.error(f"Failed to load built-in adapters: {e}")
