"""
Geodesic equation for photons in the Schwarzschild spacetime.

For a photon (ds² = 0) the motion is governed by the conserved quantities
E (energy) and L (angular momentum) and the effective-potential formalism.

In the equatorial plane (θ = π/2) of a Schwarzschild black hole of mass M
the 2nd-order geodesic equations reduce to:

    d²r/dλ² = - Γʳ_{μν} (dx^μ/dλ)(dx^ν/dλ)

with Christoffel symbols computed from the Schwarzschild metric.

We cast this as a first-order system for use with scipy.integrate.solve_ivp.
"""

import numpy as np


# ── Christoffel symbols (non-zero, Schwarzschild) ──────────────────────────
#
# The only non-trivial independent components are:
#
#   Γʳ_tt  = M(r-2M) / r³
#   Γʳ_rr  = -M / [r(r-2M)]
#   Γʳ_θθ  = -(r - 2M)
#   Γʳ_φφ  = -(r - 2M) sin²θ
#   Γᶿ_rθ  = 1/r
#   Γᶿ_φφ  = -sinθ cosθ
#   Γᵠ_rφ  = 1/r
#   Γᵠ_θφ  = cosθ / sinθ
# ───────────────────────────────────────────────────────────────────────────


def christoffel_r(r: float, theta: float, M: float,
                  dt: float, dr: float, dtheta: float, dphi: float) -> float:
    """
    Compute  -Γʳ_{μν} U^μ U^ν  (the r-acceleration).

    Parameters are the coordinate values and the 4-velocity components
    (derivatives w.r.t. affine parameter λ).
    """
    rs = 2.0 * M
    f = 1.0 - rs / r

    term_tt = M * f / r**2 * dt**2
    term_rr = -M / (r**2 * f) * dr**2
    term_thth = -f * r * dtheta**2
    term_phph = -f * r * np.sin(theta)**2 * dphi**2

    return -(term_tt + term_rr + term_thth + term_phph)


def christoffel_theta(r: float, theta: float,
                      dr: float, dtheta: float, dphi: float) -> float:
    """Compute  -Γᶿ_{μν} U^μ U^ν  (the θ-acceleration)."""
    term_rth = 2.0 / r * dr * dtheta
    term_phph = -np.sin(theta) * np.cos(theta) * dphi**2
    return -(term_rth + term_phph)


def christoffel_phi(r: float, theta: float,
                    dr: float, dtheta: float, dphi: float) -> float:
    """Compute  -Γᵠ_{μν} U^μ U^ν  (the φ-acceleration)."""
    sin_th = np.sin(theta)
    cos_th = np.cos(theta)
    if abs(sin_th) < 1e-15:
        cot = 0.0
    else:
        cot = cos_th / sin_th

    term_rphi = 2.0 / r * dr * dphi
    term_thphi = 2.0 * cot * dtheta * dphi
    return -(term_rphi + term_thphi)


def geodesic_rhs_full(lam, state, M):
    """
    Right-hand side of the full 3D geodesic equation in Schwarzschild
    coordinates (no equatorial-plane restriction).

    State vector:
        state = [t, r, θ, φ, dt/dλ, dr/dλ, dθ/dλ, dφ/dλ]

    Returns d(state)/dλ.
    """
    t, r, theta, phi, dt_dl, dr_dl, dth_dl, dphi_dl = state

    rs = 2.0 * M
    # Prevent singularity inside the horizon
    if r <= rs * 1.01:
        return np.zeros(8)

    f = 1.0 - rs / r

    # dt/dλ acceleration  (Γᵗ_{tr} = M / [r(r-2M)])
    d2t = -2.0 * M / (r**2 * f) * dr_dl * dt_dl

    d2r = christoffel_r(r, theta, M, dt_dl, dr_dl, dth_dl, dphi_dl)
    d2th = christoffel_theta(r, theta, dr_dl, dth_dl, dphi_dl)
    d2phi = christoffel_phi(r, theta, dr_dl, dth_dl, dphi_dl)

    return np.array([dt_dl, dr_dl, dth_dl, dphi_dl,
                     d2t, d2r, d2th, d2phi])


def geodesic_rhs_3d(lam, state, M):
    """
    Simplified 3-spatial geodesic RHS (drop t-coordinate tracking).

    State vector:
        state = [r, θ, φ, dr/dλ, dθ/dλ, dφ/dλ]

    We still need dt/dλ for the r-acceleration, so we reconstruct it
    from the null condition  g_{μν} dx^μ dx^ν = 0:

        (dt/dλ)² = [ g_{rr} (dr/dλ)² + r² (dθ/dλ)² + r² sin²θ (dφ/dλ)² ] / |g_{tt}|
    """
    r, theta, phi, dr_dl, dth_dl, dphi_dl = state

    rs = 2.0 * M
    if r <= rs * 1.01:
        return np.zeros(6)

    f = 1.0 - rs / r
    sin_th = np.sin(theta)

    dt_dl_sq = (dr_dl**2 / f + r**2 * dth_dl**2 + r**2 * sin_th**2 * dphi_dl**2) / f
    dt_dl_sq = max(dt_dl_sq, 0.0)
    dt_dl = np.sqrt(dt_dl_sq)

    d2r = christoffel_r(r, theta, M, dt_dl, dr_dl, dth_dl, dphi_dl)
    d2th = christoffel_theta(r, theta, dr_dl, dth_dl, dphi_dl)
    d2phi = christoffel_phi(r, theta, dr_dl, dth_dl, dphi_dl)

    return np.array([dr_dl, dth_dl, dphi_dl, d2r, d2th, d2phi])
