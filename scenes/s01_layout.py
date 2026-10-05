from common import *  # noqa: F403


class S01_LayoutIsAFunction(AlgebraScene):
    def construct(self):
        self.title("A layout is a function:  coordinate  →  index")

        def show_layout(L, name, color_by):
            M, N = L.shape
            label = T(f"L = {L}", 28, ACCENT)
            formula = T(f"L(i,j) = i*{L.stride[0]} + j*{L.stride[1]}", 22)
            hdr = VGroup(label, formula).arrange(DOWN, buff=0.15).move_to(UP * 2.35 + LEFT * 3.3)
            grid = CellGrid(M, N, size=0.62, headers=True).move_to(LEFT * 3.3 + DOWN * 0.1)
            gi = T("i", 22, FAINT).next_to(grid.row_headers, LEFT, buff=0.15)
            gj = T("j", 22, FAINT).next_to(grid.col_headers, UP, buff=0.08)
            mem = Strip(M * N, size=0.5).move_to(DOWN * 2.4)
            mem_lbl = T("memory", 20, FAINT).next_to(mem, UP, buff=0.12).align_to(mem, LEFT)
            self.play(FadeIn(hdr), FadeIn(grid), FadeIn(gi), FadeIn(gj),
                      FadeIn(mem), FadeIn(mem_lbl), run_time=0.8)
            return hdr, grid, mem, VGroup(hdr, grid, gi, gj, mem, mem_lbl)

        def walk(L, grid, mem, slow=4, color_by=lambda i, j: j):
            M, N = L.shape
            info = None
            for k in range(M * N):
                i, j = cl.idx2crd(k, L.shape)
                v = L((i, j))
                cell, slot = grid.at(i, j), mem.slot(v)
                col = PALETTE[color_by(i, j)]
                new_info = T(f"k={k:<2}  →  (i,j)=({i},{j})  →  L={v}", 24).move_to(RIGHT * 3.2 + UP * 0.6)
                fly = cell.copy()
                rt = 0.55 if k < slow else 0.18
                anims = [cell[0].animate.set_fill(col, 0.9), set_label(cell, v)]
                anims.append(FadeIn(new_info) if info is None else Transform(info, new_info))
                self.play(*anims, run_time=rt)
                fly = make_cell(v, cell[0].side_length, col, 0.9).move_to(cell)
                self.play(fly.animate.move_to(slot).scale(slot[0].side_length / cell[0].side_length),
                          run_time=rt)
                self.remove(fly)
                slot[0].set_fill(col, 0.9)
                slot.remove(slot[1])
                slot.add(make_cell(v, slot[0].side_length)[1].move_to(slot[0]))
                if info is None:
                    info = new_info
            return info

        # ---- 1) row-major
        L = cl.Layout((4, 3), (3, 1))
        _, grid, mem, grp = show_layout(L, "row-major", None)
        self.caption("Coordinates are visited column-first (colexicographic):  k = i + 4*j",
                     "each one is sent to  i*3 + j*1  in memory.  Colour = column j.", wait=0.5)
        info = walk(L, grid, mem)
        self.caption("Shape (4,3) = the coordinate space.   Stride (3,1) = where each step lands.",
                     "Here moving down a column jumps 3 slots: rows are contiguous.", wait=2.5)
        self.play(FadeOut(grp), FadeOut(info), run_time=0.6)

        # ---- 2) same shape, other strides
        L = cl.Layout((4, 3), (1, 4))
        _, grid, mem, grp = show_layout(L, "col-major", None)
        self.caption("Same coordinates, different strides (1,4):", wait=0.3)
        info = walk(L, grid, mem, slow=1)
        self.caption("Only the strides changed → only *where things land* changed.",
                     "Every algebra op below builds a new function out of old ones.", wait=3)
