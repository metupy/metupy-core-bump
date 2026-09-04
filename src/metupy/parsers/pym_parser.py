"""
PYM parser for Metupy.

Parses .pym files which combine Python code blocks,
Markdown content, and Jinja2 templates.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from metupy.utils.helpers import read_file


class PYMParser:
    """Parser for .pym files (Python + Markdown + Jinja2)."""

    def __init__(self, engine):
        """
        Initialize PYMParser.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.macro_manager = None

        if hasattr(engine, 'macro_manager') and engine.macro_manager:
            self.macro_manager = engine.macro_manager

    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse .pym file content.

        Args:
            content: Raw .pym content string.

        Returns:
            Dictionary with metadata, content, and context.
        """
        metadata, body = self._parse_frontmatter(content)

        body = self._process_macros(body)
        body = self._process_functions(body)

        python_context = self._process_python_blocks(body)

        return {
            'metadata': metadata,
            'context': python_context,
            'content': body,
        }

    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse .pym file from path.

        Args:
            file_path: Path to .pym file.

        Returns:
            Dictionary with parsed content.
        """
        content = read_file(file_path)
        return self.parse(content)

    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """
        Parse YAML frontmatter from content.

        Args:
            content: Raw content string.

        Returns:
            Tuple of (metadata, body).
        """
        metadata = {}
        body = content

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                import yaml
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2]
                except (yaml.YAMLError, ValueError):
                    pass

        return metadata, body

    def _process_macros(self, content: str) -> str:
        """
        Process macro calls in content.

        Pattern: {{ macro('name', key=value, ...) }}

        Args:
            content: Content with macro calls.

        Returns:
            Content with macros replaced.
        """
        if not self.macro_manager:
            return content

        pattern = r"\{\{\s*macro\(['\"]([^'\"]+)['\"](.*?)\)\s*\}\}"

        def replace_macro(match):
            macro_name = match.group(1)
            args_str = match.group(2).strip()

            context = self._parse_kwargs(args_str)
            return self.macro_manager.render_macro(macro_name, context)

        return re.sub(pattern, replace_macro, content, flags=re.DOTALL)

    def _process_functions(self, content: str) -> str:
        """
        Process function calls in content.

        Pattern: {{ function('name', args...) }}

        Args:
            content: Content with function calls.

        Returns:
            Content with function results.
        """
        if not self.macro_manager:
            return content

        pattern = r"\{\{\s*function\(['\"]([^'\"]+)['\"](.*?)\)\s*\}\}"

        def replace_function(match):
            func_name = match.group(1)
            args_str = match.group(2).strip()

            args, kwargs = self._parse_args(args_str)
            result = self.macro_manager.call_function(func_name, *args, **kwargs)
            return str(result)

        return re.sub(pattern, replace_function, content, flags=re.DOTALL)

    def _process_python_blocks(self, content: str) -> Dict[str, Any]:
        """
        Process Python code blocks in content.

        Pattern: ```pym ... ```

        Args:
            content: Content with Python blocks.

        Returns:
            Dictionary of variables from Python execution.
        """
        context = {}

        pattern = r'```pym\n(.*?)\n```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            code = match.group(1)

            if hasattr(self.engine, 'pym_executor') and self.engine.pym_executor:
                result = self.engine.pym_executor.execute_block(code, context)
                if isinstance(result, dict):
                    context.update(result)
            else:
                exec_context = self._fallback_execute(code, context)
                context.update(exec_context)

        return context

    def _fallback_execute(self, code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback Python execution without executor.

        Uses RestrictedPython if available.

        Args:
            code: Python code to execute.
            context: Current context.

        Returns:
            Dictionary of new variables.
        """
        result = {}

        try:
            from RestrictedPython import compile_restricted, safe_builtins
            from RestrictedPython.Eval import default_guarded_getitem

            exec_globals = {
                '__builtins__': safe_builtins,
                '_getitem_': default_guarded_getitem,
                '_getattr_': getattr,
                '_setattr_': setattr,
            }

            import json as json_module
            import re as re_module
            import math as math_module
            from datetime import datetime as dt_module

            exec_globals.update({
                'json': json_module,
                're': re_module,
                'math': math_module,
                'datetime': dt_module,
                'engine': self.engine,
                'site': getattr(self.engine, 'site_context', {}),
            })

            exec_globals.update(context)

            bytecode = compile_restricted(code, '<pym>', 'exec')
            exec(bytecode, exec_globals, exec_globals)

            for k, v in exec_globals.items():
                if not k.startswith('__') and k not in ['engine', 'site']:
                    result[k] = v

        except ImportError:
            result['__error__'] = 'RestrictedPython not installed'
        except Exception as e:
            result['__error__'] = str(e)

        return result

    def _parse_kwargs(self, args_str: str) -> Dict[str, Any]:
        """
        Parse keyword arguments from string.

        Args:
            args_str: Arguments string like "key=value, key2=value2".

        Returns:
            Dictionary of key-value pairs.
        """
        context = {}

        if not args_str.strip():
            return context

        parts = self._split_args(args_str)

        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                context[key.strip()] = self._parse_value(value.strip())

        return context

    def _parse_args(self, args_str: str) -> Tuple[List, Dict]:
        """
        Parse positional and keyword arguments.

        Args:
            args_str: Arguments string.

        Returns:
            Tuple of (positional_args, keyword_args).
        """
        args = []
        kwargs = {}

        if not args_str.strip():
            return args, kwargs

        parts = self._split_args(args_str)

        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                kwargs[key.strip()] = self._parse_value(value.strip())
            else:
                args.append(self._parse_value(part))

        return args, kwargs

    def _split_args(self, args_str: str) -> List[str]:
        """
        Split arguments by comma, respecting quotes.

        Args:
            args_str: Arguments string.

        Returns:
            List of argument strings.
        """
        parts = []
        current = ''
        in_quote = False
        quote_char = None

        for char in args_str:
            if char in ["'", '"']:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                    quote_char = None

            if char == ',' and not in_quote:
                parts.append(current)
                current = ''
            else:
                current += char

        if current.strip():
            parts.append(current)

        return parts

    def _parse_value(self, value: str) -> Any:
        """
        Parse a value string to appropriate Python type.

        Args:
            value: Value string.

        Returns:
            Parsed Python value.
        """
        value = value.strip()

        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.lower() in ['none', 'null']:
            return None

        if value.startswith('[') and value.endswith(']'):
            items = value[1:-1].split(',')
            return [self._parse_value(item) for item in items if item.strip()]

        return value