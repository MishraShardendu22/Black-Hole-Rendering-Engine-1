package main

import "C"
import (
	"unsafe"

	"github.com/hlack-bole/gocore/core"
)

//export RenderBatch
func RenderBatch(
	photons *C.double,
	nPixels C.int,
	mass C.double,
	spin C.double,
	rOuter C.double,
	rMax C.double,
	enableRedshift C.int,
	enableDoppler C.int,
	enableBeaming C.int,
	outRGB *C.float,
) {
	n := int(nPixels)
	if n <= 0 {
		return
	}

	photonSlice := unsafe.Slice((*float64)(unsafe.Pointer(photons)), n*6)
	outSlice := unsafe.Slice((*float32)(unsafe.Pointer(outRGB)), n*3)

	params := core.RenderBatchParams{
		M:              float64(mass),
		Spin:           float64(spin),
		RDiskOuter:     float64(rOuter),
		RMax:           float64(rMax),
		LambdaMax:      2000.0,
		EnableRedshift: int(enableRedshift) != 0,
		EnableDoppler:  int(enableDoppler) != 0,
		EnableBeaming:  int(enableBeaming) != 0,
	}

	core.RenderBatch(photonSlice, n, params, outSlice)
}

//export TracePixel
func TracePixel(
	r, theta, phi, rdot, thetadot, phidot C.double,
	mass, spin, rOuter, rMax C.double,
	enableRedshift, enableDoppler, enableBeaming C.int,
	outR, outG, outB *C.float,
) {
	state := [6]float64{
		float64(r), float64(theta), float64(phi),
		float64(rdot), float64(thetadot), float64(phidot),
	}
	params := core.RenderBatchParams{
		M:              float64(mass),
		Spin:           float64(spin),
		RDiskOuter:     float64(rOuter),
		RMax:           float64(rMax),
		LambdaMax:      2000.0,
		EnableRedshift: int(enableRedshift) != 0,
		EnableDoppler:  int(enableDoppler) != 0,
		EnableBeaming:  int(enableBeaming) != 0,
	}

	rgb := core.TraceOnePixel(state, params)
	*outR = C.float(rgb[0])
	*outG = C.float(rgb[1])
	*outB = C.float(rgb[2])
}

func main() {}
