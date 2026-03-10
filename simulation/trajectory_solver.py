"""
Photon trajectory solver.

Integrates the geodesic equation for each photon, detects event-horizon
capture and accretion-disk intersection, and determines the photon's fate.

The accretion disk is modelled as a geometrically thin disk in the
equatorial plane (θ = π/2) extending from the ISCO (r = 6M) to some
outer radius r_disk_outer.
"""

import numpy as np
from scipy.integrate import solve_ivp

from physics.geodesic import geodesic_rhs_3d
from physics.photon import Photon, PhotonFate
from physics.schwarzschild import schwarzschild_radius, isco_radius


def _make_events(M: float, r_max: float):
    """
    Build event functions for solve_ivp.

    Events (terminal):
        1. Photon reaches the event horizon  r ≤ r_s * 1.02
        2. Photon escapes to r > r_max
    """
    rs = schwarzschild_radius(M)
    r_horizon = rs * 1.02

    def horizon_event(lam, state):
        return state[0] - r_horizon
    horizon_event.terminal = True
    horizon_event.direction = -1  # r decreasing through threshold

    def escape_event(lam, state):
        return state[0] - r_max
    escape_event.terminal = True
    escape_event.direction = 1

    return [horizon_event, escape_event]


def _check_disk_crossing(r_arr, theta_arr, phi_arr, M, r_disk_outer):
    """
    Scan the trajectory for equatorial-plane crossings within the disk.

    The disk occupies  r_isco ≤ r ≤ r_disk_outer  at θ = π/2.
    A crossing occurs when θ passes through π/2 between consecutive steps.

    Returns
    -------
    (hit, index, r_hit, phi_hit) or (False, -1, 0, 0).
    """
    r_inner = isco_radius(M)
    half_pi = np.pi / 2.0

    for k in range(len(theta_arr) - 1):
        th0 = theta_arr[k] - half_pi
        th1 = theta_arr[k + 1] - half_pi
        if th0 * th1 < 0:
            # Linear interpolation for crossing radius
            frac = abs(th0) / (abs(th0) + abs(th1))
            r_cross = r_arr[k] + frac * (r_arr[k + 1] - r_arr[k])
            phi_cross = phi_arr[k] + frac * (phi_arr[k + 1] - phi_arr[k])
            if r_inner <= r_cross <= r_disk_outer:
                return True, k, r_cross, phi_cross
    return False, -1, 0.0, 0.0


def solve_photon(
    photon: Photon,
    M: float,
    *,
    lambda_max: float = 300.0,
    r_max: float = 200.0,
    r_disk_outer: float = 20.0,
    max_step: float = 0.5,
) -> Photon:
    """
    Integrate a single photon through Schwarzschild spacetime.

    After integration the photon.fate is set to one of:
        CAPTURED  — fell into the event horizon
        ESCAPED   — reached r_max
        HIT_DISK  — intersected the accretion disk

    Parameters
    ----------
    photon : Photon
        Must have initial state populated.
    M : float
        Black hole mass (geometrised).
    lambda_max : float
        Maximum affine parameter.
    r_max : float
        Escape radius.
    r_disk_outer : float
        Outer radius of accretion disk (in units of M).
    max_step : float
        ODE max step size.

    Returns
    -------
    The same Photon object, mutated with trajectory and fate information.
    """
    events = _make_events(M, r_max)

    def rhs(lam, state):
        return geodesic_rhs_3d(lam, state, M)

    sol = solve_ivp(
        rhs,
        (0.0, lambda_max),
        photon.initial_state,
        method="RK45",
        max_step=max_step,
        rtol=1e-8,
        atol=1e-10,
        events=events,
        args=(),
    )

    r_arr = sol.y[0]
    theta_arr = sol.y[1]
    phi_arr = sol.y[2]
    photon.store_trajectory(r_arr, theta_arr, phi_arr)

    rs = schwarzschild_radius(M)

    # Determine fate
    if len(sol.t_events[0]) > 0:
        # Horizon event triggered
        photon.fate = PhotonFate.CAPTURED
    elif len(sol.t_events[1]) > 0:
        # Escape event triggered
        photon.fate = PhotonFate.ESCAPED
    else:
        # Lambda exhausted — treat as escaped if far enough, else captured
        if r_arr[-1] > rs * 2.0:
            photon.fate = PhotonFate.ESCAPED
        else:
            photon.fate = PhotonFate.CAPTURED

    # Check disk intersection (only if not already captured)
    if photon.fate != PhotonFate.CAPTURED:
        hit, idx, r_hit, phi_hit = _check_disk_crossing(
            r_arr, theta_arr, phi_arr, M, r_disk_outer
        )
        if hit:
            photon.fate = PhotonFate.HIT_DISK
            photon.disk_r = r_hit
            photon.disk_phi = phi_hit

    return photon
