# Hlack-Bole — Full Codebase Explanation (https://www.youtube.com/watch?v=FS8NotZ3diY)

## What Is This Project?

**Hlack-Bole** is a physically accurate black hole gravitational lensing renderer. It ray-traces photons through curved spacetime using General Relativity and produces images showing the visual distortion of light around a black hole. It supports both **Schwarzschild** (non-rotating) and **Kerr** (rotating) black holes, and includes a real-time interactive viewer.

Rendered features:

- The **black hole shadow** (dark region where photons are captured by the event horizon)
- A thin **accretion disk** using the Novikov-Thorne temperature profile
- A **procedural star-field background** seen through gravitationally lensed light
- **Relativistic effects** on the disk: gravitational redshift, Doppler shift, relativistic beaming

All physics uses geometrised units ($G = c = 1$).

---

## Repository Layout

```
Hlack-Bole/
├── main.py                        # Python CLI entry point
├── Makefile                       # Build rules for Go shared library and interactive viewer
├── librender.so                   # Compiled Go shared library (loaded by Python via ctypes)
├── hlack-bole-live                # Compiled interactive viewer binary
│
├── core/                          # Python orchestration layer
│   ├── camera.py                  # Pinhole camera model
│   └── engine.py                  # Render engine (Go-first, Python fallback)
│
├── bh_math/                       # Shared math utilities (Python)
│   ├── vectors.py                 # Coordinate conversions, vector ops
│   └── integrator.py              # scipy.integrate.solve_ivp wrapper
│
├── physics/                       # Physics layer (Python)
│   ├── schwarzschild.py           # Metric components, horizon/ISCO radii
│   ├── geodesic.py                # Christoffel symbols, geodesic ODE
│   └── photon.py                  # Photon data model + fate enum
│
├── simulation/                    # Simulation layer (Python)
│   ├── ray_emitter.py             # Camera ray → photon initial state
│   └── trajectory_solver.py      # ODE integration + fate detection
│
├── renderer/                      # Rendering layer (Python)
│   ├── disk.py                    # Accretion disk colour model
│   ├── lensing_renderer.py        # Per-pixel colour dispatch
│   └── plot_renderer.py           # Matplotlib display utilities
│
└── gocore/                        # Go implementation (fast parallel engine)
    ├── render.go                  # CGo export: RenderBatch, TracePixel
    ├── go.mod
    ├── bh_math/
    │   └── vectors.go             # Vector/coordinate math (Go)
    ├── core/
    │   └── engine.go              # Goroutine worker pool
    ├── physics/
    │   ├── photon.go              # Photon struct + fate enum
    │   ├── schwarzschild.go       # Schwarzschild metric functions
    │   ├── kerr.go                # Kerr metric + geodesic RHS
    │   └── geodesic.go            # Schwarzschild geodesic ODE
    ├── renderer/
    │   ├── disk.go                # Disk colour with relativistic effects
    │   └── lensing.go             # Star-field + pixel colour dispatch
    ├── simulation/
    │   └── solver.go              # Hand-rolled adaptive RK45 (Dormand-Prince)
    └── cmd/interactive/
        └── main.go                # Real-time Ebiten viewer
```

---

## Two Execution Paths

The project has two parallel implementations that produce identical output:

| | Python | Go (`gocore/`) |
|---|---|---|
| ODE solver | `scipy.integrate.solve_ivp` | Hand-rolled Dormand-Prince RK45 |
| Parallelism | Single-threaded | Goroutine worker pool (`runtime.GOMAXPROCS`) |
| Entry point | `main.py` + `core/engine.py` | `librender.so` (ctypes) or `hlack-bole-live` |
| Relativity | Schwarzschild only | Schwarzschild + Kerr |
| Speed | Slow (seconds per frame) | Fast (milliseconds per frame) |

**How they connect:** `core/engine.py` attempts to load `librender.so` at startup via `ctypes`. If found, it delegates all rendering to Go. If not found, it falls back to pure Python. The Python layer only handles argument parsing, camera setup, and file I/O.

---

## High-Level Pipeline (per pixel)

