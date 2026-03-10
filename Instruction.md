# Black Hole Visualization Engine — Phase 1

## Objective

Build a physically accurate visualization of a Schwarzschild black hole using Python scientific libraries.

The system simulates photon trajectories near a black hole and renders gravitational lensing and the black hole shadow.

---

# Tech Stack

Language

- Python 3.11+

Libraries

- numpy
- scipy
- matplotlib
- plotly (optional)
- pygame or moderngl (for interactive renderer)

---

# Physics Model

Use the Schwarzschild metric to simulate photon motion.

Important constants

G = gravitational constant  
M = black hole mass  
c = speed of light  

Schwarzschild radius:

r_s = 2GM / c²

Photon sphere radius:

r = 3GM / c²

Shadow diameter ≈ 5.2 r_s

---

# Project Structure

```

blackhole-engine/
│
├── math/
│   ├── vectors.py
│   ├── integrator.py
│
├── physics/
│   ├── schwarzschild.py
│   ├── geodesic.py
│   ├── photon.py
│
├── simulation/
│   ├── ray_emitter.py
│   ├── trajectory_solver.py
│
├── renderer/
│   ├── disk.py
│   ├── lensing_renderer.py
│   ├── plot_renderer.py
│
├── core/
│   ├── camera.py
│   ├── engine.py
│
├── experiments/
│   ├── photon_bending_notebook.ipynb
│
├── main.py
└── requirements.txt

```

---

# Stage 1 — Mathematical Foundations

Goal: derive and verify photon bending.

Tasks

1. Implement vector utilities.
2. Define Schwarzschild radius.
3. Implement coordinate system.
4. Create notebook deriving light bending.

Deliverable

`experiments/photon_bending_notebook.ipynb`

---

# Stage 2 — Photon Trajectory Solver

Goal: simulate photon paths.

Tasks

1. Implement geodesic equation solver.
2. Use SciPy ODE integrator.

Function

```

solve_photon_path(initial_position, initial_velocity)

```

Output

```

[(x,y,z), (x,y,z), ...]

```

Each element represents photon position during integration.

---

# Stage 3 — Static Visualization

Goal: visualize lensing and shadow.

Tasks

1. Plot photon trajectories.
2. Draw accretion disk.
3. Render black hole shadow.

Libraries

- matplotlib
- plotly

Output

```

output/lensing_render.png

```

---

# Stage 4 — Relativistic Effects

Add physical realism.

Implement:

- gravitational redshift
- relativistic Doppler shift
- relativistic beaming

Disk brightness must vary based on velocity and observer angle.

---

# Stage 5 — Ray Tracing Renderer

Goal: generate full image via ray tracing.

Pipeline

```

for pixel in screen:
emit photon
integrate trajectory
check disk intersection
compute color
write framebuffer

```

Camera parameters

- position
- orientation
- field of view

---

# Stage 6 — Interactive Renderer

Add real-time viewer.

Libraries

- pygame OR moderngl

Features

- camera movement
- real-time rendering
- disk rotation

---

# Stage 7 — Validation

Verify simulation matches theory.

Measure

Photon ring radius ≈ 3GM/c²

Shadow diameter ≈ 5.2 Schwarzschild radii

Compare output with published simulations.

---

# Performance Considerations

Use numpy vectorization when possible.

Limit integration step size.

Use multiprocessing for ray tracing.

---

# Final Deliverables

1. Photon trajectory solver
2. Static lensing renderer
3. Real-time interactive visualization
4. Validation plots comparing theory vs simulation

```

---

# GitHub Copilot Prompt

Use this prompt in a **new file or comment block** to guide Copilot.

```

You are implementing a computational physics project in Python.

Goal:
Build a Schwarzschild black hole visualization engine that simulates photon trajectories and renders gravitational lensing.

Requirements:

Use Python with the following libraries:

- numpy
- scipy
- matplotlib

Physics model:

Use the Schwarzschild metric for a non-rotating black hole.

Constants:
G = gravitational constant
M = black hole mass
c = speed of light

Schwarzschild radius:
r_s = 2GM / c²

Photon sphere radius:
r = 3GM / c²

Implement the following modules:

math/

- vector utilities
- numerical integration helpers

physics/

- Schwarzschild metric
- Christoffel symbols
- geodesic equation for photons

simulation/

- photon emitter
- photon trajectory solver using scipy.integrate.solve_ivp

renderer/

- static renderer using matplotlib
- visualize photon bending
- render accretion disk and black hole shadow

core/

- camera model
- simulation controller

Main algorithm:

For each ray:

1. Emit photon from camera
2. Integrate geodesic equation
3. Determine if photon:
   - escapes
   - falls into event horizon
   - intersects accretion disk
4. Compute color and brightness
5. Write result to image buffer

Rendering output:

Generate a 2D image showing:

- black hole shadow
- gravitational lensing
- accretion disk distortion

Prioritize readable modular scientific code.
Include docstrings explaining physics equations used.
