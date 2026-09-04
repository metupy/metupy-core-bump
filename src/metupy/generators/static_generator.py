"""
Static site generator for Metupy.

Generates static HTML files from content and templates.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import markdown as md


class StaticGenerator:
    """Generate static site from content."""

    def __init__(self, engine):
        """
        Initialize StaticGenerator.

        Args:
            engine: MetupyEngine instance.
        """
        self.engine = engine

    async def generate(self) -> Dict[str, Any]:
        """
        Generate static site.

        Returns:
            Dictionary with generation statistics.
        """
        stats = {
            'pages': 0,
            'assets': 0,
            'static_files': 0,
        }

        await self._clean_output()

        stats['pages'] = await self._generate_pages()
        stats['assets'] = await self._copy_assets()
        stats['static_files'] = await self._copy_static_files()

        return stats

    async def _clean_output(self) -> None:
        """Clean output directory."""
        if self.engine.output_dir.exists():
            shutil.rmtree(self.engine.output_dir)
        self.engine.output_dir.mkdir(parents=True, exist_ok=True)

    async def _generate_pages(self) -> int:
        """
        Generate all pages to HTML.

        Returns:
            Number of pages generated.
        """
        count = 0

        content_manager = getattr(self.engine, 'content_manager', None)
        page_manager = getattr(self.engine, 'page_manager', None)

        if content_manager:
            for page in content_manager.pages:
                await self._render_page(page)
                count += 1

        if page_manager:
            for page in page_manager.pages:
                await self._render_page(page)
                count += 1

        return count

    async def _render_page(self, page) -> None:
        """
        Render single page to output.

        Args:
            page: Page instance.
        """
        template_env = getattr(self.engine, 'template_env', None)
        if not template_env:
            return

        template = template_env.get_template(page.template)
        context = page.get_context()

        if page.content_type in ['pym', 'markdown']:
            context['content'] = md.markdown(
                page.content,
                extensions=['extra', 'tables', 'fenced_code']
            )

        html = template.render(**context)

        output_path = self.engine.output_dir / page.output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
        print(f"  Generated: {page.output_path}")

    async def _copy_assets(self) -> int:
        """
        Copy assets to output.

        Returns:
            Number of files copied.
        """
        if not self.engine.assets_dir.exists():
            return 0

        assets_output = self.engine.output_dir / 'assets'
        shutil.copytree(self.engine.assets_dir, assets_output, dirs_exist_ok=True)
        return len(list(assets_output.rglob('*')))

    async def _copy_static_files(self) -> int:
        """
        Copy theme static files to output.

        Returns:
            Number of files copied.
        """
        static_dir = self.engine.theme_dir / 'static'
        if not static_dir.exists():
            return 0

        shutil.copytree(static_dir, self.engine.output_dir, dirs_exist_ok=True)
        return len(list(static_dir.rglob('*')))