```
Camera pixel (i,j)
       │
       ▼  ray_direction(i,j) → unit vector in Cartesian 3D
Camera model
       │
       ▼  Cartesian pos + dir → spherical (r, θ, φ, ṙ, θ̇, φ̇)
Ray Emitter
       │
       ▼  Integrate geodesic ODE forward in affine parameter λ
Trajectory Solver (RK45)
       │    ├─ Terminates: r ≤ r_s×1.02  → CAPTURED  → black pixel
       │    ├─ Terminates: r ≥ r_max     → ESCAPED   → star-field colour
       │    └─ θ crosses π/2 in [r_isco, r_disk]  → HIT_DISK → disk colour
       │
       ▼
Colour assignment
       │  CAPTURED  → [0, 0, 0]
       │  ESCAPED   → procedural star-field based on exit (θ, φ)
       │  HIT_DISK  → Novikov-Thorne temperature → RGB × relativistic factors
       ▼
RGB pixel → assembled image → PNG
```

---

## Python Layer — File-by-File

### `main.py` — CLI Entry Point

- Parses command-line arguments: resolution, FOV, black hole mass, camera distance/inclination, disk outer radius, spin parameter, and toggle flags for redshift/Doppler/beaming.
- Computes the camera position in Cartesian 3D from `distance` and `inclination` using spherical-to-Cartesian conversion.
- Constructs a `Camera` and an `Engine`, then calls `engine.render()` which returns a float32 RGB image array.
- Saves the result to a PNG via matplotlib with a black background.

**Key CLI flags:**

| Flag | Default | Purpose |
|------|---------|---------|
| `--resolution` | `160x120` | Image width × height |
| `--fov` | `60` | Horizontal field of view (degrees) |
| `--mass` | `1.0` | Black hole mass $M$ in geometrised units |
| `--distance` | `30.0` | Camera distance from black hole (units of $M$) |
| `--inclination` | `80.0` | Camera angle from pole (degrees) |
| `--spin` | `0.0` | Kerr spin parameter $a$ ($0 \leq a < M$) |
| `--disk-outer` | `20.0` | Outer radius of accretion disk |
| `--redshift` | `1` | Enable gravitational redshift |
| `--doppler` | `1` | Enable relativistic Doppler shift |
| `--beaming` | `1` | Enable relativistic beaming |
| `--output` | `output/lensing_render.png` | Output file path |

---

### `core/camera.py` — Pinhole Camera

Defines a pinhole camera in 3D Cartesian space.

- On construction, builds an orthonormal basis: `forward = normalize(target - position)`, `right = normalize(forward × up_hint)`, `up = right × forward`.
- `ray_direction(i, j)` — Maps pixel `(i, j)` to a unit-vector ray direction. Uses half-pixel offsets (`(j + 0.5) / nx` etc.) for uniform coverage. Accounts for FOV and aspect ratio.

$$\text{dir} = \text{forward} + u \cdot \tan(\text{fov}/2) \cdot \text{right} + v \cdot \frac{\tan(\text{fov}/2)}{\text{aspect}} \cdot \text{up}$$

---

### `core/engine.py` — Render Engine (Orchestrator)

The central coordinator. Attempts to use the Go shared library (`librender.so`) first; falls back to pure Python if it is not available.

- **`_load_go_lib()`** — Loads `librender.so` with ctypes, sets argument/return types for `RenderBatch` and `TracePixel`.
- **`_build_photon_array()`** — Iterates all pixels, computes each ray direction from the camera, converts the Cartesian position+direction to spherical coordinates, and packs everything into a flat `(n_pixels × 6)` float64 array.
- **`_render_go(lib, progress)`** — Passes the photon array to `lib.RenderBatch` in one call; receives a flat `(n × 3)` float32 RGB array back. Reshapes it to `(ny, nx, 3)`.
- **`_render_python(progress)`** — Single-threaded fallback: calls `trace_single_ray` for every pixel, accumulates results, then calls `render_image`.
- **`render()`** — Selects Go or Python path automatically.
- **`summary(photon_grid)`** — Counts fate distribution across all traced photons.

---

### `physics/schwarzschild.py` — Schwarzschild Metric

Physics formulas for a non-rotating black hole:

