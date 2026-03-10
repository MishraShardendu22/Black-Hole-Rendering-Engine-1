import numpy as np


def christoffel_r(
    r: float, theta: float, M: float,
    dt: float, dr: float, dtheta: float, dphi: float,
) -> float:
    rs = 2.0 * M
    f = 1.0 - rs / r
    term_tt = M * f / r ** 2 * dt ** 2
    term_rr = -M / (r ** 2 * f) * dr ** 2
    term_thth = -f * r * dtheta ** 2
    term_phph = -f * r * np.sin(theta) ** 2 * dphi ** 2
    return -(term_tt + term_rr + term_thth + term_phph)


def christoffel_theta(
    r: float, theta: float,
    dr: float, dtheta: float, dphi: float,
) -> float:
    term_rth = 2.0 / r * dr * dtheta
    term_phph = -np.sin(theta) * np.cos(theta) * dphi ** 2
    return -(term_rth + term_phph)


def christoffel_phi(
    r: float, theta: float,
    dr: float, dtheta: float, dphi: float,
) -> float:
    sin_th = np.sin(theta)
    cos_th = np.cos(theta)
    cot = 0.0 if abs(sin_th) < 1e-15 else cos_th / sin_th
    term_rphi = 2.0 / r * dr * dphi
    term_thphi = 2.0 * cot * dtheta * dphi
    return -(term_rphi + term_thphi)


def geodesic_rhs_full(lam, state, M):
    t, r, theta, phi, dt_dl, dr_dl, dth_dl, dphi_dl = state
    rs = 2.0 * M
    if r <= rs * 1.01:
        return np.zeros(8)
    f = 1.0 - rs / r
    d2t = -2.0 * M / (r ** 2 * f) * dr_dl * dt_dl
    d2r = christoffel_r(r, theta, M, dt_dl, dr_dl, dth_dl, dphi_dl)
    d2th = christoffel_theta(r, theta, dr_dl, dth_dl, dphi_dl)
    d2phi = christoffel_phi(r, theta, dr_dl, dth_dl, dphi_dl)
    return np.array([dt_dl, dr_dl, dth_dl, dphi_dl, d2t, d2r, d2th, d2phi])


def geodesic_rhs_3d(lam, state, M):
    r, theta, phi, dr_dl, dth_dl, dphi_dl = state
    rs = 2.0 * M
    if r <= rs * 1.01:
        return np.zeros(6)
    f = 1.0 - rs / r
    sin_th = np.sin(theta)
    dt_dl_sq = (
        dr_dl ** 2 / f
        + r ** 2 * dth_dl ** 2
        + r ** 2 * sin_th ** 2 * dphi_dl ** 2
    ) / f
    dt_dl_sq = max(dt_dl_sq, 0.0)
    dt_dl = np.sqrt(dt_dl_sq)
    d2r = christoffel_r(r, theta, M, dt_dl, dr_dl, dth_dl, dphi_dl)
    d2th = christoffel_theta(r, theta, dr_dl, dth_dl, dphi_dl)
    d2phi = christoffel_phi(r, theta, dr_dl, dth_dl, dphi_dl)
    return np.array([dr_dl, dth_dl, dphi_dl, d2r, d2th, d2phi])