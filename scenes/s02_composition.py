from common import *  # noqa: F403


class S02_Composition(AlgebraScene):
    def construct(self):
        self.part1_1d()
        self.clear_all()
        self.part2_tiler()
        self.clear_all()
        self.part3_why_nested()

    # ------------------------------------------------------------------
    def part1_1d(self):
        self.title("composition(A, B):   R(k) = A( B(k) )", "B chooses WHICH coordinates of A.  A says WHERE they live.")
        A, B = cl.Layout(12, 2), cl.Layout(4, 3)
        R = cl.composition(A, B)

        kk = Strip(4, label=lambda k: k, size=0.5, ticks=False).move_to(UP * 1.45)
        dom = Strip(12, size=0.5).move_to(DOWN * 0.05)
        mem = Strip(24, size=0.42).move_to(DOWN * 1.75)
        labels = VGroup(
            T("k  (R's domain)", 18, FAINT).next_to(kk, LEFT, buff=0.3),
            T("A's coords", 18, FAINT).next_to(dom, LEFT, buff=0.3),
            T("memory", 18, FAINT).next_to(mem, UP, buff=0.1).align_to(mem, LEFT),
        )
        eq = VGroup(T(f"A = {A}", 24, PALETTE[0]), T(f"B = {B}", 24, PALETTE[1])).arrange(RIGHT, buff=1.0)
        eq.next_to(kk, UP, buff=0.35)
        self.play(FadeIn(kk), FadeIn(dom), FadeIn(mem), FadeIn(labels), FadeIn(eq))

        arrows = VGroup()
        for k in range(4):
            b = B(k)
            a = A(b)
            col = PALETTE[k]
            a1 = down_arrow(kk.slot(k), dom.slot(b), col)
            a2 = down_arrow(dom.slot(b), mem.slot(a), col)
            self.play(kk.slot(k)[0].animate.set_fill(col, 0.9), run_time=0.25)
            self.play(GrowArrow(a1), dom.slot(b)[0].animate.set_fill(col, 0.9),
                      set_label(dom.slot(b), b), run_time=0.45)
            self.play(GrowArrow(a2), mem.slot(a)[0].animate.set_fill(col, 0.9),
                      set_label(mem.slot(a), a), run_time=0.45)
            arrows.add(a1, a2)
        res = T(f"R = {R}", 28, ACCENT).move_to(RIGHT * 3.6 + UP * 1.45)
        self.play(Write(res))
        self.caption("Read R as: 'take 4 elements of A, 3 apart'.  B's stride 3 times A's stride 2 = 6.",
                     "R's SHAPE comes from B; A only multiplies the strides in.", wait=3)

    # ------------------------------------------------------------------
    def part2_tiler(self):
        self.title("Composing with a tiler = selecting a sub-block",
                   "a tuple tiler (b0, b1) composes mode-by-mode:  A[0] o b0,  A[1] o b1")
        A = cl.Layout((4, 6), (6, 1))
        g = CellGrid(4, 6, label=lambda i, j: A((i, j)), size=0.6, headers=True).move_to(LEFT * 3.2 + DOWN * 0.1)
        alab = T(f"A = {A}  (row-major 4x6)", 22, PALETTE[0]).next_to(g, UP, buff=0.45)
        self.play(FadeIn(g), FadeIn(alab))

        def select(tiler, tiler_txt, rows, cols, col):
            R = cl.composition(A, tiler)
            hl = [g.at(i, j)[0].animate.set_fill(col, 0.9) for i in rows for j in cols]
            t = T(f"tiler = {tiler_txt}", 24, col).move_to(RIGHT * 3.2 + UP * 1.7)
            self.play(FadeIn(t), *hl, run_time=0.8)
            out = CellGrid(len(rows), len(cols), size=0.6).move_to(RIGHT * 3.2 + DOWN * 0.1)
            flies = []
            for a, i in enumerate(rows):
                for b, j in enumerate(cols):
                    c = make_cell(A((i, j)), 0.6, col, 0.9).move_to(g.at(i, j))
                    flies.append(c.animate.move_to(out.at(a, b)))
                    out.cells[(a, b)] = c
                    self.add(c)
            self.play(LaggedStart(*flies, lag_ratio=0.06), run_time=1.2)
            r = T(f"R = {R}", 26, ACCENT).next_to(out, DOWN, buff=0.4)
            self.play(Write(r))
            for (a, b), c in out.cells.items():  # double-check against the algebra
                assert int(c[1].text) == R((a, b))
            return VGroup(t, r, *out.cells.values())

        grp = select((2, 3), "(2, 3)  = (2:1, 3:1)", range(2), range(3), PALETTE[1])
        self.caption("(2,3) means: first 2 rows, first 3 cols.  R keeps A's strides (6,1):",
                     "R is a VIEW of A's memory, no data moved.", wait=2.5)
        self.play(FadeOut(grp), *[g.at(i, j)[0].animate.set_fill(DIM, 1) for i in range(4) for j in range(6)])
        grp = select((cl.Layout(2, 2), cl.Layout(3, 2)), "(2:2, 3:2)", [0, 2], [0, 2, 4], PALETTE[2])
        self.caption("(2:2, 3:2): every other row, every other column.",
                     "Tiler strides multiply A's strides:  (2*6, 2*1) = (12, 2).", wait=3)

    # ------------------------------------------------------------------
    def part3_why_nested(self):
        self.title("Why results get nested modes", "A = (6,2):(8,2)   B = (4,3):(3,1)")
        A, B = cl.Layout((6, 2), (8, 2)), cl.Layout((4, 3), (3, 1))
        R = cl.composition(A, B)

        dom = Strip(12, label=lambda k: A(k), size=0.6).move_to(UP * 1.5)
        dlab = T("A as a 1D function  k → A(k)", 18, FAINT).next_to(dom, UP, buff=0.12).align_to(dom, LEFT)
        bg = CellGrid(4, 3, label=lambda i, j: B((i, j)), size=0.55, headers=True).move_to(LEFT * 4.7 + DOWN * 1.2)
        blab = T("B(i,j) = which k", 18, PALETTE[1]).next_to(bg, UP, buff=0.35)
        rg = CellGrid(4, 3, size=0.55, headers=True).move_to(LEFT * 1.4 + DOWN * 1.2)
        rlab = T("R(i,j) = A(B(i,j))", 18, ACCENT).next_to(rg, UP, buff=0.35)
        self.play(FadeIn(dom), FadeIn(dlab), FadeIn(bg), FadeIn(blab), FadeIn(rg), FadeIn(rlab))

        for n, (i, j) in enumerate([(i, j) for j in range(3) for i in range(4)]):
            k = B((i, j))
            rt = 0.5 if n < 3 else 0.12
            src = dom.slot(k)
            c = make_cell(A(k), 0.55, PALETTE[i], 0.9).move_to(src)
            self.play(src[0].animate.set_fill(PALETTE[i], 0.9),
                      bg.at(i, j)[0].animate.set_fill(PALETTE[i], 0.9), run_time=rt)
            self.play(c.animate.move_to(rg.at(i, j)), run_time=rt)
            assert A(k) == R((i, j))
        self.caption("Walk DOWN column 0 of R:  0, 24, 2, 26 ...", wait=1)
        col = [rg.at(i, 0) for i in range(4)]
        diffs = VGroup(*[T(d, 18, ACCENT).next_to(VGroup(col[i], col[i + 1]), RIGHT, buff=0.15)
                         .shift(RIGHT * 1.1) for i, d in enumerate(["+24", "-22", "+24"])])
        box = SurroundingRectangle(VGroup(*col), color=ACCENT, buff=0.05)
        self.play(Create(box), FadeIn(diffs, lag_ratio=0.3))
        self.caption("No single stride: B's 4 steps (stride 3) cross the edge of A's first mode (size 6).",
                     "So CuTe splits mode 0:  (2,2):(24,2) = '2 steps of 24, then 2 steps of 2'.", wait=2.5)
        res = T(f"R = {R}", 26, ACCENT).move_to(RIGHT * 3.9 + DOWN * 0.5)
        expl = VGroup(T("((2,2), 3)", 22), T("  ^mode 0 split", 18, FAINT),
                      T("((24,2), 8)", 22), T("  ^its two strides", 18, FAINT)).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        expl.next_to(res, DOWN, buff=0.3)
        self.play(Write(res), FadeIn(expl))
        self.caption("Nested mode = 'this logical dimension is really several strided pieces'.",
                     "Shape still matches B (4 x 3); you index R exactly like B.", wait=3.5)
