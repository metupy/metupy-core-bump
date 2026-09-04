<p align="center">
  <img src="https://raw.githubusercontent.com/palembangpy/metupy/main/src/metupy/assets/metupy.png" alt="Metupy Logo" width="120" height="120">
  <br>
  <strong>Fast • Simple • Extensible</strong>
  <br>
  Core utilities and foundational components for Metupy static site generator.
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/metupy-core?style=for-the-badge&color=blue" alt="PyPI Version">
  <img src="https://img.shields.io/badge/tests-passing-green?style=for-the-badge" alt="Tests Passing">
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=for-the-badge" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License">
</p>

---

# Metupy

**Markdown Engine Template Utilities Python**

Metupy is a modern, powerful, and flexible static site generator (SSG) built with Python. Metupy combines the power of Markdown, Jinja2, and Python to create fast and easy-to-manage static websites.

## Key Features

- **Python Integration** - Use Python directly in your content
- **Markdown Support** - Write content with Markdown
- **Jinja2 Templating** - Powerful template engine
- **Plugin System** - Extensible with plugins
- **Theme System** - Custom themes
- **Widget System** - Reusable components
- **Studio CMS** - Content management system
- **Live Reload** - Development server with hot reload
- **Database Support** - SQLite, PostgreSQL, MySQL
- **Search** - Built-in search functionality
- **Comments** - Comment system with Redis caching
- **Responsive** - Mobile-friendly output
- **Tailwind CSS** - Modern styling with Tailwind CSS v4

## Quick Start

### Installation

```bash
pip install metupy
```

### Create New Project

```bash
pym init --name my-site --template blog && cd my-site && pym serve
```

### Development

```bash
pym serve --port 3000 --open-browser
```

### Build

```bash
pym build --clean --minify
```

### Studio CMS

```bash
pym studio --port 3001
```

## Project Structure

```bash
    my-site/
    ├── pymconfig.py          # Configuration
    ├── pages/                # Python pages
    ├── content/              # Content (.pym, .md)
    ├── themes/               # Themes
    ├── plugins/              # Plugins
    ├── widgets/              # Widgets
    ├── output/               # Build output
    └── data/                 # Database
```

## Content Examples

### Python Page

File: pages/index.py

```python
    from metupy import Page
    
    class IndexPage(Page):
        title = "Home"
        template = "index.html"
        
        def get_context(self):
            return {
                'title': self.title,
                'content': 'Welcome to Metupy!'
            }
```

### PYM Content

File: content/index.pym
```text
    ---
    title: Home
    template: default.html
    ---
    
    # Welcome to Metupy!
    
    {% for item in items %}
    - {{ item }}
    {% endfor %}
```

## Plugin Example

File: plugins/my-plugin/plugin.py

```python
    from metupy import MetupyPlugin
    
    class MyPlugin(MetupyPlugin):
        name = "my-plugin"
        version = "1.0.0"
        
        def setup(self):
            print("Plugin loaded!")
            
        def on_page_after_render(self, page, html):
            return html.replace('</body>', '<footer>Powered by My Plugin</footer></body>')
```

## Theme Example
```bash
    themes/my-theme/
    ├── theme.json
    ├── templates/
    │   ├── base.html
    │   └── default.html
```

## License

MIT License - See LICENSE for details.
<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Python-3776AB?style=flat-square" alt="Made with Python">
  <br><br>
  MIT License — see LICENSE file for details
</p>
