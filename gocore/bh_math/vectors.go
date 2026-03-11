package bh_math

import "math"

func Normalize(v [3]float64) [3]float64 {
	n := math.Sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
	if n == 0 {
		return [3]float64{}
	}
	return [3]float64{v[0] / n, v[1] / n, v[2] / n}
}

func Magnitude(v [3]float64) float64 {
	return math.Sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
}

func CartesianToSpherical(x, y, z float64) (r, theta, phi float64) {
	r = math.Sqrt(x*x + y*y + z*z)
	if r == 0 {
		return 0, 0, 0
	}
	costh := z / r
	if costh > 1 {
		costh = 1
	} else if costh < -1 {
		costh = -1
	}
	theta = math.Acos(costh)
	phi = math.Atan2(y, x)
	return
}

func SphericalToCartesian(r, theta, phi float64) (x, y, z float64) {
	sinTh := math.Sin(theta)
	x = r * sinTh * math.Cos(phi)
	y = r * sinTh * math.Sin(phi)
	z = r * math.Cos(theta)
	return
}

func CartesianVelocityToSpherical(pos, vel [3]float64) (vr, vtheta, vphi float64) {
	x, y, z := pos[0], pos[1], pos[2]
	vx, vy, vz := vel[0], vel[1], vel[2]
	r := math.Sqrt(x*x + y*y + z*z)
	rho := math.Sqrt(x*x + y*y)
	if r < 1e-15 {
		return 0, 0, 0
	}
	vr = (x*vx + y*vy + z*vz) / r
	if rho < 1e-15 {
		return vr, 0, 0
	}
	vtheta = (z*(x*vx+y*vy) - rho*rho*vz) / (r * r * rho)
	vphi = (x*vy - y*vx) / (rho * rho)
	return
}

func Cross(a, b [3]float64) [3]float64 {
	return [3]float64{
		a[1]*b[2] - a[2]*b[1],
		a[2]*b[0] - a[0]*b[2],
		a[0]*b[1] - a[1]*b[0],
	}
}

func Dot(a, b [3]float64) float64 {
	return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]
}

func Scale(v [3]float64, s float64) [3]float64 {
	return [3]float64{v[0] * s, v[1] * s, v[2] * s}
}

func Add(a, b [3]float64) [3]float64 {
	return [3]float64{a[0] + b[0], a[1] + b[1], a[2] + b[2]}
}

func Sub(a, b [3]float64) [3]float64 {
	return [3]float64{a[0] - b[0], a[1] - b[1], a[2] - b[2]}
}
