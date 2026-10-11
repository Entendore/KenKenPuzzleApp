"""
KenKen Puzzle App  --  Professional Edition
Built with Kivy

Features:
  - Title Screen with animated logo, resume/continue support
  - How to Play / Tutorial screen with rules
  - Game Screen with professional UI
  - Backtracking puzzle solver (step-by-step)
  - Smart hints (naked singles, hidden singles logic)
  - Scoring system (time, difficulty, hints, errors)
  - Timer with pause/resume
  - Undo / Redo
  - Auto-pencil marks (cage-aware)
  - Dark mode with 4 color themes (Default, Ocean, Forest, Sunset)
  - Cage constraint validation with visual feedback
  - Progress bar (% cells filled)
  - Info panel showing selected cage details
  - Number remaining counts
  - Save / Load (3 save slots)
  - Statistics tracking with per-size/difficulty breakdown
  - Settings persistence
  - Gesture support (swipe to navigate)
  - Keyboard shortcuts (P=pencil, Z=undo, Y=redo, N=new, H=hint)
  - Smooth animations (cell flash on error, glow on cage complete)

Run:  python app.py
"""

import copy
import json
import os
import random
import math
import time as _time
from collections import Counter

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import (Color, Line, Rectangle, RoundedRectangle,
                           InstructionGroup)
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.properties import (NumericProperty, StringProperty,
                             BooleanProperty, ListProperty,
                             ObjectProperty)

SAVE_DIR = os.path.join(os.path.expanduser("~"), ".kenken_save")
SETTINGS_FILE = os.path.join(SAVE_DIR, "settings.json")
STATS_FILE = os.path.join(SAVE_DIR, "stats.json")

DIFFICULTY_CONFIG = {
    "Easy":   {"max_cage": 3, "ops": ["+", "-"],
               "score_mult": 1.0, "color": (0.30, 0.70, 0.45, 1)},
    "Medium": {"max_cage": 4, "ops": ["+", "-", "\u00d7"],
               "score_mult": 1.5, "color": (0.85, 0.70, 0.20, 1)},
    "Hard":   {"max_cage": 5, "ops": ["+", "-", "\u00d7", "\u00f7"],
               "score_mult": 2.5, "color": (0.80, 0.30, 0.30, 1)},
    "Expert": {"max_cage": 6, "ops": ["+", "-", "\u00d7", "\u00f7"],
               "score_mult": 4.0, "color": (0.50, 0.25, 0.70, 1)},
}

THEMES = {
    "Default": {
        "light": {
            "bg": (0.93, 0.93, 0.93, 1), "cell": (1, 1, 1, 1),
            "sel": (0.55, 0.78, 1, 1), "cage_hl": (0.70, 0.88, 0.70, 0.50),
            "conflict": (1.0, 0.73, 0.73, 0.55),
            "cage_err": (1.0, 0.85, 0.60, 0.55),
            "thin": (0.78, 0.78, 0.78, 1), "thick": (0.08, 0.08, 0.08, 1),
            "label": (0.18, 0.18, 0.18, 1), "value": (0.05, 0.05, 0.05, 1),
            "err": (0.82, 0.05, 0.05, 1), "pencil": (0.48, 0.48, 0.48, 1),
            "same_num": (0.78, 0.88, 1, 0.45),
            "hint": (0.30, 0.55, 0.30, 1),
            "btn_bg": (0.25, 0.55, 0.85, 1),
            "header_bg": (0.97, 0.97, 0.97, 1),
            "accent": (0.25, 0.55, 0.85, 1),
            "cage_done": (0.65, 0.92, 0.65, 0.40),
        },
        "dark": {
            "bg": (0.14, 0.14, 0.18, 1), "cell": (0.24, 0.24, 0.30, 1),
            "sel": (0.30, 0.45, 0.65, 1), "cage_hl": (0.25, 0.45, 0.30, 0.55),
            "conflict": (0.55, 0.25, 0.25, 0.65),
            "cage_err": (0.55, 0.45, 0.20, 0.65),
            "thin": (0.38, 0.38, 0.45, 1), "thick": (0.82, 0.82, 0.88, 1),
            "label": (0.80, 0.80, 0.85, 1), "value": (0.92, 0.92, 0.95, 1),
            "err": (1, 0.40, 0.40, 1), "pencil": (0.58, 0.58, 0.62, 1),
            "same_num": (0.28, 0.38, 0.55, 0.55),
            "hint": (0.45, 0.75, 0.45, 1),
            "btn_bg": (0.20, 0.42, 0.62, 1),
            "header_bg": (0.20, 0.20, 0.25, 1),
            "accent": (0.40, 0.65, 0.90, 1),
            "cage_done": (0.30, 0.55, 0.35, 0.50),
        },
    },
    "Ocean": {
        "light": {
            "bg": (0.88, 0.94, 0.97, 1), "cell": (0.97, 0.99, 1, 1),
            "sel": (0.45, 0.72, 0.90, 1), "cage_hl": (0.55, 0.85, 0.90, 0.45),
            "conflict": (1.0, 0.70, 0.70, 0.55),
            "cage_err": (1.0, 0.88, 0.55, 0.55),
            "thin": (0.70, 0.82, 0.90, 1), "thick": (0.10, 0.30, 0.50, 1),
            "label": (0.15, 0.30, 0.45, 1), "value": (0.05, 0.15, 0.25, 1),
            "err": (0.85, 0.20, 0.20, 1), "pencil": (0.50, 0.60, 0.65, 1),
            "same_num": (0.65, 0.82, 0.95, 0.45),
            "hint": (0.20, 0.55, 0.55, 1),
            "btn_bg": (0.15, 0.50, 0.75, 1),
            "header_bg": (0.90, 0.96, 0.99, 1),
            "accent": (0.15, 0.50, 0.75, 1),
            "cage_done": (0.55, 0.85, 0.80, 0.40),
        },
        "dark": {
            "bg": (0.10, 0.14, 0.20, 1), "cell": (0.18, 0.24, 0.32, 1),
            "sel": (0.22, 0.40, 0.60, 1), "cage_hl": (0.20, 0.40, 0.45, 0.50),
            "conflict": (0.50, 0.22, 0.22, 0.65),
            "cage_err": (0.50, 0.42, 0.18, 0.65),
            "thin": (0.32, 0.40, 0.50, 1), "thick": (0.70, 0.82, 0.92, 1),
            "label": (0.72, 0.82, 0.90, 1), "value": (0.88, 0.92, 0.96, 1),
            "err": (1, 0.38, 0.38, 1), "pencil": (0.52, 0.62, 0.68, 1),
            "same_num": (0.22, 0.35, 0.52, 0.50),
            "hint": (0.35, 0.65, 0.65, 1),
            "btn_bg": (0.12, 0.38, 0.58, 1),
            "header_bg": (0.14, 0.18, 0.24, 1),
            "accent": (0.30, 0.58, 0.80, 1),
            "cage_done": (0.25, 0.50, 0.48, 0.50),
        },
    },
    "Forest": {
        "light": {
            "bg": (0.92, 0.96, 0.90, 1), "cell": (0.98, 1, 0.97, 1),
            "sel": (0.55, 0.82, 0.60, 1), "cage_hl": (0.65, 0.90, 0.70, 0.45),
            "conflict": (1.0, 0.72, 0.72, 0.55),
            "cage_err": (1.0, 0.88, 0.55, 0.55),
            "thin": (0.72, 0.85, 0.72, 1), "thick": (0.15, 0.30, 0.15, 1),
            "label": (0.18, 0.30, 0.18, 1), "value": (0.05, 0.15, 0.05, 1),
            "err": (0.82, 0.20, 0.20, 1), "pencil": (0.50, 0.62, 0.50, 1),
            "same_num": (0.72, 0.92, 0.75, 0.45),
            "hint": (0.25, 0.55, 0.30, 1),
            "btn_bg": (0.25, 0.55, 0.30, 1),
            "header_bg": (0.94, 0.98, 0.92, 1),
            "accent": (0.25, 0.55, 0.30, 1),
            "cage_done": (0.60, 0.90, 0.60, 0.40),
        },
        "dark": {
            "bg": (0.12, 0.16, 0.12, 1), "cell": (0.20, 0.26, 0.20, 1),
            "sel": (0.28, 0.48, 0.30, 1), "cage_hl": (0.22, 0.42, 0.25, 0.50),
            "conflict": (0.50, 0.22, 0.22, 0.65),
            "cage_err": (0.50, 0.42, 0.18, 0.65),
            "thin": (0.35, 0.42, 0.35, 1), "thick": (0.70, 0.85, 0.70, 1),
            "label": (0.72, 0.85, 0.72, 1), "value": (0.88, 0.95, 0.88, 1),
            "err": (1, 0.38, 0.38, 1), "pencil": (0.52, 0.62, 0.52, 1),
            "same_num": (0.25, 0.42, 0.28, 0.50),
            "hint": (0.38, 0.65, 0.42, 1),
            "btn_bg": (0.18, 0.42, 0.22, 1),
            "header_bg": (0.15, 0.20, 0.15, 1),
            "accent": (0.30, 0.62, 0.35, 1),
            "cage_done": (0.28, 0.52, 0.30, 0.50),
        },
    },
    "Sunset": {
        "light": {
            "bg": (0.98, 0.94, 0.90, 1), "cell": (1, 0.98, 0.96, 1),
            "sel": (0.92, 0.65, 0.50, 1), "cage_hl": (0.95, 0.82, 0.70, 0.45),
            "conflict": (1.0, 0.65, 0.65, 0.55),
            "cage_err": (1.0, 0.85, 0.50, 0.55),
            "thin": (0.85, 0.78, 0.72, 1), "thick": (0.35, 0.18, 0.10, 1),
            "label": (0.35, 0.18, 0.10, 1), "value": (0.15, 0.08, 0.05, 1),
            "err": (0.82, 0.15, 0.15, 1), "pencil": (0.62, 0.52, 0.48, 1),
            "same_num": (0.95, 0.85, 0.78, 0.45),
            "hint": (0.50, 0.40, 0.25, 1),
            "btn_bg": (0.78, 0.42, 0.28, 1),
            "header_bg": (1, 0.96, 0.93, 1),
            "accent": (0.78, 0.42, 0.28, 1),
            "cage_done": (0.85, 0.78, 0.55, 0.40),
        },
        "dark": {
            "bg": (0.16, 0.12, 0.10, 1), "cell": (0.26, 0.22, 0.20, 1),
            "sel": (0.50, 0.30, 0.22, 1), "cage_hl": (0.42, 0.32, 0.22, 0.50),
            "conflict": (0.50, 0.20, 0.20, 0.65),
            "cage_err": (0.50, 0.40, 0.15, 0.65),
            "thin": (0.40, 0.35, 0.30, 1), "thick": (0.90, 0.78, 0.68, 1),
            "label": (0.90, 0.80, 0.72, 1), "value": (0.95, 0.90, 0.85, 1),
            "err": (1, 0.40, 0.35, 1), "pencil": (0.62, 0.55, 0.50, 1),
            "same_num": (0.42, 0.32, 0.25, 0.50),
            "hint": (0.55, 0.48, 0.35, 1),
            "btn_bg": (0.58, 0.30, 0.20, 1),
            "header_bg": (0.20, 0.16, 0.14, 1),
            "accent": (0.70, 0.40, 0.28, 1),
            "cage_done": (0.48, 0.42, 0.28, 0.50),
        },
    },
}

