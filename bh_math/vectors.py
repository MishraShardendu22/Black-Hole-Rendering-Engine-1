"""
Vector utilities for 3D and 4D operations in curved spacetime.

Provides helper functions for vector arithmetic used in photon
trajectory calculations near a Schwarzschild black hole.
"""

import numpy as np


def normalize(v: np.ndarray) -> np.ndarray:
    """Return the unit vector of v."""
    norm = np.linalg.norm(v)
    if norm == 0.0:
        return v
    return v / norm


def magnitude(v: np.ndarray) -> float:
    """Return the Euclidean magnitude of v."""
    return float(np.linalg.norm(v))


def cartesian_to_spherical(x: float, y: float, z: float) -> tuple:
    """
    Convert Cartesian (x, y, z) to spherical (r, theta, phi).

    r     = sqrt(x² + y² + z²)
    theta = arccos(z / r)          — polar angle from +z axis
    phi   = arctan2(y, x)          — azimuthal angle in xy-plane
    """
    r = np.sqrt(x**2 + y**2 + z**2)
    if r == 0.0:
        return 0.0, 0.0, 0.0
    theta = np.arccos(np.clip(z / r, -1.0, 1.0))
    phi = np.arctan2(y, x)
    return float(r), float(theta), float(phi)


def spherical_to_cartesian(r: float, theta: float, phi: float) -> np.ndarray:
    """
    Convert spherical (r, theta, phi) to Cartesian (x, y, z).

    x = r sin(theta) cos(phi)
    y = r sin(theta) sin(phi)
    z = r cos(theta)
    
    """
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return np.array([x, y, z])


def cartesian_velocity_to_spherical(pos_cart: np.ndarray, vel_cart: np.ndarray) -> tuple:
    """
    Transform a Cartesian velocity vector to spherical coordinate velocities.

    Given position (x, y, z) and velocity (vx, vy, vz), returns (vr, vtheta, vphi).

    Uses the Jacobian of the Cartesian-to-spherical transformation.
    """
    x, y, z = pos_cart
    vx, vy, vz = vel_cart
    r = np.sqrt(x**2 + y**2 + z**2)
    rho = np.sqrt(x**2 + y**2)

    if r < 1e-15:
        return 0.0, 0.0, 0.0

    vr = (x * vx + y * vy + z * vz) / r

    if rho < 1e-15:
        vtheta = 0.0
        vphi = 0.0
    else:
        vtheta = (z * (x * vx + y * vy) - rho**2 * vz) / (r**2 * rho)
        vphi = (x * vy - y * vx) / rho**2

    return float(vr), float(vtheta), float(vphi)


def rotation_matrix_y(angle: float) -> np.ndarray:
    """Return the 3×3 rotation matrix about the y-axis by *angle* radians."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [ c, 0, s],
        [ 0, 1, 0],
        [-s, 0, c],
    ])


def rotation_matrix_x(angle: float) -> np.ndarray:
    """Return the 3×3 rotation matrix about the x-axis by *angle* radians."""
    c, s = np.cos(angle), np.sin(angle)
    return np.array([
        [1,  0, 0],
        [0,  c, -s],
        [0,  s,  c],
    ])
