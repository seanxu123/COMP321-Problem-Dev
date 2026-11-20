#!/usr/bin/env python3
"""Reproducible test suite generator for COMP321 'The Bathroom Job'.

Usage: python3 test_case_generator/generator.py
       python3 test_case_generator/generator.py --seed 3212026

Writes data/sample/*.in, data/secret/*.in and matching *.ans, plus
human-readable data/Description.txt. Only replaces files it manages.
All patrols are legal closed walks of exactly T steps.
"""
import argparse
import random
from pathlib import Path
from collections import deque
import ast
import builtins
import contextlib
import io

MOVES = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1), 'S': (0, 0)}
BASE = Path(__file__).resolve().parent.parent
SOLUTION = BASE / 'submissions' / 'accepted' / 'solution.py'

# Load the teammate's accepted main() without running its standalone main() call.
_source = ast.parse(SOLUTION.read_text(encoding='utf-8'))
_source.body = [node for node in _source.body if not (
    isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    and isinstance(node.value.func, ast.Name) and node.value.func.id == 'main'
)]
_namespace = {}
exec(compile(_source, str(SOLUTION), 'exec'), _namespace)
_accepted_main = _namespace['main']

def solve(src):
    lines = iter(src.splitlines())
    out = io.StringIO()
    original_input = builtins.input
    try:
        builtins.input = lambda: next(lines)
        with contextlib.redirect_stdout(out):
            _accepted_main()
    finally:
        builtins.input = original_input
    return out.getvalue().strip()

OPPOSITE={'U':'D','D':'U','L':'R','R':'L','S':'S'}

def make(R,C,T,grid,guards=()):
    assert len(grid)==R and all(len(x)==C for x in grid)
    assert ''.join(grid).count('S')==1 and ''.join(grid).count('B')==1
    for r,c,s in guards:
        assert 1<=r<=R and 1<=c<=C and len(s)==T
        cr,cc=r-1,c-1
        assert grid[cr][cc]!='#'
        for ch in s:
            dr,dc=MOVES[ch]
            cr+=dr;cc+=dc
            assert 0<=cr<R and 0<=cc<C and grid[cr][cc]!='#', (r,c,s)
        assert (cr,cc)==(r-1,c-1)
    return f'{R} {C} {T} {len(guards)}\n'+'\n'.join(grid)+'\n'+''.join(f'{r} {c} {s}\n' for r,c,s in guards)

