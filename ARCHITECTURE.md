# Hlack-Bole — Architecture Reference

## Overview

Hlack-Bole is structured as a layered pipeline. Each layer has a single responsibility and depends only on the layers below it. The render loop is strictly sequential per pixel — no shared mutable state — which makes the computation trivially parallelisable in the future.

```
┌─────────────────────────────────────────────────────┐
│                     main.py                          │
│              CLI parsing · program entry             │
└────────────────────────┬────────────────────────────┘
                         │
           ┌─────────────▼─────────────┐
           │         core/             │
           │   Camera · Engine         │
           │  (orchestration layer)    │
           └──────┬──────────┬─────────┘
                  │          │
      ┌───────────▼───┐  ┌───▼──────────────────┐
      │  simulation/  │  │      renderer/        │
      │  Ray Emitter  │  │  LensingRenderer      │
      │  Traj. Solver │  │  DiskColorModel       │
      └───────┬───────┘  │  PlotRenderer         │
              │           └───────────────────────┘
   ┌──────────▼──────────┐
   │      physics/       │
   │  Schwarzschild      │
   │  Geodesic Eqs       │
   │  Photon Model       │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │      bh_math/       │
   │  Vectors · Integr.  │
   └─────────────────────┘
```

---

## Module Dependency Graph

```
main.py
  └── core/camera.py
  └── core/engine.py
        ├── core/camera.py
        ├── simulation/ray_emitter.py
        │     ├── physics/photon.py
        │     └── bh_math/vectors.py
        ├── simulation/trajectory_solver.py
        │     ├── physics/photon.py
        │     ├── physics/geodesic.py
        │     │     └── physics/schwarzschild.py
        │     └── physics/schwarzschild.py
        └── renderer/lensing_renderer.py
              └── renderer/disk.py
                    └── physics/schwarzschild.py

renderer/plot_renderer.py  (standalone utility, no engine dependency)
  └── physics/schwarzschild.py
  └── physics/photon.py

bh_math/integrator.py  (standalone wrapper, not used in main pipeline)
```

---

## Per-Pixel Execution Sequence

This sequence runs once for **every pixel** in the output image.

```
Engine.render()
│
├─ for each pixel (i, j):
│   │
│   ├─ 1. Camera.ray_direction(i, j)
│   │       Converts pixel coordinates to a unit Cartesian ray vector.
│   │       Uses FOV and aspect ratio to map pixel → angle.
│   │
│   ├─ 2. emit_ray(cam_pos, ray_dir, M)
│   │       Converts Cartesian position + direction to spherical coords.
│   │       Applies the Jacobian for velocity transformation:
│   │         (ẋ, ẏ, ż) → (ṙ, θ̇, φ̇)
│   │       Returns a Photon with initial_state = [r, θ, φ, ṙ, θ̇, φ̇]
│   │
│   ├─ 3. solve_photon(photon, M, ...)
│   │   │
│   │   ├─ build terminal events:
│   │   │     horizon_event:  r ≤ 2M × 1.02  (terminal, direction=-1)
│   │   │     escape_event:   r ≥ r_max       (terminal, direction=+1)
│   │   │
│   │   ├─ scipy.integrate.solve_ivp(
│   │   │     fun   = geodesic_rhs_3d,
│   │   │     method= 'RK45',
│   │   │     events= [horizon_event, escape_event]
│   │   │   )
│   │   │
│   │   │   geodesic_rhs_3d(λ, y) called repeatedly by RK45:
│   │   │     y = [r, θ, φ, ṙ, θ̇, φ̇]
│   │   │     computes Γ^r_{αβ}, Γ^θ_{αβ}, Γ^φ_{αβ}  from schwarzschild.py
│   │   │     solves null condition for dt/dλ
│   │   │     returns [ṙ, θ̇, φ̇, r̈, θ̈, φ̈]
│   │   │
│   │   ├─ determine fate:
│   │   │     t_events[0] non-empty  →  CAPTURED
│   │   │     t_events[1] non-empty  →  ESCAPED
│   │   │     else                   →  CAPTURED (lambda exhausted)
│   │   │
│   │   └─ _check_disk_crossing(traj, M, r_disk_outer)
│   │         scans θ(λ) for sign changes around π/2
│   │         interpolates to find r, φ at crossing
│   │         if r_isco ≤ r_cross ≤ r_outer  →  fate = HIT_DISK
│   │         stores disk_r, disk_phi on photon
│   │
│   └─ 4. photon appended to results grid
│
└─ render_image(photon_grid, nx, ny, M, r_outer)
      for each photon:
        CAPTURED  →  [0, 0, 0]  (black shadow)
        ESCAPED   →  background_color(θ_exit, φ_exit)  (star field)
        HIT_DISK  →  disk_color(disk_r, disk_phi, M)
      returns (ny, nx, 3) float array in [0, 1]
```

---

## Key Data Structures

### `Photon`

