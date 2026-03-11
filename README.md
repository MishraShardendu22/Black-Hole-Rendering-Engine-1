# Hlack-Bole

> A physically accurate Schwarzschild black hole renderer with backward ray tracing, General Relativity geodesics, and a real-time interactive Go viewer.

![Lensing Render](output/lensing_render.png)

---

## What Is This?

Hlack-Bole simulates how light bends around a non-rotating (Schwarzschild) black hole. For every pixel in the output image, a photon is traced **backwards** from the camera through curved spacetime. Its trajectory is governed by the **Schwarzschild geodesic equations** and numerically integrated with RK45. The photon is then classified as one of three outcomes:

| Fate | Visual result |
|---|---|
| **Captured** | Falls into the event horizon → black shadow |
| **Escaped** | Reaches infinity → procedural star field |
| **Hit disk** | Crosses the equatorial accretion disk → temperature-coloured glow |

The project has two independent implementations:

- **Python** — batch offline renderer, outputs a PNG
- **Go** — real-time interactive viewer (Ebiten) + shared library (`librender.so`) callable from Python via ctypes

**Physics model:** Schwarzschild metric in geometrised units ($G = c = 1$)

---

## Features

- Backward ray tracing through Schwarzschild curved spacetime
- Schwarzschild geodesic ODE integration (Christoffel symbols, RK45 adaptive step)
- Black hole shadow (photon capture cross-section)
- Thin accretion disk with Novikov–Thorne temperature profile
- Doppler-like azimuthal brightness variation across the disk
- Gravitational redshift modelled via radial brightness falloff
- Relativistic beaming toggle
- Real-time interactive Go viewer — orbit the camera with keyboard controls
- Optional Kerr spin parameter `a` (experimental)

---

## Project Structure

```
Hlack-Bole/
├── main.py                      # Python CLI entry point
├── requirements.txt             # Python dependencies
├── Makefile                     # Build targets
├── librender.h / librender.so   # Generated: Go shared library
├── hlack-bole-live              # Generated: interactive binary
│
├── core/
│   ├── camera.py                # Pinhole camera, ray direction computation
│   └── engine.py                # Render loop orchestrator (Python)
│
├── physics/
│   ├── schwarzschild.py         # Metric functions, key radii (r_s, r_isco, r_ph)
│   ├── geodesic.py              # Christoffel symbols + geodesic ODE RHS
│   └── photon.py                # Photon data model and PhotonFate enum
│
├── bh_math/
│   ├── vectors.py               # Coordinate transforms, vector utilities
│   └── integrator.py            # SciPy ODE wrapper
│
├── simulation/
│   ├── ray_emitter.py           # Camera ray → spherical photon initial state
│   └── trajectory_solver.py     # Geodesic integration + disk/horizon detection
│
├── renderer/
│   ├── disk.py                  # Accretion disk colour and temperature model
│   ├── lensing_renderer.py      # Per-pixel colour from photon fate
│   └── plot_renderer.py         # Matplotlib PNG output
│
└── gocore/                      # Go implementation
    ├── render.go                # C-exported RenderBatch / TracePixel (shared lib)
    ├── go.mod
    ├── bh_math/vectors.go
    ├── core/engine.go           # Go render engine
    ├── physics/
    │   ├── geodesic.go
    │   ├── schwarzschild.go
    │   ├── kerr.go
    │   └── photon.go
    ├── renderer/
    │   ├── disk.go
    │   └── lensing.go
    ├── simulation/solver.go
    └── cmd/interactive/main.go  # Real-time Ebiten viewer
```

---

## Prerequisites

### Python renderer

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| numpy | ≥ 1.24 |
| scipy | ≥ 1.10 |
| matplotlib | ≥ 3.7 |

### Go interactive viewer / shared library

| Requirement | Notes |
|---|---|
| Go | 1.21+ |
| GCC | For CGo compilation |
| X11 dev headers | `libx11-dev`, `libxrandr-dev`, `libxi-dev`, `libxcursor-dev`, `libxinerama-dev` |
| libXxf86vm | `libxxf86vm-dev` (required by Ebiten/GLFW) |

On Fedora/RHEL:
```bash
sudo dnf install libX11-devel libXrandr-devel libXi-devel libXcursor-devel \
                 libXinerama-devel libXxf86vm-devel mesa-libGL-devel
```

On Ubuntu/Debian:
```bash
sudo apt install libx11-dev libxrandr-dev libxi-dev libxcursor-dev \
                 libxinerama-dev libxxf86vm-dev libgl1-mesa-dev
```

