# Project Roadmap — Black Hole Visualization Engine

---

## Phase 1 — With Libraries

**Goal:** Produce physically accurate black hole render using existing scientific/graphics tools.

### Stage 1 — Foundations

* Learn equations: Schwarzschild metric, geodesics, gravitational lensing.
* Understand photon sphere, event horizon, accretion disk math.
* Deliverable: notebook deriving light bending formula.

### Stage 2 — Numerical Simulation

* Implement photon trajectory solver.
* Use:

  * `numpy` → vector math
  * `scipy` → ODE integrator
* Output: arrays of photon paths.

### Stage 3 — Static Rendering

* Plot ray paths.
* Render disk + shadow.
* Use:

  * `matplotlib` or `plotly`
* Deliverable: image showing lensing.

### Stage 4 — Physical Accuracy

* Add:

  * Doppler shift
  * Redshift
  * Relativistic beaming
* Deliverable: physically shaded frame.

### Stage 5 — Real-Time Renderer

* Use:

  * `pygame` or `moderngl`
* Implement camera movement + ray tracing.
* Deliverable: interactive simulation.

### Stage 6 — Validation

* Compare output to published simulations.
* Measure:

  * photon ring radius
  * shadow diameter

---

## Phase 2 — Without Libraries

**Goal:** Build everything from scratch.

### Stage 1 — Math Engine

Write custom:

* vector class
* matrix class
* differential solver
* integrator (Runge–Kutta)

### Stage 2 — Physics Core

Implement manually:

* spacetime metric tensor
* Christoffel symbols
* geodesic equation solver

### Stage 3 — Software Renderer

Build:

* pixel buffer
* raster display
* color mapper

No graphics libs.

### Stage 4 — Ray Tracer

Write custom engine:

* ray emitter
* collision detection with disk
* photon orbit detection
* light bending algorithm

### Stage 5 — Optimization

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