```python
class Photon:
    r0, theta0, phi0        # initial spherical position
    rdot0, thetadot0, phidot0  # initial spherical velocity
    trajectory              # ndarray (6, N) — full path through space
    fate                    # PhotonFate enum
    color                   # (R, G, B) tuple
    brightness              # float scalar
    disk_r, disk_phi        # set only when fate == HIT_DISK
```

The trajectory array is stored in row-major order: `trajectory[0]` = r, `trajectory[1]` = θ, `trajectory[2]` = φ, `trajectory[3]` = ṙ, etc.

### `PhotonFate`

```
ESCAPED   — photon reached r_max, contributes to background/star field
CAPTURED  — photon crossed event horizon, contributes black pixel
HIT_DISK  — photon plane-crossed the equatorial disk, coloured by temperature
IN_FLIGHT — only valid during integration; never appears in final image
```

---

## Coordinate Systems

The project uses **two** coordinate systems and converts between them at exactly two points:

| System | Where used | Variables |
|--------|-----------|-----------|
| Cartesian $(x, y, z)$ | Camera, ray emission, final plotting | `cam_pos`, `ray_dir`, endpoint display |
| Spherical $(r, \theta, \phi)$ | Everything else — geodesic solver, disk model, renderer | `r`, `theta`, `phi`, `rdot`, `thetadot`, `phidot` |

**Cartesian → Spherical** happens in `emit_ray()` via `cartesian_to_spherical()` and `cartesian_velocity_to_spherical()`.

**Spherical → Cartesian** happens in `Photon.endpoint_cartesian()` for diagnostic plots.

The spherical convention is:
- $\theta = 0$ at the north pole (z-axis)
- $\theta = \pi/2$ at the equatorial plane (accretion disk location)
- $\phi$ measured in the x-y plane from the x-axis

---

## Numerical Integration Details

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Method | RK45 | Dormand-Prince adaptive Runge-Kutta 4(5) |
| Relative tolerance | 1 × 10⁻⁸ | Step accuracy |
| Absolute tolerance | 1 × 10⁻¹⁰ | Floor for near-zero components |
| Max step | 0.1 | Prevents solver skipping over disk crossings |
| Lambda span | [0, 2000] | Affine parameter range; horizon distance / r_s is ~10–100 |
| Singularity guard | r ≤ 1.01 × r_s | Returns zero derivative to halt photon gracefully |

The solver uses SciPy's **dense output** (disabled by default) capability for potential trajectory resampling. Event detection is handled by the solver's internal root-finding; the disk crossing check is done as a post-processing pass because equatorial crossings vanish in the event model when θ ≈ π/2.

---

## Accretion Disk Model

The disk colour pipeline is:

```
r, φ  (disk crossing coordinates)
  │
  ├─ disk_temperature_profile(r, M)
  │     T(r) ∝ r^{-3/4} · [1 - √(r_isco / r)]^{1/4}
  │     normalised so peak T = 1
  │
  ├─ temperature_to_rgb(T)
  │     hot-metal palette:
  │       T < 0.3  →  dark red/orange
  │       T < 0.6  →  orange/yellow
  │       T ≥ 0.6  →  yellow → white
  │
  ├─ Doppler factor: 1 + 0.4 · sin(φ)
  │     approaching side (φ ≈ π/2)  is brighter
  │     receding side  (φ ≈ 3π/2) is dimmer
  │
  └─ radial fade: linear from 1 at r_isco to 0 at r_outer
```

---

## Background Star Field

For escaped photons, the pixel colour is computed from the photon's exit direction $(\theta_{exit}, \phi_{exit})$:

```python
seed = int(theta_exit * 1000) * 10000 + int(phi_exit * 1000)
rng  = seeded_random(seed)

if rng.random() < 0.008:   # ~0.8% are bright stars
    brightness = 0.7 + 0.3 * rng.random()
    return [brightness, brightness, brightness * 0.95]
else:
    v = 0.01 + 0.02 * rng.random()
    return [v * 0.4, v * 0.4, v]    # deep blue background
```

The seed is deterministic from the exit angles, so the same ray always produces the same star/sky. This prevents aliasing artifacts where neighbouring pixels that map to similar angles would get different random colours.

---

## Extension Points

| What to extend | Where | Notes |
|----------------|-------|-------|
| Different spacetime metric | `physics/geodesic.py` | Replace Christoffel symbols for Kerr, Reissner-Nordström, etc. |
| Different disk model | `renderer/disk.py` | Swap `disk_temperature_profile` and `disk_color` |
| Parallel rendering | `core/engine.py` | `Engine.render()` loop is embarrassingly parallel; add `multiprocessing.Pool` |
| Polarisation tracking | `physics/photon.py`, `renderer/` | Add polarisation vector to Photon state, parallel-transport along geodesic |
| Real star catalogues | `renderer/lensing_renderer.py` | Replace procedural `background_color` with catalogue lookup |
| Redshift mapping | `renderer/disk.py` + `renderer/lensing_renderer.py` | Use gravitational + Doppler redshift to shift RGB spectra |
| Interactive viewer | new `renderer/interactive.py` | Add matplotlib animations or a web canvas |
