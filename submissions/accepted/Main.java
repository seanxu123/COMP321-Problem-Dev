import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.StringTokenizer;

/**
 * The Bathroom Job -- accepted solution (Java).
 *
 * Idea: the guards repeat their patrol every T steps, so the set of watched
 * cells at time t only depends on (t mod T). Michael's situation is therefore
 * fully described by (cell, t mod T), and a plain BFS over these R*C*T states
 * finds the answer. Every action (move or wait) costs one time unit, so BFS
 * level d is exactly time d and every state on level d has phase d mod T.
 *
 * Steps:
 * - Precompute which cells are watched at every phase. A guard watches the
 *       maximal horizontal and vertical wall-free run through its own cell.
 * - BFS over (phase, cell) states: a state is entered only if the new cell
 *       is not a wall and not watched at the new phase.
 *
 * Complexity: time O(R*C*T + G*T*(R+C)), memory O(R*C*T).
 */

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));

        // First line: R C T G, then R grid lines, then G guard lines.
        StringTokenizer first = new StringTokenizer(br.readLine());
        int R = Integer.parseInt(first.nextToken());
        int C = Integer.parseInt(first.nextToken());
        int T = Integer.parseInt(first.nextToken());
        int G = Integer.parseInt(first.nextToken());
        int N = R * C;

        boolean[] wall = new boolean[N];
        int start = -1, bath = -1;
        for (int i = 0; i < R; i++) {
            String row = br.readLine().trim();
            for (int j = 0; j < C; j++) {
                char ch = row.charAt(j);
                int cell = i * C + j;
                if (ch == '#') wall[cell] = true;
                else if (ch == 'S') start = cell;
                else if (ch == 'B') bath = cell;
            }
        }

        // Maximal wall-free run through each cell (column bounds / row bounds).
        int[] rowLo = new int[N], rowHi = new int[N], colLo = new int[N], colHi = new int[N];
        for (int i = 0; i < R; i++) {
            int j = 0;
            while (j < C) {
                if (wall[i * C + j]) { j++; continue; }
                int k = j;
                while (k + 1 < C && !wall[i * C + k + 1]) k++;
                for (int x = j; x <= k; x++) { rowLo[i * C + x] = j; rowHi[i * C + x] = k; }
                j = k + 1;
            }
        }
        for (int j = 0; j < C; j++) {
            int i = 0;
            while (i < R) {
                if (wall[i * C + j]) { i++; continue; }
                int k = i;
                while (k + 1 < R && !wall[(k + 1) * C + j]) k++;
                for (int x = i; x <= k; x++) { colLo[x * C + j] = i; colHi[x * C + j] = k; }
                i = k + 1;
            }
        }

        // watched[phase * N + cell] is true iff the cell is watched at that phase.
        boolean[] watched = new boolean[T * N];
        for (int g = 0; g < G; g++) {
            StringTokenizer line = new StringTokenizer(br.readLine());  // e.g. "5 4 ULRD"
            int r = Integer.parseInt(line.nextToken()) - 1;
            int c = Integer.parseInt(line.nextToken()) - 1;
            String s = line.nextToken();
            for (int t = 0; t < T; t++) {
                if (t > 0) {
                    switch (s.charAt(t - 1)) {
                        case 'U': r--; break;
                        case 'D': r++; break;
                        case 'L': c--; break;
                        case 'R': c++; break;
                        default: break;
                    }
                }
                int base = t * N;
                int cell = r * C + c;
                for (int j = rowLo[cell]; j <= rowHi[cell]; j++) watched[base + r * C + j] = true;
                for (int i = colLo[cell]; i <= colHi[cell]; i++) watched[base + i * C + c] = true;
            }
        }

        if (watched[start]) {            // phase 0, start cell
            System.out.println("CAUGHT");
            return;
        }

        // A watched (phase, cell) state can never be entered, exactly like an
        // already visited one, so the watched table doubles as the visited table.
        boolean[] visited = watched;
        visited[start] = true;
        int[] cur = new int[N];
        int[] nxt = new int[N];
        int curSize = 1;
        cur[0] = start;
        int level = 0;
        int[] dr = {0, -1, 1, 0, 0};
        int[] dc = {0, 0, 0, -1, 1};

        while (curSize > 0) {
            level++;
            int base = (level % T) * N;  // all states on this level share a phase
            int nxtSize = 0;
            for (int q = 0; q < curSize; q++) {
                int cell = cur[q];
                int r = cell / C, c = cell % C;
                for (int d = 0; d < 5; d++) {
                    int nr = r + dr[d], nc = c + dc[d];
                    if (nr < 0 || nr >= R || nc < 0 || nc >= C) continue;
                    int ncell = nr * C + nc;
                    if (wall[ncell] || visited[base + ncell]) continue;
                    if (ncell == bath) {
                        System.out.println(level);
                        return;
                    }
                    visited[base + ncell] = true;
                    nxt[nxtSize++] = ncell;
                }
            }
            int[] tmp = cur; cur = nxt; nxt = tmp;
            curSize = nxtSize;
        }
        System.out.println("CAUGHT");
    }
}