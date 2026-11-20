"""
WRONG ANSWER: runs a plain BFS where each cell is visited only once
(state = (row, col)), instead of (row, col, t mod T).
"""

import sys
from collections import deque

def main():
    d = sys.stdin.read().split()
    R, C, T, G = map(int, d[:4])
    g = d[4:4 + R]
    p = 4 + R
    D = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1), 'S': (0, 0)}
    w = [[[False] * C for _ in range(R)] for _ in range(T)]
    
    for _ in range(G):
        r = int(d[p]) - 1; c = int(d[p + 1]) - 1; s = d[p + 2]; p += 3
        for t in range(T):
            w[t][r][c] = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dr, c + dc
                while 0 <= a < R and 0 <= b < C and g[a][b] != '#':
                    w[t][a][b] = True
                    a += dr; b += dc
            dr, dc = D[s[t]]
            r += dr; c += dc
            
    for i in range(R):
        for j in range(C):
            if g[i][j] == 'S': sr, sc = i, j
            if g[i][j] == 'B': br, bc = i, j
            
    if w[0][sr][sc]:
        print("CAUGHT"); return
        
    seen = [[False] * C for _ in range(R)]   # BUG: time phase not part of state
    seen[sr][sc] = True
    q = deque([(sr, sc, 0)])
    
    while q:
        r, c, k = q.popleft()
        if (r, c) == (br, bc):
            print(k); return
        nt = (k + 1) % T
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = r + dr, c + dc
            if 0 <= a < R and 0 <= b < C and g[a][b] != '#' and not w[nt][a][b] and not seen[a][b]:
                seen[a][b] = True
                q.append((a, b, k + 1))
                
    print("CAUGHT")

main()