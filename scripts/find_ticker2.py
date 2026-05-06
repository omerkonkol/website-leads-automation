"""Extract ticker HTML at the right offset."""
import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
src = pathlib.Path('e:/system/tmp_or_gabai/_ref_newidan.html').read_text(encoding='utf-8', errors='ignore')

idx = src.find('גימור פרימיום')
start = max(0, idx - 2000)
end = min(len(src), idx + 4000)
print(src[start:end])
