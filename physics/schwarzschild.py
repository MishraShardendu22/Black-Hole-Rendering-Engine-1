import numpy as np

G_SI = 6.67430e-11
C_SI = 2.99792458e8
M_SUN_KG = 1.98892e30


def schwarzschild_radius(M: float) -> float:
    return 2.0 * M


def photon_sphere_radius(M: float) -> float:
    return 3.0 * M


def isco_radius(M: float) -> float:
    return 6.0 * M


def metric_tt(r: float, M: float) -> float:
    return -(1.0 - 2.0 * M / r)


def metric_rr(r: float, M: float) -> float:
    return 1.0 / (1.0 - 2.0 * M / r)


def metric_thth(r: float) -> float:
    return r * r


def metric_phph(r: float, theta: float) -> float:
    return r * r * np.sin(theta) ** 2


def effective_potential(r: np.ndarray, M: float, L: float) -> np.ndarray:
    return (1.0 - 2.0 * M / r) * L ** 2 / r ** 2


def critical_impact_parameter(M: float) -> float:
    return 3.0 * np.sqrt(3.0) * M