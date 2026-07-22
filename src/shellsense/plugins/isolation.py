from __future__ import annotations

import builtins
import types
from typing import Any


class SandboxExecutor:
    def __init__(self, allowed_modules: set[str] | None = None) -> None:
        self._allowed_modules = allowed_modules or {
            "os.path",
            "json",
            "re",
            "datetime",
            "math",
            "pathlib",
            "typing",
            "dataclasses",
            "enum",
            "collections",
            "functools",
            "itertools",
            "copy",
            "textwrap",
            "uuid",
        }

    def check_import(self, module_name: str) -> bool:
        for allowed in self._allowed_modules:
            if module_name == allowed or module_name.startswith(f"{allowed}."):
                return True
        return False

    def _restricted_import(self, name: str, *args: Any, **kwargs: Any) -> Any:
        if not self.check_import(name):
            raise ImportError(
                f"Module '{name}' is not in the allowed list for plugin execution"
            )
        return builtins.__import__(name, *args, **kwargs)

    def wrap_execution(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        restricted_builtins = dict(builtins.__dict__)
        restricted_builtins["__import__"] = self._restricted_import
        restricted_globals = {"__builtins__": restricted_builtins}
        restricted_globals.update(getattr(func, "__globals__", {}))

        new_func = types.FunctionType(
            func.__code__,
            restricted_globals,
            name=func.__name__,
            argdefs=func.__defaults__,
            closure=func.__closure__,
        )
        return new_func(*args, **kwargs)
