#!/usr/bin/env python3
"""Input validator for The Bathroom Job.

Checks every guarantee of the Input section, byte for byte:
single spaces, no leading zeros, no trailing whitespace, a final newline,
and no extra lines. Exits 42 on valid input; any failed assert exits 1.
"""
import re
import sys

NUM = r'(0|[1-9][0-9]*)'
MOVES = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1), 'S': (0, 0)}

data = sys.stdin.read()
assert data.endswith('\n')
lines = data[:-1].split('\n')

header = re.fullmatch(f'{NUM} {NUM} {NUM} {NUM}', lines[0])
assert header
R, C, T, G = map(int, header.groups())
assert 1 <= R <= 100 and 1 <= C <= 100 and R * C >= 2
assert 1 <= T <= 100 and 0 <= G <= 100
assert len(lines) == 1 + R + G

grid = lines[1:1 + R]
assert all(re.fullmatch(f'[.#SB]{{{C}}}', row) for row in grid)
cells = ''.join(grid)
assert cells.count('S') == 1 and cells.count('B') == 1

for line in lines[1 + R:]:
    guard = re.fullmatch(f'{NUM} {NUM} ([UDLRS]{{{T}}})', line)
    assert guard
    r, c = int(guard[1]), int(guard[2])
    assert 1 <= r <= R and 1 <= c <= C
    start = (r, c)
    assert grid[r - 1][c - 1] != '#'
    for move in guard[3]:
        dr, dc = MOVES[move]
        r, c = r + dr, c + dc
        assert 1 <= r <= R and 1 <= c <= C and grid[r - 1][c - 1] != '#'
    assert (r, c) == start

sys.exit(42)
