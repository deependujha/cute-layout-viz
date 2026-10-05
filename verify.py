"""
Cross-check layout.py (pure Python) against the real CuTe DSL.

    python verify.py            # hand-picked cases (everything used in notes + scenes) + random ones

Every layout-algebra call runs inside one @cute.jit trace on static values,
so CuTe computes the result at compile time and we just compare strings.
"""

import random
import sys

import cutlass.cute as cute

import layout as py

# ---------------------------------------------------------------------------
# cases: (op, A, B)   A/B are py.Layout, ints, or tuples (tilers)
# ---------------------------------------------------------------------------
L = py.Layout
FIXED = [
    # composition
    ("composition", L(20, 2), L(5, 4)),
    ("composition", L((6, 2), (8, 2)), L((4, 3), (3, 1))),
    ("composition", L((4, 6), (6, 1)), (2, 3)),
    ("composition", L((4, 6), (6, 1)), (L(2, 2), L(3, 2))),
    ("composition", L((4, 6), (6, 1)), L(12, 2)),
    ("composition", L((4, 6), (6, 1)), L((2, 3), (1, 2))),
    # complement
    ("complement", L(4, 1), 24),
    ("complement", L((2, 2), (1, 6)), 24),
    ("complement", L(4, 2), 24),
    ("complement", L((4, 4), (4, 1)), 16),
    ("complement", L(6, 4), 24),
    # divides
    ("logical_divide", L(24), L(4, 2)),
    ("logical_divide", L(24), L(4, 1)),
    ("logical_divide", L((8, 8), (8, 1)), (4, 4)),
    ("zipped_divide", L((8, 8), (8, 1)), (4, 4)),
    ("tiled_divide", L((8, 8), (8, 1)), (4, 4)),
    ("flat_divide", L((8, 8), (8, 1)), (4, 4)),
    ("zipped_divide", L((6, 8), (1, 6)), (2, 4)),
    ("zipped_divide", L((8, 16), (1, 8)), (4, 8)),
    ("zipped_divide", L((8, 16), (16, 1)), (4, 8)),
    ("zipped_divide", L((8, 8), (1, 8)), (L(2, 4), L(2, 4))),
    # products
    ("logical_product", L((2, 2)), L((3, 2))),
    ("logical_product", L(4, 1), L(3, 1)),
    ("logical_product", L(4, 2), L(3, 1)),
    ("blocked_product", L((2, 2)), L((3, 2))),
    ("raked_product", L((2, 2)), L((3, 2))),
    ("blocked_product", L((2, 2), (2, 1)), L((2, 3))),
    ("raked_product", L((2, 2), (2, 1)), L((2, 3))),
    ("blocked_product", L((4, 8), (8, 1)), L((2, 2))),
    # inverses / coalesce
    ("right_inverse", L((4, 8), (8, 1)), None),
    ("right_inverse", L((2, 4), (4, 1)), None),
    ("right_inverse", L((2, 2), (1, 4)), None),
    ("left_inverse", L((2, 2), (1, 4)), None),
    ("left_inverse", L(4, 2), None),
    ("left_inverse", L((2, 4), (4, 1)), None),
    ("coalesce", L((2, (1, 6)), (1, (6, 2))), None),
    ("coalesce", L((4, 2), (1, 4)), None),
    ("coalesce", L((4, 2), (2, 8)), None),
]


# ---------------------------------------------------------------------------
# random cases: compact layouts with permuted mode order (always valid)
# ---------------------------------------------------------------------------
def rand_compact(rng, rank):
    shape = tuple(rng.choice([2, 3, 4, 6, 8]) for _ in range(rank))
    order = list(range(rank))
    rng.shuffle(order)
    stride, cur = [0] * rank, 1
    for i in order:
        stride[i] = cur
        cur *= shape[i]
    return L(shape, tuple(stride)) if rank > 1 else L(shape[0], stride[0])


def rand_pow2_layout(rng, rank, max_s=8):
    shape = tuple(rng.choice([1, 2, 4, 8][: max_s.bit_length()]) for _ in range(rank))
    return rand_compact_with(shape, rng)


def rand_compact_with(shape, rng):
    order = list(range(len(shape)))
    rng.shuffle(order)
    stride, cur = [0] * len(shape), 1
    for i in order:
        stride[i] = cur
        cur *= shape[i]
    return L(shape, tuple(stride))


