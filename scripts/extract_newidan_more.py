"""Extract hero, nav, services, gallery, testimonials, and final CTA sections."""
import pathlib, re, sys
sys.stdout.reconfigure(encoding='utf-8')

src = pathlib.Path('e:/system/tmp_or_gabai/_ref_newidan.html').read_text(encoding='utf-8', errors='ignore')

# Find sections by id
print('=== <section> tags ===')
for m in re.finditer(r'<section[^>]*id=[\'"]([^\'"]+)[\'"][^>]*>', src):
    print(f'  id="{m.group(1)}" at offset {m.start()}')
print()

# Show <header> / <nav> structure
print('=== <header> / nav ===')
m = re.search(r'<header[^>]*>.*?</header>', src, flags=re.S)
if m:
    print(m.group(0)[:3500])
print()
print('--- NAV separately ---')
m2 = re.search(r'<nav[^>]*>.*?</nav>', src, flags=re.S)
if m2:
    print(m2.group(0)[:3000])