| Function | Formula | Purpose |
|----------|---------|---------|
| `schwarzschild_radius(M)` | $r_s = 2M$ | Event horizon |
| `photon_sphere_radius(M)` | $r_{ph} = 3M$ | Unstable photon circular orbit |
| `isco_radius(M)` | $r_{isco} = 6M$ | Inner edge of accretion disk |
| `metric_tt(r, M)` | $g_{tt} = -(1 - 2M/r)$ | Time metric component |
| `metric_rr(r, M)` | $g_{rr} = (1 - 2M/r)^{-1}$ | Radial metric component |
| `metric_thth(r)` | $g_{\theta\theta} = r^2$ | Polar metric component |
| `metric_phph(r, θ)` | $g_{\phi\phi} = r^2\sin^2\theta$ | Azimuthal metric component |
| `effective_potential(r, M, L)` | $V_{eff} = (1 - 2M/r) \cdot L^2/r^2$ | Photon turning points |
| `critical_impact_parameter(M)` | $b_c = 3\sqrt{3}\,M$ | Capture threshold |

---

### `physics/geodesic.py` — Geodesic ODE (Python)

Implements the Schwarzschild geodesic equation.

**Christoffel symbols** (non-zero components, equatorial-generalised):

- `christoffel_r()` — $\ddot{r}$ contributions from $\Gamma^r_{\mu\nu}$
- `christoffel_theta()` — $\ddot{\theta}$ contributions from $\Gamma^\theta_{\mu\nu}$
- `christoffel_phi()` — $\ddot{\phi}$ contributions from $\Gamma^\phi_{\mu\nu}$

**`geodesic_rhs_3d(lam, state, M)`** — Used by the solver. State is $[r, \theta, \phi, \dot{r}, \dot{\theta}, \dot{\phi}]$. Drops the time coordinate and reconstructs $\dot{t}$ from the null condition:

$$\dot{t} = \sqrt{\frac{\dot{r}^2/f + r^2\dot{\theta}^2 + r^2\sin^2\theta\,\dot{\phi}^2}{f}}, \quad f = 1 - \frac{2M}{r}$$

Returns `np.zeros(6)` when $r \leq 1.01\, r_s$ to stop integration cleanly at the horizon.

---

### `physics/photon.py` — Photon Data Model

**`PhotonFate`** enum:

| Value | Meaning |
|-------|---------|
| `ESCAPED` | Photon reached $r_{max}$ — draws background star |
| `CAPTURED` | Photon crossed event horizon — black pixel |
| `HIT_DISK` | Photon crossed equatorial plane inside disk radii |
| `IN_FLIGHT` | Integration still running |

**`Photon`** class holds: initial state $(r_0, \theta_0, \phi_0, \dot{r}_0, \dot{\theta}_0, \dot{\phi}_0)$, trajectory arrays, fate, disk hit position (`disk_r`, `disk_phi`), colour, and brightness.

---

### `bh_math/vectors.py` — Vector / Coordinate Utilities

| Function | Purpose |
|----------|---------|
| `normalize(v)` | Unit vector |
| `magnitude(v)` | Euclidean norm |
| `cartesian_to_spherical(x, y, z)` | $(x,y,z) \to (r,\theta,\phi)$ using `arccos`, `arctan2` |
| `spherical_to_cartesian(r, θ, φ)` | Inverse transform |
| `cartesian_velocity_to_spherical(pos, vel)` | Jacobian transform of velocity vector |
| `rotation_matrix_y(angle)` | 3×3 Y-axis rotation |
| `rotation_matrix_x(angle)` | 3×3 X-axis rotation |

The velocity Jacobian transform is essential: the camera generates ray directions in Cartesian space, but the geodesic ODE integrates in spherical space.

---

### `bh_math/integrator.py` — scipy Wrapper

A reusable wrapper around `scipy.integrate.solve_ivp`. Calls RK45 with configurable tolerances, max step, event functions, and dense output. Returns a plain `dict` instead of the scipy solution object. The trajectory solver calls `solve_ivp` directly, but this utility exists for standalone use.

---

### `simulation/ray_emitter.py` — Ray Emission

- **`emit_ray(cam_pos, ray_dir, M)`** — Converts Cartesian camera position and normalised ray direction into a `Photon` with spherical initial state. Speed is set to 1 (affine parameter freedom).
- **`emit_ray_grid(...)`** — Batch convenience function that generates all photons for a full pixel grid in one call.