def random_cases(n=1500, seed=0):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        kind = rng.choice(["complement", "divide", "product", "inverse", "composition"])
        if kind == "complement":
            A = rand_compact(rng, rng.randint(1, 3))
            mult = rng.choice([1, 2, 3, 4])
            # spread A out by a power of two so there are real holes
            spread = rng.choice([1, 2, 4])
            A = L(A.shape, tuple(d * spread for d in py.flatten(A.stride))) if py.is_tuple(A.shape) \
                else L(A.shape, A.stride * spread)
            out.append(("complement", A, A.cosize() * mult))
        elif kind == "divide":
            M, N = rng.choice([4, 8, 16]), rng.choice([4, 8, 16])
            A = rand_compact_with((M, N), rng)
            tiler = (rng.choice([d for d in (1, 2, 4) if M % d == 0]),
                     rng.choice([d for d in (1, 2, 4, 8) if N % d == 0]))
            op = rng.choice(["logical_divide", "zipped_divide", "tiled_divide", "flat_divide"])
            out.append((op, A, tiler))
        elif kind == "product":
            A = rand_compact_with((rng.choice([1, 2, 4]), rng.choice([1, 2, 4])), rng)
            B = rand_compact_with((rng.choice([1, 2, 3]), rng.choice([1, 2, 3])), rng)
            op = rng.choice(["logical_product", "blocked_product", "raked_product"])
            out.append((op, A, B))
        elif kind == "inverse":
            A = rand_compact(rng, rng.randint(1, 3))
            out.append((rng.choice(["right_inverse", "left_inverse"]), A, None))
        else:
            A = rand_compact_with(tuple(rng.choice([2, 4, 8]) for _ in range(2)), rng)
            n = A.size()
            s = rng.choice([d for d in (2, 4, 8, 16) if n % d == 0])
            d = rng.choice([d for d in (1, 2, 4) if (n // s) % d == 0])
            out.append(("composition", A, L(s, d)))
    return out


# ---------------------------------------------------------------------------
# run the same thing through CuTe
# ---------------------------------------------------------------------------
def to_cute(x):
    if isinstance(x, py.Layout):
        return cute.make_layout(x.shape, stride=x.stride)
    if isinstance(x, tuple):
        return tuple(to_cute(e) for e in x)
    return x


def cute_eval(op, A, B):
    fn = getattr(cute, op)
    if B is None:
        return str(fn(to_cute(A)))
    return str(fn(to_cute(A), to_cute(B)))


def py_eval(op, A, B):
    fn = getattr(py, op)
    return str(fn(A) if B is None else fn(A, B))


RESULTS = []


def canon(s):
    """Normalize 'shape:stride' so size-1 modes have stride 0 (their stride is never used)."""
    if s.startswith("<"):
        return s
    shape, stride = (eval(p) for p in s.split(":"))

    def go(sh, st):
        if isinstance(sh, tuple):
            return tuple(go(a, b) for a, b in zip(sh, st))
        return 0 if sh == 1 else st

    return f"{py.fmt(shape)}:{py.fmt(go(shape, stride))}"


def _run_all(cases):
    for op, A, B in cases:
        try:
            ours = py_eval(op, A, B)
        except AssertionError as e:
            ours = f"<assert: {e}>"
        try:
            theirs = cute_eval(op, A, B)
        except Exception as e:  # noqa: BLE001
            theirs = f"<cute error: {type(e).__name__}>"
        RESULTS.append((op, A, B, ours, theirs))


CASES = []


@cute.jit
def _trace():
    _run_all(CASES)


def main():
    CASES.extend(FIXED + random_cases())
    _trace()
    bad = 0
    for op, A, B, ours, theirs in RESULTS:
        ok = canon(ours) == canon(theirs)
        skipped = ours.startswith("<assert") and theirs.startswith("<cute error")
        if not ok and not skipped:
            bad += 1
            print(f"MISMATCH {op}({A}, {B}):\n   layout.py: {ours}\n   cute     : {theirs}")
    n_fixed = len(FIXED)
    if "-v" in sys.argv:
        for op, A, B, ours, _ in RESULTS[:n_fixed]:
            arg = "" if B is None else f", {py.fmt(B) if isinstance(B, tuple) else B}"
            print(f"{op}({A}{arg})  =  {ours}")
    print(f"\n{len(RESULTS) - bad}/{len(RESULTS)} cases agree with CuTe "
          f"({n_fixed} hand-picked, {len(RESULTS) - n_fixed} random)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
