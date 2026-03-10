# Hlack-Bole — Full Codebase Explanation

## What Is This Project?

This is a **Schwarzschild black hole gravitational lensing renderer** written in pure Python. It simulates how light (photons) bends around a non-rotating black hole and produces an image showing:

- The **black hole shadow** (the dark region where photons are captured)
- A thin **accretion disk** (hot orbiting matter glowing around the black hole)
- A **star-field background** visible through gravitationally lensed light
- **Doppler-like brightness variation** on the disk

The physics uses General Relativity — specifically the **Schwarzschild metric** in geometrised units ($G = c = 1$).

---

## High-Level Pipeline

```
main.py  →  Camera  →  Engine  →  (per pixel) Ray Emitter  →  Trajectory Solver  →  Lensing Renderer  →  PNG
```

For every pixel in the output image:

1. The **Camera** computes a ray direction.
2. The **Ray Emitter** converts that direction into a photon with initial position/velocity in spherical coordinates.
3. The **Trajectory Solver** numerically integrates the geodesic equation (Einstein's equations for light paths) using SciPy's ODE solver.
4. The photon's **fate** is determined: captured by the black hole, escaped to infinity, or hit the accretion disk.
5. The **Lensing Renderer** assigns an RGB colour based on that fate.
6. The assembled image is saved to disk.

---

## File-by-File Breakdown

### `main.py` — Entry Point

- Parses command-line arguments: resolution, field of view, black hole mass, camera distance/inclination, disk size, output path.
- Computes camera position from distance and inclination angle.
- Creates a `Camera` and `Engine` instance.
- Calls `engine.render()` which traces all rays and returns an image array.
- Saves the final image to `output/lensing_render.png` via matplotlib.

**Key CLI flags:**

| Flag | Default | Purpose |
|------|---------|---------|
| `--resolution` | `160x120` | Image width x height |
| `--fov` | `60` | Horizontal field of view (degrees) |
| `--mass` | `1.0` | Black hole mass in geometrised units |
| `--distance` | `30.0` | Camera distance from the black hole |
| `--inclination` | `80.0` | Camera angle from the pole (degrees) |
| `--disk-outer` | `20.0` | Outer radius of the accretion disk |
| `--output` | `output/lensing_render.png` | Output file path |

---

### `core/camera.py` — Pinhole Camera Model

Defines a **pinhole camera** in 3D Cartesian space.

- **Inputs:** position, look-at target, up-vector hint, field of view, resolution.
- On construction, computes an **orthonormal basis** (`forward`, `right`, `up`) from the position/target/up-hint using cross products.
- `ray_direction(i, j)` — For pixel at row `i`, column `j`, computes the unit-length 3D direction vector of the ray leaving the camera through that pixel. Uses half-pixel offsets for uniform sampling and accounts for field of view and aspect ratio.

---

### `core/engine.py` — Simulation Engine (Orchestrator)

The **central coordinator** that ties all modules together.

- **`trace_single_ray(i, j)`** — For one pixel: gets the ray direction from the camera, emits a photon, integrates its trajectory, and returns the result.
- **`render(progress=True)`** — Iterates over every pixel in the image, traces a ray for each, prints a progress bar to stderr, then calls `render_image()` to convert the traced photons into an RGB array.
- **`summary()`** — Diagnostic utility that counts how many photons were captured, escaped, or hit the disk.

---

### `physics/schwarzschild.py` — Schwarzschild Metric & Constants

Contains all the **core physics formulas** for a Schwarzschild (non-rotating) black hole:

| Function | Formula | Purpose |
|----------|---------|---------|
| `schwarzschild_radius(M)` | $r_s = 2M$ | Event horizon radius |
| `photon_sphere_radius(M)` | $r_{ph} = 3M$ | Unstable circular photon orbit |
| `isco_radius(M)` | $r_{isco} = 6M$ | Innermost stable circular orbit (inner disk edge) |
| `metric_tt`, `metric_rr`, `metric_thth`, `metric_phph` | Schwarzschild metric components $g_{\mu\nu}$ | Used by geodesic equations |
| `effective_potential(r, M, L)` | $V_{eff}(r) = (1 - 2M/r) \cdot L^2 / r^2$ | Determines photon turning points |
| `critical_impact_parameter(M)` | $b_c = 3\sqrt{3} \cdot M$ | Impact parameter below which photons are captured |

Also includes SI constants (`G`, `c`, `M_sun`) for potential unit conversions.

---

### `physics/geodesic.py` — Geodesic Equation (Equations of Motion)

Implements the **geodesic equation** — the differential equation governing how photons move through curved spacetime.

- **Christoffel symbols:** The non-zero Christoffel symbols $\Gamma^{\mu}_{\alpha\beta}$ for the Schwarzschild metric are computed in `christoffel_r()`, `christoffel_theta()`, and `christoffel_phi()`. These encode how spacetime curvature deflects light.
- **`geodesic_rhs_full()`** — Full 8-component ODE right-hand side: $\frac{d}{d\lambda}[t, r, \theta, \phi, \dot{t}, \dot{r}, \dot{\theta}, \dot{\phi}]$. Includes the time coordinate.
- **`geodesic_rhs_3d()`** — Simplified 6-component version (drops `t`). Reconstructs $dt/d\lambda$ from the **null condition** ($ds^2 = 0$, meaning the particle is a photon). This is the version actually used by the solver.

Both functions return zeros inside the horizon ($r \leq r_s \times 1.01$) to prevent numerical blowup at the singularity.

---

### `physics/photon.py` — Photon Data Model

Defines the data structures for a single photon:

- **`PhotonFate`** (enum) — Four possible outcomes:
  - `ESCAPED` — photon reached the escape radius
  - `CAPTURED` — photon fell into the event horizon
  - `HIT_DISK` — photon intersected the accretion disk
  - `IN_FLIGHT` — still being traced

- **`Photon`** class — Stores:
  - Initial spherical coordinates and velocities ($r, \theta, \phi, \dot{r}, \dot{\theta}, \dot{\phi}$)
  - Trajectory arrays (recorded during integration)
  - Fate, colour, and brightness
  - `initial_state` property returns the 6-element state vector for the ODE solver
  - `endpoint_cartesian()` converts the final trajectory point back to Cartesian

---

### `bh_math/vectors.py` — Vector Utilities

Pure math helper functions:

| Function | Purpose |
|----------|---------|
| `normalize(v)` | Returns unit vector |
| `magnitude(v)` | Euclidean norm |
| `cartesian_to_spherical(x, y, z)` | $(x,y,z) \to (r, \theta, \phi)$ |
| `spherical_to_cartesian(r, θ, φ)` | $(r, \theta, \phi) \to (x, y, z)$ |
| `cartesian_velocity_to_spherical(pos, vel)` | Transforms velocity from Cartesian to spherical using the Jacobian |
| `rotation_matrix_y(angle)` | 3×3 rotation about Y axis |
| `rotation_matrix_x(angle)` | 3×3 rotation about X axis |

The velocity transformation is critical — the camera works in Cartesian coordinates, but the geodesic solver works in spherical coordinates.

---

### `bh_math/integrator.py` — ODE Integration Wrapper

A thin wrapper around `scipy.integrate.solve_ivp`:

- **`integrate_geodesic()`** — Calls SciPy's RK45 (Runge-Kutta 4th/5th order) solver with configurable tolerances, max step size, and event functions.
- Returns a dictionary with the solution arrays, success status, and event times.

> **Note:** The trajectory solver (`trajectory_solver.py`) calls `solve_ivp` directly rather than going through this wrapper — the wrapper exists as a reusable utility.

---

### `simulation/ray_emitter.py` — Ray Emission

Converts camera-space rays into initial photon states:

- **`emit_ray(cam_pos, ray_dir, M)`** — Takes a Cartesian camera position and ray direction, converts them to spherical coordinates using the vector utilities, and returns a `Photon` object ready for integration. The affine parameter freedom is used to set the speed to 1.
- **`emit_ray_grid()`** — Batch version that generates photons for every pixel in a grid (an alternative to the per-pixel approach used by the engine).

---

### `simulation/trajectory_solver.py` — Geodesic Integration & Fate Detection

The core numerical engine that traces each photon:

- **`_make_events(M, r_max)`** — Creates two terminal event functions for the ODE solver:
  1. **Horizon event** — triggers when $r \leq r_s \times 1.02$ (photon captured)
  2. **Escape event** — triggers when $r > r_{max}$ (photon escaped)

- **`_check_disk_crossing()`** — After integration, scans the trajectory for **equatorial plane crossings** ($\theta$ passing through $\pi/2$). If the crossing radius falls within $[r_{isco}, r_{disk\_outer}]$, the photon hit the accretion disk. Uses linear interpolation to find the exact crossing point.

- **`solve_photon(photon, M, ...)`** — The main function:
  1. Calls `solve_ivp` with the geodesic RHS and event functions.
  2. Stores the trajectory on the photon.
  3. Determines fate from which event triggered (or if lambda was exhausted).
  4. Checks for disk crossings if the photon wasn't captured.
  5. Returns the mutated photon with `.fate`, `.disk_r`, `.disk_phi` set.

---

### `renderer/disk.py` — Accretion Disk Colour Model

Computes the visual appearance of the accretion disk using a simplified **Novikov-Thorne** thin-disk model:

- **`disk_temperature_profile(r, M)`** — Temperature follows $T(r) \propto r^{-3/4} [1 - \sqrt{r_{isco}/r}]^{1/4}$, normalised to a peak value of 1.
- **`temperature_to_rgb(t)`** — Maps normalised temperature to RGB using a **hot-metal palette**: cool → dark red/orange, hot → bright yellow/white.
- **`disk_color(r, phi, M, r_disk_outer)`** — Combines temperature, a Doppler-like azimuthal brightness variation ($1 + 0.4 \sin\phi$, simulating the approaching/receding sides of the orbiting disk), and a radial fade. Returns a final RGB colour.

---

### `renderer/lensing_renderer.py` — Pixel Colour Assignment

Maps photon fates to final pixel colours:

- **`background_color(θ, φ)`** — Procedural star field for escaped photons. Uses a deterministic pseudo-random function based on exit angles to sprinkle bright stars (~0.8% of pixels) on a very dark blue background.
- **`compute_pixel_color(photon, M, r_disk_outer)`** — Dispatches based on fate:
  - `CAPTURED` → black (the shadow)
  - `HIT_DISK` → colour from `disk_color()`
  - `ESCAPED` → `background_color()` based on exit direction
- **`render_image(photon_grid, nx, ny, M, r_disk_outer)`** — Loops over all traced photons and assembles the full `(ny, nx, 3)` RGB image array.

---

### `renderer/plot_renderer.py` — Matplotlib Visualisation

Plotting utilities for display and diagnostics:

- **`show_render(image, ...)`** — Displays the final lensing image with a dark background; optionally saves to file.
- **`plot_trajectories(photons, M, ...)`** — Plots photon paths in the x-z plane, colour-coded by fate (green=escaped, red=captured, yellow=hit disk). Draws reference circles for the event horizon, photon sphere, and ISCO.
- **`plot_effective_potential(M, ...)`** — Plots the effective potential $V_{eff}(r)$ for various impact parameters, illustrating which photons get captured vs. deflected.

---

## Physics Summary

| Concept | Value | Meaning |
|---------|-------|---------|
| Schwarzschild radius | $r_s = 2M$ | Event horizon — nothing escapes |
| Photon sphere | $r_{ph} = 3M$ | Unstable circular photon orbits |
| ISCO | $r_{isco} = 6M$ | Inner edge of stable orbits / accretion disk |
| Critical impact parameter | $b_c = 3\sqrt{3}M \approx 5.2M$ | Photons with $b < b_c$ are captured |
| Geodesic equation | $\frac{d^2 x^\mu}{d\lambda^2} = -\Gamma^\mu_{\alpha\beta} \frac{dx^\alpha}{d\lambda}\frac{dx^\beta}{d\lambda}$ | Equation of motion in curved spacetime |
| Null condition | $g_{\mu\nu} \frac{dx^\mu}{d\lambda}\frac{dx^\nu}{d\lambda} = 0$ | Constraint for massless particles (photons) |

---

## Data Flow Diagram

```
┌──────────┐     ray_direction(i,j)     ┌─────────────┐
│  Camera   │ ─────────────────────────► │ Ray Emitter  │
│ (camera.py)│   Cartesian unit vector   │(ray_emitter.py)│
└──────────┘                             └──────┬───────┘
                                                │  Photon (spherical coords)
                                                ▼
                                        ┌───────────────┐
                                        │  Trajectory    │
                                        │  Solver        │
                                        │(trajectory_    │
                                        │ solver.py)     │
                                        └──────┬────────┘
                                               │  geodesic_rhs_3d()
                                               │  ┌──────────────┐
                                               ├──│ Geodesic Eqs │
                                               │  │ (geodesic.py)│
                                               │  └──────────────┘
                                               │  Christoffel symbols
                                               │  ┌────────────────┐
                                               ├──│ Schwarzschild  │
                                               │  │(schwarzschild. │
                                               │  │ py)            │
                                               │  └────────────────┘
                                               │
                                               ▼
                                        fate: CAPTURED / ESCAPED / HIT_DISK
                                               │
                                               ▼
                                        ┌───────────────┐
                                        │ Lensing       │     ┌──────────┐
                                        │ Renderer      │────►│ Disk     │
                                        │(lensing_      │     │(disk.py) │
                                        │ renderer.py)  │     └──────────┘
                                        └──────┬────────┘
                                               │  RGB pixel
                                               ▼
                                        ┌───────────────┐
                                        │  Plot Renderer│ ──► output/lensing_render.png
                                        │(plot_renderer │
                                        │ .py)          │
                                        └───────────────┘
```

---

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| numpy | ≥ 1.24 | Array math, linear algebra |
| scipy | ≥ 1.10 | ODE solver (`solve_ivp` with RK45) |
| matplotlib | ≥ 3.7 | Image rendering and plotting |

---

## How To Run

```bash
# Quick low-res render (default 160×120)
python main.py

# Medium quality
python main.py --resolution 320x240

# High quality (slower)
python main.py --resolution 640x480

# Custom camera angle and disk size
python main.py --resolution 320x240 --inclination 85 --disk-outer 25
```

Output is saved to `output/lensing_render.png` by default.