---

## Installation

```bash
git clone <repo-url>
cd Hlack-Bole
pip install -r requirements.txt
```

---

## Usage

### Python — offline batch render

```bash
# Quick render at default resolution (160×120)
python main.py

# Medium quality
python main.py --resolution 320x240

# High quality
python main.py --resolution 640x480

# Custom camera and disk setup
python main.py --resolution 320x240 --inclination 85 --distance 25 --disk-outer 18

# Disable relativistic effects for comparison
python main.py --redshift 0 --doppler 0 --beaming 0
```

Output is saved to `output/lensing_render.png` by default.

#### CLI Options

| Flag | Default | Description |
|---|---|---|
| `--resolution` | `160x120` | Output image size `WxH` |
| `--fov` | `60` | Horizontal field of view in degrees |
| `--mass` | `1.0` | Black hole mass in geometrised units |
| `--distance` | `30.0` | Camera distance from the black hole (units of M) |
| `--inclination` | `80.0` | Camera polar angle from the spin axis (degrees) |
| `--disk-outer` | `20.0` | Outer radius of accretion disk (units of M) |
| `--output` | `output/lensing_render.png` | Output file path |
| `--spin` | `0.0` | Kerr spin parameter `a` (0 ≤ a < M) |
| `--redshift` | `1` | Enable gravitational redshift (0 or 1) |
| `--doppler` | `1` | Enable relativistic Doppler shift (0 or 1) |
| `--beaming` | `1` | Enable relativistic beaming (0 or 1) |

> Render time scales as O(W × H). A 160×120 render completes in seconds; 640×480 takes several minutes on a single CPU core.

---

### Go — build targets

```bash
# Build the shared library (librender.so + librender.h)
make build-go

# Build the real-time interactive viewer
make build-interactive

# Run the Python renderer at 320×240
make run

# Launch the interactive Go viewer
make run-interactive

# Remove all build artefacts
make clean
```

### Go interactive viewer controls

| Key | Action |
|---|---|
| `W / S` | Increase / decrease camera distance |
| `A / D` | Orbit camera azimuth |
| `Q / E` | Change camera inclination |
| `+ / -` | Zoom field of view |
| `R` | Reset to defaults |
| `P` | Save current frame as PNG |

---

## How It Works

### Pipeline (per pixel)

```
Camera.ray_direction(i, j)
        │
        ▼
emit_ray()   ← converts Cartesian ray to spherical initial state [r, θ, φ, ṙ, θ̇, φ̇]
        │
        ▼
solve_photon()  ← RK45 integrates geodesic_rhs_3d() until horizon or escape
        │
        ├─ CAPTURED  → black pixel
        ├─ HIT_DISK  → disk_color(r, φ, M)   ← Novikov–Thorne T(r) → RGB
        └─ ESCAPED   → background_color(θ, φ) ← procedural star field
```

### Geodesic integration

The ODE state vector is $y = [r, \theta, \phi, \dot{r}, \dot{\theta}, \dot{\phi}]$. The RHS evaluates the Schwarzschild Christoffel symbols $\Gamma^\mu_{\alpha\beta}$ at each step and enforces the null condition $g_{\mu\nu}\dot{x}^\mu\dot{x}^\nu = 0$ to derive $\dot{t}$.

Terminal events stop integration early:
- **Horizon event:** $r \leq 1.02 \, r_s$ (direction = −1)
- **Escape event:** $r \geq r_\text{max}$ (direction = +1)

Disk crossings are detected as sign changes in $\theta(\lambda) - \pi/2$, with the crossing radius linearly interpolated between steps.

### Accretion disk colour model

The disk temperature follows the **Novikov–Thorne thin-disk profile**:

$$T(r) \propto r^{-3/4} \left(1 - \sqrt{\frac{r_\text{isco}}{r}}\right)^{1/4}$$

This normalised temperature is mapped to RGB with a black-body–inspired colour ramp (dark orange → yellow → white). Doppler brightening applies a $\sin\phi$ modulation and a radial fade toward the outer edge.

---

## Architecture

