"""
Playground: run the real CuTe DSL on the examples from notes/layout_algebra.md and
print each result both as text and as a grid of indices.

    python explore.py              # everything
    python explore.py divide       # just one section (composition|complement|divide|product|inverse)

Workflow that makes this stick: read the PREDICT line, write your guess down,
then look at what CuTe printed.  Edit EXAMPLES freely.
"""

import sys

import cutlass.cute as cute


def L(shape, stride=None):
    return cute.make_layout(shape, stride=stride) if stride is not None else cute.make_layout(shape)


def grid(layout, offset=0, flat=False):
    """Print a layout as a table: rows = mode 0, cols = mode 1 (or one row if rank 1)."""
    shp = cute.shape(layout)
    if isinstance(shp, tuple) and len(shp) > 2:
        print(f"      (rank {len(shp)}: grid omitted)")
        return
    if isinstance(shp, tuple) and len(shp) == 2 and not flat:
        M, N = cute.size(layout, mode=[0]), cute.size(layout, mode=[1])
        rows = [[offset + cute.crd2idx((i, j), layout) for j in range(N)] for i in range(M)]
    else:
        rows = [[offset + cute.crd2idx(k, layout) for k in range(cute.size(layout))]]
    w = max(len(str(v)) for r in rows for v in r)
    for r in rows:
        print("      " + " ".join(str(v).rjust(w) for v in r))


def show(expr, result, predict=None, read=None, offset=0, flat=False):
    print(f"\n  >>> {expr}")
    if predict:
        print(f"      PREDICT: {predict}")
    print(f"      = {result}" + (f"   + offset {offset}" if offset else ""))
    grid(result, offset, flat)
    if read:
        print(f"      READ IT: {read}")


SECTIONS = {}


def section(fn):
    SECTIONS[fn.__name__] = fn
    return fn


@section
def composition():
    print("\n=== composition(A, B): R(c) = A(B(c)) — B picks, A places ===")
    show("composition(12:2, 4:3)", cute.composition(L(12, 1 * 2), L(4, 3)),
         "B takes every 3rd coord of A; A doubles it -> ?",
         "4 elements, stride 3*2 = 6.  Shape from B, stride from A*B.")
    A = L((4, 6), (6, 1))
    show("composition((4,6):(6,1), (2,3))", cute.composition(A, (2, 3)),
         "top-left 2x3 block of a row-major 4x6",
         "same strides as A: a view of A's top-left corner.")
    show("composition((4,6):(6,1), (2:2, 3:2))", cute.composition(A, (L(2, 2), L(3, 2))),
         "every other row and col",
         "strides multiply: (2*6, 2*1).")
    show("composition((6,2):(8,2), (4,3):(3,1))", cute.composition(L((6, 2), (8, 2)), L((4, 3), (3, 1))),
         "shape like B (4,3) -- but can mode 0 have a single stride?",
         "mode 0 = (2,2):(24,2): B's 4 steps cross A's size-6 mode, so it splits.")


@section
def complement():
    print("\n=== complement(A, n): offsets of the other copies of A that tile [0, n) ===")
    show("complement(4:1, 24)", cute.complement(L(4, 1), 24),
         "A covers 0..3. Where do the other copies start?", "6 copies, 4 apart.")
    show("complement(4:2, 24)", cute.complement(L(4, 2), 24),
         "A covers 0,2,4,6 (holes!)",
         "(2,3):(1,8): fill the hole with +1, then repeat the 8-wide block 3x.")
    show("complement((2,2):(1,6), 24)", cute.complement(L((2, 2), (1, 6)), 24),
         "A covers 0,1,6,7", "(3,2):(2,12): +0,+2,+4 fill the gap, then everything again at +12.")
    show("complement((4,4):(4,1), 16)", cute.complement(L((4, 4), (4, 1)), 16),
         "A already covers all 16", "1:0 -> nothing left: only one copy.")


