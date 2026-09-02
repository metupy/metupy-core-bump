# metupy/generators/static_generator.py
"""Static Site Generator."""

from typing import Dict, Any, List
from pathlib import Path
import asyncio
import shutil

class StaticGenerator:
    """Generates static site."""
    
    def __init__(self, engine):
        self.engine = engine
        
    async def generate(self) -> Dict[str, Any]:
        """Generate static site."""
        stats = {
            'pages': 0,
            'posts': 0,
            'docs': 0,
            'slides': 0,
            'assets': 0,
            'total_size': 0,
        }
        
        # Clean output
        await self._clean_output()
        
        # Generate pages
        stats['pages'] = await self._generate_pages()
        
        # Generate blog
        stats['posts'] = await self._generate_blog()
        
        # Generate docs
        stats['docs'] = await self._generate_docs()
        
        # Generate slides
        stats['slides'] = await self._generate_slides()
        
        # Copy assets
        stats['assets'] = await self._copy_assets()
        
        # Generate sitemap
        await self._generate_sitemap()
        
        # Generate robots.txt
        await self._generate_robots()
        
        # Calculate total size
        stats['total_size'] = self._calculate_size()
        
        return stats
        
    async def _clean_output(self):
        """Clean output directory."""
        if self.engine.output_dir.exists():
            shutil.rmtree(self.engine.output_dir)
        self.engine.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def _generate_pages(self) -> int:
        """Generate regular pages."""
        count = 0
        
        for page in self.engine.content_manager.get_pages_by_type('page'):
            html = await self.engine.renderers['page'].render(page)
            output_path = self.engine.output_dir / page.output_path
            await self._write_file(output_path, html)
            count += 1
            
        return count
        
    async def _generate_blog(self) -> int:
        """Generate blog pages."""
        count = 0
        
        # Generate individual posts
        for post in self.engine.content_manager.posts:
            html = await self.engine.renderers['blog'].render_post(post)
            output_path = self.engine.output_dir / post.output_path
            await self._write_file(output_path, html)
            count += 1
            
        # Generate blog list
        posts = self.engine.content_manager.posts
        total_pages = (len(posts) + 9) // 10  # 10 per page
        
        for page_num in range(1, total_pages + 1):
            html = await self.engine.renderers['blog'].render_list(posts, page_num)
            if page_num == 1:
                output_path = self.engine.output_dir / 'blog' / 'index.html'
            else:
                output_path = self.engine.output_dir / 'blog' / f'page-{page_num}' / 'index.html'
            await self._write_file(output_path, html)
            count += 1
            
        return count
        
    async def _generate_docs(self) -> int:
        """Generate documentation pages."""
        count = 0
        
        for doc in self.engine.content_manager.get_pages_by_type('docs'):
            html = await self.engine.renderers['docs'].render_doc(doc)
            output_path = self.engine.output_dir / doc.output_path
            await self._write_file(output_path, html)
            count += 1
            
        return count
        
    async def _generate_slides(self) -> int:
        """Generate slides."""
        count = 0
        
        for slides in self.engine.content_manager.get_pages_by_type('slides'):
            html = await self.engine.renderers['slides'].render_slides(slides)
            output_path = self.engine.output_dir / slides.output_path
            await self._write_file(output_path, html)
            count += 1
            
        return count
        
    async def _copy_assets(self) -> int:
        """Copy assets."""
        if not self.engine.assets_dir.exists():
            return 0
            
        assets_output = self.engine.output_dir / 'assets'
        shutil.copytree(self.engine.assets_dir, assets_output, dirs_exist_ok=True)
        
        return len(list(assets_output.rglob('*')))
        
    async def _generate_sitemap(self):
        """Generate sitemap.xml."""
        urls = []
        
        for page in self.engine.content_manager.pages:
            url = f"{self.engine.config.SITE_URL}{page.url}"
            urls.append(url)
            
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for url in urls:
            sitemap += f'  <url><loc>{url}</loc></url>\n'
            
        sitemap += '</urlset>'
        
        await self._write_file(
            self.engine.output_dir / 'sitemap.xml',
            sitemap
        )
        
    async def _generate_robots(self):
        """Generate robots.txt."""
        robots = f"""User-agent: *
Allow: /

Sitemap: {self.engine.config.SITE_URL}/sitemap.xml
"""
        
        await self._write_file(
            self.engine.output_dir / 'robots.txt',
            robots
        )
        
    async def _write_file(self, path: Path, content: str):
        """Write file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        
    def _calculate_size(self) -> str:
        """Calculate total size."""
        total = sum(
            f.stat().st_size
            for f in self.engine.output_dir.rglob('*')
            if f.is_file()
        )
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total < 1024:
                return f"{total:.2f} {unit}"
            total /= 1024
            
        return f"{total:.2f} TB"