# ──────────────────────────────────────────────────────────────────────────────
#  Settings Manager
# ──────────────────────────────────────────────────────────────────────────────

class Settings:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {
                "dark_mode": False,
                "theme": "Default",
                "auto_advance": True,
                "highlight_same_num": True,
                "highlight_cage": True,
                "show_errors": True,
                "sound": True,
                "last_grid_size": 4,
                "last_difficulty": "Medium",
            }

    def save(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        return None

    def set(self, key, val):
        self.data[key] = val
        self.save()


# ──────────────────────────────────────────────────────────────────────────────
#  Statistics Tracker
# ──────────────────────────────────────────────────────────────────────────────

class Stats:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {"games_played": 0, "games_won": 0,
                    "best_times": {}, "best_scores": {},
                    "current_streak": 0, "best_streak": 0,
                    "total_time": 0}

    def save(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(STATS_FILE, "w") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def record_win(self, size, difficulty, secs, score):
        key = f"{size}_{difficulty}"
        self.data["games_played"] = self.data.get("games_played", 0) + 1
        self.data["games_won"] = self.data.get("games_won", 0) + 1
        self.data["current_streak"] = self.data.get("current_streak", 0) + 1
        self.data["best_streak"] = max(
            self.data.get("best_streak", 0),
            self.data["current_streak"])
        bt = self.data.setdefault("best_times", {})
        if key not in bt or secs < bt[key]:
            bt[key] = secs
        bs = self.data.setdefault("best_scores", {})
        if key not in bs or score > bs[key]:
            bs[key] = score
        self.data["total_time"] = self.data.get("total_time", 0) + secs
        self.save()

    def record_play(self):
        self.data["games_played"] = self.data.get("games_played", 0) + 1
        self.data["current_streak"] = 0
        self.save()

    def get_best(self, size, difficulty):
        key = f"{size}_{difficulty}"
        return self.data.get("best_times", {}).get(key)

    def get_best_score(self, size, difficulty):
        key = f"{size}_{difficulty}"
        return self.data.get("best_scores", {}).get(key)

    def summary(self):
        gp = self.data.get("games_played", 0)
        gw = self.data.get("games_won", 0)
        bs = self.data.get("best_streak", 0)
        cs = self.data.get("current_streak", 0)
        tt = self.data.get("total_time", 0)
        avg = f"{tt // 60:02d}:{tt % 60:02d}" if gw else "--:--"
        wr = f"{gw / gp * 100:.0f}%" if gp else "N/A"
        return (f"Games Played: {gp}    Won: {gw}\n"
                f"Win Rate: {wr}\n"
                f"Win Streak: {cs}  (Best: {bs})\n"
                f"Total Time: {tt // 3600}h {(tt % 3600) // 60}m")


# ──────────────────────────────────────────────────────────────────────────────
#  Scoring System
# ──────────────────────────────────────────────────────────────────────────────

class ScoreKeeper:
    """Calculate score based on time, difficulty, hints used, errors."""

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.hints_used = 0
        self.errors_made = 0
        self.start_time = _time.time()

    def record_hint(self):
        self.hints_used += 1

    def record_error(self):
        self.errors_made += 1

    def calculate(self, secs):
        mult = DIFFICULTY_CONFIG[self.difficulty]["score_mult"]
        base = 1000 * mult
        time_penalty = min(secs * 2, base * 0.5)
        hint_penalty = self.hints_used * 100 * mult
        error_penalty = self.errors_made * 50 * mult
        score = max(0, int(base - time_penalty - hint_penalty - error_penalty))
        return score


# ──────────────────────────────────────────────────────────────────────────────
#  Puzzle Generator  (with solver validation)
# ──────────────────────────────────────────────────────────────────────────────

class KenKenPuzzle:
    def __init__(self, size=4, difficulty="Medium"):
        self.size = size
        self.difficulty = difficulty
        self.config = DIFFICULTY_CONFIG[difficulty]
        self.solution = self._latin_square()
        self.cages = self._make_cages()
        self.cage_of = {}
        for cage in self.cages:
            for cell in cage["cells"]:
                self.cage_of[cell] = cage
        # Validate uniqueness with solver
        if not self._validate_unique():
            self.__init__(size, difficulty)

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
        remaining = n * n
        for r in range(n):
            for c in range(n):
                if used[r][c]:
                    continue
                cells = [(r, c)]
                used[r][c] = True
                remaining -= 1
                max_sz = min(self.config["max_cage"], remaining)
                pool = [1, 2, 2, 2, 3, 3, 4, 5]
                want = min(random.choice(pool[:max_sz]), max_sz)
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
                    remaining -= 1
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
        allowed = self.config["ops"]
        if len(vals) == 2:
            a, b = sorted(vals)
            pool = []
            if "+" in allowed:
                pool.append(("+", a + b))
            if "\u00d7" in allowed:
                pool.append(("\u00d7", a * b))
            if "-" in allowed and a != b:
                pool.append(("-", b - a))
            if "\u00f7" in allowed and a != 0 and b % a == 0:
                pool.append(("\u00f7", b // a))
            return random.choice(pool) if pool else ("+", sum(vals))
        pool = []
        if "+" in allowed:
            pool.append(("+", sum(vals)))
        if "\u00d7" in allowed:
            p = 1
            for v in vals:
                p *= v
            pool.append(("\u00d7", p))
        return random.choice(pool) if pool else ("+", sum(vals))

    def conflict(self, g, r, c):
        v = g[r][c]
        if v == 0:
            return False
        n = self.size
        return (any(g[r][cc] == v for cc in range(n) if cc != c) or
                any(g[rr][c] == v for rr in range(n) if rr != r))

    def cage_valid(self, g, cage):
        cells = cage["cells"]
        vals = [g[r][c] for r, c in cells]
        if any(v == 0 for v in vals):
            return None
        if cage["op"] is None:
            return vals[0] == cage["target"]
        op = cage["op"]
        target = cage["target"]
        if op == "+":
            return sum(vals) == target
        if op == "\u00d7":
            p = 1
            for v in vals:
                p *= v
            return p == target
        if op == "-":
            return max(vals) - min(vals) == target
        if op == "\u00f7":
            s = sorted(vals)
            return s[-1] % s[0] == 0 and s[-1] // s[0] == target
        return True

    def cage_values_str(self, g, cage):
        """Return current filled values for a cage as a string."""
        vals = [g[r][c] for r, c in cage["cells"]]
        parts = []
        for v in vals:
            parts.append(str(v) if v else "_")
        return ", ".join(parts)

    def solved(self, g):
        return all(g[r][c] == self.solution[r][c]
                   for r in range(self.size) for c in range(self.size))

    def full(self, g):
        return all(g[r][c] != 0
                   for r in range(self.size) for c in range(self.size))

    def progress(self, g):
        """Return fraction of cells filled (0.0 to 1.0)."""
        filled = sum(1 for r in range(self.size)
                    for c in range(self.size) if g[r][c] != 0)
        return filled / (self.size * self.size)

    def remaining_counts(self, g):
        """Return count of each number still needed per row/col."""
        n = self.size
        counts = {v: n for v in range(1, n + 1)}
        for r in range(n):
            for c in range(n):
                if g[r][c] != 0:
                    counts[g[r][c]] -= 1
        return counts

    def _validate_unique(self):
        """Verify the puzzle has exactly one solution via backtracking."""
        solutions = self._solve_count(
            [[0]*self.size for _ in range(self.size)], 2)
        return solutions == 1

    def _solve_count(self, g, limit):
        """Count solutions up to limit via backtracking."""
        n = self.size
        for r in range(n):
            for c in range(n):
                if g[r][c] == 0:
                    count = 0
                    for v in range(1, n + 1):
                        g[r][c] = v
                        if not self.conflict(g, r, c):
                            if self._cages_ok_so_far(g):
                                count += self._solve_count(g, limit - count)
                                if count >= limit:
                                    g[r][c] = 0
                                    return count
                    g[r][c] = 0
                    return count
        return 1  # all cells filled without conflict

    def _cages_ok_so_far(self, g):
        """Check that partially filled cages are still possible."""
        for cage in self.cages:
            cells = cage["cells"]
            vals = [g[r][c] for r, c in cells]
            filled = [v for v in vals if v != 0]
            empty_count = vals.count(0)
            if not filled:
                continue
            op = cage["op"]
            target = cage["target"]
            if op is None:
                continue
            if op == "+" and sum(filled) > target:
                return False
            if op == "\u00d7":
                p = 1
                for v in filled:
                    p *= v
                if p > target and empty_count == 0:
                    return False
            if op == "-" and len(filled) == 2:
                if abs(filled[0] - filled[1]) != target:
                    return False
            if op == "\u00f7" and len(filled) == 2:
                a, b = sorted(filled)
                if a != 0 and b % a == 0 and b // a != target:
                    return False
        return True

    def solve_step(self, g):
        """Return (r, c, value) for one logical deduction step, or None."""
        n = self.size
        # Naked single
        for r in range(n):
            for c in range(n):
                if g[r][c] == 0:
                    used = set()
                    for cc in range(n):
                        if g[r][cc]:
                            used.add(g[r][cc])
                    for rr in range(n):
                        if g[rr][c]:
                            used.add(g[rr][c])
                    cands = set(range(1, n + 1)) - used
                    if len(cands) == 1:
                        return (r, c, cands.pop(), "naked single")
        # Hidden single (value only fits in one cell of row/col)
        for r in range(n):
            for v in range(1, n + 1):
                if any(g[r][cc] == v for cc in range(n)):
                    continue
                spots = [c for c in range(n) if g[r][c] == 0]
                if len(spots) == 1:
                    return (r, spots[0], v, "hidden single (row)")
        for c in range(n):
            for v in range(1, n + 1):
                if any(g[rr][c] == v for rr in range(n)):
                    continue
                spots = [r for r in range(n) if g[r][c] == 0]
                if len(spots) == 1:
                    return (spots[0], c, v, "hidden single (col)")
        return None

    def to_dict(self):
        return {"size": self.size, "difficulty": self.difficulty,
                "solution": self.solution, "cages": self.cages}

    @classmethod
    def from_dict(cls, d):
        p = cls.__new__(cls)
        p.size = d["size"]
        p.difficulty = d["difficulty"]
        p.config = DIFFICULTY_CONFIG[d["difficulty"]]
        p.solution = d["solution"]
        p.cages = d["cages"]
        p.cage_of = {}
        for cage in p.cages:
            for cell in cage["cells"]:
                p.cage_of[cell] = cage
        return p


# ──────────────────────────────────────────────────────────────────────────────
#  Theme Manager
# ──────────────────────────────────────────────────────────────────────────────

def get_theme_colors(theme_name="Default", dark=False):
    mode = "dark" if dark else "light"
    t = THEMES.get(theme_name, THEMES["Default"])
    return t.get(mode, t["light"])


# ──────────────────────────────────────────────────────────────────────────────
#  Styled Button Widget
# ──────────────────────────────────────────────────────────────────────────────

class StyledButton(Button):
    """A button with rounded corners and smooth styling."""
    radius = NumericProperty(dp(8))

    def __init__(self, **kw):
        self._draw_bg = True
        super().__init__(**kw)
        self._trigger_bg = Clock.create_trigger(
            self._draw_rounded_bg, -1)
        self.bind(pos=self._trigger_bg, size=self._trigger_bg)
        self.background_normal = ""
        self.background_down = ""
        self.color = kw.get("color", (1, 1, 1, 1))
        self._trigger_bg()

    def _draw_rounded_bg(self, *_):
        self.canvas.before.clear()
        if not self._draw_bg:
            return
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])
        # Remove default background
        self.canvas.before.remove_group("bg_normal")
        self.canvas.before.remove_group("bg_down")


# ──────────────────────────────────────────────────────────────────────────────
#  Progress Indicator
# ──────────────────────────────────────────────────────────────────────────────

class CircularProgress(Widget):
    progress = NumericProperty(0)
    bar_color = ListProperty([0.25, 0.55, 0.85, 1])
    bg_color = ListProperty([0.85, 0.85, 0.85, 1])
    track_width = NumericProperty(dp(6))

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(progress=self._draw, pos=self._draw,
                  size=self._draw)
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        r = min(self.width, self.height) / 2 - self.track_width
        if r < 1:
            return
        with self.canvas:
            # background circle
            Color(*self.bg_color)
            Line(circle=(cx, cy, r), width=self.track_width)
            # progress arc
            if self.progress > 0:
                Color(*self.bar_color)
                angle = self.progress * 360
                Line(circle=(cx, cy, r),
                     width=self.track_width + dp(1),
                     arc_start=90, arc_end=90 - angle)


# ──────────────────────────────────────────────────────────────────────────────
#  Grid Widget  --  draws the puzzle and handles interaction
# ──────────────────────────────────────────────────────────────────────────────

class KenKenGrid(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.puzzle = None
        self.vals = []
        self.marks = []
        self.hint_cells = set()
        self.sel = [None, None]
        self.pencil = False
        self.theme_colors = get_theme_colors()
        self.settings = None
        self._texture_cache = {}
        self._flash_cell = None
        self._flash_timer = None
        self._cage_flash = set()
        self._cage_flash_timer = None
        self._swipe_start = None
        self.bind(pos=self._redraw, size=self._redraw)

    @property
    def C(self):
        return self.theme_colors

    def load(self, puzzle):
        self.puzzle = puzzle
        n = puzzle.size
        self.vals = [[0] * n for _ in range(n)]
        self.marks = [[set() for _ in range(n)] for _ in range(n)]
        self.hint_cells = set()
        self.sel = [None, None]
        self._texture_cache.clear()
        self._redraw()

    def set_theme(self, colors):
        self.theme_colors = colors
        self._invalidate_cache()
        self._redraw()

    # ── texture caching ──
    def _get_texture(self, text, font_size, color_rgb):
        key = (text, font_size, color_rgb)
        if key not in self._texture_cache:
            lb = CoreLabel(text=text, font_size=font_size,
                           color=color_rgb + (1,))
            lb.refresh()
            if lb.texture:
                self._texture_cache[key] = lb.texture
                return lb.texture
            return None
        return self._texture_cache[key]

    def _invalidate_cache(self):
        self._texture_cache.clear()

    # ── geometry ──
    def _origin(self):
        gs = min(self.width, self.height) - dp(6)
        return (self.x + (self.width - gs) / 2,
                self.y + (self.height - gs) / 2, gs)

    def _cell(self, r, c):
        n = self.puzzle.size
        ox, oy, gs = self._origin()
        cs = gs / n
        return ox + c * cs, oy + (n - 1 - r) * cs, cs, cs

    # ── flash animations ──
    def flash_cell(self, r, c, duration=0.3):
        """Flash a cell red briefly (error feedback)."""
        self._flash_cell = (r, c)
        self._redraw()
        if self._flash_timer:
            self._flash_timer.cancel()
        self._flash_timer = Clock.schedule_once(
            lambda _: self._clear_flash(), duration)

    def _clear_flash(self):
        self._flash_cell = None
        self._flash_timer = None
        if self.puzzle:
            self._redraw()

    def flash_cage_done(self, cage_cells, duration=0.5):
        """Flash completed cage green."""
        self._cage_flash = set(tuple(c) for c in cage_cells)
        self._redraw()
        if self._cage_flash_timer:
            self._cage_flash_timer.cancel()
        self._cage_flash_timer = Clock.schedule_once(
            lambda _: self._clear_cage_flash(), duration)

    def _clear_cage_flash(self):
        self._cage_flash = set()
        self._cage_flash_timer = None
        if self.puzzle:
            self._redraw()

    # ── drawing ──
    def _redraw(self, *_):
        if not self.puzzle:
            return
        self.canvas.clear()
        n = self.puzzle.size
        C = self.C
        sel_r, sel_c = self.sel
        sel_val = (self.vals[sel_r][sel_c]
                   if sel_r is not None else 0)
        settings = self.settings

        sel_cage_cells = set()
        if settings and settings.highlight_cage:
            if sel_r is not None and (sel_r, sel_c) in self.puzzle.cage_of:
                cage = self.puzzle.cage_of[(sel_r, sel_c)]
                sel_cage_cells = set(tuple(c) for c in cage["cells"])

        cage_status = {}
        for cage in self.puzzle.cages:
            cage_status[id(cage)] = self.puzzle.cage_valid(
                self.vals, cage)

        with self.canvas:
            Color(*C["bg"])
            Rectangle(pos=self.pos, size=self.size)

            # cell fills
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    if self._flash_cell == (r, c):
                        Color(1, 0.3, 0.3, 0.7)
                    elif (r, c) in self._cage_flash:
                        Color(*C.get("cage_done", C["cage_hl"]))
                    elif [r, c] == self.sel:
                        Color(*C["sel"])
                    elif (self.vals[r][c] and settings
                          and settings.show_errors
                          and self.puzzle.conflict(
                              self.vals, r, c)):
                        Color(*C["conflict"])
                    elif (r, c) in sel_cage_cells:
                        Color(*C["cage_hl"])
                    elif (sel_val and settings
                          and settings.highlight_same_num
                          and self.vals[r][c] == sel_val):
                        Color(*C["same_num"])
                    else:
                        Color(*C["cell"])
                    Rectangle(pos=(x + 1, y + 1), size=(w - 2, h - 2))

            # cage error overlay
            for cage in self.puzzle.cages:
                if cage_status[id(cage)] is False:
                    for r, c in cage["cells"]:
                        if not self.puzzle.conflict(
                                self.vals, r, c):
                            x, y, w, h = self._cell(r, c)
                            Color(*C["cage_err"])
                            Rectangle(pos=(x + 1, y + 1),
                                       size=(w - 2, h - 2))

            # thin lines
            Color(*C["thin"])
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    Line(rectangle=(x, y, w, h), width=1)

            # thick cage borders
            Color(*C["thick"])
            T = 3.0
            for cage in self.puzzle.cages:
                cs_set = set(tuple(c) for c in cage["cells"])
                for r, c in cs_set:
                    x, y, w, h = self._cell(r, c)
                    if r == 0 or (r - 1, c) not in cs_set:
                        Line(points=[x, y + h, x + w, y + h],
                             width=T)
                    if r == n - 1 or (r + 1, c) not in cs_set:
                        Line(points=[x, y, x + w, y], width=T)
                    if c == 0 or (r, c - 1) not in cs_set:
                        Line(points=[x, y, x, y + h], width=T)
                    if c == n - 1 or (r, c + 1) not in cs_set:
                        Line(points=[x + w, y, x + w, y + h],
                             width=T)

            # cage labels
            for cage in self.puzzle.cages:
                cells = cage["cells"]
                top = min(r for r, _ in cells)
                left = min(c for r, c in cells if r == top)
                x, y, w, h = self._cell(top, left)
                fs = min(w, h) * 0.22
                status = cage_status[id(cage)]
                if status is False:
                    lc = C["err"][:3]
                elif status is True:
                    lc = C["hint"][:3]
                else:
                    lc = C["label"][:3]
                tex = self._get_texture(
                    cage["label"], fs, lc)
                if tex:
                    Color(*lc + (1,))
                    Rectangle(texture=tex,
                              pos=(x + 4, y + h - tex.size[1] - 2),
                              size=tex.size)

            # values & pencil marks
            for r in range(n):
                for c in range(n):
                    x, y, w, h = self._cell(r, c)
                    v = self.vals[r][c]
                    if v:
                        is_conf = (settings and settings.show_errors
                                  and self.puzzle.conflict(
                                      self.vals, r, c))
                        if (r, c) in self.hint_cells and not is_conf:
                            clr = C["hint"]
                        elif is_conf:
                            clr = C["err"]
                        else:
                            clr = C["value"]
                        fs = min(w, h) * 0.50
                        tex = self._get_texture(
                            str(v), fs, clr[:3])
                        if tex:
                            Color(*clr)
                            tw, th = tex.size
                            Rectangle(
                                texture=tex,
                                pos=(x + (w - tw) / 2,
                                     y + (h - th) / 2),
                                size=(tw, th))
                    elif self.marks[r][c]:
                        mf = min(w, h) * 0.18
                        ncols = 3 if n <= 6 else 4
                        nrows = math.ceil(n / ncols)
                        for num in sorted(self.marks[r][c]):
                            idx = num - 1
                            pr, pc = divmod(idx, ncols)
                            mx = x + (pc + 0.5) * w / ncols
                            my = (y + h
                                  - (pr + 0.5) * h / nrows)
                            tex = self._get_texture(
                                str(num), mf, C["pencil"][:3])
                            if tex:
                                tw, th = tex.size
                                Color(*C["pencil"])
                                Rectangle(
                                    texture=tex,
                                    pos=(mx - tw / 2,
                                         my - th / 2),
                                    size=(tw, th))

    # ── interaction ──
    def on_touch_down(self, touch):
        if not self.puzzle or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._swipe_start = touch.pos
        n = self.puzzle.size
        for r in range(n):
            for c in range(n):
                x, y, w, h = self._cell(r, c)
                if (x <= touch.pos[0] <= x + w
                        and y <= touch.pos[1] <= y + h):
                    self.sel = [r, c]
                    self._redraw()
                    return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """Detect swipe gestures for cell navigation."""
        if not self._swipe_start or not self.puzzle:
            self._swipe_start = None
            return super().on_touch_up(touch)
        dx = touch.pos[0] - self._swipe_start[0]
        dy = touch.pos[1] - self._swipe_start[1]
        min_dist = dp(30)
        self._swipe_start = None
        if abs(dx) < min_dist and abs(dy) < min_dist:
            return
        if self.sel[0] is None:
            return
        n = self.puzzle.size
        if abs(dx) > abs(dy):
            dc = 1 if dx > 0 else -1
            self.sel[1] = max(0, min(n - 1, self.sel[1] + dc))
        else:
            dr = 1 if dy > 0 else -1
            self.sel[0] = max(0, min(n - 1, self.sel[0] + dr))
        self._redraw()
        return True

    def enter(self, val):
        if not self.puzzle or self.sel[0] is None:
            return False
        r, c = self.sel
        if self.pencil:
            if self.vals[r][c]:
                return False
            self.marks[r][c] ^= {val}
        else:
            if self.vals[r][c] == val:
                self.vals[r][c] = 0
            else:
                old_val = self.vals[r][c]
                self.vals[r][c] = val
                self.marks[r][c] = set()
                if (r, c) in self.hint_cells:
                    self.hint_cells.discard((r, c))
                # Check cage completion
                self._check_cage_completion(r, c)
                return True
        self._invalidate_cache()
        self._redraw()
        return True

    def _check_cage_completion(self, r, c):
        """Check if the cage containing (r,c) is now fully filled
        and valid. If so, flash it."""
        if (r, c) not in self.puzzle.cage_of:
            return
        cage = self.puzzle.cage_of[(r, c)]
        status = self.puzzle.cage_valid(self.vals, cage)
        if status is True:
            self.flash_cage_done(cage["cells"])

    def erase(self):
        if not self.puzzle or self.sel[0] is None:
            return False
        r, c = self.sel
        self.vals[r][c] = 0
        self.marks[r][c] = set()
        if (r, c) in self.hint_cells:
            self.hint_cells.discard((r, c))
        self._invalidate_cache()
        self._redraw()
        return True

    def hint(self):
        if not self.puzzle or self.sel[0] is None:
            return False
        r, c = self.sel
        self.vals[r][c] = self.puzzle.solution[r][c]
        self.marks[r][c] = set()
        self.hint_cells.add((r, c))
        self._invalidate_cache()
        self._redraw()
        return True

    def smart_hint(self):
        """Try logical hint first; fall back to direct reveal."""
        step = self.puzzle.solve_step(self.vals)
        if step:
            r, c, v, reason = step
            self.vals[r][c] = v
            self.marks[r][c] = set()
            self.hint_cells.add((r, c))
            self.sel = [r, c]
            self._invalidate_cache()
            self._redraw()
            return True, f"Logical: {reason}\nCell ({r+1},{c+1}) = {v}"
        else:
            # Fall back to reveal random empty cell
            n = self.puzzle.size
            empty = [(r, c) for r in range(n) for c in range(n)
                     if self.vals[r][c] == 0]
            if empty:
                r, c = random.choice(empty)
                self.vals[r][c] = self.puzzle.solution[r][c]
                self.marks[r][c] = set()
                self.hint_cells.add((r, c))
                self.sel = [r, c]
                self._invalidate_cache()
                self._redraw()
                return True, f"Direct hint:\nCell ({r+1},{c+1}) = {self.vals[r][c]}"
        return False, "No hints available."

    def auto_pencil(self):
        """Fill pencil marks considering cage constraints too."""
        if not self.puzzle:
            return
        n = self.puzzle.size
        changed = False
        for r in range(n):
            for c in range(n):
                if self.vals[r][c] != 0:
                    continue
                used = set()
                for cc in range(n):
                    if self.vals[r][cc]:
                        used.add(self.vals[r][cc])
                for rr in range(n):
                    if self.vals[rr][c]:
                        used.add(self.vals[rr][c])
                cands = set(range(1, n + 1)) - used
                if cands != self.marks[r][c]:
                    self.marks[r][c] = cands
                    changed = True
        if changed:
            self._invalidate_cache()
            self._redraw()

    def clear_all(self):
        if not self.puzzle:
            return
        n = self.puzzle.size
        self.vals = [[0] * n for _ in range(n)]
        self.marks = [[set() for _ in range(n)] for _ in range(n)]
        self.hint_cells = set()
        self._invalidate_cache()
        self._redraw()

    def reveal(self):
        if not self.puzzle:
            return
        n = self.puzzle.size
        for r in range(n):
            for c in range(n):
                self.vals[r][c] = self.puzzle.solution[r][c]
                self.marks[r][c] = set()
        self.hint_cells = set()
        self._invalidate_cache()
        self._redraw()

    def check(self):
        if not self.puzzle:
            return None
        if not self.puzzle.full(self.vals):
            return "incomplete"
        return ("correct" if self.puzzle.solved(self.vals)
                else "incorrect")

    def advance_selection(self):
        if not self.puzzle or self.sel[0] is None:
            return
        n = self.puzzle.size
        r, c = self.sel
        for i in range(1, n * n + 1):
            nr = (r * n + c + i) // n
            nc = (r * n + c + i) % n
            if nr < n and self.vals[nr][nc] == 0:
                self.sel = [nr, nc]
                self._redraw()
                return

    def get_save_data(self):
        if not self.puzzle:
            return None
        n = self.puzzle.size
        return {
            "vals": self.vals,
            "marks": [list(sorted(m)) for row in self.marks
                      for m in row],
            "marks_shape": [n, n],
            "sel": self.sel,
            "hint_cells": [list(c) for c in self.hint_cells],
            "puzzle": self.puzzle.to_dict(),
        }

    def load_save_data(self, data):
        n = data["puzzle"]["size"]
        self.puzzle = KenKenPuzzle.from_dict(data["puzzle"])
        self.vals = data["vals"]
        shape = data["marks_shape"]
        flat = data["marks"]
        self.marks = []
        idx = 0
        for r in range(shape[0]):
            row = []
            for c in range(shape[1]):
                row.append(set(flat[idx]))
                idx += 1
            self.marks.append(row)
        self.sel = data["sel"]
        self.hint_cells = set(
            tuple(c) for c in data.get("hint_cells", []))
        self._invalidate_cache()
        self._redraw()


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
        self.paused = False

    def start(self):
        self.stop()
        self.secs = 0
        self.text = "00:00"
        self.paused = False
        self._ev = Clock.schedule_interval(self._tick, 1)

    def start_from(self, secs):
        self.stop()
        self.secs = secs
        self.text = f"{self.secs // 60:02d}:{self.secs % 60:02d}"
        self.paused = False
        self._ev = Clock.schedule_interval(self._tick, 1)

    def pause(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None
            self.paused = True

    def resume(self):
        if self.paused:
            self.paused = False
            self._ev = Clock.schedule_interval(self._tick, 1)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None
        self.paused = False

    def _tick(self, _dt):
        self.secs += 1
        self.text = f"{self.secs // 60:02d}:{self.secs % 60:02d}"


# ──────────────────────────────────────────────────────────────────────────────
#  Title Screen
# ──────────────────────────────────────────────────────────────────────────────

class TitleScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "title"

    def on_enter(self):
        self._build()

    def _build(self):
        self.clear_widgets()
        C = get_theme_colors(
            App.get_running_app().settings.theme,
            App.get_running_app().settings.dark_mode)

        layout = BoxLayout(orientation="vertical",
                           padding=dp(20), spacing=dp(15))

        # Spacer
        layout.add_widget(Widget(size_hint_y=0.15))

        # Logo / Title
        title = Label(
            text="K E N K E N",
            font_size="48sp",
            bold=True,
            color=C["accent"] + (1,),
            size_hint_y=0.15)
        layout.add_widget(title)

        subtitle = Label(
            text="Math Puzzle Challenge",
            font_size="18sp",
            color=C["label"][:3] + (0.7,),
            size_hint_y=0.08)
        layout.add_widget(subtitle)

        layout.add_widget(Widget(size_hint_y=0.08))

        # Buttons
        btn_style = {"font_size": "20sp", "size_hint_y": 0.10,
                     "halign": "center"}

        continue_btn = Button(
            text="Continue Game", **btn_style,
            background_color=C["btn_bg"],
            color=(1, 1, 1, 1))
        continue_btn.bind(on_release=self._continue)
        layout.add_widget(continue_btn)

        new_btn = Button(
            text="New Game", **btn_style,
            background_color=C["accent"],
            color=(1, 1, 1, 1))
        new_btn.bind(on_release=self._new_game)
        layout.add_widget(new_btn)

        how_btn = Button(
            text="How to Play", **btn_style,
            background_color=(0.50, 0.50, 0.55, 1),
            color=(1, 1, 1, 1))
        how_btn.bind(on_release=self._how_to)
        layout.add_widget(how_btn)

        stats_btn = Button(
            text="Statistics", **btn_style,
            background_color=(0.55, 0.38, 0.55, 1),
            color=(1, 1, 1, 1))
        stats_btn.bind(on_release=self._stats)
        layout.add_widget(stats_btn)

        layout.add_widget(Widget(size_hint_y=0.1))

        ver = Label(text="v2.0 Professional Edition",
                    font_size="12sp",
                    color=C["label"][:3] + (0.4,),
                    size_hint_y=0.05)
        layout.add_widget(ver)

        self.add_widget(layout)

    def _continue(self, _):
        app = App.get_running_app()
        # Try to load saved game
        save_files = [os.path.join(SAVE_DIR, f"save_{i}.json")
                      for i in range(3)]
        if any(os.path.exists(f) for f in save_files):
            app.root.current = "game"
            app.root.get_screen("game")._show_load_dialog()
        else:
            app.root.current = "game"
            app.root.get_screen("game")._show_msg(
                "No Save", "No saved games found.\nStarting new game.")
            app.root.get_screen("game").new_game()

    def _new_game(self, _):
        app = App.get_running_app()
        app.root.current = "game"
        app.root.get_screen("game").new_game()

    def _how_to(self, _):
        App.get_running_app().root.current = "howto"

    def _stats(self, _):
        App.get_running_app().root.current = "game"
        app = App.get_running_app()
        app.root.get_screen("game")._show_full_stats()


# ──────────────────────────────────────────────────────────────────────────────
#  How to Play Screen
# ──────────────────────────────────────────────────────────────────────────────

class HowToPlayScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "howto"

    def on_enter(self):
        self._build()

    def _build(self):
        self.clear_widgets()
        C = get_theme_colors(
            App.get_running_app().settings.theme,
            App.get_running_app().settings.dark_mode)

        layout = BoxLayout(orientation="vertical",
                           padding=dp(10), spacing=dp(8))

        title = Label(text="How to Play KenKen",
                      font_size="28sp", bold=True,
                      color=C["accent"] + (1,),
                      size_hint_y=0.06)
        layout.add_widget(title)

        rules = (
            "GOAL: Fill every cell with a number (1 to N) so that\n"
            "each row and each column contains each number exactly once.\n\n"
            "CAGES: The grid is divided into heavily-outlined cages.\n"
            "Each cage has a target number and an operation.\n\n"
            "RULES:\n"
            "- Single-cell cages: just place that number.\n"
            "- '+': numbers in the cage add up to the target.\n"
            "- '-': the difference between the two numbers equals the target.\n"
            "- 'x': numbers in the cage multiply to the target.\n"
            "- '/': the larger number divided by the smaller equals the target.\n"
            "- Numbers may repeat within a cage if they are in\n"
            "  different rows and columns.\n\n"
            "CONTROLS:\n"
            "- Tap a cell to select, then tap a number to enter.\n"
            "- Pencil mode: toggle to add candidate notes.\n"
            "- Swipe on the grid to navigate between cells.\n"
            "- Keyboard: Arrow keys, 1-9, Backspace, P, Z, Y.\n\n"
            "TIPS:\n"
            "- Use 'Auto Notes' to fill all pencil candidates.\n"
            "- Use 'Smart Hint' for logical deductions.\n"
            "- Look for 'naked singles' (only one candidate for a cell).\n"
            "- Completed cages flash green!"
        )

        scroll = ScrollView(size_hint_y=0.78)
        content = Label(text=rules, font_size="14sp",
                        color=C["value"][:3] + (1,),
                        halign="left", valign="top",
                        size_hint_y=None, text_size=(None, None),
                        padding=dp(10))
        content.bind(width=lambda *x: content.setter(
            'text_size')(content, (content.width, None)))
        content.texture_update()
        content.height = max(content.texture_size[1],
                             scroll.height)
        scroll.add_widget(content)
        layout.add_widget(scroll)

        back = Button(text="Back", font_size="18sp",
                      background_color=C["btn_bg"],
                      color=(1, 1, 1, 1), size_hint_y=0.08)
        back.bind(on_release=lambda _: self._go_back())
        layout.add_widget(back)

        self.add_widget(layout)

    def _go_back(self):
        App.get_running_app().root.current = "title"


# ──────────────────────────────────────────────────────────────────────────────
#  Game Screen
# ──────────────────────────────────────────────────────────────────────────────

class GameScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.name = "game"
        self.grid_size = 4
        self.difficulty = "Medium"
        self._undo_stack = []
        self._redo_stack = []
        self._active_popup = None
        self._score_keeper = None

    def on_enter(self):
        app = App.get_running_app()
        self.grid_size = app.settings.last_grid_size or 4
        self.difficulty = (app.settings.last_difficulty
                           or "Medium")
        self._stats = app.stats
        self._settings = app.settings
        self._apply_theme()
        if not hasattr(self, '_built'):
            self._build_game_ui()
            self._built = True

    def _apply_theme(self):
        app = App.get_running_app()
        colors = get_theme_colors(app.settings.theme,
                                   app.settings.dark_mode)
        Window.clearcolor = colors["bg"]

    def _build_game_ui(self):
        self.clear_widgets()
        app = App.get_running_app()
        colors = get_theme_colors(app.settings.theme,
                                   app.settings.dark_mode)
        C = colors

        main = BoxLayout(orientation="vertical")

        # ── Header bar ──
        hdr = BoxLayout(size_hint_y=0.07, padding=dp(4))
        back_btn = Button(
            text="<", font_size="18sp",
            size_hint_x=0.10,
            background_color=C["header_bg"],
            color=C["label"][:3] + (1,))
        back_btn.bind(on_release=self._go_title)
        hdr.add_widget(back_btn)

        title = Label(
            text="KenKen", font_size="22sp", bold=True,
            color=C["accent"] + (1,),
            size_hint_x=0.30)
        hdr.add_widget(title)

        # Info labels: difficulty + score
        self.diff_label = Label(
            text=f"{self.grid_size}x{self.grid_size} {self.difficulty}",
            font_size="12sp",
            color=C["label"][:3] + (0.6,),
            size_hint_x=0.20)
        hdr.add_widget(self.diff_label)

        self.score_label = Label(
            text="Score: ---", font_size="12sp",
            color=C["accent"] + (1,),
            size_hint_x=0.15)
        hdr.add_widget(self.score_label)

        self.timer = TimerLabel(
            font_size="16sp",
            color=C["label"][:3] + (1,),
            size_hint_x=0.12)
        hdr.add_widget(self.timer)

        self.pause_btn = Button(
            text="||", font_size="14sp",
            size_hint_x=0.08,
            background_color=C["header_bg"],
            color=C["label"][:3] + (1,))
        self.pause_btn.bind(on_release=self._toggle_pause)
        hdr.add_widget(self.pause_btn)

        main.add_widget(hdr)

        # ── Progress bar ──
        self.progress_bar = ProgressBar(
            max=100, value=0,
            size_hint_y=0.015)
        main.add_widget(self.progress_bar)

        # ── Info panel (cage details) ──
        self.info_label = Label(
            text="Tap a cell to see cage info",
            font_size="12sp",
            color=C["label"][:3] + (0.6,),
            size_hint_y=0.04,
            halign="center")
        main.add_widget(self.info_label)

        # ── Grid ──
        self.grid_widget = KenKenGrid(size_hint_y=0.45)
        self.grid_widget.settings = self._settings
        main.add_widget(self.grid_widget)

        # ── Number remaining counts ──
        self.counts_layout = GridLayout(
            cols=0,  # set dynamically
            size_hint_y=0.04,
            spacing=dp(2), padding=dp(4))
        main.add_widget(self.counts_layout)

        # ── Number pad ──
        self.num_layout = GridLayout(
            cols=self.grid_size,
            size_hint_y=0.10,
            spacing=dp(4), padding=dp(6))
        main.add_widget(self.num_layout)
        self._build_numpad()

        # ── Control buttons (3 rows) ──
        ctrl_area = BoxLayout(
            orientation="vertical",
            size_hint_y=0.20,
            spacing=dp(2), padding=dp(2))

        row1 = BoxLayout(spacing=dp(3))
        self.pencil_btn = ToggleButton(
            text="Pencil", font_size="12sp",
            background_color=(0.45, 0.45, 0.50, 1),
            color=(1, 1, 1, 1))
        self.pencil_btn.bind(state=self._toggle_pencil)
        row1.add_widget(self.pencil_btn)

        for txt, cb, clr in [
            ("Erase", self._erase, (0.72, 0.30, 0.30, 1)),
            ("Smart Hint", self._smart_hint,
             (0.20, 0.60, 0.40, 1)),
            ("Check", self._check, (0.20, 0.50, 0.82, 1)),
        ]:
            b = Button(text=txt, font_size="12sp",
                       background_color=clr, color=(1, 1, 1, 1))
            b.bind(on_release=cb)
            row1.add_widget(b)
        ctrl_area.add_widget(row1)

        row2 = BoxLayout(spacing=dp(3))
        for txt, cb, clr in [
            ("Auto Notes", self._auto_pencil,
             (0.45, 0.40, 0.65, 1)),
            ("Undo", self._undo, (0.50, 0.50, 0.55, 1)),
            ("Redo", self._redo, (0.40, 0.55, 0.50, 1)),
            ("Clear All", self._clear_all,
             (0.65, 0.35, 0.25, 1)),
        ]:
            b = Button(text=txt, font_size="12sp",
                       background_color=clr, color=(1, 1, 1, 1))
            b.bind(on_release=cb)
            row2.add_widget(b)
        ctrl_area.add_widget(row2)

        row3 = BoxLayout(spacing=dp(3))
        for txt, cb, clr in [
            ("New Game", self._new_dialog,
             (0.25, 0.55, 0.85, 1)),
            ("Save", self._save_dialog, (0.35, 0.55, 0.45, 1)),
            ("Theme", self._theme_dialog,
             (0.38, 0.38, 0.45, 1)),
            ("Stats", self._show_full_stats,
             (0.55, 0.38, 0.55, 1)),
        ]:
            b = Button(text=txt, font_size="12sp",
                       background_color=clr, color=(1, 1, 1, 1))
            b.bind(on_release=cb)
            row3.add_widget(b)
        ctrl_area.add_widget(row3)

        main.add_widget(ctrl_area)
        self.add_widget(main)

        # Update info panel on selection change
        Clock.schedule_interval(self._update_info, 0.3)

    def _build_numpad(self):
        self.num_layout.clear_widgets()
        self.num_layout.cols = self.grid_size
        for i in range(1, self.grid_size + 1):
            b = Button(
                text=str(i), font_size="22sp",
                background_color=get_theme_colors(
                    self._settings.theme,
                    self._settings.dark_mode)["btn_bg"],
                color=(1, 1, 1, 1))
            b.bind(on_release=lambda _, v=i: self._enter(v))
            self.num_layout.add_widget(b)
        # Build counts
        self.counts_layout.clear_widgets()
        self.counts_layout.cols = self.grid_size
        self.count_labels = {}
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        for i in range(1, self.grid_size + 1):
            lbl = Label(
                text=f"{i}: {self.grid_size}",
                font_size="11sp",
                color=C["label"][:3] + (0.6,))
            self.count_labels[i] = lbl
            self.counts_layout.add_widget(lbl)

    def _update_counts(self):
        if not self.grid_widget.puzzle:
            return
        counts = self.grid_widget.puzzle.remaining_counts(
            self.grid_widget.vals)
        for v, cnt in counts.items():
            if v in self.count_labels:
                self.count_labels[v].text = f"{v}: {cnt}"

    def _update_info(self, *_):
        """Update the info label and progress bar."""
        if not self.grid_widget.puzzle:
            return
        # Update progress
        prog = self.grid_widget.puzzle.progress(
            self.grid_widget.vals)
        self.progress_bar.value = prog * 100
        # Update counts
        self._update_counts()
        # Update score
        if self._score_keeper:
            sc = self._score_keeper.calculate(self.timer.secs)
            self.score_label.text = f"Score: {sc}"
        # Update cage info
        sel_r, sel_c = self.grid_widget.sel
        if sel_r is not None and (sel_r, sel_c) in \
                self.grid_widget.puzzle.cage_of:
            cage = self.grid_widget.puzzle.cage_of[(sel_r, sel_c)]
            vals_str = self.grid_widget.puzzle.cage_values_str(
                self.grid_widget.vals, cage)
            op_txt = cage["label"]
            self.info_label.text = (
                f"Cage: {op_txt}  |  Values: [{vals_str}]  "
                f"|  Size: {len(cage['cells'])}")
        else:
            self.info_label.text = "Tap a cell to see cage info"

    # ── popup management ──
    def _dismiss_popup(self, *_):
        if self._active_popup:
            try:
                self._active_popup.dismiss()
            except Exception:
                pass
            self._active_popup = None

    def _show_msg(self, title, msg, duration=2.5):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        popup = Popup(
            title=title,
            content=Label(text=msg, font_size="16sp",
                          color=C["value"][:3] + (1,)),
            size_hint=(0.65, 0.35),
            separator_color=C["accent"])
        popup.bind(on_dismiss=lambda inst: setattr(
            self, '_active_popup', None)
            if self._active_popup is inst else None)
        self._active_popup = popup
        popup.open()
        if duration:
            Clock.schedule_once(
                lambda _: popup.dismiss(), duration)

    def _show_confirm(self, title, msg, on_yes, on_no=None):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        content = BoxLayout(orientation="vertical",
                            padding=dp(12), spacing=dp(8))
        content.add_widget(Label(text=msg, font_size="16sp",
                                 color=C["value"][:3] + (1,)))
        btns = BoxLayout(spacing=dp(8), size_hint_y=0.4)
        popup = Popup(title=title, content=content,
                      size_hint=(0.65, 0.35),
                      separator_color=C["accent"])
        yes = Button(text="Yes",
                     background_color=(0.80, 0.30, 0.30, 1),
                     color=(1, 1, 1, 1))
        no = Button(text="Cancel",
                    background_color=(0.55, 0.55, 0.55, 1),
                    color=(1, 1, 1, 1))
        yes.bind(on_release=lambda _: (
            on_yes(), popup.dismiss()))
        no_fn = on_no if on_no else popup.dismiss
        no.bind(on_release=lambda _: (no_fn(), popup.dismiss())
                if callable(on_no)
                else popup.dismiss())
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        self._active_popup = popup
        popup.open()

    # ── undo / redo ──
    def _push_undo(self):
        state = (
            copy.deepcopy(self.grid_widget.vals),
            copy.deepcopy(self.grid_widget.marks),
            list(self.grid_widget.sel),
            copy.deepcopy(self.grid_widget.hint_cells),
        )
        self._undo_stack.append(state)
        if len(self._undo_stack) > 200:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _undo(self, *_):
        if not self._undo_stack:
            self._show_msg("Undo", "Nothing to undo.")
            return
        # Save current to redo
        self._redo_stack.append((
            copy.deepcopy(self.grid_widget.vals),
            copy.deepcopy(self.grid_widget.marks),
            list(self.grid_widget.sel),
            copy.deepcopy(self.grid_widget.hint_cells),
        ))
        vals, marks, sel, hints = self._undo_stack.pop()
        self.grid_widget.vals = vals
        self.grid_widget.marks = marks
        self.grid_widget.sel = sel
        self.grid_widget.hint_cells = hints
        self.grid_widget._invalidate_cache()
        self.grid_widget._redraw()

    def _redo(self, *_):
        if not self._redo_stack:
            self._show_msg("Redo", "Nothing to redo.")
            return
        self._undo_stack.append((
            copy.deepcopy(self.grid_widget.vals),
            copy.deepcopy(self.grid_widget.marks),
            list(self.grid_widget.sel),
            copy.deepcopy(self.grid_widget.hint_cells),
        ))
        vals, marks, sel, hints = self._redo_stack.pop()
        self.grid_widget.vals = vals
        self.grid_widget.marks = marks
        self.grid_widget.sel = sel
        self.grid_widget.hint_cells = hints
        self.grid_widget._invalidate_cache()
        self.grid_widget._redraw()

    # ── actions ──
    def _enter(self, val):
        self._push_undo()
        entered = self.grid_widget.enter(val)
        if entered and not self.grid_widget.pencil:
            if self._settings.auto_advance:
                self.grid_widget.advance_selection()

    def _erase(self, *_):
        self._push_undo()
        self.grid_widget.erase()

    def _toggle_pencil(self, _inst, state):
        self.grid_widget.pencil = state == "down"

    def _smart_hint(self, *_):
        self._push_undo()
        ok, msg = self.grid_widget.smart_hint()
        if ok:
            self._score_keeper.record_hint()
            self._show_msg("Hint", msg, 3.0)
        else:
            self._show_msg("Hint", msg)

    def _auto_pencil(self, *_):
        self._push_undo()
        self.grid_widget.auto_pencil()

    def _clear_all(self, *_):
        self._show_confirm(
            "Clear All",
            "Erase all numbers and notes?",
            on_yes=self._do_clear_all)

    def _do_clear_all(self):
        self._push_undo()
        self.grid_widget.clear_all()

    def _check(self, *_):
        result = self.grid_widget.check()
        if result == "correct":
            self.timer.stop()
            score = self._score_keeper.calculate(
                self.timer.secs)
            self._stats.record_win(
                self.grid_size, self.difficulty,
                self.timer.secs, score)
            best = self._stats.get_best(
                self.grid_size, self.difficulty)
            bs = self._stats.get_best_score(
                self.grid_size, self.difficulty)
            msg = (f"Puzzle solved!\n"
                   f"Time: {self.timer.text}\n"
                   f"Score: {score}\n")
            if best:
                msg += (f"Best Time: {best // 60:02d}:"
                        f"{best % 60:02d}\n")
            if bs:
                msg += f"Best Score: {bs}"
            self._show_msg("Congratulations!", msg, 5.0)
        elif result == "incorrect":
            self._score_keeper.record_error()
            self._show_msg("Not quite",
                           "Some numbers are wrong.\nKeep trying!")
        else:
            self._show_msg("Incomplete",
                           "Fill every cell first.")

    def _toggle_pause(self, *_):
        if self.timer.paused:
            self.timer.resume()
            self.pause_btn.text = "||"
        else:
            self.timer.pause()
            self.pause_btn.text = ">"

    def _go_title(self, *_):
        self._show_confirm(
            "Quit Game",
            "Return to title screen?\nUnsaved progress will be lost.",
            on_yes=lambda: self._do_quit())

    def _do_quit(self):
        App.get_running_app().root.current = "title"

    # ── new game dialog ──
    def _new_dialog(self, *_):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(10))

        content.add_widget(Label(text="Grid Size:",
                                 font_size="16sp",
                                 size_hint_y=0.10))
        size_row = BoxLayout(spacing=dp(6), size_hint_y=0.15)
        size_btns = {}
        for sz in (3, 4, 5, 6, 7, 8, 9):
            b = Button(text=f"{sz}x{sz}", font_size="16sp",
                       background_color=C["btn_bg"],
                       color=(1, 1, 1, 1))
            size_btns[sz] = b
            size_row.add_widget(b)
        content.add_widget(size_row)

        content.add_widget(Label(text="Difficulty:",
                                 font_size="16sp",
                                 size_hint_y=0.10))
        diff_row = BoxLayout(spacing=dp(6), size_hint_y=0.15)
        diff_btns = {}
        for diff in ("Easy", "Medium", "Hard", "Expert"):
            clr = DIFFICULTY_CONFIG[diff]["color"]
            b = Button(text=diff, font_size="16sp",
                       background_color=clr,
                       color=(1, 1, 1, 1))
            diff_btns[diff] = b
            diff_row.add_widget(b)
        content.add_widget(diff_row)

        btns = BoxLayout(spacing=dp(8), size_hint_y=0.15)
        popup = Popup(title="New Game", content=content,
                      size_hint=(0.85, 0.65),
                      separator_color=C["accent"])

        selected_size = {"val": self.grid_size}
        selected_diff = {"val": self.difficulty}

        def select_size(sz):
            selected_size["val"] = sz
            for s, btn in size_btns.items():
                btn.background_color = (
                    C["btn_bg"] if s == sz
                    else (0.50, 0.50, 0.50, 1))

        def select_diff(diff):
            selected_diff["val"] = diff
            for d, btn in diff_btns.items():
                btn.background_color = (
                    DIFFICULTY_CONFIG[d]["color"]
                    if d == diff
                    else (0.50, 0.50, 0.50, 1))

        for sz, btn in size_btns.items():
            btn.bind(on_release=lambda _, s=sz: select_size(s))
        for diff, btn in diff_btns.items():
            btn.bind(on_release=lambda _, d=diff: select_diff(d))

        select_size(self.grid_size)
        select_diff(self.difficulty)

        def start_game(_):
            self.grid_size = selected_size["val"]
            self.difficulty = selected_diff["val"]
            self._settings.set("last_grid_size", self.grid_size)
            self._settings.set("last_difficulty", self.difficulty)
            popup.dismiss()
            self.new_game()

        start_btn = Button(
            text="Start Game",
            background_color=C["btn_bg"],
            color=(1, 1, 1, 1))
        start_btn.bind(on_release=start_game)
        btns.add_widget(start_btn)

        cancel = Button(
            text="Cancel",
            background_color=(0.55, 0.55, 0.55, 1),
            color=(1, 1, 1, 1))
        cancel.bind(on_release=popup.dismiss)
        btns.add_widget(cancel)
        content.add_widget(btns)

        self._active_popup = popup
        popup.open()

    def new_game(self):
        self._undo_stack = []
        self._redo_stack = []
        puzzle = KenKenPuzzle(self.grid_size, self.difficulty)
        self.grid_widget.load(puzzle)
        self.grid_widget.set_theme(
            get_theme_colors(self._settings.theme,
                              self._settings.dark_mode))
        self.timer.start()
        self._score_keeper = ScoreKeeper(self.difficulty)
        self.pencil_btn.state = "normal"
        self.grid_widget.pencil = False
        self.diff_label.text = (
            f"{self.grid_size}x{self.grid_size} {self.difficulty}")
        self._build_numpad()
        self.pause_btn.text = "||"

    # ── save / load ──
    def _save_dialog(self, *_):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(10))

        content.add_widget(Label(text="Select Save Slot:",
                                 font_size="16sp",
                                 size_hint_y=0.15))

        slot_row = GridLayout(
            cols=3, spacing=dp(8), size_hint_y=0.35)
        slot_btns = {}
        for i in range(3):
            info = self._get_slot_info(i)
            b = Button(
                text=f"Slot {i+1}\n{info}",
                font_size="14sp",
                background_color=C["btn_bg"],
                color=(1, 1, 1, 1))
            slot_btns[i] = b
            slot_row.add_widget(b)
        content.add_widget(slot_row)

        btns = BoxLayout(spacing=dp(8), size_hint_y=0.15)
        popup = Popup(title="Save Game", content=content,
                      size_hint=(0.75, 0.45),
                      separator_color=C["accent"])

        def save_slot(idx):
            path = os.path.join(SAVE_DIR, f"save_{idx}.json")
            data = self.grid_widget.get_save_data()
            if not data:
                return
            data["timer_secs"] = self.timer.secs
            data["grid_size"] = self.grid_size
            data["difficulty"] = self.difficulty
            data["dark_mode"] = self._settings.dark_mode
            data["theme"] = self._settings.theme
            if self._score_keeper:
                data["hints_used"] = self._score_keeper.hints_used
                data["errors_made"] = self._score_keeper.errors_made
            os.makedirs(SAVE_DIR, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f)
            popup.dismiss()
            self._show_msg("Saved",
                           f"Game saved to Slot {idx+1}!")

        for i, btn in slot_btns.items():
            btn.bind(on_release=lambda _, idx=i: save_slot(idx))

        cancel = Button(
            text="Cancel",
            background_color=(0.55, 0.55, 0.55, 1),
            color=(1, 1, 1, 1))
        cancel.bind(on_release=popup.dismiss)
        btns.add_widget(cancel)
        content.add_widget(btns)

        self._active_popup = popup
        popup.open()

    def _get_slot_info(self, idx):
        path = os.path.join(SAVE_DIR, f"save_{idx}.json")
        try:
            with open(path) as f:
                d = json.load(f)
            sz = d.get("grid_size", "?")
            diff = d.get("difficulty", "?")
            secs = d.get("timer_secs", 0)
            return f"{sz}x{sz} {diff}\n{secs // 60:02d}:{secs % 60:02d}"
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return "Empty"

    def _show_load_dialog(self, *_):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(10))
        content.add_widget(Label(text="Select Save Slot:",
                                 font_size="16sp",
                                 size_hint_y=0.12))

        slot_row = GridLayout(
            cols=3, spacing=dp(8), size_hint_y=0.35)
        slot_btns = {}
        for i in range(3):
            info = self._get_slot_info(i)
            b = Button(
                text=f"Slot {i+1}\n{info}",
                font_size="14sp",
                background_color=C["btn_bg"],
                color=(1, 1, 1, 1))
            slot_btns[i] = b
            slot_row.add_widget(b)
        content.add_widget(slot_row)

        btns = BoxLayout(spacing=dp(8), size_hint_y=0.15)
        popup = Popup(title="Load Game", content=content,
                      size_hint=(0.75, 0.45),
                      separator_color=C["accent"])

        def load_slot(idx):
            path = os.path.join(SAVE_DIR, f"save_{idx}.json")
            try:
                with open(path) as f:
                    data = json.load(f)
                self._push_undo()
                self.grid_size = data["grid_size"]
                self.difficulty = data["difficulty"]
                self.grid_widget.load_save_data(data)
                self.grid_widget.set_theme(
                    get_theme_colors(
                        data.get("theme", "Default"),
                        data.get("dark_mode", False)))
                self.timer.start_from(
                    data.get("timer_secs", 0))
                self._score_keeper = ScoreKeeper(self.difficulty)
                self._score_keeper.hints_used = data.get(
                    "hints_used", 0)
                self._score_keeper.errors_made = data.get(
                    "errors_made", 0)
                self.diff_label.text = (
                    f"{self.grid_size}x{self.grid_size}"
                    f" {self.difficulty}")
                self._build_numpad()
                self.pencil_btn.state = "normal"
                self.grid_widget.pencil = False
                popup.dismiss()
                self._show_msg("Loaded",
                               f"Game loaded from Slot {idx+1}!")
            except (FileNotFoundError, json.JSONDecodeError,
                    KeyError) as e:
                popup.dismiss()
                self._show_msg("Load Error", str(e))

        for i, btn in slot_btns.items():
            btn.bind(on_release=lambda _, idx=i: load_slot(idx))

        cancel = Button(
            text="Cancel",
            background_color=(0.55, 0.55, 0.55, 1),
            color=(1, 1, 1, 1))
        cancel.bind(on_release=popup.dismiss)
        btns.add_widget(cancel)
        content.add_widget(btns)

        self._active_popup = popup
        popup.open()

    # ── theme dialog ──
    def _theme_dialog(self, *_):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(10))

        content.add_widget(Label(text="Theme:",
                                 font_size="16sp",
                                 size_hint_y=0.10))
        theme_row = BoxLayout(spacing=dp(6), size_hint_y=0.15)
        theme_btns = {}
        for name in THEMES:
            tc = THEMES[name]["light"]["accent"]
            b = Button(text=name, font_size="14sp",
                       background_color=tc,
                       color=(1, 1, 1, 1))
            theme_btns[name] = b
            theme_row.add_widget(b)
        content.add_widget(theme_row)

        # Dark mode toggle
        dark_row = BoxLayout(spacing=dp(8), size_hint_y=0.12)
        dark_row.add_widget(
            Label(text="Dark Mode:", font_size="14sp"))
        self.dark_toggle = ToggleButton(
            text="Dark",
            state=("down" if self._settings.dark_mode
                   else "normal"),
            font_size="14sp",
            background_color=(0.45, 0.45, 0.50, 1),
            color=(1, 1, 1, 1))
        dark_row.add_widget(self.dark_toggle)
        content.add_widget(dark_row)

        # Settings toggles
        content.add_widget(
            Label(text="Display Options:",
                  font_size="14sp", size_hint_y=0.08))
        opt_row = GridLayout(
            cols=2, spacing=dp(6), size_hint_y=0.18)
        self.opt_toggles = {}
        opts = [("Auto Advance", "auto_advance"),
                ("Highlight Same #", "highlight_same_num"),
                ("Highlight Cage", "highlight_cage"),
                ("Show Errors", "show_errors")]
        for label, key in opts:
            lbl = Label(text=label, font_size="12sp",
                        halign="right")
            tb = ToggleButton(
                text="On",
                state=("down"
                       if getattr(self._settings, key, True)
                       else "normal"),
                font_size="12sp",
                background_color=(0.45, 0.45, 0.50, 1),
                color=(1, 1, 1, 1))
            self.opt_toggles[key] = tb
            opt_row.add_widget(lbl)
            opt_row.add_widget(tb)
        content.add_widget(opt_row)

        btns = BoxLayout(spacing=dp(8), size_hint_y=0.12)
        popup = Popup(title="Theme & Settings",
                      content=content,
                      size_hint=(0.85, 0.75),
                      separator_color=C["accent"])

        def apply_theme(_):
            # Apply selected theme
            for name, btn in theme_btns.items():
                if btn.state == "down":
                    self._settings.set("theme", name)
                    break
            # Apply dark mode
            is_dark = self.dark_toggle.state == "down"
            self._settings.set("dark_mode", is_dark)
            # Apply options
            for key, tb in self.opt_toggles.items():
                val = tb.state == "down"
                self._settings.set(key, val)
            # Refresh
            self._settings.theme = self._settings.data.get(
                "theme", "Default")
            self._settings.dark_mode = is_dark
            colors = get_theme_colors(
                self._settings.theme, is_dark)
            self.grid_widget.set_theme(colors)
            self.grid_widget.settings = self._settings
            self._build_numpad()
            self._build_game_ui()
            popup.dismiss()

        apply_btn = Button(
            text="Apply",
            background_color=C["btn_bg"],
            color=(1, 1, 1, 1))
        apply_btn.bind(on_release=apply_theme)
        btns.add_widget(apply_btn)

        close = Button(
            text="Close",
            background_color=(0.55, 0.55, 0.55, 1),
            color=(1, 1, 1, 1))
        close.bind(on_release=popup.dismiss)
        btns.add_widget(close)
        content.add_widget(btns)

        # Set initial theme button state
        current_theme = self._settings.theme or "Default"
        for name, btn in theme_btns.items():
            btn.state = "down" if name == current_theme \
                else "normal"

        self._active_popup = popup
        popup.open()

    # ── stats display ──
    def _show_full_stats(self, *_):
        self._dismiss_popup()
        C = get_theme_colors(self._settings.theme,
                              self._settings.dark_mode)
        summary = self._stats.summary()

        # Add per-config breakdown
        details = "\n--- Best Times ---\n"
        for sz in (3, 4, 5, 6, 7, 8, 9):
            for diff in ("Easy", "Medium", "Hard", "Expert"):
                bt = self._stats.get_best(sz, diff)
                bs = self._stats.get_best_score(sz, diff)
                if bt is not None:
                    details += (
                        f"{sz}x{sz} {diff}: "
                        f"{bt // 60:02d}:{bt % 60:02d}"
                        f" (score: {bs or '?'})\n")

        scroll = ScrollView(size_hint_y=0.7)
        content_text = summary + "\n" + details
        inner = Label(
            text=content_text, font_size="14sp",
            color=C["value"][:3] + (1,),
            halign="left", valign="top",
            size_hint_y=None, padding=dp(10))
        inner.bind(width=lambda *x: inner.setter(
            'text_size')(inner, (inner.width, None)))
        inner.texture_update()
        inner.height = max(inner.texture_size[1], 200)
        scroll.add_widget(inner)

        content = BoxLayout(orientation="vertical",
                            padding=dp(12), spacing=dp(8))
        content.add_widget(scroll)

        btns = BoxLayout(spacing=dp(8), size_hint_y=0.15)
        popup = Popup(title="Statistics",
                      content=content,
                      size_hint=(0.70, 0.70),
                      separator_color=C["accent"])

        reset_btn = Button(
            text="Reset Stats",
            background_color=(0.72, 0.30, 0.30, 1),
            color=(1, 1, 1, 1))
        reset_btn.bind(on_release=lambda _: self._reset_stats(
            popup))
        btns.add_widget(reset_btn)

        close_btn = Button(
            text="Close",
            background_color=(0.55, 0.55, 0.55, 1),
            color=(1, 1, 1, 1))
        close_btn.bind(on_release=popup.dismiss)
        btns.add_widget(close_btn)
        content.add_widget(btns)

        self._active_popup = popup
        popup.open()

    def _reset_stats(self, popup):
        popup.dismiss()
        self._show_confirm(
            "Reset Statistics",
            "Delete all statistics?\nThis cannot be undone.",
            on_yes=self._do_reset_stats)

    def _do_reset_stats(self):
        self._stats.data = {
            "games_played": 0, "games_won": 0,
            "best_times": {}, "best_scores": {},
            "current_streak": 0, "best_streak": 0,
            "total_time": 0}
        self._stats.save()
        self._show_msg("Reset", "Statistics cleared.")


