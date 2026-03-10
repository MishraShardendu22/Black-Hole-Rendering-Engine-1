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
    sol = solve_ivp(
        rhs,
        lambda_span,
        y0,
        method='RK45',
        max_step=max_step,
        rtol=rtol,
        atol=atol,
        events=events,
        dense_output=dense_output,
    )
    return {
        't': sol.t,
        'y': sol.y,
        'success': sol.success,
        'message': sol.message,
        't_events': sol.t_events,
    }