@section
def divide():
    print("\n=== divide: re-index A as (inside tile, which tile) ===")
    show("logical_divide(24:1, 4:1)", cute.logical_divide(L(24, 1), L(4, 1)),
         "contiguous tiles of 4", "(4,6):(1,4) -> column t is tile t.")
    show("logical_divide(24:1, 4:2)", cute.logical_divide(L(24, 1), L(4, 2)),
         "tile = {0,2,4,6}; other tiles = complement(4:2,24)",
         "(4,(2,3)):(2,(1,8)) -> row: step 2 in a tile; cols: +1 then +8 between tiles.")
    A = L((8, 8), (8, 1))
    for fn in ("logical_divide", "zipped_divide", "tiled_divide", "flat_divide"):
        show(f"{fn}((8,8):(8,1), (4,4))", getattr(cute, fn)(A, (4, 4)),
             "same function, different grouping of modes" if fn != "logical_divide" else
             "each dim split in place: ((4,2),(4,2))")
    Z = cute.zipped_divide(L((8, 8), (8, 1)), (2, 4))
    show("Z = zipped_divide((8,8):(8,1), (2,4))", Z, "((tile),(rest)) = ((2,4),(4,2))",
         "column = one tile; row = same position in every tile.")
    # slicing a LAYOUT gives (sub-layout, offset); a tensor folds the offset into its pointer
    sub, off = cute.slice_and_offset(((None, None), 5), Z)
    show("Z[((None,None), 5)]   <- a CTA's tile", sub,
         "tile #5 = tile-row 1, tile-col 1", "rows 2-3, cols 4-7 of A: same strides, shifted start.",
         offset=off)
    sub, off = cute.slice_and_offset((3, None), Z)
    show("Z[(3, None)]          <- a thread's strided share", sub,
         "element #3 of every tile", "(4,2):(16,4) from offset 9: one element per tile.", offset=off)


@section
def product():
    print("\n=== product: copies of A, arranged by B ===")
    A, B = L((2, 2), (1, 2)), L((3, 2), (1, 3))
    show("logical_product((2,2):(1,2), (3,2):(1,3))", cute.logical_product(A, B),
         "(A, complement(A,24) o B)", "mode 0 = inside block, mode 1 = which copy (copies start at 4n).")
    show("blocked_product(A, B)", cute.blocked_product(A, B),
         "6x4, each 2x2 copy contiguous", "row mode = (inside block 2, which block 3).")
    show("raked_product(A, B)", cute.raked_product(A, B),
         "6x4, copies interleaved", "row mode = (which block 3, inside block 2).")
    show("tile_to_shape((2,2):(1,2), (6,4))", cute.tile_to_shape(A, (6, 4), (0, 1)),
         "grow a small atom to fill a shape", "same picture as blocked_product with a compact B.")


@section
def inverse():
    print("\n=== inverses: memory index -> coordinate ===")
    show("right_inverse((2,4):(4,1))", cute.right_inverse(L((2, 4), (4, 1))),
         "who lives at slot i?", "i = a + 4b -> coordinate 2a + b.", flat=True)
    show("left_inverse((2,2):(1,4))", cute.left_inverse(L((2, 2), (1, 4))),
         "undo L on 0,1,4,5", "slots 2,3,6,7 are never hit: their values are junk.", flat=True)
    show("right_inverse((2,2):(1,4))", cute.right_inverse(L((2, 2), (1, 4))),
         "longest run 0,1,2,... L hits", "2:1 -> a 2-wide vector is the most you can do.", flat=True)
    show("coalesce((4,2):(1,4))", cute.coalesce(L((4, 2), (1, 4))),
         "same function, fewer modes?", "8:1 -> it's just contiguous.")


WANT = sys.argv[1:] or list(SECTIONS)


@cute.jit
def main():
    for name in WANT:
        SECTIONS[name]()


if __name__ == "__main__":
    main()
