# Contributing to Hlack-Bole

Thank you for your interest in contributing. This document explains the project conventions, how to set up a development environment, and the workflow for submitting changes.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Running the Renderer](#running-the-renderer)
- [Adding New Physics](#adding-new-physics)
- [Adding New Render Features](#adding-new-render-features)
- [Testing Your Changes](#testing-your-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)

---

## Getting Started

1. Fork the repository.
2. Clone your fork:

   ```bash
   git clone https://github.com/your-username/Hlack-Bole.git
   cd Hlack-Bole
   ```

3. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Verify the setup by running a quick render:

   ```bash
   python main.py --resolution 80x60
   ```

   This should complete in under a minute and write `output/lensing_render.png`.

---

## Project Structure

```
Hlack-Bole/
├── main.py                   Entry point, CLI argument parsing
├── core/
│   ├── camera.py             Pinhole camera model
│   └── engine.py             Render loop orchestrator
├── physics/
│   ├── schwarzschild.py      Metric functions, key radii, SI constants
│   ├── geodesic.py           Christoffel symbols, geodesic ODE right-hand side
│   └── photon.py             Photon data class and PhotonFate enum
├── bh_math/
│   ├── vectors.py            Coordinate transforms and vector utilities
│   └── integrator.py        scipy.integrate.solve_ivp wrapper
├── simulation/
│   ├── ray_emitter.py        Converts camera rays to initial Photon states
│   └── trajectory_solver.py Integrates geodesic, detects fate and disk crossing
├── renderer/
│   ├── disk.py               Accretion disk temperature and colour model
│   ├── lensing_renderer.py   Maps photon fates to RGB pixel values
│   └── plot_renderer.py      Matplotlib diagnostics and final image display
├── output/                   Rendered images (gitignored)
├── README.md
├── EXPLANATION.md            File-by-file codebase walkthrough
├── ARCHITECTURE.md           Dependency graph, per-pixel sequence, data structures
└── requirements.txt
```

See [EXPLANATION.md](EXPLANATION.md) for a detailed description of every file and [ARCHITECTURE.md](ARCHITECTURE.md) for the full execution sequence and data structures.

---

## Development Setup

### Recommended Tools

- **Python 3.10+** — the project uses f-strings and `enum`, no version-specific features beyond that.
- A virtual environment manager such as `venv` or `conda`.
- An editor with Python language support (VS Code + Pylance works well).

### Optional: Faster Renders During Development

Use a very small resolution to shorten iteration cycles:

```bash
python main.py --resolution 64x48
```

For trajectory or physics debugging, `plot_renderer.py` functions can be called standalone from a Python REPL without running the full render.

---

## Code Style

- Follow **PEP 8**: 4-space indentation, max line length of 100 characters.
- Use descriptive variable names that match the physics notation where applicable (`r`, `theta`, `phi`, `rdot`, `M` are standard throughout).
- Keep units consistent: **geometrised units** ($G = c = 1$) everywhere inside the solver. Only `physics/schwarzschild.py` holds SI constants, and only for reference/conversion use.
- No docstrings are used in this project — write self-explanatory function signatures and keep helper logic small enough to be obvious.
- Avoid abbreviations in function names. Prefer `compute_pixel_color` over `calc_color`.
- One class per file is the norm; do not mix multiple unrelated classes in a single module.

---

## Adding New Physics

### Replacing or Adding a Spacetime Metric

The geodesic right-hand side is in `physics/geodesic.py`. To support a different metric:

1. Add (or replace) the Christoffel symbol functions for the new metric.
2. Update `geodesic_rhs_3d()` to call those functions instead.
3. Update the singularity guard: `if r <= 1.01 * schwarzschild_radius(M): return zeros`.
4. Update `physics/schwarzschild.py` if the key radii change (photon sphere, ISCO, critical impact parameter).
5. Run with `--resolution 80x60` and verify the shadow shape looks physically correct.

### Kerr Black Hole (Rotating)

Kerr requires tracking the spin parameter `a` and updating:

- Christoffel symbols (Boyer-Lindquist coordinates)
- The null condition (metric is no longer diagonal in $t$, $\phi$)
- Horizon radius: $r_+ = M + \sqrt{M^2 - a^2}$
- ISCO radius depends on spin direction

---

## Adding New Render Features

### Changing the Disk Appearance

Edit `renderer/disk.py`:

- `disk_temperature_profile(r, M)` — change the radial temperature law.
- `temperature_to_rgb(t)` — change the colour palette.
- `disk_color(r, phi, M, r_disk_outer)` — change the Doppler or fade model.

All three functions are isolated from the rest of the renderer.

### Changing the Background

Edit `background_color()` in `renderer/lensing_renderer.py`. The function receives `(theta, phi)` — the exit direction of the escaped photon — and returns an RGB triple.

### Parallel Rendering

The per-pixel loop in `core/engine.py` is embarrassingly parallel. To add multiprocessing:

1. Extract `Engine.trace_single_ray` as a module-level function.
2. Use `multiprocessing.Pool.starmap` over the list of `(i, j)` pixel coordinates.
3. Reassemble the flat results list into the 2D grid.

---

## Testing Your Changes

There is currently no automated test suite. When making a change:

1. **Sanity render** — Run `python main.py --resolution 80x60` and compare to a known-good output.
2. **Trajectory check** — Use `plot_renderer.plot_trajectories()` with a small batch of photons at varying impact parameters. Photons with $b < 3\sqrt{3} M$ should be captured; photons with larger $b$ should escape.
3. **Effective potential** — Use `plot_renderer.plot_effective_potential()` to visualise the potential barrier. The peak should occur near $r = 3M$.
4. **Smoke test** — Verify that no unhandled exceptions occur for edge cases:
   - Camera placed at low inclination ($\leq 5°$)
   - Very small black hole mass (`--mass 0.1`)
   - Camera placed close to the black hole (`--distance 10`)

---

## Submitting a Pull Request

1. Create a feature branch off `main`:

   ```bash
   git checkout -b feature/my-change
   ```

2. Make your changes with focused, atomic commits.
3. Verify the sanity render still produces a visually correct image.
4. Push and open a pull request against `main` with:
   - A clear description of what changed and why.
   - A before/after render comparison if the change affects image output.
   - Notes on any physics approximations or tradeoffs made.

Contributions that change the physics model should include a reference to the relevant paper or textbook section.
