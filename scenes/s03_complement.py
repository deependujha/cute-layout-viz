from common import *  # noqa: F403


class S03_Complement(AlgebraScene):
    def construct(self):
        self.title("complement(A, n):  where do the OTHER copies of A go?",
                   "A + complement(A) together hit every index in [0, n) exactly once")
        A = cl.Layout((2, 2), (1, 6))
        n = 24
        C = cl.complement(A, n)

        mem = Strip(n, size=0.5).move_to(UP * 0.6)
        mlab = T("memory [0, 24)", 18, FAINT).next_to(mem, UP, buff=0.12).align_to(mem, LEFT)
        alab = T(f"A = {A}   footprint: {sorted(A.values())}", 24, PALETTE[0]).move_to(UP * 2.0)
        self.play(FadeIn(mem), FadeIn(mlab), FadeIn(alab))
        self.play(*[mem.slot(v)[0].animate.set_fill(PALETTE[0], 0.95) for v in A.values()],
                  *[set_label(mem.slot(v), "A") for v in A.values()], run_time=0.8)
        self.caption("A covers 4 slots with holes in between.  Question: by which offsets can I shift",
                     "copies of this footprint so that the copies tile all 24 slots with no overlap?", wait=2)

        offsets = C.values()
        offlab = VGroup()
        for c, off in enumerate(offsets):
            if c == 0:
                continue
            col = PALETTE[c % len(PALETTE)]
            ghost = VGroup(*[make_cell("", 0.5, col, 0.95).move_to(mem.slot(v)) for v in A.values()])
            ghost.shift(UP * 1.0)
            o = T(f"+{off}", 20, col)
            self.play(FadeIn(ghost), run_time=0.25)
            targets = [mem.slot(v + off) for v in A.values()]
            o.next_to(targets[0], DOWN, buff=0.35)
            self.play(*[g.animate.move_to(t) for g, t in zip(ghost, targets)], FadeIn(o), run_time=0.6)
            self.remove(ghost)
            for t in targets:
                t[0].set_fill(col, 0.95)
            offlab.add(o)
        o0 = T("+0", 20, PALETTE[0]).next_to(mem.slot(0), DOWN, buff=0.35)
        self.play(FadeIn(o0))
        res = T(f"complement(A, 24) = {C}", 26, ACCENT).move_to(DOWN * 1.2)
        self.play(Write(res))
        self.caption("Offsets 0,2,4 fill the gap inside A (shape 3, stride 2);",
                     "then the whole block repeats once more at +12 (shape 2, stride 12).", wait=2.5)

        # ---- the bijection table
        hdr = VGroup(T(f"A = {A}", 24, PALETTE[0]), T(f"C = complement(A, 24) = {C}", 24, ACCENT))
        hdr.arrange(RIGHT, buff=1.0).move_to(UP * 2.0)
        self.play(FadeOut(VGroup(mem, mlab, offlab, o0)), ReplacementTransform(VGroup(alab, res), hdr),
                  run_time=0.8)
        tbl = CellGrid(4, 6, label=lambda i, j: A(i) + C(j), fill=lambda i, j: PALETTE[j], size=0.6,
                       headers=True).move_to(DOWN * 0.45)
        rl = T("c  (coord of A)", 18, FAINT).next_to(tbl, LEFT, buff=0.5)
        cl_ = T("c*  (coord of complement)", 18, FAINT).next_to(tbl, UP, buff=0.4)
        self.play(FadeIn(tbl), FadeIn(rl), FadeIn(cl_))
        vals = sorted(A(i) + C(j) for i in range(4) for j in range(6))
        assert vals == list(range(24))
        self.caption("Table of A(c) + C(c*): every number 0..23 appears exactly once.",
                     "(A, complement) glued together = a bijection = '(which element, which copy)'.", wait=2.5)
        self.caption("This is the engine behind divide and product:",
                     "divide: A is a tile -> complement = where the other tiles are.   product: same, then arranged.",
                     wait=3.5)
