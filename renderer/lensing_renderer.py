"""
Lensing renderer — maps photon fates to pixel colours.

After every photon has been traced, this module walks the image buffer
and assigns an RGB value to each pixel depending on the photon's fate:

    CAPTURED  → black  (shadow)
    HIT_DISK  → colour from the disk model
    ESCAPED   → background (star field or solid colour)
"""

import numpy as np

from physics.photon import PhotonFate
from renderer.disk import disk_color


def background_color(theta: float, phi: float) -> np.ndarray:
    """
    Simple procedural star-field / background for escaped photons.

    Stars are generated pseudo-randomly based on the exit angle.
    """
    # Deterministic "stars" via a hash-like function
    seed = int(abs(np.sin(theta * 127.1 + phi * 311.7) * 43758.5453)) % 1000
    if seed < 8:
        # Bright star
        brightness = 0.6 + 0.4 * (seed / 8.0)
        return np.array([brightness, brightness, brightness * 0.95])
    # Dark sky with faint blue tint
    return np.array([0.0, 0.0, 0.02])


def compute_pixel_color(photon, M: float, r_disk_outer: float) -> np.ndarray:
    """
    Determine the RGB colour for a single photon/pixel.

    Parameters
    ----------
    photon : Photon
        Traced photon with .fate and trajectory populated.
    M : float
        Black hole mass.
    r_disk_outer : float
        Outer edge of the accretion disk.

    Returns
    -------
    (3,) float array with values in [0, 1].
    """
    if photon.fate == PhotonFate.CAPTURED:
        return np.array([0.0, 0.0, 0.0])

    if photon.fate == PhotonFate.HIT_DISK:
        r_hit = getattr(photon, "disk_r", 0.0)
        phi_hit = getattr(photon, "disk_phi", 0.0)
        return disk_color(r_hit, phi_hit, M, r_disk_outer)

    # ESCAPED — use endpoint direction as background lookup
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
    """
    Convert a list of traced photons into an RGB image array.

    Parameters
    ----------
    photon_grid : list of (i, j, Photon)
        Each tuple contains pixel row, column, and traced Photon.
    nx, ny : int
        Image width and height.
    M : float
        Black hole mass.
    r_disk_outer : float
        Outer edge of accretion disk.

    Returns
    -------
    (ny, nx, 3) float array — the rendered image.
    """
    image = np.zeros((ny, nx, 3))
    for i, j, photon in photon_grid:
        image[i, j] = compute_pixel_color(photon, M, r_disk_outer)
    return image