---

### `simulation/trajectory_solver.py` — Integration & Fate Detection

- **`_make_events(M, r_max)`** — Two terminal event callbacks for `solve_ivp`:
  - `horizon_event`: $r - 1.02\,r_s = 0$, fires when photon reaches the horizon
  - `escape_event`: $r - r_{max} = 0$, fires when photon escapes
- **`_check_disk_crossing(r, θ, φ, M, r_{disk})`** — Scans consecutive trajectory steps for a sign change in $\theta - \pi/2$. When found, linearly interpolates to the exact equatorial crossing and checks if the radius is inside $[r_{isco}, r_{disk\_outer}]$.
- **`solve_photon(photon, M, ...)`** — Main function:
  1. Calls `solve_ivp` (RK45, rtol=1e-8, atol=1e-10)
  2. Stores trajectory arrays on the photon
  3. Sets `fate` from which event fired (or guesses from final $r$ if lambda exhausted)
  4. If not captured, checks for disk crossing and sets `disk_r`, `disk_phi`

---

### `renderer/disk.py` — Accretion Disk Colour (Python)

Implements a simplified **Novikov-Thorne** thin-disk colour model.

- **`disk_temperature_profile(r, M)`** — Normalised temperature:

$$T_{norm}(r) = \frac{r^{-3/4}\left(1 - \sqrt{r_{isco}/r}\right)^{1/4}}{T_{peak}}$$

- **`temperature_to_rgb(t)`** — Hot-metal colour ramp: cool → red, warm → orange/yellow, hot → white.

$$R = \text{clip}(1.5t), \quad G = \text{clip}(1.5t - 0.4), \quad B = \text{clip}(2t - 1.2)$$

- **`disk_color(r, φ, M, r_{disk})`** — Applies azimuthal Doppler modulation ($1 + 0.4\sin\phi$) and a radial brightness fade, returning the final RGB.

---

### `renderer/lensing_renderer.py` — Pixel Colour Dispatch

- **`background_color(θ, φ)`** — Deterministic pseudo-random star field. Computes `seed = |sin(127.1θ + 311.7φ)| × 43758 mod 1000`. Seeds < 8 (~0.8% of directions) are drawn as white-ish stars; the rest are near-black space.
- **`compute_pixel_color(photon, M, r_disk)`** — Routes by fate: black for captured, disk colour for disk hits, star field for escaped.
- **`render_image(...)`** — Assembles `(ny, nx, 3)` float64 image from a list of `(i, j, photon)` tuples.

---

### `renderer/plot_renderer.py` — Matplotlib Utilities

- **`show_render(image, ...)`** — Displays the rendered image with a black background; optional file save.
- **`plot_trajectories(photons, M, ...)`** — Overlays projected photon paths on a 2D plane, coloured by fate. Draws event horizon, photon sphere, and ISCO circles.
- **`plot_effective_potential(M, ...)`** — Plots $V_{eff}(r)$ curves for multiple impact parameters to visualise the capture threshold.

---

## Go Layer (`gocore/`) — File-by-File

The Go layer is a fully self-contained implementation of the same physics. It compiles to either:

- `librender.so` — a shared library loaded by Python via ctypes
- `hlack-bole-live` — a standalone interactive viewer

---

### `render.go` — CGo Export Layer

The bridge between Python and Go. Exports two C-callable functions via CGo:

- **`RenderBatch(photons, nPixels, mass, spin, ...)`** — Accepts a flat array of `n × 6` photon initial states from Python, dispatches to `core.RenderBatch`, writes `n × 3` float32 RGB results back.
- **`TracePixel(r, θ, φ, ṙ, θ̇, φ̇, mass, spin, ...)`** — Traces a single photon and returns three float32 pointers (R, G, B). Useful for debugging.

`main()` is empty — required by Go for `c-shared` build mode.

---

### `gocore/core/engine.go` — Goroutine Worker Pool

