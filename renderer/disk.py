"""
Accretion-disk colour model.

The thin accretion disk lies in the equatorial plane from r_isco to
r_outer.  We assign colour and brightness based on the radial position
using a simple temperature-profile model:

    T(r) ∝ r^{-3/4} [1 - √(r_isco / r)]^{1/4}

This comes from the Novikov-Thorne thin-disk model.  We map temperature
to colour via a simplified blackbody palette.
"""

import numpy as np
from physics.schwarzschild import isco_radius


def disk_temperature_profile(r: float, M: float) -> float:
    """
    Normalised temperature of the accretion disk at radius r.

    T(r) ∝ r^{-3/4} · [1 - sqrt(r_isco / r)]^{1/4}

    Returns a value in [0, 1] (normalised to peak temperature).
    """
    r_in = isco_radius(M)
    if r <= r_in:
        return 0.0
    raw = r**(-0.75) * max(0.0, 1.0 - np.sqrt(r_in / r))**0.25
    # Normalise so peak ≈ 1 (peak near ≈ 1.36 * r_isco)
    r_peak = 1.36 * r_in
    peak = r_peak**(-0.75) * max(0.0, 1.0 - np.sqrt(r_in / r_peak))**0.25
    if peak < 1e-15:
        return 0.0
    return raw / peak


def temperature_to_rgb(t_norm: float) -> np.ndarray:
    """
    Map a normalised temperature t ∈ [0, 1] to an RGB colour.

    Uses a simple hot-metal palette:
        cool  → dark red/orange
        hot   → bright yellow/white
    """
    t = np.clip(t_norm, 0.0, 1.0)
    r = np.clip(1.5 * t, 0.0, 1.0)
    g = np.clip(1.5 * t - 0.4, 0.0, 1.0)
    b = np.clip(2.0 * t - 1.2, 0.0, 1.0)
    return np.array([r, g, b])


def disk_color(r: float, phi: float, M: float,
               r_disk_outer: float) -> np.ndarray:
    """
    Compute the RGB colour for a disk-hit at coordinates (r, φ).

    Includes a simple Doppler-inspired azimuthal brightness variation:
    material orbiting in one direction appears brighter on the approaching
    side.  We model this as:

        brightness_factor = 1 + 0.4 · sin(φ)
    """
    r_in = isco_radius(M)
    if r < r_in or r > r_disk_outer:
        return np.zeros(3)

    t_norm = disk_temperature_profile(r, M)
    rgb = temperature_to_rgb(t_norm)

    # Doppler-like boost (simplified)
    doppler = 1.0 + 0.4 * np.sin(phi)

    # Radial fall-off beyond the bright inner region
    radial_fade = np.clip(1.0 - (r - r_in) / (r_disk_outer - r_in), 0.0, 1.0)

    brightness = t_norm * doppler * (0.3 + 0.7 * radial_fade)
    return np.clip(rgb * brightness, 0.0, 1.0)
