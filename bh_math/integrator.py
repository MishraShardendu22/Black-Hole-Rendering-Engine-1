"""
Numerical integration helpers.

Thin wrappers around scipy.integrate for solving ODEs that arise
from the geodesic equation in the Schwarzschild metric.
"""

from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


def integrate_geodesic(
    rhs: Callable,
    y0: np.ndarray,
    lambda_span: tuple,
    *,
    max_step: float = 0.5,
    rtol: float = 1e-8,
    atol: float = 1e-10,
    events: list | None = None,
    dense_output: bool = False,
) -> dict:
    """
    Integrate a system of ODEs (the geodesic equation) using RK45.

    Parameters
    ----------
    rhs : callable
        Right-hand side  dy/dλ = rhs(λ, y).
    y0 : array
        Initial state vector [r, θ, φ, dr/dλ, dθ/dλ, dφ/dλ].
    lambda_span : (λ_start, λ_end)
        Affine-parameter integration bounds.
    max_step : float
        Maximum step size in λ.
    events : list of callables, optional
        Event functions (e.g. hitting the event horizon).
    dense_output : bool
        Whether to produce a continuous solution.

    Returns
    -------
    dict with keys:
        't'  — affine parameter values
        'y'  — state vectors at each t
        'success' — bool
        'message' — solver message
        't_events' — event times
    """
    sol = solve_ivp(
        rhs,
        lambda_span,
        y0,
        method="RK45",
        max_step=max_step,
        rtol=rtol,
        atol=atol,
        events=events,
        dense_output=dense_output,
    )
    return {
        "t": sol.t,
        "y": sol.y,
        "success": sol.success,
        "message": sol.message,
        "t_events": sol.t_events,
    }
