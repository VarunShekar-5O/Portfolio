import sys
import pygame as pyg
from typing import List, Optional, Tuple
import random

# ---------------------------
# Ultimate Tic-Tac-Toe (Pygame)
# Two-player local by default; optional simple AI for 'O' (toggle with A)
# Controls:
#   - Left click to place a mark in a legal cell.
#   - R to restart.
#   - A to toggle simple AI for O (random legal move).
#   - ESC or window close to quit.
# ---------------------------

# region ----- Init/Config -----
WIDTH, HEIGHT = 720, 720
FPS = 60
BG = (245, 246, 248)
LINE_COLOR = (30, 30, 30)
SUBLINE_COLOR = (120, 120, 120)
ACTIVE_HL = (210, 235, 255)
FREE_HL = (230, 230, 230)
LASTMOVE_HL = (255, 238, 173)
X_COLOR = (220, 55, 55)
O_COLOR = (55, 110, 220)
WIN_OVERLAY = (0, 0, 0, 160)

CELL_PADDING = 10
THIN = 2
THICK = 6

# Fonts are initialized after pyg.init() so we set placeholders here
FONT_LARGE = None
FONT_MED = None
FONT_SMALL = None

# endregion

#region ----- Game Logic -----
LINES = [
    # rows
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    # cols
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    # diags
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


class SubBoard:
    '''
    Keeps a 3×3 of cells, tracks status (None, 'X', 'O', 'D'), and validates placements. 
    It updates winner/draw immediately after each move to avoid re-scanning on every frame.
    '''
    def __init__(self) -> None:
        # 3x3 cells: None | 'X' | 'O'
        self.cells: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        # status: None=in progress, 'X'/'O'=won, 'D'=draw
        self.status: Optional[str] = None
        self.last_move: Optional[Tuple[int, int]] = None  # (r,c) within subboard

    def place(self, r: int, c: int, player: str) -> bool:
        if self.status is not None:
            return False
        if self.cells[r][c] is not None:
            return False
        self.cells[r][c] = player
        self.last_move = (r, c)
        self._update_status()
        return True

    def _update_status(self) -> None:
        # check win
        for line in LINES:
            a = self.cells[line[0][0]][line[0][1]]
            b = self.cells[line[1][0]][line[1][1]]
            c = self.cells[line[2][0]][line[2][1]]
            if a and a == b == c:
                self.status = a
                return
        # check draw
        if all(self.cells[r][c] is not None for r in range(3) for c in range(3)):
            self.status = 'D'
        else:
            self.status = None

    def legal_cells(self) -> List[Tuple[int, int]]:
        if self.status is not None:
            return []
        return [(r, c) for r in range(3) for c in range(3) if self.cells[r][c] is None]


class UltimateGame:
    '''
    Holds the 3×3 grid of SubBoards, current turn, 
    the active_board the next player must use (or None for “free choice”), and meta_status.
    
    place_global(gR, gC) maps global coordinates (0–8, 0–8) to sub-board + cell, enforces legality, 
    flips turns, updates the meta state, and routes the next active board.
    
    meta_legal_boards() encapsulates the “forced board vs free choice” rule so rendering and input can query it cleanly.
    legal_global_moves() is handy for AI or hints.
    '''
    def __init__(self) -> None:
        self.meta: List[List[SubBoard]] = [[SubBoard() for _ in range(3)] for _ in range(3)]
        self.meta_status: Optional[str] = None  # None, 'X', 'O', 'D'
        self.turn: str = 'X'
        self.active_board: Optional[Tuple[int, int]] = None  # None means any unfinished board
        self.last_global_move: Optional[Tuple[int, int]] = None  # (R,C) global 0..8
        self.ai_o: bool = False  # simple random AI for O

    def restart(self) -> None:
        self.__init__()

    def meta_legal_boards(self) -> List[Tuple[int, int]]:
        if self.meta_status is not None:
            return []
        if self.active_board is None:
            return [(R, C) for R in range(3) for C in range(3) if self.meta[R][C].status is None]
        R, C = self.active_board
        if self.meta[R][C].status is None:
            return [self.active_board]
        else:
            # target board finished -> free choice among unfinished boards
            return [(r, c) for r in range(3) for c in range(3) if self.meta[r][c].status is None]

    def legal_global_moves(self) -> List[Tuple[int, int]]:
        moves = []
        for (R, C) in self.meta_legal_boards():
            sb = self.meta[R][C]
            for (r, c) in sb.legal_cells():
                moves.append((R * 3 + r, C * 3 + c))
        return moves

    def place_global(self, gR: int, gC: int) -> bool:
        if self.meta_status is not None:
            return False
        # map to subboard
        R, C = gR // 3, gC // 3
        r, c = gR % 3, gC % 3
        # check if board is legal
        legal_boards = self.meta_legal_boards()
        if (R, C) not in legal_boards:
            return False
        sb = self.meta[R][C]
        if not sb.place(r, c, self.turn):
            return False
        self.last_global_move = (gR, gC)
        # update meta status
        self._update_meta_status()
        # set next active board
        self.active_board = (r, c)
        # if target board is finished, free choice
        if self.meta[r][c].status is not None:
            self.active_board = None
        # swap turn
        self.turn = 'O' if self.turn == 'X' else 'X'
        return True

    def _update_meta_status(self) -> None:
        # derive meta board as 3x3 of statuses where only X/O count
        meta_marks: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        for R in range(3):
            for C in range(3):
                s = self.meta[R][C].status
                meta_marks[R][C] = s if s in ('X', 'O') else None
        # check win
        for line in LINES:
            a = meta_marks[line[0][0]][line[0][1]]
            b = meta_marks[line[1][0]][line[1][1]]
            c = meta_marks[line[2][0]][line[2][1]]
            if a and a == b == c:
                self.meta_status = a
                return
        # draw if all subboards ended and no winner
        if all(self.meta[R][C].status is not None for R in range(3) for C in range(3)):
            self.meta_status = 'D'
        else:
            self.meta_status = None

# endregion

#region ----- Rendering -----
'''
Thin lines for every cell; thick lines for the 3×3 meta grid.

Blue highlight for the allowed sub-board(s); soft gray for other open boards when play is “free”.

A subtle gold highlight on the last move to orient players.

When a sub-board is won, it gets a translucent overlay with a big X/O; draws show “Draw”.

A win/draw overlay at the end with “Press R to play again”.
'''
def draw_board(screen: pyg.Surface, game: UltimateGame) -> None:
    screen.fill(BG)
    W, H = screen.get_size()
    cell_w = W // 9
    cell_h = H // 9

    # highlight allowed boards
    allowed = set(game.meta_legal_boards())
    for R in range(3):
        for C in range(3):
            x = C * 3 * cell_w
            y = R * 3 * cell_h
            rect = pyg.Rect(x, y, 3 * cell_w, 3 * cell_h)
            if (R, C) in allowed and game.meta_status is None:
                pyg.draw.rect(screen, ACTIVE_HL, rect)
            elif game.active_board is None and game.meta[R][C].status is None and game.meta_status is None:
                pyg.draw.rect(screen, FREE_HL, rect)

    # subgrid thin lines
    for i in range(10):
        # vertical
        x = i * cell_w
        pyg.draw.line(screen, SUBLINE_COLOR, (x, 0), (x, H), THIN)
        # horizontal
        y = i * cell_h
        pyg.draw.line(screen, SUBLINE_COLOR, (0, y), (W, y), THIN)

    # meta thick lines
    for i in range(4):
        x = i * 3 * cell_w
        pyg.draw.line(screen, LINE_COLOR, (x, 0), (x, H), THICK)
        y = i * 3 * cell_h
        pyg.draw.line(screen, LINE_COLOR, (0, y), (W, y), THICK)

    # draw marks and last move highlight
    if game.last_global_move:
        gR, gC = game.last_global_move
        hl_rect = pyg.Rect(gC * cell_w, gR * cell_h, cell_w, cell_h)
        s = pyg.Surface((cell_w, cell_h), pyg.SRCALPHA)
        s.fill((*LASTMOVE_HL, 120))
        screen.blit(s, hl_rect)

    for R in range(3):
        for C in range(3):
            sb = game.meta[R][C]
            for r in range(3):
                for c in range(3):
                    val = sb.cells[r][c]
                    if val is None:
                        continue
                    gx = (C * 3 + c) * cell_w
                    gy = (R * 3 + r) * cell_h
                    draw_mark(screen, val, gx, gy, cell_w, cell_h)

    # subboard win overlays
    for R in range(3):
        for C in range(3):
            sb = game.meta[R][C]
            if sb.status in ('X', 'O'):
                x = C * 3 * cell_w
                y = R * 3 * cell_h
                overlay = pyg.Surface((3 * cell_w, 3 * cell_h), pyg.SRCALPHA)
                overlay.fill((255, 255, 255, 150))
                screen.blit(overlay, (x, y))
                text_surf = FONT_LARGE.render(sb.status, True, X_COLOR if sb.status == 'X' else O_COLOR)
                tw, th = text_surf.get_size()
                screen.blit(text_surf, (x + (3 * cell_w - tw) // 2, y + (3 * cell_h - th) // 2))
            elif sb.status == 'D':
                x = C * 3 * cell_w
                y = R * 3 * cell_h
                overlay = pyg.Surface((3 * cell_w, 3 * cell_h), pyg.SRCALPHA)
                overlay.fill((255, 255, 255, 140))
                screen.blit(overlay, (x, y))
                text_surf = FONT_MED.render('Draw', True, (60, 60, 60))
                tw, th = text_surf.get_size()
                screen.blit(text_surf, (x + (3 * cell_w - tw) // 2, y + (3 * cell_h - th) // 2))

    # turn + instructions footer
    info = f"Turn: {game.turn}    |    Click to play    |    R: restart    A: toggle AI ({'ON' if game.ai_o else 'OFF'})"
    text = FONT_SMALL.render(info, True, (40, 40, 40))
    screen.blit(text, (16, H - text.get_height() - 10))

    # meta winner overlay
    if game.meta_status is not None:
        s = pyg.Surface((W, H), pyg.SRCALPHA)
        s.fill(WIN_OVERLAY)
        screen.blit(s, (0, 0))
        if game.meta_status in ('X', 'O'):
            msg = f"{game.meta_status} wins!"
        else:
            msg = "It's a draw!"
        big = FONT_LARGE.render(msg, True, (255, 255, 255))
        small = FONT_MED.render("Press R to play again", True, (230, 230, 230))
        screen.blit(big, (W // 2 - big.get_width() // 2, H // 2 - big.get_height()))
        screen.blit(small, (W // 2 - small.get_width() // 2, H // 2 + 10))


def draw_mark(screen: pyg.Surface, val: str, x: int, y: int, w: int, h: int) -> None:
    cx, cy = x + w // 2, y + h // 2
    pad = min(w, h) // 2 - CELL_PADDING
    if val == 'X':
        color = X_COLOR
        pyg.draw.line(screen, color, (cx - pad, cy - pad), (cx + pad, cy + pad), 6)
        pyg.draw.line(screen, color, (cx - pad, cy + pad), (cx + pad, cy - pad), 6)
    else:
        color = O_COLOR
        pyg.draw.circle(screen, color, (cx, cy), pad, 6)
#endregion

#region ----- Input Mapping -----
def mouse_to_global(grid_pos: Tuple[int, int], size: Tuple[int, int]) -> Tuple[int, int]:
    mx, my = grid_pos
    W, H = size
    cell_w = W // 9
    cell_h = H // 9
    gC = mx // cell_w
    gR = my // cell_h
    gC = max(0, min(8, gC))
    gR = max(0, min(8, gR))
    return gR, gC
#endregion

#region ----- Simple AI (random legal for 'O') -----

def ai_move(game: UltimateGame) -> Optional[Tuple[int, int]]:
    legal = game.legal_global_moves()
    if not legal:
        return None
    return random.choice(legal)
#endregion

#region ----- Main Loop -----

def main() -> None:
    global FONT_LARGE, FONT_MED, FONT_SMALL
    pyg.init()
    pyg.display.set_caption('Ultimate Tic-Tac-Toe')
    screen = pyg.display.set_mode((WIDTH, HEIGHT), pyg.RESIZABLE)
    clock = pyg.time.Clock()

    # fonts
    FONT_LARGE = pyg.font.SysFont('arial', 96, bold=True)
    FONT_MED = pyg.font.SysFont('arial', 36, bold=True)
    FONT_SMALL = pyg.font.SysFont('arial', 20)

    game = UltimateGame()

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                running = False
            elif event.type == pyg.KEYDOWN:
                if event.key == pyg.K_ESCAPE:
                    running = False
                elif event.key == pyg.K_r:
                    game.restart()
                elif event.key == pyg.K_a:
                    game.ai_o = not game.ai_o
            elif event.type == pyg.MOUSEBUTTONDOWN and event.button == 1:
                if game.meta_status is None:
                    gR, gC = mouse_to_global(pyg.mouse.get_pos(), screen.get_size())
                    game.place_global(gR, gC)

        # AI turn
        if game.meta_status is None and game.ai_o and game.turn == 'O':
            move = ai_move(game)
            if move:
                game.place_global(*move)

        draw_board(screen, game)
        pyg.display.flip()

    pyg.quit()
#endregion

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        pyg.quit()
        raise