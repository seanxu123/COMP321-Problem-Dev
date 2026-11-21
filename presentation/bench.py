#!/usr/bin/env python3
"""Time every submission on every test file and write bench.csv for the slides.

Usage: python3 presentation/bench.py   (needs python3, javac and java on PATH)
Each time is the median of RUNS wall-clock runs, JVM/interpreter start-up included.
"""
import csv
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = 3


def run(cmd, path):
    times, out = [], None
    for _ in range(RUNS):
        with path.open('rb') as f:
            start = time.perf_counter()
            out = subprocess.run(cmd, stdin=f, capture_output=True, text=True, check=True).stdout.strip()
            times.append(time.perf_counter() - start)
    return statistics.median(times), out


def main():
    classes = tempfile.mkdtemp()
    subprocess.run(['javac', '-d', classes, str(ROOT / 'submissions/accepted/Main.java')], check=True)
    solutions = {
        'python': [sys.executable, str(ROOT / 'submissions/accepted/solution.py')],
        'java': ['java', '-cp', classes, 'Main'],
        'wrong': [sys.executable, str(ROOT / 'submissions/wrong_answer/wrong_answer.py')],
    }
    rows = []
    for i, path in enumerate(sorted(ROOT.glob('data/*/*.in')), 1):
        expected = path.with_suffix('.ans').read_text().strip()
        R, C, T, G = map(int, path.read_text().split()[:4])
        row = {'idx': i, 'file': path.stem, 'cells': R * C, 'T': T, 'G': G}
        for name, cmd in solutions.items():
            seconds, out = run(cmd, path)
            row[name] = f'{seconds:.3f}'
            row[name + '_ok'] = int(out == expected)
        assert row['python_ok'] and row['java_ok'], row
        rows.append(row)

    with (Path(__file__).parent / 'bench.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    for name in solutions:
        times = [float(r[name]) for r in rows]
        worst = max(rows, key=lambda r: float(r[name]))
        passed = sum(r[name + '_ok'] for r in rows)
        print(f'{name:6} total {sum(times):5.2f}s  worst {worst[name]}s ({worst["file"]})  correct {passed}/{len(rows)}')


if __name__ == '__main__':
    main()
