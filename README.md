# cl-algebra: CuTe layout algebra, made visible

Companion to `../notes/layout_algebra.md`. Suggested order: read a section of the notes, watch its video, then run `explore.py <section>` and predict the output before you look.

| | |
|---|---|
| `videos/` | 7 manim animations (720p): layout as a function, composition, complement, 1D divide, zipped_divide + slicing, products, inverses |
| `explore.py` | every example from the notes run through the real CuTe DSL and printed as grids. `python explore.py [composition\|complement\|divide\|product\|inverse]` |
| `layout.py` | the whole algebra in plain Python (~250 lines, no deps). Read it to see the actual algorithms. |
| `verify.py` | checks `layout.py` against CuTe on ~1500 cases (hand-picked + random). `python verify.py -v` |
| `gpu_partition.py` | runs on the L4: CTAs take tiles with `zipped_divide`, then threads take strided or chunked shares. Checked against torch on row- and column-major memory. |
| `scenes/` | manim sources; every number drawn comes from `layout.py` |
| `render.sh` | re-render videos: `./render.sh` (720p), `./render.sh -ql` (fast preview), `./render.sh -qh` (1080p) |

## Environment notes

- CuTe DSL (`nvidia-cutlass-dsl` 4.8) runs in the Studio's main conda env (numpy 1.26).
- manim 0.21 needs numpy ≥ 2.1, and the Studio doesn't allow venvs. So manim is installed with `pip install --target .manim_pkgs manim` and loaded via `PYTHONPATH` (`render.sh` does this for you). The scenes don't import cutlass, which is why `layout.py` exists.
- Where the DSL and C++ CuTe differ in how they *print* a result (size-1 strides, how much products get simplified), `layout.py` follows the DSL.
