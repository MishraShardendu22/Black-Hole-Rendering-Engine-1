package physics

import "math"

func SchwarzschildRadius(M float64) float64 {
	return 2.0 * M
}

func PhotonSphereRadius(M float64) float64 {
	return 3.0 * M
}

func ISCORadius(M float64) float64 {
	return 6.0 * M
}

func MetricTT(r, M float64) float64 {
	return -(1.0 - 2.0*M/r)
}

func MetricRR(r, M float64) float64 {
	return 1.0 / (1.0 - 2.0*M/r)
}

func MetricThTh(r float64) float64 {
	return r * r
}

func MetricPhPh(r, theta float64) float64 {
	s := math.Sin(theta)
	return r * r * s * s
}

func EffectivePotential(r, M, L float64) float64 {
	return (1.0 - 2.0*M/r) * L * L / (r * r)
}

func CriticalImpactParameter(M float64) float64 {
	return 3.0 * math.Sqrt(3.0) * M
}
