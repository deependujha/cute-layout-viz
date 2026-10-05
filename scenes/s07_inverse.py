from common import *  # noqa: F403


class S07_Inverses(AlgebraScene):
    def construct(self):
        self.bijective()
        self.clear_all()
        self.with_holes()

    def bijective(self):
        self.title("right_inverse / left_inverse:  index → coordinate",
                   "L maps coordinate k to memory.  The inverse answers: 'who lives at memory slot i?'")
        L = cl.Layout((2, 4), (4, 1))
        Ri = cl.right_inverse(L)
        dom = Strip(8, label=lambda k: k, size=0.6, ticks=False).move_to(UP * 1.2)
        mem = Strip(8, size=0.6, ticks=False).move_to(DOWN * 0.9)
        labs = VGroup(T("coord k", 18, FAINT).next_to(dom, LEFT, buff=0.4),
                      T("memory i", 18, FAINT).next_to(mem, LEFT, buff=0.4),
                      T(f"L = {L}", 24, PALETTE[0]).next_to(dom, RIGHT, buff=0.6))
        self.play(FadeIn(dom), FadeIn(mem), FadeIn(labs))
        arr = VGroup()
        for k in range(8):
            v = L(k)
            arr.add(Arrow(dom.slot(k).get_bottom(), mem.slot(v).get_top(), buff=0.05, stroke_width=2.5,
                          color=PALETTE[k % 8], tip_length=0.15))
        self.play(LaggedStart(*[GrowArrow(a) for a in arr], lag_ratio=0.12),
                  *[set_label(mem.slot(L(k)), f"k{k}") for k in range(8)], run_time=2)
        self.caption("Read memory left to right: k0, k2, k4, k6, k1, ...  That sequence IS the inverse.", wait=2)
        ri = T(f"right_inverse(L) = {Ri}", 24, ACCENT).next_to(mem, DOWN, buff=0.5)
        rev = VGroup(*[Arrow(mem.slot(L(k)).get_top(), dom.slot(k).get_bottom(), buff=0.05, stroke_width=2.5,
                             color=PALETTE[k % 8], tip_length=0.15) for k in range(8)])
        for i in range(8):
            assert L(Ri(i)) == i
        self.play(ReplacementTransform(arr, rev), Write(ri), run_time=1.5)
        self.caption("Bijective L: left and right inverse are the same thing, a permutation back.",
                     "(4,2):(2,1) reads 'i = a + 4b  ->  k = 2a + b'.", wait=3)

    def with_holes(self):
        self.title("When L has holes, the two inverses differ",
                   "L = (2,2):(1,4) touches memory {0,1,4,5} out of 8")
        L = cl.Layout((2, 2), (1, 4))
        Li, Ri = cl.left_inverse(L), cl.right_inverse(L)
        mem = Strip(8, size=0.62).move_to(UP * 0.9)
        hits = set(L.values())
        self.play(FadeIn(mem))
        self.play(*[mem.slot(L(k))[0].animate.set_fill(PALETTE[k], 0.95) for k in range(4)],
                  *[set_label(mem.slot(L(k)), f"k{k}") for k in range(4)])

        back = CellGrid(1, 8, label=lambda i, j: Li(j), size=0.62,
                        fill=lambda i, j: PALETTE[Li(j)] if j in hits else DIM).move_to(DOWN * 0.6)
        bl = T(f"left_inverse(L) = {Li}", 22, ACCENT).next_to(back, DOWN, buff=0.3)
        mlab = T("L's image", 16, FAINT).next_to(mem, LEFT, buff=0.3)
        blab = T("Li(i)", 16, FAINT).next_to(back, LEFT, buff=0.3)
        self.add(mlab, blab)
        for k in range(4):
            assert Li(L(k)) == k
        self.play(FadeIn(back), Write(bl))
        self.caption("left_inverse:  Li(L(k)) == k.  It UNDOES L on every slot L touches (coloured).",
                     "Grey slots are never written by L, so whatever Li says there is meaningless.", wait=3)

        rr = SurroundingRectangle(VGroup(mem.slot(0), mem.slot(1)), color=WHITE, buff=0.04, stroke_width=4)
        rl = T(f"right_inverse(L) = {Ri}", 22, ACCENT).next_to(bl, DOWN, buff=0.35)
        self.play(Create(rr), Write(rl))
        self.caption("right_inverse covers only the longest run 0,1,2,... that L hits contiguously:",
                     "size(right_inverse) = 2 = how many elements you can move with ONE vector access.", wait=3)
        self.caption("That's what max_common_vector / auto-vectorised copies compute under the hood:",
                     "coalesce(composition(src, right_inverse(dst)))  -> its first stride-1 mode.", wait=4)
