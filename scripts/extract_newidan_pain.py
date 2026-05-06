"""Extract the pain section + neighboring sections from newidan HTML
to understand exact structure, classes, and data-aos values."""
import pathlib, re, sys

sys.stdout.reconfigure(encoding='utf-8')
src = pathlib.Path('e:/system/tmp_or_gabai/_ref_newidan.html').read_text(encoding='utf-8', errors='ignore')

# Find the section containing 'זה נשמע לכם מוכר'
idx = src.find('זה נשמע לכם')
print(f'pain headline at offset: {idx}')
print()

# Get 5000 chars before and 5000 after
start = max(0, idx - 5000)
end = min(len(src), idx + 7000)
chunk = src[start:end]
print('=== CONTEXT AROUND PAIN HEADLINE ===')
print(chunk)
