"""
Photon model for ray-tracing in Schwarzschild spacetime.

A photon is characterised by its initial position in spherical
coordinates (r, θ, φ) and an initial direction vector.  We store
the full state needed by the geodesic integrator and track the
photon's fate (escaped, captured, hit disk).
"""

from enum import Enum, auto

import numpy as np


class PhotonFate(Enum):
    """Possible outcomes for a traced photon."""
    ESCAPED = auto()
    CAPTURED = auto()
    HIT_DISK = auto()
    IN_FLIGHT = auto()


class Photon:
    """
    Container for a single photon's state and trajectory history.

    Attributes
    ----------
    r0, theta0, phi0 : float
        Initial spherical coordinates.
    dr0, dtheta0, dphi0 : float
        Initial coordinate velocities w.r.t. affine parameter.
    trajectory : list of np.ndarray
        Recorded (r, θ, φ) along the path.
    fate : PhotonFate
        Outcome after integration.
    color : np.ndarray
        RGB colour assigned after tracing.
    """

    def __init__(self, r, theta, phi, dr, dtheta, dphi):
        self.r0 = r
        self.theta0 = theta
        self.phi0 = phi
        self.dr0 = dr
        self.dtheta0 = dtheta
        self.dphi0 = dphi

        self.trajectory_r = np.empty(0)
        self.trajectory_theta = np.empty(0)
        self.trajectory_phi = np.empty(0)

        self.fate = PhotonFate.IN_FLIGHT
        self.color = np.array([0.0, 0.0, 0.0])
        self.brightness = 0.0

    @property
    def initial_state(self) -> np.ndarray:
        """Return the 6-element state vector for the integrator."""
        return np.array([
            self.r0, self.theta0, self.phi0,
            self.dr0, self.dtheta0, self.dphi0,
        ])

    def store_trajectory(self, r_arr, theta_arr, phi_arr):
        """Record trajectory arrays from the solver."""
        self.trajectory_r = np.asarray(r_arr)
        self.trajectory_theta = np.asarray(theta_arr)
        self.trajectory_phi = np.asarray(phi_arr)

    def endpoint_cartesian(self) -> np.ndarray:
        """Cartesian position of the last recorded point."""
        if len(self.trajectory_r) == 0:
            return np.zeros(3)
        r = self.trajectory_r[-1]
        th = self.trajectory_theta[-1]
        ph = self.trajectory_phi[-1]
        return np.array([
            r * np.sin(th) * np.cos(ph),
            r * np.sin(th) * np.sin(ph),
            r * np.cos(th),
        ])