```
┌──────────────────────────────────────┐
│               main.py                │
│         CLI parsing · entry          │
└────────────────┬─────────────────────┘
                 │
     ┌───────────▼───────────┐
     │         core/         │
     │   Camera · Engine     │
     └──────┬────────┬───────┘
            │        │
  ┌─────────▼──┐  ┌──▼─────────────────┐
  │ simulation/│  │     renderer/      │
  │ Ray Emitter│  │ LensingRenderer    │
  │ Traj Solver│  │ DiskColorModel     │
  └─────┬──────┘  │ PlotRenderer       │
        │          └────────────────────┘
  ┌─────▼──────┐
  │  physics/  │
  │Schwarzschild│
  │  Geodesic  │
  │   Photon   │
  └─────┬──────┘
        │
  ┌─────▼──────┐
  │  bh_math/  │
  │ Vectors    │
  │ Integrator │
  └────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full dependency graph and per-pixel execution sequence, and [EXPLANATION.md](EXPLANATION.md) for a file-by-file code walkthrough.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Physics Reference

The Schwarzschild line element in geometrised units:

```
ds² = -(1 - 2M/r) dt² + (1 - 2M/r)⁻¹ dr² + r² dθ² + r² sin²θ dφ²
```

| Quantity | Value | Physical meaning |
|---|---|---|
| Event horizon | r = 2M | Photons inside are not traced |
| Photon sphere | r = 3M | Unstable circular photon orbit |
| ISCO | r = 6M | Inner edge of the accretion disk |
| Critical impact parameter | bₐ = 3√3 M | Photons with b < bₐ are captured |

Photon motion is governed by the null geodesic equation:

```
d²x^μ/dλ² + Γ^μ_{αβ} (dx^α/dλ)(dx^β/dλ) = 0
```

The Christoffel symbols `Γ^μ_{αβ}` are computed analytically from the Schwarzschild metric. The null condition `g_{μν} dx^μ dx^ν = 0` is enforced at each integration step to reconstruct `dt/dλ`.

---

## Rendering Pipeline

```
For each pixel (i, j):
  1. Camera.ray_direction(i, j)          → Cartesian unit ray vector
  2. emit_ray(pos, dir, M)               → Photon in spherical coords
  3. solve_photon(photon, M, ...)        → Integrate geodesic (RK45)
     ├─ horizon event → PhotonFate.CAPTURED
     ├─ escape event  → PhotonFate.ESCAPED
     └─ disk crossing → PhotonFate.HIT_DISK
  4. compute_pixel_color(photon)         → RGB value
     ├─ CAPTURED  → black
     ├─ HIT_DISK  → disk_color(r, φ)    (Novikov-Thorne + Doppler)
     └─ ESCAPED   → background_color(θ, φ) (procedural stars)
  5. Write pixel to image buffer
```

---

## Development Roadmap

### Phase 1 — Library-Based Renderer (current)

- [x] Schwarzschild metric and Christoffel symbols
- [x] Full 3D geodesic ODE solver (RK45 via SciPy)
- [x] Event horizon and escape detection
- [x] Thin accretion disk (ISCO to outer radius)
- [x] Novikov-Thorne temperature profile
- [x] Doppler-like azimuthal brightness variation
- [x] Procedural star field for escaped rays
- [x] CLI with configurable camera and physics parameters

### Phase 2 — Physical Accuracy

- [ ] Gravitational redshift on disk emission
- [ ] Relativistic Doppler shift (full formula)
- [ ] Relativistic beaming
- [ ] Physically shaded frames

### Phase 3 — Real-Time Renderer

- [ ] Interactive camera (pygame / moderngl)
- [ ] GPU-accelerated ray tracing
- [ ] Kerr metric (rotating black holes)

### Phase 4 — From-Scratch Engine

- [ ] Custom vector and matrix library
- [ ] Custom Runge–Kutta integrator
- [ ] Custom pixel buffer and rasteriser
- [ ] No external dependencies

---

## Output

The renderer writes a PNG to `output/lensing_render.png` by default. The image is saved via matplotlib with a black background at 150 DPI.

For trajectory visualisation and effective-potential plots, use the utilities in `renderer/plot_renderer.py` directly.

---

## License

MIT


Implement:

* spatial partitioning
* multithreading
* fixed-step integrator tuning

### Stage 6 — Engine Architecture

Structure modules:

```md
math/
physics/
renderer/
core/
```

### Stage 7 — Verification

Check:

* light deflection angle vs theory
* orbit stability
* energy conservation

---

## Skill Stack Required

* Differential geometry
* Numerical methods
* Computational physics
* Linear algebra
* Rendering pipelines

---

## Final Deliverables

Phase 1 → Accurate simulation using tools
Phase 2 → Fully self-built relativistic rendering engine

---
