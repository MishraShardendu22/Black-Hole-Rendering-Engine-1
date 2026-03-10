import numpy as np

from physics.schwarzschild import isco_radius


def disk_temperature_profile(r: float, M: float) -> float:
    r_in = isco_radius(M)
    if r <= r_in:
        return 0.0
    raw = r ** (-0.75) * max(0.0, 1.0 - np.sqrt(r_in / r)) ** 0.25
    r_peak = 1.36 * r_in
    peak = r_peak ** (-0.75) * max(0.0, 1.0 - np.sqrt(r_in / r_peak)) ** 0.25
    if peak < 1e-15:
        return 0.0
    return raw / peak


def temperature_to_rgb(t_norm: float) -> np.ndarray:
    t = np.clip(t_norm, 0.0, 1.0)
    r = np.clip(1.5 * t, 0.0, 1.0)
    g = np.clip(1.5 * t - 0.4, 0.0, 1.0)
    b = np.clip(2.0 * t - 1.2, 0.0, 1.0)
    return np.array([r, g, b])


def disk_color(r: float, phi: float, M: float, r_disk_outer: float) -> np.ndarray:
    r_in = isco_radius(M)
    if r < r_in or r > r_disk_outer:
        return np.zeros(3)
    t_norm = disk_temperature_profile(r, M)
    rgb = temperature_to_rgb(t_norm)
    doppler = 1.0 + 0.4 * np.sin(phi)
    radial_fade = np.clip(1.0 - (r - r_in) / (r_disk_outer - r_in), 0.0, 1.0)
    brightness = t_norm * doppler * (0.3 + 0.7 * radial_fade)
    return np.clip(rgb * brightness, 0.0, 1.0)