- **`RenderBatch(photons, nPixels, params, outRGB)`** — Creates `runtime.GOMAXPROCS(0)` goroutines. Each goroutine pulls pixel indices from a buffered channel, creates a `Photon`, calls `SolvePhoton`, then `ComputePixelColor`, and writes RGB into the shared output slice. Uses `sync.WaitGroup` for completion.
- **`TraceOnePixel(state, params)`** — Single-pixel convenience for the interactive viewer.

No locks needed on `outRGB` because each goroutine writes to a disjoint index range.

---

### `gocore/bh_math/vectors.go` — Vector & Coordinate Math (Go)

Mirrors `bh_math/vectors.py` exactly. All functions operate on `[3]float64` arrays:

| Function | Purpose |
|----------|---------|
| `Normalize(v)` | Unit vector |
| `Magnitude(v)` | Euclidean length |
| `CartesianToSpherical(x,y,z)` | $(x,y,z) \to (r,\theta,\phi)$ |
| `SphericalToCartesian(r,θ,φ)` | Inverse |
| `CartesianVelocityToSpherical(pos, vel)` | Jacobian velocity transform |
| `Cross(a, b)` | 3D cross product |
| `Dot(a, b)` | Dot product |
| `Scale(v, s)` | Scalar multiply |
| `Add(a, b)`, `Sub(a, b)` | Vector addition/subtraction |

Used by the interactive viewer (`main.go`) to build the camera basis and photon array.

---

### `gocore/physics/photon.go` — Photon Struct

```go
type PhotonFate int   // Escaped, Captured, HitDisk, InFlight

type Photon struct {
    R0, Theta0, Phi0    float64  // initial position (spherical)
    DR0, DTheta0, DPhi0 float64  // initial velocities
    TrajectoryR/Theta/Phi []float64
    Fate         PhotonFate
    DiskR, DiskPhi, DiskThetaDot float64
    Brightness   float64
    Color        [3]float32
}
```

`NewPhoton(r, θ, φ, ṙ, θ̇, φ̇)` creates a photon with `Fate = InFlight`.

---

### `gocore/physics/schwarzschild.go` — Schwarzschild Functions (Go)

Go equivalents of `physics/schwarzschild.py`:

- `SchwarzschildRadius(M)`, `PhotonSphereRadius(M)`, `ISCORadius(M)`
- `MetricTT`, `MetricRR`, `MetricThTh`, `MetricPhPh`
- `EffectivePotential(r, M, L)`, `CriticalImpactParameter(M)`

---

### `gocore/physics/geodesic.go` — Schwarzschild Geodesic (Go)

Go equivalent of `physics/geodesic.py`:

- `ChristoffelR`, `ChristoffelTheta`, `ChristoffelPhi` — same formulas as Python versions
- `GeodesicRHS3D(lam, state, M)` — 6-component ODE RHS, reconstructs $\dot{t}$ from null condition

---

### `gocore/physics/kerr.go` — Kerr Metric & Geodesic

Implements the full **Kerr metric** in Boyer-Lindquist coordinates for rotating black holes. This is absent in the Python layer.

**Key quantities:**

$$\Sigma = r^2 + a^2\cos^2\theta, \quad \Delta = r^2 - 2Mr + a^2$$

$$r_+ = M + \sqrt{M^2 - a^2} \quad \text{(event horizon)}$$

Helper functions: `KerrSigma`, `KerrDelta`, `KerrEventHorizon`, `KerrISCO` (prograde ISCO using the Bardeen formula), and all 5 Boyer-Lindquist metric components.

**`GeodesicRHSKerr(lam, state, M, a)`** — Computes the geodesic acceleration using the Euler-Lagrange equations for the Kerr Lagrangian $\mathcal{L} = \frac{1}{2}g_{\mu\nu}\dot{x}^\mu\dot{x}^\nu = 0$:

1. Reconstructs $\dot{t}$ by solving the null-condition quadratic in $\dot{t}$
2. Computes all metric partial derivatives ($\partial_r g_{\mu\nu}$, $\partial_\theta g_{\mu\nu}$) analytically
3. Applies the Euler-Lagrange formula for $\ddot{r}$ and $\ddot{\theta}$
4. Solves the 2×2 linear system for $\ddot{t}$ and $\ddot{\phi}$ from the conserved energy and angular momentum equations

