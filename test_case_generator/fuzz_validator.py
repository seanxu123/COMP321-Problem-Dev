"""Differential fuzz: validate.py vs an independent byte-level oracle.

Mutates the real test inputs and checks that validate.py and a second,
regex-free parser written from the statement agree on every mutant.

Usage: python3 test_case_generator/fuzz_validator.py [mutants=3000]
Exit 0 only if the controls pass and the two never disagree.
"""
import random
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
VALIDATOR = REPO / 'input_format_validators' / 'validate.py'
STEP = {ord('U'): (-1, 0), ord('D'): (1, 0), ord('L'): (0, -1), ord('R'): (0, 1), ord('S'): (0, 0)}


def num(tok, lo, hi):
    if not tok or any(b not in b'0123456789' for b in tok) or (len(tok) > 1 and tok[:1] == b'0'):
        raise ValueError(tok)
    v = int(tok)
    if not lo <= v <= hi:
        raise ValueError(v)
    return v


def oracle(data: bytes) -> bool:
    try:
        lines = data.split(b'\n')
        if lines.pop() != b'':
            return False                          # missing final newline
        head = lines[0].split(b' ')
        if len(head) != 4:
            return False
        R, C, T = num(head[0], 1, 100), num(head[1], 1, 100), num(head[2], 1, 100)
        G = num(head[3], 0, 100)
        if R * C < 2 or len(lines) != 1 + R + G:
            return False
        grid = lines[1:1 + R]
        for row in grid:
            if len(row) != C or any(b not in b'.#SB' for b in row):
                return False
        flat = b''.join(grid)
        if flat.count(b'S') != 1 or flat.count(b'B') != 1:
            return False
        for line in lines[1 + R:]:
            parts = line.split(b' ')
            if len(parts) != 3:
                return False
            r, c, s = num(parts[0], 1, R), num(parts[1], 1, C), parts[2]
            if len(s) != T or any(b not in STEP for b in s):
                return False
            pos = (r - 1, c - 1)
            cur = pos
            if grid[cur[0]][cur[1]] == ord('#'):
                return False
            for b in s:
                cur = (cur[0] + STEP[b][0], cur[1] + STEP[b][1])
                if not (0 <= cur[0] < R and 0 <= cur[1] < C) or grid[cur[0]][cur[1]] == ord('#'):
                    return False
            if cur != pos:
                return False
        return True
    except (ValueError, IndexError):
        return False


def validator(data: bytes) -> bool:
    rc = subprocess.run([sys.executable, str(VALIDATOR)], input=data,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    assert rc in (1, 42), f'unexpected exit code {rc}'
    return rc == 42


def mutate(data: bytes, rng: random.Random) -> bytes:
    b = bytearray(data)
    op = rng.randrange(6)
    i = rng.randrange(len(b))
    alphabet = b'0123456789 \n\r\t.#SBUDLRx-'
    if op == 0:
        del b[i]
    elif op == 1:
        b.insert(i, rng.choice(alphabet))
    elif op == 2:
        b[i] = rng.choice(alphabet)
    elif op == 3:                                 # replace with a same-class byte
        cls = next((k for k in (b'0123456789', b'.#SB', b'UDLRS') if b[i] in k), alphabet)
        b[i] = rng.choice(cls)
    else:                                         # duplicate or drop a whole line
        lines = bytes(b).split(b'\n')
        j = rng.randrange(len(lines) - 1)
        if op == 4:
            lines.insert(j, lines[j])
        else:
            del lines[j]
        return b'\n'.join(lines)
    return bytes(b)


def main():
    inputs = sorted((REPO / 'data').glob('*/*.in'))
    # Control 1: both accept every real file.
    for p in inputs:
        d = p.read_bytes()
        assert oracle(d) and validator(d), p
    # Control 2: both reject hand-made broken inputs, one rule each.
    ok = b'1 3 2 1\nS.B\n1 3 LR\n'
    assert oracle(ok) and validator(ok)
    bad = [b'1 3 2 1\nS.B\n1 3 LR', b'1 3 2 1 \nS.B\n1 3 LR\n', b'01 3 2 1\nS.B\n1 3 LR\n',
           b'1 3 2 1\r\nS.B\r\n1 3 LR\r\n', b'1 3 2 1\nSSB\n1 3 LR\n', b'1 3 2 1\nS.B\n1 3 LL\n',
           b'1 3 2 1\nS#B\n1 3 LR\n', b'1 1 1 0\nS\n', b'1 3 2 1\nS.B\n1 3 LR\n\n', b'']
    for d in bad:
        assert not oracle(d) and not validator(d), d
    # Differential run on small files (fast) plus a few large ones.
    rng = random.Random(321)
    small = [p.read_bytes() for p in inputs if p.stat().st_size < 4000]
    large = [p.read_bytes() for p in inputs if p.stat().st_size >= 4000]
    accepted = disagree = 0
    for k in range(N):
        src = rng.choice(large if k % 20 == 0 else small)
        m = mutate(src, rng)
        o, v = oracle(m), validator(m)
        accepted += v
        if o != v:
            disagree += 1
            print('DISAGREE oracle', o, 'validator', v, repr(m[:200]))
    print(f'controls ok; {N} mutants, {accepted} still valid, {N - accepted} rejected, {disagree} disagreements')
    sys.exit(1 if disagree else 0)


if __name__ == '__main__':
    main()
