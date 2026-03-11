package renderer

import (
	"math"

	"github.com/hlack-bole/gocore/physics"
)

func DiskTemperatureProfile(r, M float64) float64 {
	rIn := physics.ISCORadius(M)
	if r <= rIn {
		return 0
	}
	raw := math.Pow(r, -0.75) * math.Pow(math.Max(0, 1.0-math.Sqrt(rIn/r)), 0.25)
	rPeak := 1.36 * rIn
	peak := math.Pow(rPeak, -0.75) * math.Pow(math.Max(0, 1.0-math.Sqrt(rIn/rPeak)), 0.25)
	if peak < 1e-15 {
		return 0
	}
	return raw / peak
}

func TemperatureToRGB(tNorm float64) [3]float32 {
	t := clamp64(tNorm, 0, 1)
	r := clamp64(1.5*t, 0, 1)
	g := clamp64(1.5*t-0.4, 0, 1)
	b := clamp64(2.0*t-1.2, 0, 1)
	return [3]float32{float32(r), float32(g), float32(b)}
}

func DiskColorBasic(r, phi, M, rDiskOuter float64) [3]float32 {
	rIn := physics.ISCORadius(M)
	if r < rIn || r > rDiskOuter {
		return [3]float32{}
	}
	tNorm := DiskTemperatureProfile(r, M)
	rgb := TemperatureToRGB(tNorm)
	doppler := 1.0 + 0.4*math.Sin(phi)
	radialFade := clamp64(1.0-(r-rIn)/(rDiskOuter-rIn), 0, 1)
	brightness := tNorm * doppler * (0.3 + 0.7*radialFade)
	return [3]float32{
		clamp32(rgb[0] * float32(brightness)),
		clamp32(rgb[1] * float32(brightness)),
		clamp32(rgb[2] * float32(brightness)),
	}
}

func GravitationalRedshift(r, M float64) float64 {
	rs := physics.SchwarzschildRadius(M)
	val := 1.0 - rs/r
	if val <= 0 {
		return 0
	}
	return math.Sqrt(val)
}

func KeplerianOmega(r, M float64) float64 {
	return math.Sqrt(M / (r * r * r))
}

func DopplerFactor(r, phi, M float64) float64 {
	rs := physics.SchwarzschildRadius(M)
	f := 1.0 - rs/r
	if f <= 0 {
		return 1
	}
	omega := KeplerianOmega(r, M)
	v := omega * r / math.Sqrt(f)
	if v >= 1 {
		v = 0.999
	}
	gamma := 1.0 / math.Sqrt(1.0-v*v)
	D := 1.0 / (gamma * (1.0 - v*math.Cos(phi)))
	return D
}

func DiskColorRelativistic(r, phi, M, rDiskOuter float64, enableRedshift, enableDoppler, enableBeaming bool) [3]float32 {
	var rIn float64
	rIn = physics.ISCORadius(M)
	if r < rIn || r > rDiskOuter {
		return [3]float32{}
	}

	tNorm := DiskTemperatureProfile(r, M)

	D := 1.0
	if enableDoppler {
		D = DopplerFactor(r, phi, M)
	}

	zGrav := 1.0
	if enableRedshift {
		zGrav = GravitationalRedshift(r, M)
	}

	tObserved := tNorm
	if enableBeaming {
		tObserved = tNorm * D
	}
	rgb := TemperatureToRGB(tObserved)

	D3 := 1.0
	if enableDoppler {
		D3 = D * D * D
	}
	brightness := zGrav * D3
	radialFade := clamp64(1.0-(r-rIn)/(rDiskOuter-rIn), 0, 1)
	brightness *= tNorm * (0.3 + 0.7*radialFade)

	return [3]float32{
		clamp32(rgb[0] * float32(brightness)),
		clamp32(rgb[1] * float32(brightness)),
		clamp32(rgb[2] * float32(brightness)),
	}
}

func clamp64(v, lo, hi float64) float64 {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func clamp32(v float32) float32 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}
