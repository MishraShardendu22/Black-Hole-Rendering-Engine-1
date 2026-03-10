"""
Schwarzschild metric and related quantities.

The Schwarzschild line element in geometrised units (G = c = 1) reads:

    ds² = -(1 - r_s/r) dt² + (1 - r_s/r)⁻¹ dr² + r² dΩ²

where r_s = 2M is the Schwarzschild radius and dΩ² = dθ² + sin²θ dφ².

Throughout this module we work in *geometrised* units so the only free
parameter is M (the black hole mass in length units).
"""

import numpy as np

# ---------------------------------------------------------------------------
# Physical constants (SI) — used only when converting to/from SI.
# ---------------------------------------------------------------------------
G_SI = 6.67430e-11       # m³ kg⁻¹ s⁻²
C_SI = 2.99792458e8      # m s⁻¹
M_SUN_KG = 1.98892e30    # kg


def schwarzschild_radius(M: float) -> float:
    """
    Schwarzschild radius in geometrised units.

        r_s = 2M

    (In SI: r_s = 2GM/c².)
    """
    return 2.0 * M


def photon_sphere_radius(M: float) -> float:
    """
    Photon sphere radius: the unstable circular orbit for photons.

        r_ph = 3M

    (In SI: r_ph = 3GM/c².)
    """
    return 3.0 * M


def isco_radius(M: float) -> float:
    """
    Innermost stable circular orbit (ISCO) for massive particles.

        r_isco = 6M

    Used as the inner edge of a thin accretion disk.
    """
    return 6.0 * M


# ---------------------------------------------------------------------------
# Metric components  g_{μν}  in Schwarzschild coordinates (t, r, θ, φ).
# ---------------------------------------------------------------------------

def metric_tt(r: float, M: float) -> float:
    """g_{tt} = -(1 - r_s / r)."""
    return -(1.0 - 2.0 * M / r)


def metric_rr(r: float, M: float) -> float:
    """g_{rr} = (1 - r_s / r)⁻¹."""
    return 1.0 / (1.0 - 2.0 * M / r)


def metric_thth(r: float) -> float:
    """g_{θθ} = r²."""
    return r * r


def metric_phph(r: float, theta: float) -> float:
    """g_{φφ} = r² sin²θ."""
    return r * r * np.sin(theta) ** 2


# ---------------------------------------------------------------------------
# Effective potential for photon orbits (equatorial, per unit E²).
#
#   V_eff(r) = (1 - r_s/r) L² / r²
#
# A photon with impact parameter b = L/E has turning points where
# V_eff(r) = 1.
# ---------------------------------------------------------------------------

def effective_potential(r: np.ndarray, M: float, L: float) -> np.ndarray:
    """
    Effective radial potential for a photon with angular momentum L.

        V_eff(r) = (1 - 2M/r) · L² / r²
    """
    return (1.0 - 2.0 * M / r) * L**2 / r**2


def critical_impact_parameter(M: float) -> float:
    """
    Critical impact parameter: photons with b = b_c are captured
    onto the photon sphere.

        b_c = 3√3 · M

    (In SI: b_c = 3√3 GM / c².)
    """
    return 3.0 * np.sqrt(3.0) * M
