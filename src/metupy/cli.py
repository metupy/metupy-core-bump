"""
Metupy CLI - Command Line Interface.

Provides the `pym` command with subcommands for managing
Metupy static site generator projects.
"""

import argparse
import asyncio
import base64
import json
import shutil
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich import box

console = Console()


class MetupyArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser with Rich-styled help output."""

    def print_help(self, file=None):
        """Print help with Rich styling."""
        console.print(self._format_help_rich())

    def format_help(self):
        """Format help text."""
        return ""

    def format_usage(self):
        """Format usage without braces."""
        return "pym [options] command"

    def _format_help_rich(self) -> Panel:
        """Build Rich Panel for help output."""
        commands_table = Table(
            show_header=True,
            box=box.SIMPLE,
            expand=True,
            padding=(0, 1),
        )
        commands_table.add_column("Command", style="bold green", width=15, no_wrap=True)
        commands_table.add_column("Description", style="white", overflow="fold")

        if self._subparsers:
            for action in self._actions:
                if isinstance(action, argparse._SubParsersAction):
                    for name, subparser in action.choices.items():
                        description = subparser.description or ""
                        commands_table.add_row(name, description)

        options_table = Table(
            show_header=True,
            box=box.SIMPLE,
            expand=True,
            padding=(0, 1),
        )
        options_table.add_column("Option", style="bold green", width=20, no_wrap=True)
        options_table.add_column("Description", style="white", overflow="fold")

        for action in self._actions:
            if isinstance(action, argparse._HelpAction):
                options_table.add_row(", ".join(action.option_strings), action.help)
            elif isinstance(action, argparse._VersionAction):
                options_table.add_row(", ".join(action.option_strings), action.help)

        renderables = [
            f"[bold cyan]Usage:[/bold cyan] [white]{self.format_usage()}[/white]",
            "",
            f"[bold white]{self.description}[/bold white]",
            "",
            "[bold yellow]Commands:[/bold yellow]",
            commands_table,
            "",
            "[bold yellow]Options:[/bold yellow]",
            options_table,
        ]

        if self.epilog:
            renderables.append("")
            renderables.append(f"[dim]{self.epilog}[/dim]")

        content = Group(*renderables)

        return Panel(
            content,
            title="[bold cyan]Metupy[/bold cyan]",
            border_style="blue",
            padding=(1, 2),
        )

    def error(self, message):
        """Show error with Rich styling."""
        console.print(f"[bold red]Error:[/bold red] {message}")
        console.print()
        self.print_help()
        sys.exit(2)


def create_parser() -> MetupyArgumentParser:
    """Create argument parser for CLI."""
    parser = MetupyArgumentParser(
        prog='pym',
        description='Metupy - Markdown Engine Template Utilities Python',
        epilog='For more information, visit: https://metupy.dev',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='pym 1.0.0 (Metupy)',
        help='Show version information'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    serve_parser = subparsers.add_parser(
        'serve',
        help='Serve site with livereload',
        description='Start development server with live reload on port 3155'
    )
    serve_parser.add_argument('--host', default='localhost', help='Host to bind')
    serve_parser.add_argument('--port', type=int, default=3155, help='Port to bind')
    serve_parser.add_argument('--open-browser', action='store_true', help='Open browser automatically')

    build_parser = subparsers.add_parser(
        'build',
        help='Build static site',
        description='Generate static site to output directory'
    )
    build_parser.add_argument('--output', '-o', default=None, help='Output directory override')

    studio_parser = subparsers.add_parser(
        'studio',
        help='Open Metupy Studio',
        description='Start Metupy Studio CMS on port 3154'
    )
    studio_parser.add_argument('--port', type=int, default=3154, help='Studio port')
    studio_parser.add_argument('--no-browser', action='store_true', help='Do not open browser')
    studio_parser.add_argument('--host', default='localhost', help='Host to bind')

    init_parser = subparsers.add_parser(
        'init',
        help='Initialize new Metupy project',
        description='Create minimal project structure based on template'
    )
    init_parser.add_argument('--name', help='Project name')
    init_parser.add_argument(
        '--template',
        choices=['docs', 'basic'],
        default='docs',
        help='Project template (default: docs)'
    )
    init_parser.add_argument('--force', action='store_true', help='Force creation')

    info_parser = subparsers.add_parser(
        'info',
        help='Show project information',
        description='Display information about the current project'
    )

    return parser


def _open_browser_delayed(url: str, delay: float = 1.5) -> None:
    """Open browser after delay."""
    import threading
    import time

    def _open():
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def _print_banner(title: str, subtitle: str, color: str = "cyan") -> None:
    """Print styled banner."""
    console.print(Panel.fit(
        f"[bold {color}]{title}[/bold {color}]\n[dim]{subtitle}[/dim]",
        border_style=color,
        padding=(1, 2),
    ))


def _install_theme_to_workspace(theme_name: str = 'peradocs') -> None:
    """
    Copy bundled theme from Metupy package to ~/.metupy/themes/.

    Args:
        theme_name: Theme name to install.
    """
    workspace_themes = Path.home() / '.metupy' / 'themes'
    workspace_themes.mkdir(parents=True, exist_ok=True)

    theme_dest = workspace_themes / theme_name

    if theme_dest.exists() and (theme_dest / 'templates').exists():
        return

    try:
        import metupy
        package_dir = Path(metupy.__file__).parent
        bundled_theme = package_dir / 'themes' / theme_name

        if bundled_theme.exists() and (bundled_theme / 'templates').exists():
            if theme_dest.exists():
                shutil.rmtree(theme_dest)
            shutil.copytree(bundled_theme, theme_dest)
            return
    except (ImportError, AttributeError):
        pass

    # Create minimal fallback theme
    theme_dest.mkdir(parents=True, exist_ok=True)
    (theme_dest / 'theme.json').write_text(
        json.dumps(
            {
                "name": theme_name,
                "version": "1.0.0",
                "description": f"{theme_name} theme",
                "author": "Metupy Team",
            },
            indent=2,
        ),
        encoding='utf-8',
    )

    templates_dir = theme_dest / 'templates'
    templates_dir.mkdir(exist_ok=True)
    partials_dir = templates_dir / '_partials'
    partials_dir.mkdir(exist_ok=True)

    base_template = '''<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ site.name }}</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <style>
        body { font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 2em; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { font-family: monospace; }
        footer { border-top: 1px solid #eee; margin-top: 40px; padding-top: 20px; text-align: center; color: #666; }
    </style>
</head>
<body>
    <header><h1>{{ site.name }}</h1></header>
    <main>{% block content %}{% endblock %}</main>
    <footer><p>Built with Metupy - {{ config.ACTIVE_THEME }}</p></footer>
</body>
</html>'''

    layout_template = '''{% extends "base.html" %}
{% block content %}
<article>
    <h1>{{ title }}</h1>
    {{ content | safe }}
</article>
{% endblock %}'''

    (templates_dir / 'base.html').write_text(base_template, encoding='utf-8')
    (templates_dir / 'layout.html').write_text(layout_template, encoding='utf-8')

    # Create a minimal sidebar partial to avoid missing include errors
    sidebar_template = '''<aside class="metu-docs-sidebar">
    {% for group in sidebar_groups %}
    <div class="metu-sidebar-group">
        <h3>{{ group.title }}</h3>
        <ul>
            {% for item in group.items %}
            <li>
                <a href="{{ item.url }}" class="{% if item.current %}metu-active{% endif %}">
                    {{ item.title }}
                </a>
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
</aside>'''
    (partials_dir / '_sidebar.html').write_text(sidebar_template, encoding='utf-8')

    static_dir = theme_dest / 'static'
    static_dir.mkdir(exist_ok=True)


def cmd_serve(args: argparse.Namespace) -> None:
    """Handle serve command."""
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config

    config = get_config()
    if hasattr(config, 'DEV_HOST'):
        config.DEV_HOST = args.host
    if hasattr(config, 'DEV_PORT'):
        config.DEV_PORT = args.port

    engine = MetupyEngine()

    console.print(f"[green]➜[/green] Starting server at [bold cyan]http://{args.host}:{args.port}[/bold cyan]")

    if args.open_browser:
        _open_browser_delayed(f'http://{args.host}:{args.port}')

    try:
        asyncio.run(engine.serve(verbose=False))
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def cmd_build(args: argparse.Namespace) -> None:
    """Handle build command."""
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config

    config = get_config()
    if args.output:
        config.OUTPUT_DIR = Path(args.output)

    engine = MetupyEngine()

    try:
        asyncio.run(engine.build(verbose=False))
        console.print("[green]✓[/green] Build completed.")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def cmd_studio(args: argparse.Namespace) -> None:
    """Handle studio command."""
    from metupy.core.engine import MetupyEngine
    from metupy.config import get_config

    config = get_config()
    if hasattr(config, 'STUDIO_PORT'):
        config.STUDIO_PORT = args.port
    if hasattr(config, 'STUDIO_HOST'):
        config.STUDIO_HOST = args.host

    engine = MetupyEngine()

    console.print(f"[green]➜[/green] Starting Studio at [bold magenta]http://{args.host}:{args.port}[/bold magenta]")

    if not args.no_browser:
        _open_browser_delayed(f'http://{args.host}:{args.port}')

    try:
        asyncio.run(engine.start_studio())
    except KeyboardInterrupt:
        console.print("\n[yellow]Studio stopped[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


def cmd_init(args: argparse.Namespace) -> None:
    """Handle init command. Creates a minimal docs project."""
    project_name = args.name or Path.cwd().name
    template = args.template or 'docs'

    project_dir = Path(project_name)

    if project_dir.exists() and not args.force:
        if not Confirm.ask(f"[yellow]Directory '{project_name}' already exists. Continue?[/yellow]"):
            return

    project_dir.mkdir(parents=True, exist_ok=True)

    # Install theme internally
    _install_theme_to_workspace('peradocs')

    # Create pymconfig.py
    config_content = _create_config_content(project_name, template)
    (project_dir / 'pymconfig.py').write_text(config_content, encoding='utf-8')

    # Create content
    _create_template_content(project_dir, template)

    # Create favicon
    _create_favicon(project_dir)

    # Create .gitignore
    _create_gitignore(project_dir)

    console.print(Panel.fit(
        f"[bold green]✓[/bold green] Project [bold]{project_name}[/bold] created successfully.\n"
        f"[dim]Next: [cyan]cd {project_name}[/cyan] then [cyan]pym serve[/cyan][/dim]",
        border_style="green",
        padding=(1, 2),
    ))


def _create_config_content(project_name: str, template: str = 'docs') -> str:
    """Generate pymconfig.py content."""
    if template == 'docs':
        content_dir = 'BASE_DIR / "docs"'
    else:
        content_dir = 'BASE_DIR / "content"'

    return f'''"""
