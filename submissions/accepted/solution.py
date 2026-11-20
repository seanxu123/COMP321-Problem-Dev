"""
The Bathroom Job -- accepted solution (Python 3).

Idea
----
The guards repeat their patrol every T steps, so the set of watched cells at
time t only depends on (t mod T).  Michael's situation is therefore fully
described by the pair (cell, t mod T), and we run a plain BFS over these
R * C * T states.  Every action (move or wait) costs one time unit, so the
BFS level d is exactly the time d, and every state on level d has phase
d mod T.  The first level at which the bathroom is reached is the answer.

Steps
-----
1. Precompute, for every phase, which cells are watched: simulate each guard
   for T steps and, at every step, mark its own cell and walk in the four
   directions until a wall (or the border) stops the line of sight.
2. BFS over (phase, cell) states.  A state is entered only if the new cell is
   not a wall and not watched at the new phase.

Complexity
----------
Time   : O(R*C*T + G*T*(R+C))
Memory : O(R*C*T)
"""

def main():
    # First line: R C T G, then R grid lines, then G guard lines.
    R, C, T, G = map(int, input().split())
    grid = [input().strip() for _ in range(R)]
    

    # Locate Dante's start and the bathroom.
    start_r = start_c = bath_r = bath_c = -1
    for i in range(R):
        for j in range(C):
            if grid[i][j] == 'S':
                start_r, start_c = i, j
            elif grid[i][j] == 'B':
                bath_r, bath_c = i, j

    # watched[t][r][c] is True iff cell (r, c) is watched at phase t.
    watched = [[[False] * C for _ in range(R)] for _ in range(T)]
    step = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1), 'S': (0, 0)}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for _ in range(G):
        row, col, patrol = input().split()   # e.g. "5 4 ULRD"
        r = int(row) - 1
        c = int(col) - 1
        for t in range(T):
            if t > 0:                      # apply the action of step t-1
                dr, dc = step[patrol[t - 1]]
                r += dr
                c += dc
            watched[t][r][c] = True        # the guard sees its own cell
            for dr, dc in directions:      # ...and the four lines of sight
                nr, nc = r + dr, c + dc
                while 0 <= nr < R and 0 <= nc < C and grid[nr][nc] != '#':
                    watched[t][nr][nc] = True
                    nr += dr
                    nc += dc

    # Dante is already detected at time 0.
    if watched[0][start_r][start_c]:
        print("CAUGHT")
        return

    # A watched (phase, cell) state can never be entered, exactly like an
    # already visited one, so visited starts as a copy of the watched table.
    visited = [[row[:] for row in layer] for layer in watched]
    visited[0][start_r][start_c] = True

    # Dante can wait or move in one of the four directions.
    actions = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))

    frontier = [(start_r, start_c)]        # cells reached at the current level
    level = 0
    while frontier:
        level += 1
        phase = level % T                  # all states on this level share it
        next_frontier = []
        for r, c in frontier:
            for dr, dc in actions:
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= R or nc < 0 or nc >= C:
                    continue
                if grid[nr][nc] == '#' or visited[phase][nr][nc]:
                    continue
                if nr == bath_r and nc == bath_c:
                    print(level)           # first arrival = minimum time
                    return
                visited[phase][nr][nc] = True
                next_frontier.append((nr, nc))
        frontier = next_frontier

    print("CAUGHT")


main()