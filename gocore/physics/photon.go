package physics

type PhotonFate int

const (
	Escaped PhotonFate = iota
	Captured
	HitDisk
	InFlight
)

type Photon struct {
	R0, Theta0, Phi0    float64
	DR0, DTheta0, DPhi0 float64

	TrajectoryR     []float64
	TrajectoryTheta []float64
	TrajectoryPhi   []float64

	Fate         PhotonFate
	DiskR        float64
	DiskPhi      float64
	DiskThetaDot float64
	Brightness   float64
	Color        [3]float32
}

func (p *Photon) InitialState() [6]float64 {
	return [6]float64{p.R0, p.Theta0, p.Phi0, p.DR0, p.DTheta0, p.DPhi0}
}

func NewPhoton(r, theta, phi, dr, dtheta, dphi float64) *Photon {
	return &Photon{
		R0: r, Theta0: theta, Phi0: phi,
		DR0: dr, DTheta0: dtheta, DPhi0: dphi,
		Fate: InFlight,
	}
}
