import ctypes
import os
import sys
import time

import numpy as np

from core.camera import Camera
from simulation.ray_emitter import emit_ray
from simulation.trajectory_solver import solve_photon
from renderer.lensing_renderer import render_image, compute_pixel_color
from physics.photon import PhotonFate
from bh_math.vectors import cartesian_to_spherical, cartesian_velocity_to_spherical, normalize

_go_lib = None
_GO_LIB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'librender.so')


def _load_go_lib():
    global _go_lib
    if _go_lib is not None:
        return _go_lib
    if not os.path.isfile(_GO_LIB_PATH):
        return None
    _go_lib = ctypes.CDLL(_GO_LIB_PATH)
    _go_lib.RenderBatch.argtypes = [
        ctypes.POINTER(ctypes.c_double),  # photons
        ctypes.c_int,                     # n_pixels
        ctypes.c_double,                  # mass
        ctypes.c_double,                  # spin
        ctypes.c_double,                  # r_outer
        ctypes.c_double,                  # r_max
        ctypes.c_int,                     # enable_redshift
        ctypes.c_int,                     # enable_doppler
        ctypes.c_int,                     # enable_beaming
        ctypes.POINTER(ctypes.c_float),   # out_rgb
    ]
    _go_lib.RenderBatch.restype = None
    _go_lib.TracePixel.argtypes = [
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    _go_lib.TracePixel.restype = None
    return _go_lib


class Engine:

    def __init__(
        self,
        M: float = 1.0,
        camera: Camera | None = None,
        r_disk_outer: float = 20.0,
        lambda_max: float = 300.0,
        r_max: float = 200.0,
        spin: float = 0.0,
        enable_redshift: bool = True,
        enable_doppler: bool = True,
        enable_beaming: bool = True,
    ):
        self.M = M
        self.r_disk_outer = r_disk_outer
        self.lambda_max = lambda_max
        self.r_max = r_max
        self.spin = spin
        self.enable_redshift = enable_redshift
        self.enable_doppler = enable_doppler
        self.enable_beaming = enable_beaming

        if camera is None:
            self.camera = Camera(
                position=np.array([30.0, 0.0, 5.0]),
                target=np.array([0.0, 0.0, 0.0]),
                fov_deg=60.0,
                resolution=(160, 120),
            )
        else:
            self.camera = camera

    def _build_photon_array(self) -> np.ndarray:
        nx, ny = self.camera.nx, self.camera.ny
        photons = np.empty((ny * nx, 6), dtype=np.float64)
        idx = 0
        for i in range(ny):
            for j in range(nx):
                ray_dir = self.camera.ray_direction(i, j)
                direction = normalize(ray_dir)
                vel_cart = direction * 1.0
                cam = self.camera.position
                r, theta, phi = cartesian_to_spherical(*cam)
                vr, vtheta, vphi = cartesian_velocity_to_spherical(cam, vel_cart)
                photons[idx] = [r, theta, phi, vr, vtheta, vphi]
                idx += 1
        return photons

    def trace_single_ray(self, i: int, j: int):
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
        lib = _load_go_lib()
        if lib is not None:
            return self._render_go(lib, progress)
        return self._render_python(progress)

    def _render_go(self, lib, progress: bool) -> np.ndarray:
        nx, ny = self.camera.nx, self.camera.ny
        n = nx * ny

        if progress:
            sys.stderr.write('  Building photon array...\n')
            sys.stderr.flush()

        photons_flat = self._build_photon_array()
        inp = photons_flat.astype(np.float64).flatten()
        out = (ctypes.c_float * (n * 3))()
        inp_ptr = inp.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

        if progress:
            sys.stderr.write(f'  Tracing {n} rays via Go engine...\n')
            sys.stderr.flush()

        t0 = time.time()
        lib.RenderBatch(
            inp_ptr, n,
            self.M, self.spin, self.r_disk_outer, self.r_max,
            int(self.enable_redshift), int(self.enable_doppler), int(self.enable_beaming),
            out,
        )
        elapsed = time.time() - t0

        if progress:
            sys.stderr.write(f'  Done in {elapsed:.1f}s\n')
            sys.stderr.flush()

        rgb = np.frombuffer(out, dtype=np.float32).reshape(ny, nx, 3).copy()
        return rgb

    def _render_python(self, progress: bool) -> np.ndarray:
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
                    f'\r  Tracing rays: {pct:5.1f}%'
                    f' ({idx + 1}/{total})  [{elapsed:.1f}s]'
                )
                sys.stderr.flush()

        if progress:
            elapsed = time.time() - t0
            sys.stderr.write(
                f'\r  Tracing rays: 100.0% ({total}/{total})  [{elapsed:.1f}s]\n'
            )
            sys.stderr.flush()

        image = render_image(traced, nx, ny, self.M, self.r_disk_outer)
        return image

    def summary(self, photon_grid: list) -> dict:
        counts = {f: 0 for f in PhotonFate}
        for _, _, p in photon_grid:
            counts[p.fate] += 1
        return counts