# metupy/parsers/markdown_parser.py
"""Markdown Parser - Enhanced markdown parsing."""

import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
from markdown.inlinepatterns import Pattern
from typing import Dict, Any, Optional
import re

class MetupyMarkdownParser:
    """Enhanced markdown parser for Metupy."""
    
    def __init__(self, engine):
        self.engine = engine
        self.md = self._create_markdown_instance()
        
    def _create_markdown_instance(self) -> markdown.Markdown:
        """Create markdown instance with extensions."""
        extensions = self.engine.config.MARKDOWN_EXTENSIONS
        extension_configs = self.engine.config.MARKDOWN_EXTENSION_CONFIGS
        
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs=extension_configs,
            output_format='html5',
        )
        
        # Add custom extensions
        md.preprocessors.register(CustomPreprocessor(md), 'custom_preprocessor', 175)
        md.postprocessors.register(CustomPostprocessor(md), 'custom_postprocessor', 25)
        
        return md
        
    def convert(self, content: str) -> str:
        """Convert markdown to HTML."""
        if not content:
            return ""
            
        # Reset markdown instance
        self.md.reset()
        
        # Convert
        return self.md.convert(content)
        
    def strip_markdown(self, content: str) -> str:
        """Strip markdown syntax and return plain text."""
        # Remove code blocks
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Remove inline code
        content = re.sub(r'`.*?`', '', content)
        
        # Remove headers
        content = re.sub(r'#{1,6}\s*', '', content)
        
        # Remove bold/italic
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        
        # Remove links
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        
        # Remove images
        content = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', content)
        
        # Remove blockquotes
        content = re.sub(r'^\s*>\s*', '', content, flags=re.MULTILINE)
        
        # Remove lists
        content = re.sub(r'^\s*[-+*]\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s*', '', content, flags=re.MULTILINE)
        
        # Remove horizontal rules
        content = re.sub(r'^\s*[-*_]{3,}\s*$', '', content, flags=re.MULTILINE)
        
        # Clean up
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
        
    def extract_toc(self, content: str) -> list:
        """Extract table of contents from markdown."""
        toc = []
        pattern = r'^(#{1,6})\s+(.*?)$'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            
            # Generate anchor
            anchor = title.lower()
            anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
            anchor = anchor.replace(' ', '-')
            
            toc.append({
                'level': level,
                'title': title,
                'anchor': anchor,
            })
            
        return toc
        
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown."""
        metadata = {}
        
        # Extract tags
        tags = re.findall(r'#(\w+)', content)
        if tags:
            metadata['tags'] = list(set(tags))
            
        # Extract links
        links = re.findall(r'\[(.*?)\]\((.*?)\)', content)
        if links:
            metadata['links'] = [{'text': text, 'url': url} for text, url in links]
            
        # Extract images
        images = re.findall(r'!\[(.*?)\]\((.*?)\)', content)
        if images:
            metadata['images'] = [{'alt': alt, 'src': src} for alt, src in images]
            
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            metadata['code_blocks'] = [
                {'language': lang, 'code': code}
                for lang, code in code_blocks
            ]
            
        return metadata
        
    def highlight_code(self, code: str, language: str = '') -> str:
        """Highlight code syntax."""
        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name, guess_lexer
            from pygments.formatters import HtmlFormatter
            
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = guess_lexer(code)
                
            formatter = HtmlFormatter(cssclass='highlight')
            return highlight(code, lexer, formatter)
        except:
            return f'<pre><code>{code}</code></pre>'

class CustomPreprocessor(Preprocessor):
    """Custom preprocessor for Metupy markdown."""
    
    def run(self, lines):
        new_lines = []
        
        for line in lines:
            # Custom processing
            line = self._process_metupy_syntax(line)
            new_lines.append(line)
            
        return new_lines
        
    def _process_metupy_syntax(self, line):
        """Process Metupy-specific syntax."""
        # Process widget syntax: {{ widget 'name' key=value }}
        widget_pattern = r"\{\{\s*widget\s+'([^']+)'\s*(.*?)\s*\}\}"
        match = re.match(widget_pattern, line)
        if match:
            widget_name = match.group(1)
            widget_params = match.group(2)
            return f'[METUPY_WIDGET:{widget_name}:{widget_params}]'
            
        # Process component syntax: {{ component 'name' }}
        component_pattern = r"\{\{\s*component\s+'([^']+)'\s*\}\}"
        match = re.match(component_pattern, line)
        if match:
            component_name = match.group(1)
            return f'[METUPY_COMPONENT:{component_name}]'
            
        return line

class CustomPostprocessor(Postprocessor):
    """Custom postprocessor for Metupy markdown."""
    
    def run(self, text):
        # Process widgets
        text = self._process_widgets(text)
        
        # Process components
        text = self._process_components(text)
        
        return text
        
    def _process_widgets(self, text):
        """Process widget placeholders."""
        pattern = r'\[METUPY_WIDGET:([^:]+):(.*?)\]'
        
        def replace_widget(match):
            widget_name = match.group(1)
            widget_params = match.group(2)
            
            # Parse parameters
            params = {}
            for param in widget_params.split():
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value.strip("'\"")
                    
            return f'<div class="metupy-widget" data-widget="{widget_name}" data-params="{widget_params}"></div>'
            
        return re.sub(pattern, replace_widget, text)
        
    def _process_components(self, text):
        """Process component placeholders."""
        pattern = r'\[METUPY_COMPONENT:([^\]]+)\]'
        
        def replace_component(match):
            component_name = match.group(1)
            return f'<div class="metupy-component" data-component="{component_name}"></div>'
            
        return re.sub(pattern, replace_component, text)