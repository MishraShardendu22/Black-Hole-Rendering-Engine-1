package simulation

import (
	"math"

	"github.com/hlack-bole/gocore/physics"
)

var dpA = [7][6]float64{
	{},
	{1.0 / 5},
	{3.0 / 40, 9.0 / 40},
	{44.0 / 45, -56.0 / 15, 32.0 / 9},
	{19372.0 / 6561, -25360.0 / 2187, 64448.0 / 6561, -212.0 / 729},
	{9017.0 / 3168, -355.0 / 33, 46732.0 / 5247, 49.0 / 176, -5103.0 / 18656},
	{35.0 / 384, 0, 500.0 / 1113, 125.0 / 192, -2187.0 / 6784, 11.0 / 84},
}

var dpC = [7]float64{0, 1.0 / 5, 3.0 / 10, 4.0 / 5, 8.0 / 9, 1, 1}

var dpB5 = [7]float64{35.0 / 384, 0, 500.0 / 1113, 125.0 / 192, -2187.0 / 6784, 11.0 / 84, 0}

var dpE = [7]float64{
	71.0 / 57600, 0, -71.0 / 16695, 71.0 / 1920,
	-17253.0 / 339200, 22.0 / 525, -1.0 / 40,
}

const dim = 6

type RHSFunc func(lam float64, y [6]float64) [6]float64

type SolverParams struct {
	RTol       float64
	ATol       float64
	HInitial   float64
	HMax       float64
	LambdaMax  float64
	M          float64
	Spin       float64
	RMax       float64
	RDiskOuter float64
}

func rk45step(f RHSFunc, lam float64, y [dim]float64, h float64) (y5, y4 [dim]float64, k [7][dim]float64) {
	k[0] = f(lam, y)
	for s := 1; s < 7; s++ {
		var ys [dim]float64
		for i := 0; i < dim; i++ {
			ys[i] = y[i]
			for j := 0; j < s; j++ {
				ys[i] += h * dpA[s][j] * k[j][i]
			}
		}
		k[s] = f(lam+dpC[s]*h, ys)
	}
	for i := 0; i < dim; i++ {
		y5[i] = y[i]
		for s := 0; s < 7; s++ {
			y5[i] += h * dpB5[s] * k[s][i]
		}
	}
	for i := 0; i < dim; i++ {
		y4[i] = y5[i]
		for s := 0; s < 7; s++ {
			y4[i] -= h * dpE[s] * k[s][i]
		}
	}
	return
}

func errorNorm(y4, y5 [dim]float64, atol, rtol float64) float64 {
	var sumSq float64
	for i := 0; i < dim; i++ {
		sc := atol + rtol*math.Max(math.Abs(y4[i]), math.Abs(y5[i]))
		e := (y5[i] - y4[i]) / sc
		sumSq += e * e
	}
	return math.Sqrt(sumSq / float64(dim))
}

func interpolateLinear(y0, y1 [dim]float64, frac float64) [dim]float64 {
	var out [dim]float64
	for i := 0; i < dim; i++ {
		out[i] = y0[i] + frac*(y1[i]-y0[i])
	}
	return out
}

func horizonEvent(y [dim]float64, M, a float64) float64 {
	var rH float64
	if a == 0 {
		rH = physics.SchwarzschildRadius(M) * 1.02
	} else {
		rH = physics.KerrEventHorizon(M, a) * 1.02
	}
	return y[0] - rH
}

func escapeEvent(y [dim]float64, rMax float64) float64 {
	return y[0] - rMax
}

func diskCrossingEvent(y [dim]float64) float64 {
	return y[1] - math.Pi/2.0
}

