"""Tiny integration checks of the extractor's actual function definitions.

Usage: python test_average_duration.py --extractor path/to/extract_hist_features.py
Requires pandas. All I/O uses temporary fixtures; upstream imports are avoided
because const.py creates directories as an import side effect.
"""
import argparse
import ast
import contextlib
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import pandas as pd

EXTRACTOR = Path(__file__).resolve().parents[1] / 'artifact' / 'evaluation' / 'extract_hist_features.py'


def extract(sequence):
    tree = ast.parse(EXTRACTOR.read_text(encoding='utf-8'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('update_history', 'build_historical_data')]
    assert len(functions) == 2
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        metadata = []
        for build, stage, test, duration in sequence:
            metadata.append(dict(project='p', pr_name='PR', build_id=build,
                                 stage_id=stage, build_timestamp=build))
        pd.DataFrame(metadata).drop_duplicates().to_csv(root / 'dataset.csv', index=False)
        for build, stage in sorted({(x[0], x[1]) for x in sequence}):
            dest = root / 'processed' / 'p' / f'PR_build{build}' / f'stage_{stage}'
            dest.mkdir(parents=True)
            rows = [dict(testclass=t, duration=d, outcome=0) for b, s, t, d in sequence
                    if b == build and s == stage]
            pd.DataFrame(rows).to_csv(dest / 'test_class.csv', index=False)
        namespace = dict(pd=pd, os=os,
            const=SimpleNamespace(DATASET_FILE=str(root / 'dataset.csv')),
            eval_const=SimpleNamespace(feadir=str(root / 'features'), trdir=str(root / 'processed'),
                                       TEST_CLASS_CSV='test_class.csv', HIST_FILE='historical.csv', FAIL=1))
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(EXTRACTOR), 'exec'), namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            namespace['build_historical_data']('p')
        result = {}
        for build, stage in sorted({(x[0], x[1]) for x in sequence}):
            path = root / 'features' / 'p' / f'PR_build{build}' / f'stage_{stage}' / 'historical.csv'
            for row in pd.read_csv(path).to_dict('records'):
                result[build, stage, row['testclass']] = row
        return result


class ProposedFixTests(unittest.TestCase):
    def test_cold_start_is_zero(self):
        result = extract([(1, 'a', 'x', 4), (2, 'a', 'y', 90)])
        self.assertEqual(result[1, 'a', 'x']['average_duration'], 0)
        self.assertEqual(result[2, 'a', 'y']['average_duration'], 0)

    def test_state_updates_and_rounding(self):
        durations = [1.2344, 1.2347, 20.0]
        result = extract([(i+1, 'a', 'x', d) for i, d in enumerate(durations)])
        self.assertEqual([result[i, 'a', 'x']['average_duration'] for i in (1, 2, 3)],
                         [0, round(durations[0], 3), round(sum(durations[:2]) / 2, 3)])
        self.assertEqual(result[3, 'a', 'x']['last_duration'], durations[1])

    def test_current_duration_changes_future_not_current_feature(self):
        baseline = extract([(1, 'a', 'x', 2), (2, 'a', 'x', 4), (3, 'a', 'x', 6)])
        altered = extract([(1, 'a', 'x', 2), (2, 'a', 'x', 40), (3, 'a', 'x', 6)])
        self.assertEqual(baseline[2, 'a', 'x'], altered[2, 'a', 'x'])
        self.assertEqual(baseline[3, 'a', 'x']['average_duration'], 3)
        self.assertEqual(altered[3, 'a', 'x']['average_duration'], 21)

    def test_stage_histories_remain_separate(self):
        result = extract([(1, 'a', 'x', 2), (2, 'b', 'x', 50), (3, 'a', 'x', 8)])
        self.assertEqual(result[2, 'b', 'x']['average_duration'], 0)
        self.assertEqual(result[3, 'a', 'x']['average_duration'], 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--extractor', type=Path, default=EXTRACTOR)
    args, remainder = parser.parse_known_args()
    EXTRACTOR = args.extractor
    unittest.main(argv=['test_average_duration.py'] + remainder)
