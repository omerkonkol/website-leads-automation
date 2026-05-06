"""Analyze newidan.co.il source: list CSS/JS, animation hints, section markers."""
import pathlib, re, sys

sys.stdout.reconfigure(encoding='utf-8')
src = pathlib.Path('e:/system/tmp_or_gabai/_ref_newidan.html').read_text(encoding='utf-8', errors='ignore')
print(f'HTML size: {len(src):,} bytes')
print()

# CSS files
print('=== CSS files ===')
for url in re.findall(r'<link[^>]+href=[\'"]([^\'"]+\.css[^\'"]*)[\'"]', src):
    print(f'  {url}')
print()

# JS files
print('=== JS files ===')
for url in re.findall(r'<script[^>]+src=[\'"]([^\'"]+)[\'"]', src):
    print(f'  {url}')
print()

# Animation library hints
print('=== Animation library mentions ===')
for word in ['gsap', 'aos', 'framer', 'animate.css', 'wow.js', 'lottie', 'motion', 'scrollmagic', 'splittext', 'splittype']:
    n = len(re.findall(rf'\b{re.escape(word)}\b', src, flags=re.I))
    if n: print(f'  "{word}": {n}x')
print()

# Inline keyframes count
print(f'inline @keyframes count: {len(re.findall(r"@keyframes", src))}')
print()

# Look for specific animation patterns in inline code
print('=== Inline animation keywords ===')
for word in ['data-aos', 'data-anim', 'data-scroll', 'animate-', 'scroll-trigger']:
    n = len(re.findall(rf'{re.escape(word)}', src, flags=re.I))
    if n: print(f'  "{word}": {n}x')
print()

# Find section anchors / navigation structure
print('=== Sections (id/class hints) ===')
# Find h2 headlines
h2s = re.findall(r'<h2[^>]*>(.+?)</h2>', src, flags=re.S)
for h in h2s[:20]:
    txt = re.sub(r'<[^>]+>', ' ', h)
    txt = re.sub(r'\s+', ' ', txt).strip()
    if txt: print(f'  H2: {txt[:80]}')
print()

# Find class names with 'pain', 'callout', 'badge', 'photo', 'image'
print('=== Specific class names ===')
classes = set()
for m in re.findall(r'class=[\'"]([^\'"]+)[\'"]', src):
    for c in m.split():
        if any(k in c.lower() for k in ['pain','callout','badge','photo','image','hero','nav','section','card','testimonial']):
            classes.add(c)
for c in sorted(classes)[:50]: print(f'  {c}')
