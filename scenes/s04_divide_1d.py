from common import *  # noqa: F403


class S04_LogicalDivide1D(AlgebraScene):
    def construct(self):
        self.title("logical_divide(A, T) = composition(A, (T, complement(T, size A)))",
                   "the tiler T picks one tile; its complement enumerates all the other tiles")
        A = cl.Layout(24, 1)
        for tiler, wait_extra in [(cl.Layout(4, 1), 0), (cl.Layout(4, 2), 1.5)]:
            self.one(A, tiler, wait_extra)

    def one(self, A, Tl, wait_extra):
        n = A.size()
        Cm = cl.complement(Tl, n)
        D = cl.logical_divide(A, Tl)
        ntiles = Cm.size()

        mem = Strip(n, label=lambda k: k, size=0.5, ticks=False).move_to(UP * 1.35)
        hdr = VGroup(T(f"A = {A}", 22, FAINT), T(f"T = {Tl}", 22, PALETTE[0]),
                     T(f"complement(T, {n}) = {Cm}", 22, PALETTE[1])).arrange(RIGHT, buff=0.7).move_to(UP * 2.2)
        self.play(FadeIn(mem), FadeIn(hdr[0]))
        self.play(FadeIn(hdr[1]), *[mem.slot(A(v))[0].animate.set_fill(PALETTE[0], 0.95) for v in Tl.values()])
        self.caption(f"T picks coordinates {Tl.values()} of A: that's tile #0.", wait=1.2)
        self.play(FadeIn(hdr[2]))
        for t, off in enumerate(Cm.values()):
            if t == 0:
                continue
            self.play(*[mem.slot(A(v + off))[0].animate.set_fill(PALETTE[t % 8], 0.95)
                        for v in Tl.values()], run_time=0.35)
        self.caption(f"complement(T) = tile starts {Cm.values()}: the other {ntiles - 1} tiles.", wait=1.5)

        # rearrange into (inside tile, which tile)
        grid = CellGrid(Tl.size(), ntiles, size=0.5, headers=True).move_to(DOWN * 1.15)
        rlab = T("mode 0:\ninside tile", 16, FAINT).next_to(grid, LEFT, buff=0.4)
        clab = T("mode 1: which tile", 16, FAINT).next_to(grid, RIGHT, buff=0.4)
        self.play(FadeIn(grid), FadeIn(rlab), FadeIn(clab), run_time=0.5)
        flies = []
        for t in range(ntiles):
            for e in range(Tl.size()):
                v = D((e, t))
                src = mem.slot(v)
                c = make_cell(v, 0.5, PALETTE[t % 8], 0.95).move_to(src)
                self.add(c)
                flies.append(c.animate.move_to(grid.at(e, t)))
        self.play(LaggedStart(*flies, lag_ratio=0.03), run_time=2)
        res = T(f"logical_divide(A, T) = {D}", 26, ACCENT).next_to(grid, DOWN, buff=0.3)
        self.play(Write(res))
        if Tl.stride == 1:
            self.caption("Contiguous tiler: tiles are plain chunks. Mode 1 stride 4 = 'next tile is 4 further'.",
                         wait=2.5)
        else:
            self.caption("Strided tiler: each tile is 4 elements 2 apart; tiles interleave in pairs.",
                         "Read the result: (4, (2,3)) : (2, (1,8)) = 4 inside a tile, step 2 | "
                         "6 tiles: +1, then +8.", wait=2.5 + wait_extra)
            self.caption("Same 24 elements, just re-indexed as (inside-tile, which-tile).",
                         "Nothing moved in memory; the layout is a new way to NAME the same slots.", wait=3)
        self.clear_all(keep_title=True)
