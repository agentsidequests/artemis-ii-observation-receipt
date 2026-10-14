"""A publication guard must not regenerate a rejected physical interpretation."""
import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WithdrawnVisualGuardTests(unittest.TestCase):
    def test_legacy_cli_stops_before_optional_imports_or_output_writes(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'src/render_flash_analysis_charts.py')],
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('withdrawn timeline and distance-advantage graphics', result.stderr)
        self.assertNotIn('ModuleNotFoundError', result.stderr)
        self.assertFalse((ROOT / 'Artemis-II-Flash-Chart-4-Distance-Advantage.png').exists())
        self.assertFalse((ROOT / 'Artemis-II-Flash-Chart-1-Timeline.png').exists())

    def test_imported_entrypoints_raise_before_drawing_or_loading(self):
        source = (ROOT / 'src/render_flash_analysis_charts.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        for name in ('main', 'render_flash_timeline', 'render_distance_advantage'):
            node = functions[name]
            self.assertIsInstance(node.body[0], ast.Raise, name)
            isolated = ast.Module(body=[node], type_ignores=[])
            namespace = {}
            exec(compile(isolated, '<withdrawn-entrypoint>', 'exec'), namespace)
            with self.assertRaisesRegex(RuntimeError, 'Withdrawn|disabled'):
                namespace[name](*([] if name == 'main' else [{}]))


if __name__ == '__main__':
    unittest.main()
