"""Shared drawing helpers for the layout-algebra scenes."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from manim import *  # noqa: E402,F401,F403

import layout as cl  # noqa: E402,F401

MONO = "DejaVu Sans Mono"
BG = "#14161c"
DIM = "#2a2f3a"
FAINT = "#6b7280"
ACCENT = "#FFD166"
# 8 colors that stay distinguishable on a dark background
PALETTE = ["#4C9BE8", "#F28E2B", "#59A14F", "#E15759",
           "#B07AA1", "#EDC948", "#76B7B2", "#FF9DA7"]

config.background_color = BG


def T(s, size=28, color=WHITE, **kw):
    return Text(str(s), font=MONO, font_size=size, color=color, **kw)


def make_cell(label, size=0.5, fill=DIM, opacity=1.0, text_color=WHITE):
    sq = Square(side_length=size, stroke_color="#c9ced6", stroke_width=1.2,
                fill_color=fill, fill_opacity=opacity)
    s = str(label)
    fs = size * (40 if len(s) <= 1 else 34 if len(s) == 2 else 26)
    txt = T(s, fs, text_color).move_to(sq) if s != "" else VGroup().move_to(sq)
    txt.set_z_index(1)  # numbers always draw above any square, even mid-animation
    return VGroup(sq, txt)


def set_label(cell, label, color=WHITE):
    """Return an animation that rewrites the number inside a cell."""
    new = make_cell(label, cell[0].side_length)[1].set_color(color).move_to(cell[0])
    new.set_z_index(cell[1].z_index)
    return Transform(cell[1], new)


class CellGrid(VGroup):
    """rows x cols squares; label(i,j) and fill(i,j) are callables."""

    def __init__(self, rows, cols, label=lambda i, j: "", fill=lambda i, j: DIM,
                 size=0.5, headers=False, header_color=FAINT):
        super().__init__()
        self.rows, self.cols, self.size = rows, cols, size
        self.cells = {}
        body = VGroup()
        for i in range(rows):
            for j in range(cols):
                c = make_cell(label(i, j), size, fill(i, j))
                c.move_to(RIGHT * j * size + DOWN * i * size)
                self.cells[(i, j)] = c
                body.add(c)
        self.body = body
        self.add(body)
        self.row_headers = VGroup()
        self.col_headers = VGroup()
        if headers:
            hs = size * 26
            for i in range(rows):
                self.row_headers.add(T(i, hs, header_color).next_to(self.cells[(i, 0)], LEFT, buff=0.12))
            for j in range(cols):
                self.col_headers.add(T(j, hs, header_color).next_to(self.cells[(0, j)], UP, buff=0.1))
            self.add(self.row_headers, self.col_headers)
        self.move_to(ORIGIN)

    def at(self, i, j):
        return self.cells[(i, j)]


class Strip(CellGrid):
    """A 1-row grid that represents linear memory / a 1D domain, with index ticks."""

    def __init__(self, n, label=lambda k: "", fill=lambda k: DIM, size=0.42, ticks=True):
        super().__init__(1, n, lambda i, j: label(j), lambda i, j: fill(j), size=size)
        self.n = n
        self.ticks = VGroup()
        if ticks:
            for k in range(n):
                self.ticks.add(T(k, size * 24, FAINT).next_to(self.cells[(0, k)], DOWN, buff=0.06))
            self.add(self.ticks)

    def slot(self, k):
        return self.cells[(0, k)]


class AlgebraScene(Scene):
    """Scene with a persistent title + one swappable caption line at the bottom."""

    def setup(self):
        self._caption = None
        self._title = None

    def title(self, text, sub=None):
        grp = VGroup(T(text, 30, ACCENT))
        if sub:
            grp.add(T(sub, 20, FAINT))
        grp.arrange(DOWN, buff=0.12)
        if grp.width > 13.2:
            grp.scale_to_fit_width(13.2)
        grp.to_edge(UP, buff=0.3)
        anims = [FadeIn(grp, shift=DOWN * 0.2)]
        if self._title is not None:
            anims.append(FadeOut(self._title))
        self.play(*anims, run_time=0.8)
        self._title = grp
        return grp

    def caption(self, *lines, wait=1.5, color=WHITE, size=22):
        grp = VGroup(*[T(l, size, color) for l in lines]).arrange(DOWN, buff=0.12)
        if grp.width > 13.2:
            grp.scale_to_fit_width(13.2)
        grp.to_edge(DOWN, buff=0.35)
        anims = [FadeIn(grp, shift=UP * 0.15)]
        if self._caption is not None:
            anims.append(FadeOut(self._caption))
        self.play(*anims, run_time=0.6)
        self._caption = grp
        if wait:
            self.wait(wait)
        return grp

    def clear_all(self, keep_title=False):
        keep = {self._title} if keep_title else set()
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=0.6)
        self._caption = None
        if not keep_title:
            self._title = None


def arrow(a, b, color=ACCENT, buff=0.06, width=2.5):
    return Arrow(a.get_center() if hasattr(a, "get_center") else a,
                 b.get_center() if hasattr(b, "get_center") else b,
                 buff=buff, stroke_width=width, color=color,
                 max_tip_length_to_length_ratio=0.12, tip_length=0.15)


def down_arrow(a, b, color=ACCENT):
    """Arrow from bottom of a to top of b."""
    return Arrow(a.get_bottom(), b.get_top(), buff=0.04, stroke_width=2.5, color=color,
                 max_tip_length_to_length_ratio=0.2, tip_length=0.14)
