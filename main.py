import argparse
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')

from core.camera import Camera
from core.engine import Engine
from renderer.plot_renderer import show_render


def parse_args():
    parser = argparse.ArgumentParser(
        description='Schwarzschild black hole gravitational lensing renderer.'
    )
    parser.add_argument(
        '--resolution', type=str, default='160x120',
        help='Image resolution WxH (e.g. 320x240). Default: 160x120.'
    )
    parser.add_argument(
        '--fov', type=float, default=60.0,
        help='Horizontal field of view in degrees. Default: 60.'
    )
    parser.add_argument(
        '--mass', type=float, default=1.0,
        help='Black hole mass in geometrised units. Default: 1.0.'
    )
    parser.add_argument(
        '--distance', type=float, default=30.0,
        help='Camera distance from the black hole (units of M). Default: 30.'
    )
    parser.add_argument(
        '--inclination', type=float, default=80.0,
        help='Camera inclination angle in degrees from the pole. Default: 80.'
    )
    parser.add_argument(
        '--disk-outer', type=float, default=20.0,
        help='Outer radius of accretion disk (units of M). Default: 20.'
    )
    parser.add_argument(
        '--output', type=str, default='output/lensing_render.png',
        help='Output file path. Default: output/lensing_render.png.'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        nx, ny = (int(x) for x in args.resolution.split('x'))
    except ValueError:
        print('Error: resolution must be in WxH format (e.g. 320x240).')
        sys.exit(1)

    M = args.mass
    inc_rad = np.deg2rad(args.inclination)
    cam_pos = np.array([
        args.distance * np.sin(inc_rad),
        0.0,
        args.distance * np.cos(inc_rad),
    ])

    camera = Camera(
        position=cam_pos,
        target=np.array([0.0, 0.0, 0.0]),
        up=np.array([0.0, 0.0, 1.0]),
        fov_deg=args.fov,
        resolution=(nx, ny),
    )

    engine = Engine(
        M=M,
        camera=camera,
        r_disk_outer=args.disk_outer,
        lambda_max=400.0,
        r_max=250.0,
    )

    print('Schwarzschild Black Hole Renderer')
    print(f'  Mass           : {M}')
    print(f'  Resolution     : {nx} x {ny}')
    print(f'  FoV            : {args.fov}°')
    print(f'  Camera distance: {args.distance} M')
    print(f'  Inclination    : {args.inclination}°')
    print(f'  Disk outer     : {args.disk_outer} M')
    print(f'  Output         : {args.output}')
    print()

    t0 = time.time()
    image = engine.render(progress=True)
    elapsed = time.time() - t0

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 10 * ny / nx))
    ax.imshow(image, origin='upper', interpolation='bilinear')
    ax.set_title(
        'Schwarzschild Black Hole — Gravitational Lensing',
        fontsize=14, color='white', pad=12
    )
    ax.axis('off')
    fig.patch.set_facecolor('black')
    fig.tight_layout()
    fig.savefig(args.output, dpi=150, bbox_inches='tight', facecolor='black')
    plt.close(fig)

    print(f'\nDone in {elapsed:.1f}s — saved to {args.output}')


if __name__ == '__main__':
    main()