"""Pin the existing accounting result into a separate portable app case."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'observation-receipt'
OWNER = APP / 'cases/artemis-ii-robustness'
PINS = {
    'contract': ('paper-review/tag-weight-robustness/contract.json', '8930e45b9e01be7c7887ae3fbb905be81dd3d0dbcb46cde9d9a7c66a8ac850bf'),
    'result': ('paper-review/tag-weight-robustness/result.json', 'afa22634e5bd5883d6bf5b22b76a708df3f7c976011786e94c045ef695a64c76'),
    'manifest': ('results/stage10o-product-relationship-manifest.csv', '8edd58437cc609229edb5abb41c4e00048bb420354f1ac17a269da92c17e4729'),
}


def prepare():
    files, sources = {}, {}
    for name, (parent, digest) in PINS.items():
        data = (ROOT / parent).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Qualified source changed: ' + parent)
        filename = name + ('.csv' if name == 'manifest' else '.json')
        files['sources/' + filename] = data
        sources[name] = {'path': 'cases/artemis-ii-robustness/sources/' + filename,
                         'bytes': len(data), 'sha256': digest}
    case = {'case_kind': 'tag_weight_robustness', 'case_version': '1.0.0',
            'case_id': 'artemis-ii-tag-weight-robustness', 'title': 'A majority is not a margin of safety.',
            'sources': sources, 'defaults': {'unit': 'all_representation_bytes',
                                            'population': 'frozen_nonblank_subset', 'budget': 0}}
    files['case.json'] = (json.dumps(case, indent=2) + '\n').encode('utf-8')
    return files


def run(mode):
    files = prepare()
    for name, data in files.items():
        path = OWNER / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError('Existing app source differs; no overwrite: ' + name)
        if mode == '--check' and not path.is_file():
            raise ValueError('Prepared app source absent: ' + name)
    if mode == '--write':
        for name, data in files.items():
            path = OWNER / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(data)
    return {'pass': True, 'files': len(files), 'new_analysis': False}


if __name__ == '__main__':
    if sys.argv[1:] not in [['--write'], ['--check']]:
        raise SystemExit('Use --write or --check')
    print(json.dumps(run(sys.argv[1])))
