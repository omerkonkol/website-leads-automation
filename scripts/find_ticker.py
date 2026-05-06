"""Find the dark scrolling ticker section in newidan HTML."""
import pathlib, re, sys
sys.stdout.reconfigure(encoding='utf-8')
src = pathlib.Path('e:/system/tmp_or_gabai/_ref_newidan.html').read_text(encoding='utf-8', errors='ignore')

# The screenshot shows phrases like 'גימור פרימיום', 'ניקיון מופתי', 'זמינות בפריסה רחבה', 'עבודה מהלב'
for needle in ['גימור פרימיום','ניקיון מופתי','זמינות בפריסה','עבודה מהלב']:
    idx = src.find(needle)
    print(f'"{needle}" at offset: {idx}')

# Anchor on first match
idx = src.find('עבודה מהלב')
if idx > 0:
    start = max(0, idx - 4000)
    end = min(len(src), idx + 4000)
    print('\n=== TICKER CONTEXT ===\n')
    print(src[start:end])
