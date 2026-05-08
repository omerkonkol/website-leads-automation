#!/usr/bin/env python3
"""
script.v2.py - Website Cloner (1:1)
Downloads a complete website exactly as-is: HTML (fully rendered), CSS, JS, images, fonts, videos.
Rewrites all URLs to relative local paths so the result works offline.

Usage:
    python script.v2.py <url> [output_dir]
    python script.v2.py https://eshelhamizug.co.il/
    python script.v2.py https://eshelhamizug.co.il/ ./my_clone

Requirements (install once):
    pip install playwright requests beautifulsoup4
    playwright install chromium
"""

import sys
import os
import re
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("WARNING: playwright not installed. Falling back to static requests (JS-rendered content will be missing).")
    print("Install: pip install playwright && playwright install chromium\n")


class WebsiteCloner:
    def __init__(self, url, output_dir, include_external=False):
        self.base_url = url.rstrip('/') + '/'
        parsed = urlparse(url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme
        self.output_dir = Path(output_dir)
        self.include_external = include_external
        self.downloaded = set()
        self.url_map = {}  # original_url -> local_relative_path (string)
        self.session = requests.Session()
        self.session.verify = False  # some Israeli sites have intermediate cert issues
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        requests.packages.urllib3.disable_warnings()

    def clone(self):
        print(f"\n{'='*60}")
        print(f"Cloning: {self.base_url}")
        print(f"Output:  {self.output_dir.resolve()}")
        print(f"{'='*60}\n")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Render page and collect all asset URLs from network
        print("[1/5] Rendering page and intercepting network requests...")
        html, intercepted_urls = self._render_page()
        print(f"      -> {len(intercepted_urls)} asset URLs intercepted")

        # Step 2: Download intercepted assets
        print("\n[2/5] Downloading intercepted assets...")
        for url in intercepted_urls:
            self._download_asset(url)

        # Step 3: Parse HTML for any assets missed by interception
        print("\n[3/5] Parsing HTML for additional assets...")
        extra = self._extract_assets_from_html(html)
        new_assets = extra - self.downloaded
        print(f"      -> {len(new_assets)} additional assets found")
        for url in sorted(new_assets):
            self._download_asset(url)

        # Step 4: Rewrite HTML and save index.html
        print("\n[4/5] Rewriting URLs in HTML...")
        rewritten_html = self._rewrite_html(html)
        index_path = self.output_dir / 'index.html'
        index_path.write_text(rewritten_html, encoding='utf-8', errors='replace')
        print(f"      -> Saved index.html")

        # Step 5: Rewrite URLs in all downloaded CSS files
        print("\n[5/5] Rewriting URLs in CSS files...")
        self._rewrite_css_files()

        total = len(self.downloaded)
        print(f"\n{'='*60}")
        print(f"Done! {total} assets downloaded.")
        print(f"Open: {index_path.resolve()}")
        print(f"{'='*60}\n")

    # -------------------------------------------------------------------------
    # Page rendering
    # -------------------------------------------------------------------------

    def _render_page(self):
        if not HAS_PLAYWRIGHT:
            resp = self.session.get(self.base_url, timeout=30, verify=False)
            resp.raise_for_status()
            return resp.text, []

        intercepted_urls = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )
            page = context.new_page()

            def on_request(request):
                url = request.url
                if request.resource_type in ('stylesheet', 'script', 'image', 'font', 'media', 'other'):
                    if self._should_download(url):
                        intercepted_urls.append(url)

            page.on('request', on_request)

            print("      -> Navigating (waiting for networkidle)...")
            page.goto(self.base_url, wait_until='networkidle', timeout=90000)

            # Scroll through entire page to trigger lazy-loaded content
            print("      -> Scrolling to trigger lazy loading...")
            page_height = page.evaluate('document.body.scrollHeight')
            scroll_pos = 0
            while scroll_pos < page_height:
                page.evaluate(f'window.scrollTo(0, {scroll_pos})')
                page.wait_for_timeout(150)
                scroll_pos += 600
                # page height can grow as lazy items load
                page_height = page.evaluate('document.body.scrollHeight')

            # Wait for any deferred scripts that fire after scroll
            page.wait_for_timeout(3000)
            page.evaluate('window.scrollTo(0, 0)')

            html = page.content()
            browser.close()

        return html, list(set(intercepted_urls))

    # -------------------------------------------------------------------------
    # Asset helpers
    # -------------------------------------------------------------------------

    def _should_download(self, url):
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            if self.include_external:
                return True
            domain = parsed.netloc
            return domain == self.base_domain or domain.endswith('.' + self.base_domain)
        except Exception:
            return False

    def _url_to_local_path(self, url):
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if path.startswith('/'):
            path = path[1:]
        if not path or path.endswith('/'):
            path = path + 'index.html'

        # Sanitize Windows-illegal characters
        path = path.replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')

        # Handle query strings (WordPress cache-busters like ?ver=6.4)
        if parsed.query:
            q_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
            stem, ext = os.path.splitext(path)
            if not ext:
                ext = '.html'
            path = f"{stem}.{q_hash}{ext}"

        # Ensure extension exists for paths without one
        if not os.path.splitext(path)[1]:
            path = path.rstrip('/') + '/index.html'

        return path

    def _download_asset(self, url):
        # Normalize: strip fragment
        url = url.split('#')[0]
        if not url or url in self.downloaded:
            return
        if not self._should_download(url):
            return

        self.downloaded.add(url)
        local_path = self._url_to_local_path(url)
        full_path = self.output_dir / local_path

        # Skip if already on disk (re-runs)
        if full_path.exists():
            self.url_map[url] = local_path
            return

        try:
            resp = self.session.get(url, timeout=30, stream=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  SKIP  {url[:80]}  ({e})")
            return

        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(full_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=16384):
                    f.write(chunk)
            self.url_map[url] = local_path
            print(f"  OK    {local_path}")
        except Exception as e:
            print(f"  ERR   {local_path}: {e}")

    # -------------------------------------------------------------------------
    # Asset extraction from HTML
    # -------------------------------------------------------------------------

    def _extract_assets_from_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        assets = set()

        def add(raw):
            if not raw:
                return
            raw = raw.strip()
            if raw.startswith('data:') or raw.startswith('#') or raw.startswith('javascript:'):
                return
            abs_url = urljoin(self.base_url, raw).split('#')[0]
            if self._should_download(abs_url):
                assets.add(abs_url)

        # <link rel="stylesheet">
        for tag in soup.find_all('link', href=True):
            rel = tag.get('rel', [])
            if isinstance(rel, list):
                rel = ' '.join(rel)
            if 'stylesheet' in rel or 'preload' in rel or 'icon' in rel:
                add(tag['href'])

        # <script src>
        for tag in soup.find_all('script', src=True):
            add(tag['src'])

        # <img src, data-src, srcset>
        for tag in soup.find_all('img'):
            add(tag.get('src'))
            add(tag.get('data-src'))
            add(tag.get('data-lazy-src'))
            for srcset_url in self._parse_srcset(tag.get('srcset', '')):
                add(srcset_url)

        # <source>, <video>, <audio>
        for tag in soup.find_all(['source', 'video', 'audio']):
            add(tag.get('src'))
            for srcset_url in self._parse_srcset(tag.get('srcset', '')):
                add(srcset_url)

        # Inline style url()
        for tag in soup.find_all(style=True):
            for m in re.finditer(r'url\(["\']?([^"\')\s]+)["\']?\)', tag['style']):
                add(m.group(1))

        # <style> blocks
        for style in soup.find_all('style'):
            if style.string:
                for m in re.finditer(r'url\(["\']?([^"\')\s]+)["\']?\)', style.string):
                    add(m.group(1))

        return assets

    def _parse_srcset(self, srcset):
        urls = []
        if not srcset:
            return urls
        for part in srcset.split(','):
            part = part.strip()
            tokens = part.split()
            if tokens:
                urls.append(tokens[0])
        return urls

    # -------------------------------------------------------------------------
    # URL rewriting
    # -------------------------------------------------------------------------

    def _abs_to_local(self, raw_url, page_path='index.html'):
        if not raw_url:
            return raw_url
        raw_url = raw_url.strip()
        if raw_url.startswith('data:') or raw_url.startswith('#') or raw_url.startswith('javascript:'):
            return raw_url
        abs_url = urljoin(self.base_url, raw_url).split('#')[0]
        if abs_url in self.url_map:
            local = self.url_map[abs_url]
            page_dir = os.path.dirname(page_path)
            rel = os.path.relpath(local, page_dir).replace('\\', '/')
            return rel
        return raw_url

    def _rewrite_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        # Remove <base> tag (breaks relative paths)
        for tag in soup.find_all('base'):
            tag.decompose()

        # Rewrite standard src/href attributes
        attr_tags = {
            'link': 'href',
            'script': 'src',
            'img': 'src',
            'video': 'src',
            'audio': 'src',
            'source': 'src',
            'iframe': 'src',
        }
        for tag_name, attr in attr_tags.items():
            for tag in soup.find_all(tag_name):
                if tag.get(attr):
                    tag[attr] = self._abs_to_local(tag[attr])

        # data-src (lazy loading)
        for tag in soup.find_all(attrs={'data-src': True}):
            tag['data-src'] = self._abs_to_local(tag['data-src'])

        for tag in soup.find_all(attrs={'data-lazy-src': True}):
            tag['data-lazy-src'] = self._abs_to_local(tag['data-lazy-src'])

        # srcset
        for tag in soup.find_all(attrs={'srcset': True}):
            tag['srcset'] = self._rewrite_srcset(tag['srcset'])

        # Inline style url()
        for tag in soup.find_all(style=True):
            tag['style'] = self._rewrite_css_url_string(tag['style'], 'index.html')

        # <style> blocks
        for style in soup.find_all('style'):
            if style.string:
                style.string = self._rewrite_css_url_string(style.string, 'index.html')

        return str(soup)

    def _rewrite_srcset(self, srcset, page_path='index.html'):
        if not srcset:
            return srcset
        parts = []
        for part in srcset.split(','):
            part = part.strip()
            tokens = part.split()
            if not tokens:
                continue
            url_part = self._abs_to_local(tokens[0], page_path)
            if len(tokens) > 1:
                parts.append(f"{url_part} {tokens[1]}")
            else:
                parts.append(url_part)
        return ', '.join(parts)

    def _rewrite_css_url_string(self, content, css_path):
        def replacer(m):
            inner = m.group(1).strip()
            # Strip surrounding quotes
            if (inner.startswith('"') and inner.endswith('"')) or \
               (inner.startswith("'") and inner.endswith("'")):
                inner = inner[1:-1]
            if inner.startswith('data:') or inner.startswith('#'):
                return m.group(0)
            abs_url = urljoin(self.base_url, inner).split('#')[0]
            if abs_url in self.url_map:
                local = self.url_map[abs_url]
                css_dir = os.path.dirname(css_path)
                rel = os.path.relpath(local, css_dir).replace('\\', '/')
                return f"url('{rel}')"
            return m.group(0)

        return re.sub(r'url\((["\']?[^"\')\s]+["\']?)\)', replacer, content)

    def _rewrite_css_files(self):
        css_files = [(url, local) for url, local in self.url_map.items() if local.endswith('.css')]
        print(f"      -> {len(css_files)} CSS files to rewrite")

        for url, local_path in css_files:
            full_path = self.output_dir / local_path
            if not full_path.exists():
                continue
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')

                # First pass: find and download any assets referenced in this CSS
                for m in re.finditer(r'url\(["\']?([^"\')\s]+)["\']?\)', content):
                    raw = m.group(1).strip('"\'')
                    if not raw.startswith('data:') and not raw.startswith('#'):
                        abs_asset = urljoin(url, raw).split('#')[0]
                        if self._should_download(abs_asset):
                            self._download_asset(abs_asset)

                # Also handle @import
                for m in re.finditer(r'@import\s+["\']([^"\']+)["\']', content):
                    abs_import = urljoin(url, m.group(1)).split('#')[0]
                    if self._should_download(abs_import):
                        self._download_asset(abs_import)

                # Second pass: rewrite
                rewritten = self._rewrite_css_url_string(content, local_path)
                full_path.write_text(rewritten, encoding='utf-8', errors='replace')
                print(f"  CSS   {local_path}")
            except Exception as e:
                print(f"  ERR   CSS rewrite {local_path}: {e}")


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith('http'):
        url = 'https://' + url

    if len(sys.argv) >= 3:
        output_dir = sys.argv[2]
    else:
        domain = urlparse(url).netloc
        output_dir = f"cloned_{domain}"

    cloner = WebsiteCloner(url, output_dir)
    cloner.clone()


if __name__ == '__main__':
    main()
