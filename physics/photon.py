from enum import Enum, auto

import numpy as np


class PhotonFate(Enum):
    ESCAPED = auto()
    CAPTURED = auto()
    HIT_DISK = auto()
    IN_FLIGHT = auto()


class Photon:

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
        return np.array([
            self.r0, self.theta0, self.phi0,
            self.dr0, self.dtheta0, self.dphi0,
        ])

    def store_trajectory(self, r_arr, theta_arr, phi_arr):
        self.trajectory_r = np.asarray(r_arr)
        self.trajectory_theta = np.asarray(theta_arr)
        self.trajectory_phi = np.asarray(phi_arr)

    def endpoint_cartesian(self) -> np.ndarray:
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