package renderer

import (
	"math"

	"github.com/hlack-bole/gocore/physics"
)

type RenderParams struct {
	M              float64
	Spin           float64
	RDiskOuter     float64
	RMax           float64
	EnableRedshift bool
	EnableDoppler  bool
	EnableBeaming  bool
}

func BackgroundColor(theta, phi float64) [3]float32 {
	seed := int(math.Abs(math.Sin(theta*127.1+phi*311.7)*43758.5453)) % 1000
	if seed < 8 {
		brightness := float32(0.6 + 0.4*float64(seed)/8.0)
		return [3]float32{brightness, brightness, brightness * 0.95}
	}
	return [3]float32{0, 0, 0.02}
}

func ComputePixelColor(photon *physics.Photon, p RenderParams) [3]float32 {
	switch photon.Fate {
	case physics.Captured:
		return [3]float32{0, 0, 0}

	case physics.HitDisk:
		return DiskColorRelativistic(
			photon.DiskR, photon.DiskPhi, p.M, p.RDiskOuter,
			p.EnableRedshift, p.EnableDoppler, p.EnableBeaming,
		)

	default:
		n := len(photon.TrajectoryTheta)
		if n > 0 {
			return BackgroundColor(photon.TrajectoryTheta[n-1], photon.TrajectoryPhi[n-1])
		}
		return BackgroundColor(math.Pi/2, 0)
	}
}
