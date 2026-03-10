"""
Matplotlib-based plotting utilities for the black hole visualisation.

Provides functions to:
    1. Display the final rendered lensing image.
    2. Plot individual photon trajectories (polar and Cartesian).
    3. Overlay the Schwarzschild radius and photon sphere on trajectory plots.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from physics.schwarzschild import schwarzschild_radius, photon_sphere_radius, isco_radius


def show_render(image: np.ndarray, title: str = "Schwarzschild Black Hole",
                save_path: str | None = None):
    """
    Display the rendered image with matplotlib.

    Parameters
    ----------
    image : (H, W, 3) float array in [0, 1].
    title : str
    save_path : str or None
        If given, save the figure to this path.
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image, origin="upper", interpolation="bilinear")
    ax.set_title(title, fontsize=14, color="white")
    ax.axis("off")
    fig.patch.set_facecolor("black")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="black")
        print(f"Saved render to {save_path}")
    plt.show()


def plot_trajectories(
    photons,
    M: float,
    title: str = "Photon Trajectories",
    save_path: str | None = None,
):
    """
    Plot a collection of photon trajectories in the x-z plane.

    Also draws the event horizon, photon sphere, and ISCO.
    """
    rs = schwarzschild_radius(M)
    r_ph = photon_sphere_radius(M)
    r_is = isco_radius(M)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor("black")
    fig.patch.set_facecolor("black")

    # Draw reference circles
    for radius, color, label in [
        (rs, "#ff4444", f"Event Horizon (r={rs:.1f}M)"),
        (r_ph, "#ffaa00", f"Photon Sphere (r={r_ph:.1f}M)"),
        (r_is, "#4488ff", f"ISCO (r={r_is:.1f}M)"),
    ]:
        circle = Circle((0, 0), radius, fill=False,
                         edgecolor=color, linewidth=1.5,
                         linestyle="--", label=label)
        ax.add_patch(circle)

    # Black hole disk
    bh = Circle((0, 0), rs, color="black", zorder=5)
    ax.add_patch(bh)

    # Plot each trajectory
    from physics.photon import PhotonFate
    color_map = {
        PhotonFate.ESCAPED: "#88cc88",
        PhotonFate.CAPTURED: "#ff6666",
        PhotonFate.HIT_DISK: "#ffcc44",
        PhotonFate.IN_FLIGHT: "#aaaaaa",
    }

    for photon in photons:
        r = photon.trajectory_r
        theta = photon.trajectory_theta
        phi = photon.trajectory_phi
        if len(r) == 0:
            continue
        x = r * np.sin(theta) * np.cos(phi)
        z = r * np.cos(theta)
        c = color_map.get(photon.fate, "#ffffff")
        ax.plot(x, z, color=c, linewidth=0.6, alpha=0.7)

    lim = 30 * M
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("x / M", color="white")
    ax.set_ylabel("z / M", color="white")
    ax.set_title(title, color="white", fontsize=14)
    ax.tick_params(colors="white")
    ax.legend(loc="upper right", fontsize=8, facecolor="#222222",
              edgecolor="white", labelcolor="white")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="black")
        print(f"Saved trajectory plot to {save_path}")
    plt.show()


def plot_effective_potential(M: float, save_path: str | None = None):
    """
    Plot the effective potential V_eff(r) for several impact parameters b.

    Illustrates captured vs. deflected photon orbits.
    """
    from physics.schwarzschild import effective_potential, critical_impact_parameter

    b_crit = critical_impact_parameter(M)
    r = np.linspace(2.1 * M, 30 * M, 500)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor("black")
    fig.patch.set_facecolor("black")

    for frac, ls in [(0.8, "--"), (1.0, "-"), (1.1, "--"), (1.5, ":")]:
        b = frac * b_crit
        L = b  # In geometrised units E=1 → L = b
        V = effective_potential(r, M, L)
        label = f"b = {frac:.1f} b_c"
        ax.plot(r / M, V, linestyle=ls, label=label, linewidth=1.5)

    ax.axhline(1.0, color="white", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("r / M", color="white")
    ax.set_ylabel("V_eff / E²", color="white")
    ax.set_title("Effective Potential for Photon Orbits", color="white")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#222222", edgecolor="white", labelcolor="white")
    ax.set_ylim(0, 2.0)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor="black")
    plt.show()
