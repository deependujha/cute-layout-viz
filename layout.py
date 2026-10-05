"""
A tiny, readable, pure-Python model of CuTe layout algebra.

Why this exists:
  * The manim scenes need layout math but live in a separate numpy-2 env that
    can't import cutlass.  This file has zero dependencies.
  * Reading ~150 lines of the actual algorithms is the fastest way to stop
    treating the algebra as magic.
  * `verify.py` checks every function here against the real CuTe DSL, so the
    numbers in the animations are CuTe's numbers.

Conventions (same as CuTe):
  * shape / stride are ints or (nested) tuples of the same structure.
  * Coordinates are colexicographic: the LEFTMOST mode varies fastest.
"""

from __future__ import annotations

from functools import reduce
from itertools import product as _cartesian


# --------------------------------------------------------------------------
# int-tuple helpers
# --------------------------------------------------------------------------
def is_tuple(x):
    return isinstance(x, tuple)


def flatten(t):
    if not is_tuple(t):
        return (t,)
    return tuple(x for e in t for x in flatten(e))


def prod(t):
    return reduce(lambda a, b: a * b, flatten(t), 1)


def prefix_product(t, init=1):
    """Compact column-major strides for shape t:  (4,(2,3)) -> (1,(4,8))."""
    if not is_tuple(t):
        return init
    out = []
    for e in t:
        out.append(prefix_product(e, init))
        init *= prod(e)
    return tuple(out)


def idx2crd(idx, shape):
    """Linear index -> natural coordinate (colexicographic)."""
    if not is_tuple(shape):
        return idx
    out = []
    for s in shape:
        out.append(idx2crd(idx % prod(s), s))
        idx //= prod(s)
    return tuple(out)


def crd2idx(crd, shape, stride):
    """Coordinate (int, tuple, or nested) -> index = <coord, stride>."""
    if is_tuple(crd):
        return sum(crd2idx(c, s, d) for c, s, d in zip(crd, shape, stride))
    if is_tuple(shape):  # an int fed into a multi-mode: unfold it first
        return crd2idx(idx2crd(crd, shape), shape, stride)
    return crd * stride


def fmt(t):
    """CuTe-style printing: no spaces, (x) for 1-tuples is just x."""
    if not is_tuple(t):
        return str(t)
    return "(" + ",".join(fmt(e) for e in t) + ")"


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
class Layout:
    def __init__(self, shape, stride=None):
        self.shape = shape
        self.stride = prefix_product(shape) if stride is None else stride

    # --- a layout is a function ---------------------------------------
    def __call__(self, crd):
        return crd2idx(crd, self.shape, self.stride)

    def size(self):  # how many coordinates (domain size)
        return prod(self.shape)

    def cosize(self):  # how far into memory it reaches (codomain size)
        return self(self.size() - 1) + 1

    def rank(self):
        return len(self.shape) if is_tuple(self.shape) else 1

    def __getitem__(self, i):  # i-th top-level mode
        if is_tuple(self.shape):
            return Layout(self.shape[i], self.stride[i])
        assert i == 0
        return self

    def __iter__(self):
        return (self[i] for i in range(self.rank()))

    def values(self):
        """[L(0), L(1), ...] in colexicographic coordinate order."""
        return [self(i) for i in range(self.size())]

    def __eq__(self, o):
        return isinstance(o, Layout) and (self.shape, self.stride) == (o.shape, o.stride)

    def __repr__(self):
        return f"{fmt(self.shape)}:{fmt(self.stride)}"


def make_layout(*layouts):
    """Concatenate layouts as modes:  make_layout(A, B) = (A, B)."""
    if len(layouts) == 1:
        return layouts[0]
    return Layout(tuple(l.shape for l in layouts), tuple(l.stride for l in layouts))


def as_layout(x):
    return x if isinstance(x, Layout) else Layout(x)


# --------------------------------------------------------------------------
# coalesce: same function, fewest modes
# --------------------------------------------------------------------------
def coalesce(L, profile=None):
    if profile is not None and is_tuple(profile):  # by-mode coalesce
        return make_layout(*(coalesce(L[i]) for i in range(L.rank())))
    shapes, strides = [], []
    for s, d in zip(flatten(L.shape), flatten(L.stride)):
        if s == 1:
            continue  # size-1 modes do nothing
        if shapes and strides[-1] * shapes[-1] == d:
            shapes[-1] *= s  # (s0,s1):(d0,s0*d0)  ==  s0*s1:d0
        else:
            shapes.append(s)
            strides.append(d)
    if not shapes:
        return Layout(1, 0)
    if len(shapes) == 1:
        return Layout(shapes[0], strides[0])
    return Layout(tuple(shapes), tuple(strides))


