from common import *  # noqa: F403


class S05_ZippedDivide2D(AlgebraScene):
    def construct(self):
        self.title("zipped_divide(A, (2,4))  →  ((tile), (rest))",
                   "a tuple tiler divides each mode; zipped gathers the tile modes and the rest modes")
        A = cl.Layout((8, 8), (8, 1))
        tile = (2, 4)
        Z = cl.zipped_divide(A, tile)  # ((2,4),(4,2)):((8,1),(16,4))
        ntile_r, ntile_c = 8 // tile[0], 8 // tile[1]

        def tid(i, j):  # which tile (colexicographic over (4,2))
            return i // tile[0] + (j // tile[1]) * ntile_r

        def pos(i, j):  # position inside tile (colex over (2,4))
            return i % tile[0] + (j % tile[1]) * tile[0]

        g = CellGrid(8, 8, label=lambda i, j: A((i, j)), size=0.48, headers=True).move_to(LEFT * 3.6 + DOWN * 0.35)
        glab = T(f"A = {A}  (8x8 row-major)", 20, FAINT).next_to(g, UP, buff=0.3)
        self.play(FadeIn(g), FadeIn(glab))
        self.play(LaggedStart(*[g.at(i, j)[0].animate.set_fill(PALETTE[tid(i, j)], 0.95)
                                for j in range(8) for i in range(8)], lag_ratio=0.01), run_time=1.5)
        self.caption("(2,4) cuts every 2 rows and every 4 columns: 4 x 2 = 8 tiles (colour = tile).", wait=1.5)

        out = CellGrid(8, 8, size=0.48, headers=True).move_to(RIGHT * 3.4 + DOWN * 0.35)
        rlab = T("mode 0\nelem in tile\n(2,4)", 16, FAINT).next_to(out, LEFT, buff=0.35)
        clab = T("mode 1: which tile (4,2)", 16, FAINT).next_to(out, UP, buff=0.3)
        self.play(FadeIn(out), FadeIn(rlab), FadeIn(clab))
        flies = []
        for j in range(8):
            for i in range(8):
                v = A((i, j))
                r, c = pos(i, j), tid(i, j)
                assert Z((r, c)) == v  # same function as CuTe's zipped_divide
                m = make_cell(v, 0.48, PALETTE[c], 0.95).move_to(g.at(i, j))
                out.cells[(r, c)] = m
                self.add(m)
                flies.append(m.animate.move_to(out.body[r * 8 + c]))
        self.play(LaggedStart(*flies, lag_ratio=0.012), run_time=2.5)
        res = T(f"{Z}", 26, ACCENT).next_to(out, DOWN, buff=0.3)
        self.play(Write(res))
        self.caption("Each COLUMN is one tile.  Mode-0 strides (8,1) are A's own: walking inside a tile",
                     "is walking A.  Mode-1 strides (16,4) = tile height 2 x 8 and tile width 4 x 1.", wait=3)

        # ---- slicing mode 1: a CTA's view
        t = 5
        colbox = SurroundingRectangle(VGroup(*[out.cells[(r, t)] for r in range(8)]), color=WHITE, buff=0.03)
        src = VGroup(*[g.at(i, j) for i in range(8) for j in range(8) if tid(i, j) == t])
        srcbox = SurroundingRectangle(src, color=WHITE, buff=0.03)
        self.play(Create(colbox), Create(srcbox))
        self.caption(f"Z[(None, {t})]  fixes mode 1 → one whole tile.",
                     "That's how a CTA grabs its block:  gA = zipped_divide(mA, tile)[(None, bid)]", wait=3)
        self.play(FadeOut(colbox), FadeOut(srcbox))

        # ---- slicing mode 0: a thread's view
        e = 3
        rowbox = SurroundingRectangle(VGroup(*[out.cells[(e, c)] for c in range(8)]), color=WHITE, buff=0.03)
        hits = [g.at(i, j) for i in range(8) for j in range(8) if pos(i, j) == e]
        boxes = VGroup(*[SurroundingRectangle(h, color=WHITE, buff=0.02, stroke_width=4) for h in hits])
        self.play(Create(rowbox), Create(boxes))
        self.caption(f"Z[({e}, None)]  fixes mode 0 → element #{e} of EVERY tile: a strided set.",
                     "That's a thread's share when the 'tile' is the thread layout (see gpu_partition.py).", wait=3.5)
        self.play(FadeOut(rowbox), FadeOut(boxes))
        self.caption("logical / zipped / tiled / flat_divide = same function, different mode grouping:",
                     "logical ((2,4),(4,2))  zipped ((2,4),(4,2))  tiled ((2,4),4,2)  flat (2,4,4,2)  [shapes]",
                     wait=4)