pymconfig.py - Metupy Project Configuration.

Edit values below to configure your site.
All variables MUST be UPPERCASE.
"""

from pathlib import Path

SITE_NAME = "{project_name}"
SITE_VERSION = "1.0.0"
SITE_DESCRIPTION = "Built with Metupy SSG"
SITE_AUTHOR = "Your Name"
SITE_KEYWORDS = ["metupy", "static-site", "ssg"]
SITE_LANG = "en"
SITE_TIMEZONE = "UTC"

SITE_URL = "http://localhost:3155"
SITE_BASE_URL = "/"
SITE_CANONICAL_URL = f"{{SITE_URL}}/"

BASE_DIR = Path(__file__).parent
CONTENT_DIR = {content_dir}
OUTPUT_DIR = Path.home() / ".metupy" / "output" / "{project_name}"
THEME_DIR = Path.home() / ".metupy" / "themes" / "peradocs"
ASSETS_DIR = CONTENT_DIR / "assets"
DATA_DIR = BASE_DIR / "data"

ACTIVE_THEME = "peradocs"
ACTIVE_PLUGINS = []

BUILD_MINIFY_HTML = False
BUILD_MINIFY_CSS = False
BUILD_MINIFY_JS = False
BUILD_GENERATE_SITEMAP = True
BUILD_GENERATE_FEED = True
BUILD_CACHE_ENABLED = True
BUILD_PRETTY_URLS = True

DEV_HOST = "localhost"
DEV_PORT = 3155
DEV_DEBUG = True
DEV_LIVE_RELOAD = True
DEV_OPEN_BROWSER = True

STUDIO_ENABLED = True
STUDIO_HOST = "localhost"
STUDIO_PORT = 3154
STUDIO_AUTO_OPEN = True
STUDIO_REQUIRE_LOGIN = True

DB_ENGINE = "sqlite"
DB_PATH = DATA_DIR / "metupy.db"

CACHE_ENABLED = False
CACHE_TYPE = "memory"

SECRET_KEY = "dev-secret-key-change-in-production"

MARKDOWN_EXTENSIONS = ["extra", "tables", "fenced_code"]
MARKDOWN_EXTENSION_CONFIGS = {{}}

JINJA_EXTENSIONS = ["jinja2.ext.do", "jinja2.ext.loopcontrols"]

DEBUG = True
TESTING = False
PRODUCTION = False
'''


def _create_template_content(project_dir: Path, template: str) -> None:
    """Create content files based on selected template."""
    if template == 'docs':
        docs_dir = project_dir / 'docs'
        docs_dir.mkdir(parents=True, exist_ok=True)

        index_content = '''---
title: Home
template: layout.html
type: docs
order: 0
---

# Welcome to Documentation

This is your documentation site built with Metupy.

## Getting Started

Write your documentation here using Markdown.
'''
        (docs_dir / 'index.pym').write_text(index_content, encoding='utf-8')
    else:
        content_dir = project_dir / 'content'
        content_dir.mkdir(parents=True, exist_ok=True)

        index_content = '''---
title: Home
template: layout.html
---

# Welcome to Metupy

This is your new Metupy site.
'''
        (content_dir / 'index.pym').write_text(index_content, encoding='utf-8')


def _create_favicon(project_dir: Path) -> None:
    """Create default favicon.png."""
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ'
        'AAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    (project_dir / 'favicon.png').write_bytes(png_data)


def _create_gitignore(project_dir: Path) -> None:
    """Create .gitignore file."""
    gitignore = """# Metupy
public/
__pycache__/
*.pyc
.env
data/*.db
.DS_Store
"""
    (project_dir / '.gitignore').write_text(gitignore, encoding='utf-8')


def cmd_info(args: argparse.Namespace) -> None:
    """Handle info command."""
    from metupy.config import get_config

    config = get_config()
    table = Table(title="Project Info", box=box.ROUNDED)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green", width=50, overflow="fold")

    table.add_row("Site Name", str(getattr(config, 'SITE_NAME', 'N/A')))
    table.add_row("Site URL", str(getattr(config, 'SITE_URL', 'N/A')))
    table.add_row("Active Theme", str(getattr(config, 'ACTIVE_THEME', 'default')))
    table.add_row("Studio Port", str(getattr(config, 'STUDIO_PORT', 3154)))
    table.add_row("Serve Port", str(getattr(config, 'DEV_PORT', 3155)))

    console.print(table)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    handlers = {
        'serve': cmd_serve,
        'build': cmd_build,
        'studio': cmd_studio,
        'init': cmd_init,
        'info': cmd_info,
    }

    handler = handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
    else:
        console.print(f"[bold red]Unknown command:[/bold red] {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()