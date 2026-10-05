"""
Divide, on real hardware.

A 16x32 matrix is split with zipped_divide into (8,16) tiles: one CTA per tile.
Inside each tile, 32 threads (arranged 4x8) take their share of elements in two
different ways -- both are just "zipped_divide, then slice one of the two modes":

  strided  : zipped_divide(tile, (4,8))  -> ((4,8),(2,2))   thread t = slice MODE 0
             "thread t takes position t inside every 4x8 sub-tile"
  chunked  : zipped_divide(tile, (2,2))  -> ((2,2),(4,8))   thread t = slice MODE 1
             "thread t takes the whole t-th 2x2 sub-tile"

Every element records (who owns it), we copy back to the host and check it
against a plain-index formula with torch.  We run it twice -- once on a
row-major tensor, once on a column-major one -- to show the partitioning is
*logical*: it is defined on coordinates, so memory order doesn't change who
owns (i, j).

    python gpu_partition.py
"""

import torch

import cutlass
import cutlass.cute as cute
from cutlass.cute.runtime import from_dlpack

M, N = 16, 32
BLK = (8, 16)  # CTA tile
THR = (4, 8)  # 32 threads as a 4x8 grid
VAL = (2, 2)  # values per thread = BLK / THR


@cute.kernel
def partition_kernel(mBlk: cute.Tensor, mStrided: cute.Tensor, mChunked: cute.Tensor):
    bx, by, _ = cute.arch.block_idx()
    tid, _, _ = cute.arch.thread_idx()
    bid = bx + by * (M // BLK[0])

    # ---- CTA level: (elem-in-tile, which-tile); keep mode 0, pick tile (bx,by) in mode 1.
    # Note ((None, None), ...) rather than (None, ...): the latter keeps mode 0 as ONE
    # nested mode ((8,16)) of rank 1; spelling out both sub-modes gives a rank-2 (8,16).
    gBlk = cute.zipped_divide(mBlk, BLK)[((None, None), (bx, by))]  # (8,16)
    gStr = cute.zipped_divide(mStrided, BLK)[((None, None), (bx, by))]
    gChk = cute.zipped_divide(mChunked, BLK)[((None, None), (bx, by))]

    # ---- thread level, strided: ((4,8),(2,2)) -> fix MODE 0 = my position in each sub-tile
    tStr = cute.zipped_divide(gStr, THR)[(tid, None)]  # (2,2) values for this thread
    tBlk = cute.zipped_divide(gBlk, THR)[(tid, None)]

    # ---- thread level, chunked: ((2,2),(4,8)) -> fix MODE 1 = which sub-tile is mine
    tChk = cute.zipped_divide(gChk, VAL)[(None, tid)]  # (2,2) values for this thread

    for v in cutlass.range_constexpr(cute.size(tStr)):
        tStr[v] = tid
        tBlk[v] = bid
        tChk[v] = tid


@cute.jit
def launch(mBlk: cute.Tensor, mStrided: cute.Tensor, mChunked: cute.Tensor):
    if cutlass.const_expr(True):
        print("  tensor layout seen by CuTe :", mBlk.layout)
        print("  zipped_divide(tensor, BLK) :", cute.zipped_divide(mBlk.layout, BLK))
    grid = (M // BLK[0], N // BLK[1], 1)
    partition_kernel(mBlk, mStrided, mChunked).launch(grid=grid, block=(cute.size(THR), 1, 1))


def expected():
    i = torch.arange(M).view(M, 1).expand(M, N)
    j = torch.arange(N).view(1, N).expand(M, N)
    bi, bj = i // BLK[0], j // BLK[1]  # which CTA tile
    ti, tj = i % BLK[0], j % BLK[1]  # coordinate inside the tile
    blk = bi + bj * (M // BLK[0])  # colexicographic: mode 0 fastest
    # strided: thread coordinate = position inside a 4x8 sub-tile
    strided = (ti % THR[0]) + (tj % THR[1]) * THR[0]
    # chunked: thread coordinate = which 2x2 sub-tile
    chunked = (ti // VAL[0]) + (tj // VAL[1]) * THR[0]
    return blk.int(), strided.int(), chunked.int()


def show(name, t, rows=8, cols=16):
    print(f"  {name} (top-left CTA tile, {rows}x{cols}):")
    for r in range(rows):
        print("    " + " ".join(f"{int(x):2d}" for x in t[r, :cols]))


def run(order):
    def alloc():
        if order == "row-major":
            return torch.full((M, N), -1, dtype=torch.int32, device="cuda")
        return torch.full((N, M), -1, dtype=torch.int32, device="cuda").t()  # column-major view

    outs = [alloc() for _ in range(3)]
    print(f"\n=== {order} storage, torch strides {outs[0].stride()} ===")
    launch(*[from_dlpack(t) for t in outs])
    torch.cuda.synchronize()
    blk, strided, chunked = (t.cpu() for t in outs)
    exp = expected()
    for name, got, want in zip(["block id", "thread (strided)", "thread (chunked)"],
                               [blk, strided, chunked], exp):
        assert torch.equal(got, want), f"{order}: {name} mismatch\n{got}\n{want}"
    show("thread id, strided  = slice mode 0 of zipped_divide(tile, (4,8))", strided)
    show("thread id, chunked  = slice mode 1 of zipped_divide(tile, (2,2))", chunked)
    print("  block ids, whole matrix:")
    for r in range(M):
        print("    " + "".join(str(int(x)) for x in blk[r]))
    print(f"  OK: all {M * N} owners match the index formulas")
    return blk, strided, chunked


if __name__ == "__main__":
    a = run("row-major")
    b = run("column-major")
    assert all(torch.equal(x, y) for x, y in zip(a, b))
    print("\nSame owners for row-major and column-major memory: divide is LOGICAL.")