# --------------------------------------------------------------------------
# composition: R(c) = A(B(c))
# --------------------------------------------------------------------------
def composition(A, B):
    # A tuple tiler means "compose mode-by-mode":  (B0, B1) applies B0 to A[0] ...
    if is_tuple(B):
        assert len(B) <= A.rank()
        modes = [composition(A[i], B[i]) for i in range(len(B))]
        modes += [A[i] for i in range(len(B), A.rank())]  # untouched modes pass through
        return make_layout(*modes)
    B = as_layout(B)

    # B with several modes: compose each one; result keeps B's structure.
    if is_tuple(B.shape):
        return make_layout(*(composition(A, b) for b in B))

    # B is a single mode  s:d  -> "take s elements of A, d apart".
    s, d = B.shape, B.stride
    if d == 0:
        return Layout(s, 0)
    flatA = coalesce(A)
    a_shapes, a_strides = flatten(flatA.shape), flatten(flatA.stride)
    out_s, out_d = [], []
    for a_s, a_d in zip(a_shapes[:-1], a_strides[:-1]):
        # Walk through A's modes, fastest first.  First skip d elements at a
        # time ("divide out" the stride), then take as many as fit ("mod out").
        assert a_s % d == 0 or d % a_s == 0, f"divisibility fails: {A} o {B}"
        take = min(max(1, a_s // d), s)
        assert s % take == 0, f"divisibility fails: {A} o {B}"
        if take != 1:
            out_s.append(take)
            out_d.append(d * a_d)
        s //= take
        d = -(-d // a_s)  # ceil div: stride left over for the next mode
    if s != 1 or not out_s:
        out_s.append(s)
        out_d.append(d * a_strides[-1] if s != 1 else 0)  # CuTe writes size-1 strides as 0
    if len(out_s) == 1:
        return Layout(out_s[0], out_d[0])
    return Layout(tuple(out_s), tuple(out_d))


# --------------------------------------------------------------------------
# complement: the layout of "where copies of A go" to fill [0, cotarget)
# --------------------------------------------------------------------------
def complement(A, cotarget=1):
    A = as_layout(A)
    out_s, out_d = [], []
    cur = 1  # everything in [0, cur) is already covered
    for d, s in sorted(zip(flatten(A.stride), flatten(A.shape))):
        if d == 0 or s == 1:
            continue
        assert d % cur == 0, f"{A} has no complement (overlapping/odd strides)"
        out_s.append(d // cur)  # how many copies fit in the gap below stride d
        out_d.append(cur)
        cur = s * d
    out_s.append(-(-cotarget // cur))  # then repeat the whole footprint
    out_d.append(cur)
    return coalesce(Layout(tuple(out_s), tuple(out_d)))


# --------------------------------------------------------------------------
# divide = composition with (tiler, complement(tiler))
# --------------------------------------------------------------------------
def logical_divide(A, tiler):
    if is_tuple(tiler):  # by-mode
        modes = [logical_divide(A[i], tiler[i]) for i in range(len(tiler))]
        modes += [A[i] for i in range(len(tiler), A.rank())]
        return make_layout(*modes)
    T = as_layout(tiler)
    return composition(A, make_layout(T, complement(T, A.size())))


def zipped_divide(A, tiler):
    D = logical_divide(A, tiler)
    if not is_tuple(tiler):
        return D
    r = len(tiler)
    tile = make_layout(*(D[i][0] for i in range(r)))
    rest = make_layout(*([D[i][1] for i in range(r)] + [D[i] for i in range(r, D.rank())]))
    return make_layout(tile, rest)


def tiled_divide(A, tiler):
    Z = zipped_divide(A, tiler)
    return make_layout(Z[0], *Z[1]) if is_tuple(Z[1].shape) else Z


def flat_divide(A, tiler):
    Z = zipped_divide(A, tiler)
    return make_layout(*Z[0], *Z[1])


# --------------------------------------------------------------------------
# product = A, plus copies of A arranged by B
# --------------------------------------------------------------------------
def logical_product(A, B):
    B = as_layout(B)
    copies = complement(A, A.size() * B.cosize())  # all slots a copy of A can start at
    return make_layout(A, composition(copies, B))  # ...arranged in B's pattern


def _pad(L, r):
    return make_layout(*[L[i] for i in range(L.rank())] + [Layout(1, 0)] * (r - L.rank()))


def _zip_modes(X, Y, r):
    return make_layout(*(make_layout(X[i], Y[i]) for i in range(r)))


def _drop_ones(L):
    """Remove size-1 sub-modes inside each top-level mode (no merging)."""
    modes = []
    for m in L:
        sd = [(s, d) for s, d in zip(flatten(m.shape), flatten(m.stride)) if s != 1]
        if not sd:
            modes.append(Layout(1, 0))
        elif len(sd) == 1:
            modes.append(Layout(*sd[0]))
        else:
            modes.append(Layout(tuple(s for s, _ in sd), tuple(d for _, d in sd)))
    return make_layout(*modes)


# blocked / raked are the SAME logical_product, regrouped per dimension.
# (These match what the CuTe DSL prints; C++ CuTe may simplify a bit more.)
def blocked_product(A, B):
    r = max(A.rank(), B.rank())
    A, B = _pad(A, r), _pad(B, r)
    P = logical_product(A, B)  # (block, copies)
    return _zip_modes(P[0], P[1], r)  # dim i = (inside block, which block)


def raked_product(A, B):
    r = max(A.rank(), B.rank())
    A, B = _pad(A, r), _pad(B, r)
    P = logical_product(A, B)
    return _drop_ones(_zip_modes(P[1], P[0], r))  # dim i = (which block, inside block)


# --------------------------------------------------------------------------
# inverses
# --------------------------------------------------------------------------
def right_inverse(L):
    """R with L(R(i)) == i for i in [0, size(R)).  size(R) = contiguous prefix."""
    flat_s, flat_d = flatten(L.shape), flatten(L.stride)
    out_s, out_d = [], []
    cur = 1
    for d, s, rd in sorted(zip(flat_d, flat_s, flatten(prefix_product(L.shape)))):
        if s == 1:
            continue
        if d != cur:
            break  # hole in memory -> contiguous prefix ends here
        out_s.append(s)
        out_d.append(rd)
        cur = s * d
    if not out_s:
        return Layout(1, 0)
    return coalesce(Layout(tuple(out_s), tuple(out_d)))


def left_inverse(L):
    """R with R(L(c)) == c for every coordinate c of L.

    Walk L's modes in stride order.  Index i in memory decomposes as
    i = sum(k_m * stride_m); R reads off each k_m and multiplies by that mode's
    coordinate stride.  Memory slots L never hits map somewhere arbitrary.
    """
    modes = sorted((d, s, rd) for s, d, rd in zip(flatten(L.shape), flatten(L.stride),
                                                  flatten(prefix_product(L.shape)))
                   if s != 1 and d != 0)
    if not modes:
        return Layout(1, 0)
    out_s, out_d = [], []
    if modes[0][0] != 1:  # memory below the smallest stride is never hit
        out_s.append(modes[0][0])
        out_d.append(0)
    for k, (d, s, rd) in enumerate(modes):
        nxt = modes[k + 1][0] if k + 1 < len(modes) else d * s
        out_s.append(nxt // d)  # this mode "owns" memory until the next stride starts
        out_d.append(rd)
    return coalesce(Layout(tuple(out_s), tuple(out_d)))


# --------------------------------------------------------------------------
# small conveniences used by the scenes / notes
# --------------------------------------------------------------------------
def grid(L):
    """2D table of L(i,j) for a rank-2 layout (rows = mode 0)."""
    M, N = prod(L[0].shape), prod(L[1].shape)
    return [[L((i, j)) for j in range(N)] for i in range(M)]


def show(L, title=""):
    if title:
        print(title)
    print(f"  {L}")
    if L.rank() == 2:
        g = grid(L)
        w = max(len(str(v)) for row in g for v in row)
        for row in g:
            print("   " + " ".join(str(v).rjust(w) for v in row))
    else:
        print("   " + " ".join(str(v) for v in L.values()))


if __name__ == "__main__":
    show(composition(Layout((6, 2), (8, 2)), Layout((4, 3), (3, 1))), "composition")
    show(complement(Layout((2, 2), (1, 6)), 24), "complement")
    show(logical_divide(Layout(24), Layout(4, 2)), "logical_divide")
    show(zipped_divide(Layout((8, 8), (8, 1)), (4, 4)), "zipped_divide")
    show(blocked_product(Layout((2, 2)), Layout((3, 2))), "blocked_product")
    show(raked_product(Layout((2, 2)), Layout((3, 2))), "raked_product")
    show(left_inverse(Layout((2, 2), (1, 4))), "left_inverse")
