"""
KenKen Puzzle App – built with Kivy
Run:  python kenken.py
"""

import random
import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Rectangle
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp


# ──────────────────────────────────────────────────────────────────────────────
#  Puzzle Generator
# ──────────────────────────────────────────────────────────────────────────────

class KenKenPuzzle:
    """Generate and store a random KenKen puzzle."""

    def __init__(self, size=4):
        self.size = size
        self.solution = self._latin_square()
        self.cages = self._make_cages()
        self.cage_of = {}
        for cage in self.cages:
            for cell in cage["cells"]:
                self.cage_of[cell] = cage

    def _latin_square(self):
        n = self.size
        base = list(range(1, n + 1))
        g = [base[i:] + base[:i] for i in range(n)]
        random.shuffle(g)
        cols = list(zip(*g))
        random.shuffle(cols)
        return [list(r) for r in zip(*cols)]

    def _make_cages(self):
        n = self.size
        used = [[False] * n for _ in range(n)]
        cages = []
        for r in range(n):
            for c in range(n):
                if used[r][c]:
                    continue
                cells = [(r, c)]
                used[r][c] = True
                want = random.choices([1, 2, 2, 2, 3, 3, 4], k=1)[0]
                while len(cells) < want:
                    nbs = []
                    for cr, cc in cells:
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < n and 0 <= nc < n and not used[nr][nc]:
                                nbs.append((nr, nc))
                    if not nbs:
                        break
                    pick = random.choice(nbs)
                    cells.append(pick)
                    used[pick[0]][pick[1]] = True
                vals = [self.solution[r][c] for r, c in cells]
                if len(cells) == 1:
                    cages.append({"cells": cells, "target": vals[0],
                                  "op": None, "label": str(vals[0])})
                else:
                    op, tgt = self._pick_op(vals)
                    cages.append({"cells": cells, "target": tgt,
                                  "op": op, "label": f"{tgt}{op}"})
        return cages

    def _pick_op(self, vals):
        if len(vals) == 2:
            a, b = sorted(vals)
            pool = [("+", a + b), ("\u00d7", a * b)]
            if a != b:
                pool.append(("-", b - a))
            if a > 0 and b % a == 0:
                pool.append(("\u00f7", b // a))
            return random.choice(pool)
        pool = [("+", sum(vals))]
        p = 1
        for v in vals:
            p *= v
        pool.append(("\u00d7", p))
        return random.choice(pool)

    def conflict(self, g, r, c):
        v = g[r][c]
        if v == 0:
            return False
        n = self.size
        return (any(g[r][cc] == v for cc in range(n) if cc != c) or
                any(g[rr][c] == v for rr in range(n) if rr != r))

    def solved(self, g):
        return all(g[r][c] == self.solution[r][c]
                   for r in range(self.size) for c in range(self.size))

    def full(self, g):
        return all(g[r][c] != 0
                   for r in range(self.size) for c in range(self.size))


# ──────────────────────────────────────────────────────────────────────────────
#  Grid Widget  –  draws the puzzle and handles touch selection
# ──────────────────────────────────────────────────────────────────────────────

class KenKenGrid(Widget):
    # Colour palette
    C_BG       = (0.93, 0.93, 0.93, 1)
    C_CELL     = (1.00, 1.00, 1.00, 1)
    C_SEL      = (0.55, 0.78, 1.00, 1)
    C_CONFLICT = (1.00, 0.73, 0.73, 0.55)
    C_THIN     = (0.78, 0.78, 0.78, 1)
    C_THICK    = (0.08, 0.08, 0.08, 1)
    C_LABEL    = (0.18, 0.18, 0.18, 1)
    C_VALUE    = (0.05, 0.05, 0.05, 1)
    C_ERR      = (0.82, 0.05, 0.05, 1)
    C_PENCIL   = (0.48, 0.48, 0.48, 1)
    C_SAME_NUM = (0.78, 0.88, 1.00, 0.45)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.puzzle = None
        self.vals = []
        self.marks = []
        self.sel = [None, None]
        self.pencil = False
        self.bind(pos=self._redraw, size=self._redraw)

    def load(self, puzzle):
        self.puzzle = puzzle
        n = puzzle.size
        self.vals = [[0] * n for _ in range(n)]
        self.marks = [[set() for _ in range(n)] for _ in range(n)]
        self.sel = [None, None]
        self._redraw()

    # ── geometry ────────────────────────────────────────────────────────
    def _origin(self):
        gs = min(self.width, self.height) - dp(6)
        return (self.x + (self.width - gs) / 2,
                self.y + (self.height - gs) / 2, gs)

    def _cell(self, r, c):
        n = self.puzzle.size
        ox, oy, gs = self._origin()
        cs = gs / n
        return ox + c * cs, oy + (n - 1 - r) * cs, cs, cs

    # ── drawing ─────────────────────────────────────────────────────────
    def _redraw(self, *_):
        if not self.puzzle:
            return
        self.canvas.clear()
        n = self.puzzle.size
        sel_r, sel_c = self.sel
        sel_val = self.vals[sel_r][sel_c] if sel_r is not None else 0

        with self.canvas:
            # overall background
            Color(*self.C_BG)
            Rectangle(pos=self.pos, size=self.size)

            # cell fills
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    if [r, c] == self.sel:
                        Color(*self.C_SEL)
                    elif sel_val and self.vals[r][c] == sel_val:
                        Color(*self.C_SAME_NUM)
                    else:
                        Color(*self.C_CELL)
                    Rectangle(pos=(x + 1, y + 1), size=(w - 2, h - 2))

            # conflict overlay
            for r in range(n):
                for c in range(n):
                    if self.vals[r][c] and self.puzzle.conflict(self.vals, r, c):
                        x, y, w, h = self._cell(r, c)
                        Color(*self.C_CONFLICT)
                        Rectangle(pos=(x + 1, y + 1), size=(w - 2, h - 2))

            # thin grid lines
            Color(*self.C_THIN)
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    Line(rectangle=(x, y, w, h), width=1)

            # thick cage borders
            Color(*self.C_THICK)
            T = 3.0
            for cage in self.puzzle.cages:
                cs = set(tuple(c) for c in cage["cells"])
                for r, c in cs:
                    x, y, w, h = self._cell(r, c)
                    if r == 0 or (r - 1, c) not in cs:
                        Line(points=[x, y + h, x + w, y + h], width=T)
                    if r == n - 1 or (r + 1, c) not in cs:
                        Line(points=[x, y, x + w, y], width=T)
                    if c == 0 or (r, c - 1) not in cs:
                        Line(points=[x, y, x, y + h], width=T)
                    if c == n - 1 or (r, c + 1) not in cs:
                        Line(points=[x + w, y, x + w, y + h], width=T)

            # cage labels (top‑left of topmost‑leftmost cell)
            for cage in self.puzzle.cages:
                cells = cage["cells"]
                top = min(r for r, _ in cells)
                left = min(c for r, c in cells if r == top)
                x, y, w, h = self._cell(top, left)
                fs = min(w, h) * 0.22
                lb = CoreLabel(text=cage["label"], font_size=fs,
                               color=self.C_LABEL[:3] + (1,))
                lb.refresh()
                if lb.texture:
                    Color(*self.C_LABEL)
                    Rectangle(texture=lb.texture,
                              pos=(x + 4, y + h - lb.texture.size[1] - 2),
                              size=lb.texture.size)

            # user values & pencil marks
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    v = self.vals[r][c]
                    if v:
                        clr = self.C_ERR if self.puzzle.conflict(self.vals, r, c) \
                            else self.C_VALUE
                        fs = min(w, h) * 0.50
                        lb = CoreLabel(text=str(v), font_size=fs,
                                       color=clr[:3] + (1,))
                        lb.refresh()
                        if lb.texture:
                            tw, th = lb.texture.size
                            Color(*clr)
                            Rectangle(texture=lb.texture,
                                      pos=(x + (w - tw) / 2, y + (h - th) / 2),
                                      size=(tw, th))
                    elif self.marks[r][c]:
                        mf = min(w, h) * 0.18
                        ncols = 3 if n <= 6 else 4
                        nrows = math.ceil(n / ncols)
                        for num in sorted(self.marks[r][c]):
                            idx = num - 1
                            pr, pc = divmod(idx, ncols)
                            mx = x + (pc + 0.5) * w / ncols
                            my = y + h - (pr + 0.5) * h / nrows
                            ml = CoreLabel(text=str(num), font_size=mf,
                                           color=self.C_PENCIL[:3] + (1,))
                            ml.refresh()
                            if ml.texture:
                                tw, th = ml.texture.size
                                Color(*self.C_PENCIL)
                                Rectangle(texture=ml.texture,
                                          pos=(mx - tw / 2, my - th / 2),
                                          size=(tw, th))

    # ── interaction ─────────────────────────────────────────────────────
    def on_touch_down(self, touch):
        if not self.puzzle or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        n = self.puzzle.size
        for r in range(n):
            for c in range(n):
                x, y, w, h = self._cell(r, c)
                if x <= touch.pos[0] <= x + w and y <= touch.pos[1] <= y + h:
                    self.sel = [r, c]
                    self._redraw()
                    return True
        return super().on_touch_down(touch)

    def enter(self, val):
        if not self.puzzle or self.sel[0] is None:
            return
        r, c = self.sel
        if self.pencil:
            if self.vals[r][c]:
                return
            self.marks[r][c] ^= {val}
        else:
            if self.vals[r][c] == val:
                self.vals[r][c] = 0
            else:
                self.vals[r][c] = val
                self.marks[r][c] = set()
        self._redraw()

    def erase(self):
        if not self.puzzle or self.sel[0] is None:
            return
        r, c = self.sel
        self.vals[r][c] = 0
        self.marks[r][c] = set()
        self._redraw()

    def hint(self):
        if not self.puzzle or self.sel[0] is None:
            return False
        r, c = self.sel
        self.vals[r][c] = self.puzzle.solution[r][c]
        self.marks[r][c] = set()
        self._redraw()
        return True

    def reveal(self):
        if not self.puzzle:
            return
        n = self.puzzle.size
        for r in range(n):
            for c in range(n):
                self.vals[r][c] = self.puzzle.solution[r][c]
                self.marks[r][c] = set()
        self._redraw()

    def check(self):
        if not self.puzzle:
            return None
        if not self.puzzle.full(self.vals):
            return "incomplete"
        return "correct" if self.puzzle.solved(self.vals) else "incorrect"


# ──────────────────────────────────────────────────────────────────────────────
#  Timer Label
# ──────────────────────────────────────────────────────────────────────────────

class TimerLabel(Label):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.secs = 0
        self._ev = None
        self.text = "00:00"
        self.halign = "center"

    def start(self):
        self.stop()
        self.secs = 0
        self.text = "00:00"
        self._ev = Clock.schedule_interval(self._tick, 1)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, _dt):
        self.secs += 1
        self.text = f"{self.secs // 60:02d}:{self.secs % 60:02d}"


# ──────────────────────────────────────────────────────────────────────────────
#  Root Widget – assembles all UI pieces
# ──────────────────────────────────────────────────────────────────────────────

class KenKenRoot(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)
        self.grid_size = 4
        self._build_ui()
        self.new_game()

    # ── UI construction ─────────────────────────────────────────────────
    def _build_ui(self):
        # title row
        hdr = BoxLayout(size_hint_y=0.06, padding=dp(4))
        hdr.add_widget(Label(text="KenKen", font_size="26sp",
                             color=(0.15, 0.15, 0.15, 1)))
        self.timer = TimerLabel(font_size="18sp",
                                color=(0.4, 0.4, 0.4, 1),
                                size_hint_x=0.35)
        hdr.add_widget(self.timer)
        self.add_widget(hdr)

        # grid
        self.grid_widget = KenKenGrid(size_hint_y=0.58)
        self.add_widget(self.grid_widget)

        # number pad
        self.num_layout = GridLayout(cols=self.grid_size,
                                     size_hint_y=0.14,
                                     spacing=dp(4), padding=dp(6))
        self.add_widget(self.num_layout)
        self._build_numpad()

        # control buttons  (2 rows)
        ctrl_area = BoxLayout(orientation="vertical",
                              size_hint_y=0.18,
                              spacing=dp(2), padding=dp(4))

        row1 = BoxLayout(spacing=dp(4))
        self.pencil_btn = ToggleButton(
            text="Pencil", font_size="14sp",
            background_color=(0.45, 0.45, 0.50, 1), color=(1, 1, 1, 1))
        self.pencil_btn.bind(state=self._toggle_pencil)
        row1.add_widget(self.pencil_btn)

        for txt, cb, clr in [
            ("Erase", lambda _: self.grid_widget.erase(),
             (0.72, 0.30, 0.30, 1)),
            ("Hint", lambda _: self._hint(),
             (0.20, 0.60, 0.40, 1)),
            ("Check", lambda _: self._check(),
             (0.20, 0.50, 0.82, 1)),
        ]:
            b = Button(text=txt, font_size="14sp",
                       background_color=clr, color=(1, 1, 1, 1))
            b.bind(on_release=cb)
            row1.add_widget(b)
        ctrl_area.add_widget(row1)

        row2 = BoxLayout(spacing=dp(4))
        for txt, cb, clr in [
            ("New Game", lambda _: self._new_dialog(),
             (0.25, 0.55, 0.85, 1)),
            ("Reveal", lambda _: self._reveal(),
             (0.65, 0.45, 0.20, 1)),
            ("Undo", lambda _: self._undo(),
             (0.50, 0.50, 0.55, 1)),
        ]:
            b = Button(text=txt, font_size="14sp",
                       background_color=clr, color=(1, 1, 1, 1))
            b.bind(on_release=cb)
            row2.add_widget(b)
        ctrl_area.add_widget(row2)

        self.add_widget(ctrl_area)

        # undo stack
        self._undo_stack = []

    def _build_numpad(self):
        self.num_layout.clear_widgets()
        self.num_layout.cols = self.grid_size
        for i in range(1, self.grid_size + 1):
            b = Button(text=str(i), font_size="22sp",
                       background_color=(0.25, 0.55, 0.85, 1),
                       color=(1, 1, 1, 1))
            b.bind(on_release=lambda _, v=i: self._enter(v))
            self.num_layout.add_widget(b)

    # ── actions ─────────────────────────────────────────────────────────
    def _push_undo(self):
        import copy
        self._undo_stack.append((
            copy.deepcopy(self.grid_widget.vals),
            copy.deepcopy(self.grid_widget.marks),
            list(self.grid_widget.sel)
        ))
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)

    def _undo(self):
        if not self._undo_stack:
            return
        vals, marks, sel = self._undo_stack.pop()
        self.grid_widget.vals = vals
        self.grid_widget.marks = marks
        self.grid_widget.sel = sel
        self.grid_widget._redraw()

    def _enter(self, val):
        self._push_undo()
        self.grid_widget.enter(val)

    def _toggle_pencil(self, _inst, state):
        self.grid_widget.pencil = state == "down"

    def _hint(self):
        self._push_undo()
        if not self.grid_widget.hint():
            self._show_msg("Hint", "Select a cell first, then tap Hint.")

    def _reveal(self):
        content = BoxLayout(orientation="vertical", padding=dp(12),
                            spacing=dp(8))
        content.add_widget(Label(text="Reveal the entire solution?",
                                 font_size="16sp"))
        btns = BoxLayout(spacing=dp(8), size_hint_y=0.4)
        popup = Popup(title="Reveal", content=content,
                      size_hint=(0.6, 0.32))
        yes = Button(text="Yes", background_color=(0.8, 0.3, 0.3, 1))
        no = Button(text="Cancel")
        yes.bind(on_release=lambda _: (
            self._push_undo(),
            self.grid_widget.reveal(),
            self.timer.stop(),
            popup.dismiss()))
        no.bind(on_release=popup.dismiss)
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup.open()

    def _check(self):
        result = self.grid_widget.check()
        if result == "correct":
            self.timer.stop()
            self._show_msg("Congratulations!",
                           "Puzzle solved correctly!\n"
                           f"Time: {self.timer.text}")
        elif result == "incorrect":
            self._show_msg("Not quite",
                           "Some numbers are wrong.\nKeep trying!")
        else:
            self._show_msg("Incomplete",
                           "Fill in every cell before checking.")

    def _show_msg(self, title, msg):
        popup = Popup(title=title,
                      content=Label(text=msg, font_size="16sp"),
                      size_hint=(0.65, 0.32))
        popup.open()
        Clock.schedule_once(lambda _: popup.dismiss(), 2.5)

    # ── new game dialog ─────────────────────────────────────────────────
    def _new_dialog(self):
        content = BoxLayout(orientation="vertical", padding=dp(12),
                            spacing=dp(8))
        content.add_widget(Label(text="Choose grid size:",
                                 font_size="16sp", size_hint_y=0.25))
        btns = GridLayout(cols=3, size_hint_y=0.45, spacing=dp(6))
        popup = Popup(title="New Game", content=content,
                      size_hint=(0.6, 0.38))
        for sz in (4, 5, 6):
            b = Button(text=f"{sz} \u00d7 {sz}", font_size="20sp",
                       background_color=(0.25, 0.55, 0.85, 1),
                       color=(1, 1, 1, 1))
            b.bind(on_release=lambda _, s=sz: (
                self._set_size(s), popup.dismiss()))
            btns.add_widget(b)
        content.add_widget(btns)
        cancel = Button(text="Cancel", size_hint_y=0.2,
                        background_color=(0.55, 0.55, 0.55, 1),
                        color=(1, 1, 1, 1))
        cancel.bind(on_release=popup.dismiss)
        content.add_widget(cancel)
        popup.open()

    def _set_size(self, sz):
        self.grid_size = sz
        self._build_numpad()
        self.new_game()

    def new_game(self):
        self._undo_stack = []
        puzzle = KenKenPuzzle(self.grid_size)
        self.grid_widget.load(puzzle)
        self.timer.start()
        self.pencil_btn.state = "normal"
        self.grid_widget.pencil = False


# ──────────────────────────────────────────────────────────────────────────────
#  Application
# ──────────────────────────────────────────────────────────────────────────────

class KenKenApp(App):
    def build(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        self.root = KenKenRoot()
        Window.bind(on_keyboard=self._on_key)
        return self.root

    def _on_key(self, _win, key, _sc, codepoint, _mod):
        gw = self.root.grid_widget
        # number entry
        if codepoint and codepoint.isdigit():
            v = int(codepoint)
            if 1 <= v <= gw.puzzle.size:
                self.root._enter(v)
                return True
        # backspace / delete
        if key in (8, 46, 127):
            gw.erase()
            return True
        # escape – deselect
        if key == 27:
            gw.sel = [None, None]
            gw._redraw()
            return True
        # arrow keys
        moves = {273: (-1, 0), 274: (1, 0), 275: (0, 1), 276: (0, -1)}
        if key in moves:
            dr, dc = moves[key]
            if gw.puzzle and gw.sel[0] is not None:
                n = gw.puzzle.size
                gw.sel = [max(0, min(n - 1, gw.sel[0] + dr)),
                          max(0, min(n - 1, gw.sel[1] + dc))]
                gw._redraw()
            return True
        return False


if __name__ == "__main__":
    KenKenApp().run()