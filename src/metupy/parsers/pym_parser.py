# metupy/parsers/pym_parser.py
"""PYM Parser - Parse .pym files (Python + Markdown + Jinja2)."""

import ast
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import markdown
from jinja2 import Template, TemplateSyntaxError

class PYMParser:
    """Parser for .pym files."""
    
    def __init__(self, engine):
        self.engine = engine
        self.template_env = engine.template_env
        self.markdown_parser = engine.markdown_parser
        
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse .pym file content."""
        # Parse frontmatter
        metadata, body = self._parse_frontmatter(content)
        
        # Parse Python code blocks
        python_context = self._parse_python_blocks(body)
        
        # Parse markdown content
        markdown_html = self._parse_markdown(body)
        
        # Parse Jinja2 templates
        rendered_content = self._render_jinja2(markdown_html, python_context)
        
        return {
            'metadata': metadata,
            'context': python_context,
            'content': rendered_content,
            'raw_content': body,
            'markdown_html': markdown_html,
        }
        
    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse frontmatter from content."""
        metadata = {}
        body = content
        
        # YAML frontmatter
        if content.startswith('---'):
            match = re.match(r'^---\n(.*?)\n---\n?(.*)$', content, re.DOTALL)
            if match:
                try:
                    metadata = yaml.safe_load(match.group(1)) or {}
                    body = match.group(2)
                except yaml.YAMLError as e:
                    print(f"Error parsing YAML frontmatter: {e}")
                    
        # Python frontmatter
        elif content.startswith('```python'):
            match = re.match(r'^```python\n(.*?)\n```\n?(.*)$', content, re.DOTALL)
            if match:
                try:
                    exec_globals = {}
                    exec(match.group(1), exec_globals)
                    metadata = {
                        k: v for k, v in exec_globals.items()
                        if not k.startswith('__') and k.isupper()
                    }
                    body = match.group(2)
                except Exception as e:
                    print(f"Error parsing Python frontmatter: {e}")
                    
        return metadata, body
        
    def _parse_python_blocks(self, content: str) -> Dict[str, Any]:
        """Parse and execute Python code blocks."""
        context = {}
        
        # Find Python code blocks
        pattern = r'```python\n(.*?)\n```'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            python_code = match.group(1)
            exec_context = self._execute_python(python_code)
            context.update(exec_context)
            
        # Also find inline Python expressions
        context.update(self._parse_inline_python(content))
        
        return context
        
    def _parse_inline_python(self, content: str) -> Dict[str, Any]:
        """Parse inline Python expressions {{ python_code }}."""
        context = {}
        
        # Find inline Python
        pattern = r'\{\{\s*python\s+(.*?)\s*\}\}'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            python_code = match.group(1)
            try:
                exec_globals = {}
                exec(python_code, exec_globals)
                context.update({
                    k: v for k, v in exec_globals.items()
                    if not k.startswith('__')
                })
            except Exception as e:
                print(f"Error executing inline Python: {e}")
                
        return context
        
    def _parse_markdown(self, content: str) -> str:
        """Parse markdown content."""
        # Remove Python code blocks
        content = re.sub(r'```python\n.*?\n```', '', content, flags=re.DOTALL)
        
        # Remove inline Python
        content = re.sub(r'\{\{\s*python\s+.*?\s*\}\}', '', content, flags=re.DOTALL)
        
        # Convert markdown to HTML
        return self.markdown_parser.convert(content)
        
    def _render_jinja2(self, content: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 templates."""
        try:
            template = self.template_env.from_string(content)
            return template.render(**context)
        except TemplateSyntaxError as e:
            print(f"Jinja2 syntax error: {e}")
            return content
        except Exception as e:
            print(f"Error rendering template: {e}")
            return content
            
    def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely."""
        try:
            # Create execution context
            exec_globals = {
                '__builtins__': __builtins__,
                'engine': self.engine,
                'config': self.engine.config,
                'site': self.engine.site_context,
            }
            
            exec(code, exec_globals)
            
            # Extract variables
            return {
                k: v for k, v in exec_globals.items()
                if not k.startswith('__') and k not in ['engine', 'config', 'site']
            }
        except Exception as e:
            print(f"Error executing Python code: {e}")
            return {}
            
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse .pym file from path."""
        content = file_path.read_text(encoding='utf-8')
        return self.parse(content)
        
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract only metadata from content."""
        metadata, _ = self._parse_frontmatter(content)
        return metadata
        
    def extract_python_context(self, content: str) -> Dict[str, Any]:
        """Extract Python context from content."""
        _, body = self._parse_frontmatter(content)
        return self._parse_python_blocks(body)
        
    def extract_markdown(self, content: str) -> str:
        """Extract markdown content."""
        _, body = self._parse_frontmatter(content)
        return self._parse_markdown(body)