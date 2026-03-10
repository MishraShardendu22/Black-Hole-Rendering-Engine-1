import numpy as np

from bh_math.vectors import (
    cartesian_to_spherical,
    cartesian_velocity_to_spherical,
    normalize,
)
from physics.photon import Photon


def emit_ray(
    cam_pos_cart: np.ndarray,
    ray_dir_cart: np.ndarray,
    M: float,
) -> Photon:
    r, theta, phi = cartesian_to_spherical(*cam_pos_cart)
    direction = normalize(ray_dir_cart)
    speed = 1.0
    vel_cart = direction * speed
    vr, vtheta, vphi = cartesian_velocity_to_spherical(cam_pos_cart, vel_cart)
    return Photon(r, theta, phi, vr, vtheta, vphi)


def emit_ray_grid(
    cam_pos_cart: np.ndarray,
    forward: np.ndarray,
    up: np.ndarray,
    fov_deg: float,
    nx: int,
    ny: int,
    M: float,
) -> list:
    forward = normalize(forward)
    right = normalize(np.cross(forward, up))
    up = np.cross(right, forward)

    aspect = nx / ny
    fov_rad = np.deg2rad(fov_deg)
    half_w = np.tan(fov_rad / 2.0)
    half_h = half_w / aspect

    photons = []
    for i in range(ny):
        v = 1.0 - 2.0 * (i + 0.5) / ny
        for j in range(nx):
            u = -1.0 + 2.0 * (j + 0.5) / nx
            ray_dir = normalize(forward + u * half_w * right + v * half_h * up)
            photon = emit_ray(cam_pos_cart, ray_dir, M)
            photons.append((i, j, photon))
    return photons