package physics

import "math"

func ChristoffelR(r, theta, M, dt, dr, dtheta, dphi float64) float64 {
	rs := 2.0 * M
	f := 1.0 - rs/r
	termTT := M * f / (r * r) * dt * dt
	termRR := -M / (r * r * f) * dr * dr
	termThTh := -f * r * dtheta * dtheta
	sinTh := math.Sin(theta)
	termPhPh := -f * r * sinTh * sinTh * dphi * dphi
	return -(termTT + termRR + termThTh + termPhPh)
}

func ChristoffelTheta(r, theta, dr, dtheta, dphi float64) float64 {
	termRTh := 2.0 / r * dr * dtheta
	termPhPh := -math.Sin(theta) * math.Cos(theta) * dphi * dphi
	return -(termRTh + termPhPh)
}

func ChristoffelPhi(r, theta, dr, dtheta, dphi float64) float64 {
	sinTh := math.Sin(theta)
	cosTh := math.Cos(theta)
	var cot float64
	if math.Abs(sinTh) < 1e-15 {
		cot = 0
	} else {
		cot = cosTh / sinTh
	}
	termRPhi := 2.0 / r * dr * dphi
	termThPhi := 2.0 * cot * dtheta * dphi
	return -(termRPhi + termThPhi)
}

func GeodesicRHS3D(lam float64, state [6]float64, M float64) [6]float64 {
	r := state[0]
	theta := state[1]
	drDl := state[3]
	dthDl := state[4]
	dphiDl := state[5]

	rs := 2.0 * M
	if r <= rs*1.01 {
		return [6]float64{}
	}

	f := 1.0 - rs/r
	sinTh := math.Sin(theta)

	dtDlSq := (drDl*drDl/f + r*r*dthDl*dthDl + r*r*sinTh*sinTh*dphiDl*dphiDl) / f
	if dtDlSq < 0 {
		dtDlSq = 0
	}
	dtDl := math.Sqrt(dtDlSq)

	d2r := ChristoffelR(r, theta, M, dtDl, drDl, dthDl, dphiDl)
	d2th := ChristoffelTheta(r, theta, drDl, dthDl, dphiDl)
	d2phi := ChristoffelPhi(r, theta, drDl, dthDl, dphiDl)

	return [6]float64{drDl, dthDl, dphiDl, d2r, d2th, d2phi}
}
