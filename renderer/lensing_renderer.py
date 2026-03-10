import numpy as np

from physics.photon import PhotonFate
from renderer.disk import disk_color


def background_color(theta: float, phi: float) -> np.ndarray:
    seed = int(abs(np.sin(theta * 127.1 + phi * 311.7) * 43758.5453)) % 1000
    if seed < 8:
        brightness = 0.6 + 0.4 * (seed / 8.0)
        return np.array([brightness, brightness, brightness * 0.95])
    return np.array([0.0, 0.0, 0.02])


def compute_pixel_color(photon, M: float, r_disk_outer: float) -> np.ndarray:
    if photon.fate == PhotonFate.CAPTURED:
        return np.array([0.0, 0.0, 0.0])

    if photon.fate == PhotonFate.HIT_DISK:
        r_hit = getattr(photon, 'disk_r', 0.0)
        phi_hit = getattr(photon, 'disk_phi', 0.0)
        return disk_color(r_hit, phi_hit, M, r_disk_outer)

    if len(photon.trajectory_theta) > 0:
        th = photon.trajectory_theta[-1]
        ph = photon.trajectory_phi[-1]
    else:
        th, ph = np.pi / 2, 0.0
    return background_color(th, ph)


def render_image(
    photon_grid: list,
    nx: int,
    ny: int,
    M: float,
    r_disk_outer: float,
) -> np.ndarray:
    image = np.zeros((ny, nx, 3))
    for i, j, photon in photon_grid:
        image[i, j] = compute_pixel_color(photon, M, r_disk_outer)
    return image