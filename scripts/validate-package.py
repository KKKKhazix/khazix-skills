"""Validate shipped resources, frontmatter, marketplace paths and AIHOT hashes."""
import hashlib
import json
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
skills = list(ROOT.glob('*/SKILL.md'))
for entry in skills:
    content = entry.read_text(encoding='utf-8')
    meta = yaml.safe_load(content.split('---', 2)[1])
    # Agent Skills specification: https://agentskills.io/specification
    assert meta['name'] == entry.parent.name, entry
    assert re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', meta['name']) and len(meta['name']) <= 64, entry
    assert 0 < len(meta['description']) <= 1024, entry
    assert len(meta.get('compatibility', '')) <= 500, entry
    assert all(isinstance(v, str) for v in (meta.get('metadata') or {}).values()), entry
    for link in re.findall(r'\]\(((?:references|scripts|assets)/[^)#]+)', content):
        assert (entry.parent / link).is_file(), (entry, link)
for line in (ROOT / 'aihot/manifest.sha256').read_text(encoding='utf-8').splitlines():
    checksum, name = line.split()
    assert hashlib.sha256((ROOT / 'aihot' / name).read_bytes()).hexdigest() == checksum, name
plugin = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))['plugins'][0]
assert plugin['source'] == './'
assert {Path(p).name for p in plugin['skills']} == {p.parent.name for p in skills}
for path in ROOT.glob('*/references/*.json'):
    json.loads(path.read_text(encoding='utf-8'))
print(f'Package validated: {len(skills)} skills and their supporting resources')
