"""
PYM executor for Metupy.

Executes Python code blocks from .pym files safely.
Uses RestrictedPython when available, falls back to
whitelisted imports.
"""

import re
from typing import Any, Dict, List, Optional


class PYMExecutor:
    """Execute Python blocks from .pym files."""

    def __init__(self, engine):
        """
        Initialize PYMExecutor.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.context: Dict[str, Any] = {}
        self.allowed_imports = self._get_allowed_imports()
        self.restricted_available = self._check_restricted()

    def _check_restricted(self) -> bool:
        """
        Check if RestrictedPython is available.

        Returns:
            True if RestrictedPython is installed.
        """
        try:
            from RestrictedPython import compile_restricted
            return True
        except ImportError:
            return False

    def _get_allowed_imports(self) -> Dict[str, Any]:
        """
        Get safe modules allowed for import.

        Returns:
            Dictionary of module name to module object.
        """
        safe_modules = {}

        module_names = [
            'json', 're', 'math', 'random', 'statistics',
            'datetime', 'itertools', 'collections', 'functools',
            'typing', 'pathlib', 'uuid', 'hashlib', 'base64',
            'html', 'string', 'numbers',
        ]

        for name in module_names:
            try:
                safe_modules[name] = __import__(name)
            except ImportError:
                pass

        return safe_modules

    def execute_block(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a Python code block.

        Args:
            code: Python code to execute.
            context: Existing context variables.

        Returns:
            Dictionary of resulting variables.
        """
        self.context = {}

        if context:
            self.context.update(context)

        self.context['site'] = getattr(self.engine, 'site_context', {})

        if self.restricted_available:
            return self._execute_restricted(code)
        else:
            return self._execute_whitelist(code)

    def _execute_restricted(self, code: str) -> Dict[str, Any]:
        """
        Execute using RestrictedPython.

        Args:
            code: Python code.

        Returns:
            Dictionary of variables.
        """
        from RestrictedPython import compile_restricted, safe_builtins
        from RestrictedPython.Eval import default_guarded_getitem

        exec_globals = {
            '__builtins__': safe_builtins,
            '_getitem_': default_guarded_getitem,
            '_getattr_': getattr,
            '_setattr_': setattr,
            '_iter_': iter,
            '_print_': print,
        }

        exec_globals.update(self.allowed_imports)
        exec_globals.update(self.context)
        exec_globals['engine'] = self.engine

        result = {}

        try:
            bytecode = compile_restricted(code, '<pym>', 'exec')
            exec(bytecode, exec_globals, exec_globals)

            for key, value in exec_globals.items():
                if not key.startswith('__') and key not in ['engine']:
                    result[key] = value

        except Exception as e:
            result['__error__'] = str(e)

        return result

    def _execute_whitelist(self, code: str) -> Dict[str, Any]:
        """
        Execute with whitelisted imports.

        Args:
            code: Python code.

        Returns:
            Dictionary of variables.
        """
        exec_globals = {
            '__builtins__': self._get_safe_builtins(),
            '__import__': self._safe_import,
        }

        exec_globals.update(self.allowed_imports)
        exec_globals.update(self.context)
        exec_globals['engine'] = self.engine

        result = {}

        try:
            exec(code, exec_globals)

            for key, value in exec_globals.items():
                if not key.startswith('__') and key not in ['engine']:
                    result[key] = value

        except Exception as e:
            result['__error__'] = str(e)

        return result

    def _safe_import(self, name: str, *args, **kwargs):
        """
        Safe import - only whitelisted modules.

        Args:
            name: Module name.

        Returns:
            Module object.

        Raises:
            ImportError: If module not whitelisted.
        """
        if name in self.allowed_imports:
            return self.allowed_imports[name]
        raise ImportError(f"Import '{name}' is not allowed in .pym files")

    def _get_safe_builtins(self) -> Dict:
        """
        Get safe builtins.

        Returns:
            Dictionary of safe builtin functions.
        """
        import builtins

        safe = {}

        allowed_names = [
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
            'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
            'min', 'max', 'sum', 'abs', 'round', 'pow',
            'print', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr',
            'any', 'all', 'next', 'iter',
            'format', 'repr', 'ascii', 'chr', 'ord', 'hex', 'oct', 'bin',
            'Exception', 'ValueError', 'TypeError', 'KeyError',
            'IndexError', 'AttributeError', 'StopIteration',
        ]

        for name in allowed_names:
            if hasattr(builtins, name):
                safe[name] = getattr(builtins, name)

        return safe