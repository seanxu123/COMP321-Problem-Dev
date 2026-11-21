#!/usr/bin/env python3
"""Verify test-file naming, input validity, patrol closures, answers and sample data.

Usage: python3 test_case_generator/verify_suite.py
Every input must pass input_format_validators/validate.py (exit code 42).
"""
from pathlib import Path
from generator import solve, MOVES
from collections import deque
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent
VALIDATOR=ROOT/'input_format_validators'/'validate.py'

def check_input(path):
    with path.open('rb') as f:
        assert subprocess.run([sys.executable,VALIDATOR],stdin=f).returncode==42, path

def parse(text):
    lines = text.splitlines()
    R, C, T, G = map(int, lines[0].split())
    grid = lines[1:1+R]
    guards = []
    for line in lines[1+R:]:
        r, c, path = line.split()
        guards.append((int(r)-1, int(c)-1, path))
    return R, C, T, grid, guards

def independent_solve(text):
    """Slow direct-ray implementation for small cases; structurally different from oracle."""
    R,C,T,grid,guards=parse(text)
    if R*C*T>2000:return None
    sightings=[]
    for t in range(T):
        seen=set()
        for r,c,s in guards:
            for ch in s[:t]:
                dr,dc=MOVES[ch];r+=dr;c+=dc
            seen.add((r,c))
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr,cc=r+dr,c+dc
                while 0<=rr<R and 0<=cc<C and grid[rr][cc]!='#':
                    seen.add((rr,cc));rr+=dr;cc+=dc
        sightings.append(seen)
    s=next((r,c) for r in range(R) for c in range(C) if grid[r][c]=='S')
    if s in sightings[0]:return 'CAUGHT'
    q=deque([(s[0],s[1],0)]);visited={(s[0],s[1],0)}
    while q:
        r,c,d=q.popleft()
        if grid[r][c]=='B':return str(d)
        phase=(d+1)%T
        for dr,dc in ((0,0),(1,0),(-1,0),(0,1),(0,-1)):
            rr,cc=r+dr,c+dc
            state=(rr,cc,phase)
            if 0<=rr<R and 0<=cc<C and grid[rr][cc]!='#' and (rr,cc) not in sightings[phase] and state not in visited:
                visited.add(state);q.append((rr,cc,d+1))
    return 'CAUGHT'

def main():
    total=0;cross=0;maxbytes=0
    for folder in ['sample','secret']:
        directory=ROOT/'data'/folder
        ins=sorted(directory.glob('*.in'))
        ans=sorted(directory.glob('*.ans'))
        assert [p.stem for p in ins]==[p.stem for p in ans]
        assert len(ins)>=(3 if folder=='sample' else 20)
        for inputfile in ins:
            text=inputfile.read_text('ascii');check_input(inputfile)
            answer=(directory/(inputfile.stem+'.ans')).read_text('ascii').strip()
            assert answer==solve(text), inputfile
            independent=independent_solve(text)
            if independent is not None:
                assert answer==independent,(inputfile,answer,independent)
                cross+=1
            maxbytes+=inputfile.stat().st_size
            total+=1
    assert maxbytes<50_000_000
    assert (ROOT/'data/sample/sample01.ans').read_text().strip()=='7'
    assert (ROOT/'data/sample/sample02.ans').read_text().strip()=='CAUGHT'
    print(f'PASS: {total} input/answer pairs, {cross} independently cross-checked, {maxbytes} total input bytes')

if __name__=='__main__':main()
