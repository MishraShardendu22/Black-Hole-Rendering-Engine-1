package physics

import "math"

func KerrSigma(r, theta, a float64) float64 {
	costh := math.Cos(theta)
	return r*r + a*a*costh*costh
}

func KerrDelta(r, M, a float64) float64 {
	return r*r - 2.0*M*r + a*a
}

func KerrEventHorizon(M, a float64) float64 {
	return M + math.Sqrt(M*M-a*a)
}

func KerrISCO(M, a float64) float64 {
	if a == 0 {
		return 6.0 * M
	}
	aOverM := a / M
	z1 := 1.0 + math.Cbrt(1.0-aOverM*aOverM)*(math.Cbrt(1.0+aOverM)+math.Cbrt(1.0-aOverM))
	z2 := math.Sqrt(3.0*aOverM*aOverM + z1*z1)
	return M * (3.0 + z2 - math.Sqrt((3.0-z1)*(3.0+z1+2.0*z2)))
}

func KerrMetricTT(r, theta, M, a float64) float64 {
	sig := KerrSigma(r, theta, a)
	return -(1.0 - 2.0*M*r/sig)
}

func KerrMetricTPhi(r, theta, M, a float64) float64 {
	sig := KerrSigma(r, theta, a)
	sinTh := math.Sin(theta)
	return -2.0 * M * a * r * sinTh * sinTh / sig
}

func KerrMetricRR(r, theta, M, a float64) float64 {
	sig := KerrSigma(r, theta, a)
	delta := KerrDelta(r, M, a)
	return sig / delta
}

func KerrMetricThTh(r, theta, a float64) float64 {
	return KerrSigma(r, theta, a)
}

func KerrMetricPhPh(r, theta, M, a float64) float64 {
	sig := KerrSigma(r, theta, a)
	sinTh := math.Sin(theta)
	sin2 := sinTh * sinTh
	return (r*r + a*a + 2.0*M*a*a*r*sin2/sig) * sin2
}

func GeodesicRHSKerr(lam float64, state [6]float64, M, a float64) [6]float64 {
	r := state[0]
	theta := state[1]
	drDl := state[3]
	dthDl := state[4]
	dphiDl := state[5]

	rPlus := KerrEventHorizon(M, a)
	if r <= rPlus*1.01 {
		return [6]float64{}
	}

	sinTh := math.Sin(theta)
	cosTh := math.Cos(theta)
	sin2 := sinTh * sinTh
	cos2 := cosTh * cosTh

	sig := r*r + a*a*cos2
	delta := r*r - 2.0*M*r + a*a
	sig2 := sig * sig

	gtt := -(1.0 - 2.0*M*r/sig)
	gtphi := -2.0 * M * a * r * sin2 / sig
	grr := sig / delta
	gphph := (r*r + a*a + 2.0*M*a*a*r*sin2/sig) * sin2

	A := gtt
	B := 2.0 * gtphi * dphiDl
	C := grr*drDl*drDl + sig*dthDl*dthDl + gphph*dphiDl*dphiDl

	disc := B*B - 4.0*A*C
	if disc < 0 {
		disc = 0
	}
	dtDl := (-B + math.Sqrt(disc)) / (2.0 * A)
	if dtDl < 0 {
		dtDl = (-B - math.Sqrt(disc)) / (2.0 * A)
	}
	if dtDl < 0 {
		dtDl = 0
	}

	dSigDr := 2.0 * r
	dSigDth := -2.0 * a * a * sinTh * cosTh
	dDeltaDr := 2.0*r - 2.0*M

	dgttDr := -2.0 * M * (sig - r*dSigDr) / sig2
	dgttDth := 2.0 * M * r * dSigDth / sig2

	dgtphiDr := -2.0 * M * a * sin2 * (sig - r*dSigDr) / sig2
	dgtphiDth := -2.0 * M * a * r * (2.0*sinTh*cosTh*sig - sin2*dSigDth) / sig2

	dgrrDr := (dSigDr*delta - sig*dDeltaDr) / (delta * delta)
	dgrrDth := dSigDth / delta

	dgththDr := dSigDr
	dgththDth := dSigDth

	innerA := r*r + a*a + 2.0*M*a*a*r*sin2/sig
	dInnerADr := 2.0*r + 2.0*M*a*a*sin2*(sig-r*dSigDr)/sig2
	dgphphDr := dInnerADr * sin2
	dInnerADth := 2.0 * M * a * a * r * (2.0*sinTh*cosTh*sig - sin2*dSigDth) / sig2
	dgphphDth := dInnerADth*sin2 + innerA*2.0*sinTh*cosTh

	d2r := (0.5*dgttDr*dtDl*dtDl +
		dgtphiDr*dtDl*dphiDl +
		0.5*dgphphDr*dphiDl*dphiDl +
		0.5*dgththDr*dthDl*dthDl -
		0.5*dgrrDr*drDl*drDl -
		dgrrDth*drDl*dthDl) / grr

	gthth := sig
	d2th := (0.5*dgttDth*dtDl*dtDl +
		dgtphiDth*dtDl*dphiDl +
		0.5*dgrrDth*drDl*drDl +
		0.5*dgphphDth*dphiDl*dphiDl -
		0.5*dgththDth*dthDl*dthDl -
		dgththDr*drDl*dthDl) / gthth

	Xt := -(dgttDr*dtDl*drDl + dgttDth*dtDl*dthDl + dgtphiDr*dphiDl*drDl + dgtphiDth*dphiDl*dthDl)
	Xphi := -(dgtphiDr*dtDl*drDl + dgtphiDth*dtDl*dthDl + dgphphDr*dphiDl*drDl + dgphphDth*dphiDl*dthDl)

	det := gtt*gphph - gtphi*gtphi
	if math.Abs(det) < 1e-30 {
		return [6]float64{}
	}
	d2phi := (-gtphi*Xt + gtt*Xphi) / det

	return [6]float64{drDl, dthDl, dphiDl, d2r, d2th, d2phi}
}

func GeodesicRHS(lam float64, state [6]float64, M, a float64) [6]float64 {
	if a == 0 {
		return GeodesicRHS3D(lam, state, M)
	}
	return GeodesicRHSKerr(lam, state, M, a)
}