**`GeodesicRHS(lam, state, M, a)`** — Dispatcher: calls `GeodesicRHS3D` when $a = 0$ (Schwarzschild), else `GeodesicRHSKerr`.

---

### `gocore/simulation/solver.go` — Adaptive RK45 (Dormand-Prince)

A hand-rolled **Dormand-Prince RK45** integrator — no external dependencies. This gives total control over step-size adaptation and event detection, which `scipy.solve_ivp` handles internally in Python.

**Dormand-Prince coefficients** (`dpA`, `dpB5`, `dpE`) are hardcoded as the standard Butcher tableau.

**`rk45step(f, lam, y, h)`** — Computes one RK45 step: evaluates $f$ at 7 internal stages and returns both the 5th-order solution `y5` and the embedded 4th-order `y4` for error estimation.

**`errorNorm(y4, y5, atol, rtol)`** — Computes the mixed absolute/relative error norm per component; step is accepted when error ≤ 1.

**`SolvePhoton(photon, params)`** — Main integration loop:

1. Advances with adaptive step size
2. After each accepted step, checks three event functions:
   - `horizonEvent`: $r$ crossed below $1.02 r_+$ → `Captured`
   - `escapeEvent`: $r$ exceeded $r_{max}$ → `Escaped`
   - `diskCrossingEvent`: $\theta$ crossed $\pi/2$ → possible `HitDisk`
3. When a disk crossing is detected, **bisects** the interval (60 iterations) to precisely locate the equatorial crossing point and records `DiskR`, `DiskPhi`, `DiskThetaDot`
4. Step size is scaled by $0.9 \cdot \text{err}^{-0.2}$, clamped to $[0.2,\, 5] \times h$

---

### `gocore/renderer/disk.go` — Disk Colour with Relativistic Effects

Implements the Novikov-Thorne disk colour model plus three optional relativistic corrections:

- **`DiskTemperatureProfile(r, M)`** — Same formula as Python: $r^{-3/4}(1 - \sqrt{r_{in}/r})^{1/4}$, normalised at peak
- **`TemperatureToRGB(t)`** — Hot-metal ramp, matching Python
- **`GravitationalRedshift(r, M)`** — $z_{grav} = \sqrt{1 - r_s/r}$ — light loses energy climbing out of the gravity well; disk appears cooler/dimmer from far away
- **`KeplerianOmega(r, M)`** — $\Omega = \sqrt{M/r^3}$ — orbital angular velocity of disk matter
- **`DopplerFactor(r, φ, M)`** — Full relativistic Doppler:

$$v = \frac{\Omega r}{\sqrt{1 - r_s/r}}, \quad \gamma = \frac{1}{\sqrt{1-v^2}}, \quad D = \frac{1}{\gamma(1 - v\cos\phi)}$$

- **`DiskColorRelativistic(...)`** — Combines all effects:

$$\text{brightness} = z_{grav} \cdot D^3 \cdot T_{norm} \cdot \text{radialFade}$$

  where $D^3$ accounts for: one factor from photon energy shift, one from photon rate, one from solid-angle beaming (relativistic beaming). Each effect is independently togglable.

---

### `gocore/renderer/lensing.go` — Pixel Colour Dispatch (Go)

Go equivalent of `renderer/lensing_renderer.py`:

- **`BackgroundColor(θ, φ)`** — Identical pseudo-random star field formula as Python
- **`ComputePixelColor(photon, params)`** — Returns black for captured, disk colour (relativistic) for disk hits, star field for escaped photons

---

### `gocore/cmd/interactive/main.go` — Real-Time Interactive Viewer

A live OpenGL-backed viewer using the **Ebiten** game engine (`github.com/hajimehoshi/ebiten/v2`).

**Render resolution:** 160×120 internally, scaled up 5× to 800×600 for display. This keeps frame time low enough for interactive use.

**`Game` struct** — holds all adjustable parameters:

| Field | Controlled by | Effect |
|-------|---------------|--------|
| `distance` | W / S keys | Camera orbital radius |
| `inclination` | ↑ / ↓ arrow keys | Camera polar angle |
| `azimuth` | ← / → arrow keys | Camera azimuthal angle |
| `fov` | `=` / `-` keys | Field of view |
| `spin` | A / D keys | Kerr spin parameter $a$ |

