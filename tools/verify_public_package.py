"""Verify a complete shipped file inventory. Identity checks are not scientific acceptance."""
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def included(path):
    parts = path.relative_to(ROOT).parts
    return not ('.git' in parts or '__pycache__' in parts or '.build' in parts or 'site' in parts or '.vercel' in parts or
                path.relative_to(ROOT).as_posix().startswith('observation-receipt/build/'))


def validate_inventory(root, manifest):
    errors = []
    names = set()
    for row in manifest['files']:
        name = row['path']
        relative = Path(name)
        if (relative.is_absolute() or name.startswith('/') or re.match(r'^[A-Za-z]:', name)
                or '..' in relative.parts or '\\' in name or name in names):
            errors.append('Unsafe or duplicate package path: ' + name)
            continue
        names.add(name)
        path = root / relative
        if not path.is_file() or path.is_symlink() or root.resolve() not in path.resolve().parents:
            errors.append('Missing or nonregular file: ' + name)
            continue
        payload = path.read_bytes()
        if len(payload) != row['bytes'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
            errors.append('Package byte identity mismatch: ' + name)
    return errors, names


def reading_links(root):
    errors = []
    docs = ['README.md', 'EVIDENCE-MAP.md', 'REPRODUCIBILITY.md',
            'THIRD-PARTY-NOTICES.md', 'METHOD-HISTORY.md', 'TIMING-SOURCE-QUALIFICATION.md',
            'PUBLIC-ANALYSIS-DRAFT.md', 'ARTEMIS-II-TWO-GATE-SPECIALIST-REVIEW-PACKET.md',
            'ARTEMIS-II-EVIDENCE-ACCOUNTING-BRIEF.md',
            'paper-review/identity-census/CENSUS-REPORT.md',
            'paper-review/order-robust-reconstruction/CANDIDATE-REPORT.md',
            'paper-review/downstream-sensitivity/SENSITIVITY-REPORT.md',
            'paper-review/range-geometry/RANGE-RECONCILIATION.md']
    for name in docs:
        path = root / name
        if not path.exists():
            errors.append('Missing reading entry: ' + name)
            continue
        text = path.read_text(encoding='utf-8-sig')
        if chr(0x2014) in text:
            errors.append('Em dash in owned current reading copy: ' + name)
        for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            target = match.group(1).strip('<>').split('#', 1)[0]
            if not target or target.startswith(('https://', 'http://', 'data:', 'mailto:')):
                continue
            if target.startswith(('/', '\\')) or re.match(r'^[A-Za-z]:', target):
                errors.append('Nonportable reading link: ' + name)
                continue
            linked = (path.parent / unquote(target)).resolve()
            if root not in linked.parents or not linked.is_file():
                errors.append('Missing or out-of-package reading link: ' + name + ' -> ' + target)
    return errors


def main():
    manifest = json.loads((ROOT / 'PACKAGE-MANIFEST.json').read_text(encoding='utf-8'))
    errors, names = validate_inventory(ROOT, manifest)
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and included(p)}
    extras = actual - names - {'PACKAGE-MANIFEST.json'}
    if extras:
        errors.append('Unmanifested shipped files: ' + ', '.join(sorted(extras)))
    errors.extend(reading_links(ROOT))
    for name in names:
        path = ROOT / name
        if path.suffix == '.py':
            try:
                ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
            except (SyntaxError, UnicodeError) as error:
                errors.append('Python syntax failure: ' + name + ': ' + str(error))
    provenance = json.loads((ROOT / 'EXPORT-PROVENANCE.json').read_text(encoding='utf-8'))
    for row in provenance['files']:
        path = ROOT / row['path']
        data = path.read_bytes()
        if len(data) != row['exported_bytes'] or hashlib.sha256(data).hexdigest() != row['exported_sha256']:
            errors.append('Export provenance mismatch: ' + row['path'])
        if row['native_source'] and row['disposition'] != 'UNCHANGED':
            errors.append('Native evidence was transformed: ' + row['path'])
    print(json.dumps({'pass': not errors, 'manifested_files': len(names),
                      'source_provenance_files': len(provenance['files']),
                      'errors': errors, 'claim': 'Package identity, selected reading links and Python syntax only; not scientific or human acceptance.'}, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
