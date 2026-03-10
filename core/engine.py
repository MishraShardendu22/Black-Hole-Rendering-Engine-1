"""
Simulation engine — orchestrates ray emission, tracing, and rendering.

The Engine ties together the camera, ray emitter, trajectory solver,
and lensing renderer into a single streamlined pipeline.

Pipeline per frame:
    1. For each pixel, compute ray direction from the camera.
    2. Emit a photon along that direction.
    3. Integrate the geodesic equation.
    4. Determine photon fate (captured / escaped / hit disk).
    5. Assign colour and write into the image buffer.
"""

import sys
import time
import numpy as np

from core.camera import Camera
from simulation.ray_emitter import emit_ray
from simulation.trajectory_solver import solve_photon
from renderer.lensing_renderer import render_image, compute_pixel_color
from physics.photon import PhotonFate


class Engine:
    """
    Black-hole visualisation engine.

    Parameters
    ----------
    M : float
        Black hole mass in geometrised units (length).
    camera : Camera
        The observer's camera.
    r_disk_outer : float
        Outer radius of the accretion disk (multiples of M).
    lambda_max : float
        Maximum affine parameter for geodesic integration.
    r_max : float
        Escape radius.
    """

    def __init__(
        self,
        M: float = 1.0,
        camera: Camera | None = None,
        r_disk_outer: float = 20.0,
        lambda_max: float = 300.0,
        r_max: float = 200.0,
    ):
        self.M = M
        self.r_disk_outer = r_disk_outer
        self.lambda_max = lambda_max
        self.r_max = r_max

        if camera is None:
            # Default camera: positioned on the +x axis looking at the origin
            self.camera = Camera(
                position=np.array([30.0, 0.0, 5.0]),
                target=np.array([0.0, 0.0, 0.0]),
                fov_deg=60.0,
                resolution=(160, 120),
            )
        else:
            self.camera = camera

    def trace_single_ray(self, i: int, j: int):
        """Trace a single pixel (i, j) and return (i, j, photon)."""
        ray_dir = self.camera.ray_direction(i, j)
        photon = emit_ray(self.camera.position, ray_dir, self.M)
        solve_photon(
            photon,
            self.M,
            lambda_max=self.lambda_max,
            r_max=self.r_max,
            r_disk_outer=self.r_disk_outer,
        )
        return i, j, photon

    def render(self, progress: bool = True) -> np.ndarray:
        """
        Render the full image by tracing all pixels.

        Parameters
        ----------
        progress : bool
            Print a progress bar to stderr.

        Returns
        -------
        (ny, nx, 3) float image array.
        """
        nx, ny = self.camera.nx, self.camera.ny
        total = nx * ny
        traced = []

        t0 = time.time()
        for idx, (i, j) in enumerate(
            ((i, j) for i in range(ny) for j in range(nx))
        ):
            result = self.trace_single_ray(i, j)
            traced.append(result)
            if progress and (idx + 1) % max(1, total // 40) == 0:
                pct = 100.0 * (idx + 1) / total
                elapsed = time.time() - t0
                sys.stderr.write(
                    f"\r  Tracing rays: {pct:5.1f}% "
                    f"({idx+1}/{total})  [{elapsed:.1f}s]"
                )
                sys.stderr.flush()

        if progress:
            elapsed = time.time() - t0
            sys.stderr.write(
                f"\r  Tracing rays: 100.0% "
                f"({total}/{total})  [{elapsed:.1f}s]\n"
            )
            sys.stderr.flush()

        image = render_image(traced, nx, ny, self.M, self.r_disk_outer)
        return image

    def summary(self, photon_grid: list) -> dict:
        """Return a count of photon fates for diagnostics."""
        counts = {f: 0 for f in PhotonFate}
        for _, _, p in photon_grid:
            counts[p.fate] += 1
        return counts
