# metupy/parsers/template_parser.py
"""Template Parser untuk Metupy."""

from jinja2 import Environment, Template, TemplateSyntaxError
from typing import Dict, Any, List, Optional
import re

class TemplateParser:
    """Parses and renders Jinja2 templates."""
    
    def __init__(self, engine):
        self.engine = engine
        self.env = engine.template_env
        
    def parse(self, content: str) -> Template:
        """Parse template content."""
        return self.env.from_string(content)
        
    def render(self, content: str, context: Dict[str, Any]) -> str:
        """Render template content."""
        try:
            template = self.parse(content)
            return template.render(**context)
        except TemplateSyntaxError as e:
            print(f"Template syntax error: {e}")
            return content
        except Exception as e:
            print(f"Template render error: {e}")
            return content
            
    def extract_variables(self, content: str) -> List[str]:
        """Extract template variables."""
        variables = set()
        
        # Find {{ variable }} patterns
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'
        for match in re.finditer(pattern, content):
            variables.add(match.group(1).split('.')[0])
            
        # Find {% set variable = ... %} patterns
        pattern = r'\{%\s*set\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*='
        for match in re.finditer(pattern, content):
            variables.add(match.group(1))
            
        # Find {% for variable in ... %} patterns
        pattern = r'\{%\s*for\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+in'
        for match in re.finditer(pattern, content):
            variables.add(match.group(1))
            
        return list(variables)
        
    def extract_blocks(self, content: str) -> List[str]:
        """Extract template blocks."""
        blocks = []
        
        # Find {% block name %} patterns
        pattern = r'\{%\s*block\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%\}'
        for match in re.finditer(pattern, content):
            blocks.append(match.group(1))
            
        return blocks
        
    def extract_includes(self, content: str) -> List[str]:
        """Extract template includes."""
        includes = []
        
        # Find {% include 'template.html' %} patterns
        pattern = r'\{%\s*include\s+[\'"]([^\'"]+)[\'"]\s*%\}'
        for match in re.finditer(pattern, content):
            includes.append(match.group(1))
            
        return includes
        
    def extract_extends(self, content: str) -> Optional[str]:
        """Extract template extends."""
        # Find {% extends 'template.html' %} pattern
        pattern = r'\{%\s*extends\s+[\'"]([^\'"]+)[\'"]\s*%\}'
        match = re.search(pattern, content)
        return match.group(1) if match else None
        
    def validate_template(self, content: str) -> Dict[str, Any]:
        """Validate template syntax."""
        try:
            self.env.parse(content)
            return {
                'valid': True,
                'errors': [],
            }
        except TemplateSyntaxError as e:
            return {
                'valid': False,
                'errors': [{
                    'line': e.lineno,
                    'message': str(e),
                }],
            }