func bisectEvent(lam0, lam1 float64, y0, y1 [dim]float64, eventFunc func([dim]float64) float64) (float64, [dim]float64) {
	v0 := eventFunc(y0)
	for iter := 0; iter < 60; iter++ {
		mid := 0.5 * (lam0 + lam1)
		if lam1-lam0 < 1e-8 {
			yMid := interpolateLinear(y0, y1, 0.5)
			return mid, yMid
		}
		frac := (mid - lam0) / (lam1 - lam0)
		yMid := interpolateLinear(y0, y1, frac)
		vMid := eventFunc(yMid)
		if v0*vMid <= 0 {
			lam1 = mid
			y1 = yMid
		} else {
			lam0 = mid
			y0 = yMid
			v0 = vMid
		}
	}
	yMid := interpolateLinear(y0, y1, 0.5)
	return 0.5 * (lam0 + lam1), yMid
}

func SolvePhoton(photon *physics.Photon, params SolverParams) {
	M := params.M
	a := params.Spin
	rMax := params.RMax
	rDiskOuter := params.RDiskOuter

	var rInner float64
	if a == 0 {
		rInner = physics.ISCORadius(M)
	} else {
		rInner = physics.KerrISCO(M, a)
	}

	rhs := func(lam float64, y [6]float64) [6]float64 {
		return physics.GeodesicRHS(lam, y, M, a)
	}

	y := photon.InitialState()
	lam := 0.0
	h := params.HInitial

	maxSteps := 20000
	trajR := make([]float64, 0, maxSteps)
	trajTh := make([]float64, 0, maxSteps)
	trajPh := make([]float64, 0, maxSteps)

	trajR = append(trajR, y[0])
	trajTh = append(trajTh, y[1])
	trajPh = append(trajPh, y[2])

	for lam < params.LambdaMax {
		if h > params.HMax {
			h = params.HMax
		}
		if lam+h > params.LambdaMax {
			h = params.LambdaMax - lam
		}
		if h < 1e-14 {
			break
		}

		y5, y4, _ := rk45step(rhs, lam, y, h)
		err := errorNorm(y4, y5, params.ATol, params.RTol)

		if err <= 1.0 {
			yOld := y
			lamOld := lam
			y = y5
			lam += h

			trajR = append(trajR, y[0])
			trajTh = append(trajTh, y[1])
			trajPh = append(trajPh, y[2])

			hEvOld := horizonEvent(yOld, M, a)
			hEvNew := horizonEvent(y, M, a)
			if hEvOld > 0 && hEvNew <= 0 {
				photon.Fate = physics.Captured
				break
			}

			eEvOld := escapeEvent(yOld, rMax)
			eEvNew := escapeEvent(y, rMax)
			if eEvOld < 0 && eEvNew >= 0 {
				photon.Fate = physics.Escaped
				break
			}

			dEvOld := diskCrossingEvent(yOld)
			dEvNew := diskCrossingEvent(y)
			if dEvOld*dEvNew < 0 {
				_, yHit := bisectEvent(lamOld, lam, yOld, y, diskCrossingEvent)
				rCross := yHit[0]
				phiCross := yHit[2]
				thetaDotCross := yHit[4]
				if rCross >= rInner && rCross <= rDiskOuter {
					photon.Fate = physics.HitDisk
					photon.DiskR = rCross
					photon.DiskPhi = phiCross
					photon.DiskThetaDot = thetaDotCross
					break
				}
			}

			if err > 0 {
				factor := 0.9 * math.Pow(err, -0.2)
				if factor > 5 {
					factor = 5
				}
				h *= factor
			} else {
				h *= 5
			}
		} else {
			factor := 0.9 * math.Pow(err, -0.2)
			if factor < 0.2 {
				factor = 0.2
			}
			h *= factor
		}
	}

	photon.TrajectoryR = trajR
	photon.TrajectoryTheta = trajTh
	photon.TrajectoryPhi = trajPh

	if photon.Fate == physics.InFlight {
		rs := physics.SchwarzschildRadius(M)
		if len(trajR) > 0 && trajR[len(trajR)-1] > rs*2.0 {
			photon.Fate = physics.Escaped
		} else {
			photon.Fate = physics.Captured
		}
	}
}
