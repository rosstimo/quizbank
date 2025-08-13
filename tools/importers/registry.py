from __future__ import annotations
from importlib import import_module
import pkgutil
from typing import Callable, Dict

def discover_importers() -> Dict[str, Callable]:
    """
    Auto-import all modules in tools.importers.formats and return
    a map: format_name -> import_items(path: Path, opts) -> List[dict]
    """
    import tools.importers.formats as pkg
    importer_map: Dict[str, Callable] = {}
    for m in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        mod = import_module(m.name)
        fmt = getattr(mod, "FORMAT_NAME", None)
        func = getattr(mod, "import_items", None)
        if isinstance(fmt, str) and callable(func):
            importer_map[fmt] = func
    return importer_map
