import numpy as np
from bh_math.vectors import normalize


class Camera:

    def __init__(
        self,
        position: np.ndarray,
        target: np.ndarray,
        up: np.ndarray = np.array([0.0, 0.0, 1.0]),
        fov_deg: float = 60.0,
        resolution: tuple = (160, 120),
    ):
        self.position = np.asarray(position, dtype=float)
        self.target = np.asarray(target, dtype=float)
        self.up_hint = np.asarray(up, dtype=float)
        self.fov_deg = fov_deg
        self.nx, self.ny = resolution

        self.forward = normalize(self.target - self.position)
        self.right = normalize(np.cross(self.forward, self.up_hint))
        self.up = np.cross(self.right, self.forward)

    def ray_direction(self, i: int, j: int) -> np.ndarray:
        aspect = self.nx / self.ny
        fov_rad = np.deg2rad(self.fov_deg)
        half_w = np.tan(fov_rad / 2.0)
        half_h = half_w / aspect

        u = -1.0 + 2.0 * (j + 0.5) / self.nx
        v = 1.0 - 2.0 * (i + 0.5) / self.ny

        direction = self.forward + u * half_w * self.right + v * half_h * self.up
        return normalize(direction)