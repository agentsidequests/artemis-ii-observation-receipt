"""Inventory and package public release source. Never reads Git credentials or history."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '.build', '.vercel', 'site', '__pycache__'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def files():
    result = []
    for item in ROOT.rglob('*'):
        relative = item.relative_to(ROOT)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if relative.as_posix().startswith('observation-receipt/build/'):
            continue
        if item.is_symlink():
            raise ValueError('Symlink is not a release source file: ' + str(relative))
        if item.is_file():
            result.append(item)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix())


def inventory():
    provenance_path = ROOT / 'EXPORT-PROVENANCE.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    owned_changes = []
    for row in provenance['files']:
        data = (ROOT / row['path']).read_bytes()
        changed = digest(data) != row['exported_sha256'] or len(data) != row['exported_bytes']
        if row['native_source'] and changed:
            raise ValueError('Native source drift: ' + row['path'])
        if changed:
            owned_changes.append(row['path'])
            row['exported_sha256'] = digest(data)
            row['exported_bytes'] = len(data)
            row['disposition'] = 'OWNED_PUBLIC_PROJECTION'
    provenance['public_release'] = {'version': '1.0.0', 'date': '2026-10-14',
                                    'native_source_changed': False,
                                    'scope': 'Hosting projection, release instructions, privacy-check vocabulary and source inventory. No scientific recalculation.'}
    provenance_path.write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8', newline='\n')
    rows = []
    for item in files():
        name = item.relative_to(ROOT).as_posix()
        if name == 'PACKAGE-MANIFEST.json':
            continue
        data = item.read_bytes()
        rows.append({'path': name, 'bytes': len(data), 'sha256': digest(data)})
    manifest = {'schema_version': 1, 'date': '2026-10-14', 'version': '1.0.0',
                'status': 'PUBLIC_RESEARCH_PROTOTYPE_SOURCE', 'history_included': False,
                'files': rows}
    (ROOT / 'PACKAGE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'pass': True, 'files': len(rows) + 1, 'native_source_changed': False,
                      'owned_provenance_rows_updated': owned_changes}))


def package(destination):
    manifest = json.loads((ROOT / 'PACKAGE-MANIFEST.json').read_text(encoding='utf-8'))
    names = [row['path'] for row in manifest['files']] + ['PACKAGE-MANIFEST.json']
    for row in manifest['files']:
        data = (ROOT / row['path']).read_bytes()
        if digest(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('Source inventory mismatch: ' + row['path'])
    if set(names) != {p.relative_to(ROOT).as_posix() for p in files()}:
        raise ValueError('Uninventoried or missing source files')
    target = Path(destination).resolve()
    if ROOT == target or ROOT in target.parents or target.exists():
        raise ValueError('Use a new package filename outside the source checkout')
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name in sorted(names):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, (ROOT / name).read_bytes())
    print(json.dumps({'pass': True, 'files': len(names), 'bytes': target.stat().st_size,
                      'sha256': digest(target.read_bytes())}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory', 'zip'])
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.action == 'inventory':
        inventory()
    elif args.output:
        package(args.output)
    else:
        parser.error('zip requires --output')