**`Update()`** — Called every tick (~60 Hz). Reads keyboard state and updates parameters.

**`Draw(screen)`** — Called every frame:

1. Calls `buildPhotonArray(renderW, renderH)` to recompute all photon initial states from the current camera position
2. Calls `core.RenderBatch(...)` — the same Go worker pool used by the Python ctypes path
3. Converts the float32 RGB pixels to `color.RGBA` and uploads to an Ebiten image
4. Draws the image scaled up with nearest-neighbour filtering (intentionally pixelated look)
5. Overlays FPS and camera parameters via `ebitenutil.DebugPrint`

**`saveHighRes()`** — Triggered by pressing `R`. Runs asynchronously (goroutine), renders at 640×480, and saves to `output/render_<unix_timestamp>.png`.

**`buildPhotonArray(nx, ny)`** — Mirrors `Engine._build_photon_array` in Python: builds the camera basis from `distance`, `inclination`, `azimuth`, then iterates all pixels.

---

## Physics Summary

| Quantity | Schwarzschild ($a=0$) | Kerr ($a > 0$) |
|----------|-----------------------|----------------|
| Event horizon | $r_s = 2M$ | $r_+ = M + \sqrt{M^2 - a^2}$ |
| Photon sphere | $r_{ph} = 3M$ | More complex, dependent on $a$ |
| ISCO | $r_{isco} = 6M$ | $r_{isco}(a)$ — shrinks as $a \to M$ |
| Critical impact param | $b_c = 3\sqrt{3}\,M$ | Changes with $a$ |
| Metric | Diagonal, 4 components | 5 components + $g_{t\phi}$ off-diagonal |
| Frame-dragging | None | Yes — $g_{t\phi}$ couples $t$ and $\phi$ |

The geodesic equation in both cases:

$$\frac{d^2 x^\mu}{d\lambda^2} = -\Gamma^\mu_{\alpha\beta} \frac{dx^\alpha}{d\lambda}\frac{dx^\beta}{d\lambda}$$

For photons, the null condition $g_{\mu\nu}\dot{x}^\mu\dot{x}^\nu = 0$ provides one constraint, allowing $\dot{t}$ to be reconstructed from the remaining coordinates and eliminating it from the ODE state.

---

## Build System

```
make build-go         # Compiles librender.so (Python ctypes target)
make build-interactive  # Compiles hlack-bole-live (Ebiten viewer)
make build-all        # Both
```

The interactive build requires X11 development libraries (`libX11`, `libXrandr`, `libXi`, `libXcursor`, `libXinerama`). On Fedora: `sudo dnf install libX11-devel libXrandr-devel libXi-devel libXcursor-devel libXinerama-devel`.

Note: `libXxf86vm` is a legacy library. If the linker cannot find it, install `libXxf86vm-devel` or add `-tags noopengl` to the build flags.

---

## Dependencies

**Python:**

| Library | Purpose |
|---------|---------|
| `numpy` | Array math |
| `scipy` | ODE solver (`solve_ivp`, RK45) |
| `matplotlib` | Image saving and trajectory plots |

**Go:**

| Module | Purpose |
|--------|---------|
| `github.com/hajimehoshi/ebiten/v2` | Real-time interactive window (interactive viewer only) |
| Standard library only | Everything else (`math`, `sync`, `runtime`, `image`, etc.) |

---

## How To Run

```bash
# Default 160×120 render (auto-uses Go engine if librender.so is present)
python main.py

# Medium quality
python main.py --resolution 320x240

# High quality with Kerr black hole (spin a=0.9)
python main.py --resolution 640x480 --spin 0.9 --inclination 75

# Force edge-on view with large disk
python main.py --resolution 320x240 --inclination 90 --disk-outer 30

# Interactive real-time viewer (requires build-interactive)
./hlack-bole-live
```

Controls for the interactive viewer:

| Key | Action |
|-----|--------|
| ↑ / ↓ | Orbit camera up/down (inclination) |
| ← / → | Orbit camera left/right (azimuth) |
| W / S | Zoom in/out (camera distance) |
| A / D | Decrease/increase Kerr spin $a$ |
| = / - | Narrow/widen field of view |
| R | Save 640×480 PNG to `output/` |
