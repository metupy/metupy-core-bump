"""
Template parser for Metupy.

Provides Jinja2 template parsing and validation.
"""

import re
from typing import Any, Dict, List, Optional

from jinja2 import Template, TemplateSyntaxError


class TemplateParser:
    """Parse and validate Jinja2 templates."""

    def __init__(self, engine):
        """
        Initialize TemplateParser.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine
        self.env = getattr(engine, 'template_env', None)

    def parse(self, content: str) -> Template:
        """
        Parse template content.

        Args:
            content: Template string.

        Returns:
            Jinja2 Template instance.
        """
        if self.env:
            return self.env.from_string(content)
        return Template(content)

    def render(self, content: str, context: Dict[str, Any]) -> str:
        """
        Render template with context.

        Args:
            content: Template content.
            context: Rendering context.

        Returns:
            Rendered string.
        """
        try:
            template = self.parse(content)
            return template.render(**context)
        except (TemplateSyntaxError, Exception) as e:
            return f"[Template error: {e}]"

    def extract_variables(self, content: str) -> List[str]:
        """
        Extract variable names from template.

        Args:
            content: Template content.

        Returns:
            List of variable names used.
        """
        variables = set()

        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'
        for match in re.finditer(pattern, content):
            variables.add(match.group(1).split('.')[0])

        pattern = r'\{%\s*for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in'
        for match in re.finditer(pattern, content):
            variables.add(match.group(1))

        return list(variables)

    def extract_blocks(self, content: str) -> List[str]:
        """
        Extract block names from template.

        Args:
            content: Template content.

        Returns:
            List of block names.
        """
        blocks = []
        pattern = r'\{%\s*block\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%\}'
        for match in re.finditer(pattern, content):
            blocks.append(match.group(1))
        return blocks

    def extract_extends(self, content: str) -> Optional[str]:
        """
        Extract parent template from extends.

        Args:
            content: Template content.

        Returns:
            Parent template name or None.
        """
        pattern = r'\{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%\}'
        match = re.search(pattern, content)
        return match.group(1) if match else None

    def validate_template(self, content: str) -> Dict[str, Any]:
        """
        Validate template syntax.

        Args:
            content: Template content.

        Returns:
            Dictionary with validation result.
        """
        try:
            if self.env:
                self.env.parse(content)
            else:
                Template(content)
            return {'valid': True, 'errors': []}
        except TemplateSyntaxError as e:
            return {
                'valid': False,
                'errors': [{'line': e.lineno, 'message': str(e)}],
            }