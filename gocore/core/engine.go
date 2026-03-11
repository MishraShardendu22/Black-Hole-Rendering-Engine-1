package core

import (
	"runtime"
	"sync"

	"github.com/hlack-bole/gocore/physics"
	"github.com/hlack-bole/gocore/renderer"
	"github.com/hlack-bole/gocore/simulation"
)

type RenderBatchParams struct {
	M              float64
	Spin           float64
	RDiskOuter     float64
	RMax           float64
	LambdaMax      float64
	EnableRedshift bool
	EnableDoppler  bool
	EnableBeaming  bool
}

func RenderBatch(photons []float64, nPixels int, params RenderBatchParams, outRGB []float32) {
	nWorkers := runtime.GOMAXPROCS(0)
	if nWorkers < 1 {
		nWorkers = 1
	}

	jobs := make(chan int, nPixels)
	var wg sync.WaitGroup

	solverParams := simulation.SolverParams{
		RTol:       1e-8,
		ATol:       1e-10,
		HInitial:   0.1,
		HMax:       1.0,
		LambdaMax:  params.LambdaMax,
		M:          params.M,
		Spin:       params.Spin,
		RMax:       params.RMax,
		RDiskOuter: params.RDiskOuter,
	}

	renderParams := renderer.RenderParams{
		M:              params.M,
		Spin:           params.Spin,
		RDiskOuter:     params.RDiskOuter,
		RMax:           params.RMax,
		EnableRedshift: params.EnableRedshift,
		EnableDoppler:  params.EnableDoppler,
		EnableBeaming:  params.EnableBeaming,
	}

	for w := 0; w < nWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range jobs {
				off := idx * 6
				p := physics.NewPhoton(
					photons[off], photons[off+1], photons[off+2],
					photons[off+3], photons[off+4], photons[off+5],
				)
				simulation.SolvePhoton(p, solverParams)
				rgb := renderer.ComputePixelColor(p, renderParams)
				oOff := idx * 3
				outRGB[oOff] = rgb[0]
				outRGB[oOff+1] = rgb[1]
				outRGB[oOff+2] = rgb[2]
			}
		}()
	}

	for i := 0; i < nPixels; i++ {
		jobs <- i
	}
	close(jobs)
	wg.Wait()
}

func TraceOnePixel(state [6]float64, params RenderBatchParams) [3]float32 {
	p := physics.NewPhoton(state[0], state[1], state[2], state[3], state[4], state[5])

	solverParams := simulation.SolverParams{
		RTol:       1e-8,
		ATol:       1e-10,
		HInitial:   0.1,
		HMax:       1.0,
		LambdaMax:  params.LambdaMax,
		M:          params.M,
		Spin:       params.Spin,
		RMax:       params.RMax,
		RDiskOuter: params.RDiskOuter,
	}

	renderParams := renderer.RenderParams{
		M:              params.M,
		Spin:           params.Spin,
		RDiskOuter:     params.RDiskOuter,
		RMax:           params.RMax,
		EnableRedshift: params.EnableRedshift,
		EnableDoppler:  params.EnableDoppler,
		EnableBeaming:  params.EnableBeaming,
	}

	simulation.SolvePhoton(p, solverParams)
	return renderer.ComputePixelColor(p, renderParams)
}
