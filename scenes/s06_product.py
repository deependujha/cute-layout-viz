from common import *  # noqa: F403


class S06_Product(AlgebraScene):
    def construct(self):
        self.title("logical_product(A, B):  A, repeated in the pattern B",
                   "= (A,  complement(A, size(A)*cosize(B)) o B)")
        A = cl.Layout((2, 2), (1, 2))
        B = cl.Layout((3, 2), (1, 3))
        P = cl.logical_product(A, B)
        C = cl.complement(A, A.size() * B.cosize())
        BP = cl.blocked_product(A, B)
        RP = cl.raked_product(A, B)

        # --- the two ingredients
        ga = CellGrid(2, 2, label=lambda i, j: A((i, j)), fill=lambda i, j: PALETTE[0], size=0.6).move_to(LEFT * 4.5 + UP * 1.0)
        la = T(f"block A = {A}", 20, PALETTE[0]).next_to(ga, UP, buff=0.25)
        gb = CellGrid(3, 2, label=lambda i, j: B((i, j)), size=0.6, headers=True).move_to(LEFT * 0.8 + UP * 0.8)
        lb = T(f"B = {B}", 20, WHITE).next_to(gb, UP, buff=0.35)
        lb2 = T("(copy #n goes at row/col of n)", 15, FAINT).next_to(lb, DOWN, buff=0.08)
        self.play(FadeIn(ga), FadeIn(la), FadeIn(gb), FadeIn(lb))
        self.caption("A is the thing to copy.  B is the arrangement of copies: a 3x2 grid of copies,",
                     "numbered column-first.", wait=2)

        cl_ = T(f"complement(A, 4*6=24) = {C}", 20, PALETTE[1]).move_to(RIGHT * 3.5 + UP * 1.9)
        cl2 = T("copy #n starts at 4n", 18, FAINT).next_to(cl_, DOWN, buff=0.12)
        self.play(FadeIn(cl_), FadeIn(cl2))
        self.play(*[set_label(gb.at(i, j), f"+{C(B((i, j)))}") for i in range(3) for j in range(2)],
                  *[gb.at(i, j)[0].animate.set_fill(PALETTE[B((i, j))], 0.95) for i in range(3) for j in range(2)])
        pl = T(f"P = {P}", 20, ACCENT).next_to(cl2, DOWN, buff=0.35)
        pl2 = T("     (block)     (copies placed by B)", 15, FAINT).next_to(pl, DOWN, buff=0.08)
        self.play(Write(pl), FadeIn(pl2))
        self.caption("complement says WHERE copies may start (offsets 0,4,8,...).  Composing it with B",
                     "arranges those offsets in B's 3x2 pattern.  Result: (inside block, which copy).", wait=3)

        # --- blocked product grid
        self.play(FadeOut(VGroup(gb, lb, cl_, cl2, pl2)), pl.animate.move_to(UP * 2.05 + RIGHT * 2.8).scale(0.9),
                  ga.animate.move_to(LEFT * 5.2 + UP * 1.0))
        R, Cc = 6, 4
        bg = CellGrid(R, Cc, label=lambda i, j: BP((i, j)), fill=lambda i, j: PALETTE[BP((i, j)) // 4],
                      size=0.55, headers=True).move_to(LEFT * 1.6 + DOWN * 0.25)
        blab = VGroup(T("blocked_product =", 16, ACCENT), T(f"{BP}", 16, ACCENT)).arrange(DOWN, buff=0.08).next_to(bg, DOWN, buff=0.2)
        self.play(FadeIn(bg), FadeIn(blab))
        self.caption("blocked: row = (inside block, which block).  Each copy of A sits together as a 2x2 block.",
                     "(colour = which copy; the copy's 4 values are 4n..4n+3)", wait=3)

        # --- raked: same 24 values, each moves to its raked position
        rg = CellGrid(R, Cc, size=0.55, headers=True).move_to(RIGHT * 3.6 + DOWN * 0.25)
        rlab = VGroup(T("raked_product =", 16, ACCENT), T(f"{RP}", 16, ACCENT)).arrange(DOWN, buff=0.08).next_to(rg, DOWN, buff=0.2)
        where = {RP((i, j)): (i, j) for i in range(R) for j in range(Cc)}
        self.play(FadeIn(rg), FadeIn(rlab))
        flies = []
        for i in range(R):
            for j in range(Cc):
                v = BP((i, j))
                m = bg.at(i, j).copy()
                self.add(m)
                flies.append(m.animate.move_to(rg.at(*where[v])))
        self.play(LaggedStart(*flies, lag_ratio=0.04), run_time=2.5)
        self.caption("raked: row = (which block, inside block).  Same copies, but their elements are",
                     "dealt out like cards: neighbours belong to DIFFERENT copies.", wait=3)
        self.caption("Same logical_product, regrouped.  blocked = each owner's stuff is contiguous;",
                     "raked = owners interleave (e.g. threads taking turns -> coalesced access).", wait=4)