def random_patrol(r,c,grid,T,rng):
    R,C=len(grid),len(grid[0]); position=(r-1,c-1); forward=[]
    # A forward random walk and its reverse is always a legal closed patrol.
    # Random rests allow odd lengths, stationary guards and intermittent motion.
    for _ in range(T//2):
        opts=[d for d,(dr,dc) in MOVES.items() if 0<=position[0]+dr<R and 0<=position[1]+dc<C and grid[position[0]+dr][position[1]+dc]!='#']
        ch=rng.choice(opts)
        forward.append(ch)
        dr,dc=MOVES[ch];position=(position[0]+dr,position[1]+dc)
    return ''.join(forward)+('S' if T%2 else '')+''.join(OPPOSITE[ch] for ch in reversed(forward))

def random_case(R,C,T,G,wall_rate,rng,start_goal='random'):
    assert R*C>=2
    rows=[['#' if rng.random()<wall_rate else '.' for _ in range(C)] for _ in range(R)]
    # Choose S/B from distinct non-wall cells, force extra floor if required.
    floor=[(r,c) for r in range(R) for c in range(C) if rows[r][c]!='#']
    if len(floor)<2:
        rows[0][0]=rows[R-1][C-1]='.'
        floor=[(r,c) for r in range(R) for c in range(C) if rows[r][c]!='#']
    if start_goal=='far':
        a=(0,0);b=(R-1,C-1)
        rows[a[0]][a[1]]=rows[b[0]][b[1]]='.'
    else:
        a,b=rng.sample(floor,2)
    rows[a[0]][a[1]]='S';rows[b[0]][b[1]]='B'
    grid=[''.join(row) for row in rows]
    floor=[(r,c) for r in range(R) for c in range(C) if grid[r][c]!='#']
    guards=[]
    for _ in range(G):
        r,c=rng.choice(floor)
        guards.append((r+1,c+1,random_patrol(r+1,c+1,grid,T,rng)))
    return make(R,C,T,grid,guards)

def maze(R,C,T,rng):
    # Serpentine one-cell-wide corridor; forces a long BFS path.
    rows=[['#']*C for _ in range(R)]
    for r in range(0,R,2):
        for c in range(C):rows[r][c]='.'
        if r+1<R:rows[r+1][C-1 if (r//2)%2==0 else 0]='.'
    a=(0,0);last=(R-1,C-1) if R%2 else (R-2, C-1 if ((R-2)//2)%2==0 else 0)
    # Final row for odd R is a horizontal corridor; end depends on direction.
    if R%2: last=(R-1, C-1 if ((R-1)//2)%2==0 else 0)
    rows[a[0]][a[1]]='S';rows[last[0]][last[1]]='B'
    return make(R,C,T,[''.join(row) for row in rows])

def static_distance(src):
    """Shortest path ignoring guards; useful as a baseline for timing traps."""
    lines=src.splitlines()
    R,C,T,G=map(int,lines[0].split())
    grid=lines[1:R+1]
    start=next((r,c) for r in range(R) for c in range(C) if grid[r][c]=='S')
    q=deque([(start[0],start[1],0)])
    seen={start}
    while q:
        r,c,d=q.popleft()
        if grid[r][c]=='B':return d
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr,cc=r+dr,c+dc
            if 0<=rr<R and 0<=cc<C and grid[rr][cc]!='#' and (rr,cc) not in seen:
                seen.add((rr,cc))
                q.append((rr,cc,d+1))
    return None

def create_suite(seed):
    rng=random.Random(seed)
    suite=[]
    def add(group,name,src,reason):suite.append((group,name,src,reason))
    # Two exact samples from problem.en.tex; keep these stable.
    add('sample','sample01',make(5,7,4,['.......','.....#S','.......','##.....','....B.#'],[(5,4,'ULRD'),(2,5,'LRLR')]),'Official sample 1: moving guards, blocked sight lines and an optimal route of 7 steps.')
    add('sample','sample02',make(1,3,2,['S.B'],[(1,3,'LR')]),'Official sample 2: Michael is watched at time 0; expected CAUGHT.')
    add('sample','sample03',make(3,4,2,['S.#B','..#.','....']), 'Extra sample: no guards but a wall detour; basic shortest path.')
    # Fixed, independently understandable edge cases.
    add('secret','secret01',make(1,2,1,['SB']), 'Minimum valid grid; no guards; direct adjacent destination.')
    add('secret','secret02',make(2,1,100,['S','B']), 'Single-column grid with maximum cycle length, zero guards.')
    add('secret','secret03',make(1,2,1,['SB'],[(1,2,'S')]), 'Stationary guard watches the entire row at time zero.')
    add('secret','secret04',make(3,3,4,['S#B','###','...']), 'Disconnected components separated by walls; unreachable with G=0.')
    add('secret','secret05',make(3,5,2,['S#..B','.###.','.....']), 'Long wall detour on a small grid; no guards.')
    add('secret','secret06',make(3,3,3,['S#.','###','.#B']), 'Impossible: S and B are permanently separated.')
    add('secret','secret07',make(3,5,4,['S#...','.#.#.','...#B'],[(1,3,'SSSS')]), 'Line-of-sight blocked by walls and isolated paths.')
    add('secret','secret08',make(3,3,1,['S#B','.#.','...'],[(3,2,'S')]), 'T=1; stationary guard, watches row and column behind walls.')
    add('secret','secret09',make(2,5,2,['S...B','#####'],[(1,3,'LR')]), 'No safe way past a guard sharing the sole corridor.')
    add('secret','secret10',make(5,5,4,['S#...','.#.#.','...#.','###..','....B'],[(1,3,'SSSS')]), 'Guard vision on disconnected branch; walls block sight.')
    # Random and stress coverage, deterministic from seed.
    specs=[
       ('secret11',2,2,2,0,0.0,'random','Tiny open grid, no guards.'),
       ('secret12',4,7,5,2,0.18,'random','Small moving-guard random case with odd patrol length.'),
       ('secret13',6,6,8,4,0.32,'random','Dense walls and guards, possible unreachable states.'),
       ('secret14',10,10,9,8,0.12,'far','Open-medium grid with multiple moving patrols.'),
       ('secret15',12,12,12,0,0.30,'far','Medium no-guard maze with many dead ends.'),
       ('secret16',25,25,7,12,0.05,'far','Moderately large, mostly open surveillance network.'),
       ('secret17',25,25,15,35,0.35,'random','Heavy walls with overlapping and isolated patrols.'),
       ('secret18',35,40,20,15,0.20,'far','Rectangular grid, long cyclic dynamics.'),
       ('secret19',60,60,30,0,0.15,'far','Large grid, no guards; basic pathfinding under constraints.'),
       ('secret20',60,60,30,30,0.22,'random','Large random walls and many patrols.'),
       ('secret21',100,100,100,0,0.0,'far','Maximal dimensions and T, no guards, long shortest path.'),
       ('secret22',100,100,100,100,0.02,'random','All parameters at maximum; dense moving-guard visibility.'),
       ('secret23',100,100,1,100,0.50,'random','Max dimensions/guards with stationary vision and many wall partitions.'),
       ('secret24',1,100,100,0,0.0,'far','Single long row and maximal T; no patrols.'),
       ('secret25',100,1,100,0,0.0,'far','Single long column and maximal T; no patrols.'),
       ('secret26',40,40,100,60,0.42,'far','Large patrol period and wall-heavy scenario.'),
       ('secret27',50,70,99,50,0.08,'random','Odd T near maximum; mixed moving and stationary guards.'),
       ('secret28',100,100,2,2,0.0,'far','Largest open grid, sparse guards, shortest path with periodic visibility.'),
    ]
    for name,R,C,T,G,w,sg,desc in specs:
        add('secret',name,random_case(R,C,T,G,w,rng,sg),desc)
    add('secret','secret29',maze(99,99,10,rng),'Long serpentine corridor forces thousands of steps; tests BFS queue behavior.')
    # Deliberately construct a timing trap: central guard patrol makes
    # detouring/waiting relevant, across a wall barrier.
    add('secret','secret30',make(4,6,4,['S#...B','.#.##.','......','######'],[(1,4,'LRLR')]),'Guard patrol behind a wall; timed visibility and alternative route checks.')
    # Search reproducibly for reachable cases where ignoring time gives a
    # strictly shorter (wrong) answer. This explicitly tests wait/detour logic.
    trap_rng=random.Random(21993)
    traps=0
    for attempt in range(30000):
        case=random_case(5,7,trap_rng.choice([2,3,4,5,6]),
                         trap_rng.choice([1,2,3]),trap_rng.uniform(.24,.48),
                         trap_rng,'far')
        dist=static_distance(case)
        if dist is None:continue
        ans=solve(case)
        if ans!='CAUGHT' and int(ans)>dist:
            traps+=1
            add('secret',f'secret{30+traps:02d}',case,
                f'Timing trap #{traps}: spatial shortest path {dist} steps, actual safe minimum {ans}.')
            if traps==6:break
    assert traps==6, 'Could not generate required timing traps'
    return suite

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=int,default=3212026)
    ap.add_argument('--data-dir',type=Path,default=BASE/'data')
    args=ap.parse_args()
    data=args.data_dir
    suite=create_suite(args.seed)
    descriptions=['Test case descriptions for The Bathroom Job','Generator: test_case_generator/generator.py',f'Random seed: {args.seed}', '']
    for group,name,src,reason in suite:
        dest=data/group
        dest.mkdir(parents=True,exist_ok=True)
        (dest/f'{name}.in').write_text(src,encoding='ascii')
        ans=solve(src)
        (dest/f'{name}.ans').write_text(ans+'\n',encoding='ascii')
        descriptions.append(f'{group}/{name}.in -> {group}/{name}.ans | {reason} | Answer: {ans}')
    (data/'Description.txt').write_text('\n'.join(descriptions)+'\n',encoding='utf-8')
    print(f'Created {len(suite)} input/answer pairs: '+', '.join(f'{x}: {sum(s[0]==x for s in suite)}' for x in ('sample','secret')))
    print('Files saved under:',data)

if __name__=='__main__':main()