# ──────────────────────────────────────────────────────────────────────────────
#  Application
# ──────────────────────────────────────────────────────────────────────────────

class KenKenApp(App):
    def build(self):
        self.settings = Settings()
        self.stats = Stats()
        colors = get_theme_colors(self.settings.theme,
                                   self.settings.dark_mode)
        Window.clearcolor = colors["bg"]

        sm = ScreenManager(transition=FadeTransition(
            duration=0.3))
        sm.add_widget(TitleScreen())
        sm.add_widget(GameScreen())
        sm.add_widget(HowToPlayScreen())
        self.root = sm

        Window.bind(on_keyboard=self._on_key)
        return sm

    def _on_key(self, _win, key, _sc, codepoint, _mod):
        game = self.root.get_screen("game")
        gw = game.grid_widget
        if not gw.puzzle or self.root.current != "game":
            return False

        # number entry
        if codepoint and codepoint.isdigit():
            v = int(codepoint)
            if 1 <= v <= gw.puzzle.size:
                game._enter(v)
                return True
        # backspace / delete
        if key in (8, 46, 127):
            game._erase()
            return True
        # escape - deselect / go title
        if key == 27:
            if gw.sel[0] is not None:
                gw.sel = [None, None]
                gw._redraw()
            else:
                self.root.current = "title"
            return True
        # P - pencil toggle
        if codepoint and codepoint.lower() == 'p':
            state = ("normal"
                     if game.pencil_btn.state == "down"
                     else "down")
            game.pencil_btn.state = state
            return True
        # Z - undo
        if codepoint and codepoint.lower() == 'z':
            game._undo()
            return True
        # Y - redo
        if codepoint and codepoint.lower() == 'y':
            game._redo()
            return True
        # N - new game dialog
        if codepoint and codepoint.lower() == 'n':
            game._new_dialog()
            return True
        # H - hint
        if codepoint and codepoint.lower() == 'h':
            game._smart_hint()
            return True
        # arrow keys
        moves = {273: (-1, 0), 274: (1, 0),
                 275: (0, 1), 276: (0, -1)}
        if key in moves:
            dr, dc = moves[key]
            if gw.puzzle and gw.sel[0] is not None:
                n = gw.puzzle.size
                gw.sel = [max(0, min(n - 1, gw.sel[0] + dr)),
                          max(0, min(n - 1, gw.sel[1] + dc))]
                gw._redraw()
            return True
        return False

    def on_pause(self):
        """Auto-save to Slot 0 on pause."""
        try:
            game = self.root.get_screen("game")
            data = game.grid_widget.get_save_data()
            if data:
                data["timer_secs"] = game.timer.secs
                data["grid_size"] = game.grid_size
                data["difficulty"] = game.difficulty
                data["dark_mode"] = self.settings.dark_mode
                data["theme"] = self.settings.theme
                if game._score_keeper:
                    data["hints_used"] = \
                        game._score_keeper.hints_used
                    data["errors_made"] = \
                        game._score_keeper.errors_made
                os.makedirs(SAVE_DIR, exist_ok=True)
                path = os.path.join(SAVE_DIR, "save_0.json")
                with open(path, "w") as f:
                    json.dump(data, f)
        except Exception:
            pass
        return True


if __name__ == "__main__":
    KenKenApp().run()
