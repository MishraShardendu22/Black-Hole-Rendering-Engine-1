package main

import (
	"fmt"
	"image"
	"image/color"
	"image/png"
	"log"
	"math"
	"os"
	"runtime"
	"time"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/inpututil"

	bhmath "github.com/hlack-bole/gocore/bh_math"
	"github.com/hlack-bole/gocore/core"
)

const (
	renderW    = 160
	renderH    = 120
	windowW    = 800
	windowH    = 600
	fovDefault = 60.0
)

type Game struct {
	distance    float64
	inclination float64
	azimuth     float64
	fov         float64
	spin        float64
	mass        float64
	rDiskOuter  float64
	rMax        float64
	pixels      []float32
	img         *image.RGBA
	fps         float64
}

func newGame() *Game {
	return &Game{
		distance:    30.0,
		inclination: math.Pi * 80 / 180,
		azimuth:     0,
		fov:         fovDefault,
		spin:        0,
		mass:        1.0,
		rDiskOuter:  20.0,
		rMax:        250.0,
		pixels:      make([]float32, renderW*renderH*3),
		img:         image.NewRGBA(image.Rect(0, 0, renderW, renderH)),
	}
}

func (g *Game) Update() error {
	dt := 0.02
	if ebiten.IsKeyPressed(ebiten.KeyArrowUp) {
		g.inclination -= dt * 0.5
		if g.inclination < 0.05 {
			g.inclination = 0.05
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyArrowDown) {
		g.inclination += dt * 0.5
		if g.inclination > math.Pi-0.05 {
			g.inclination = math.Pi - 0.05
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyArrowLeft) {
		g.azimuth -= dt * 0.5
	}
	if ebiten.IsKeyPressed(ebiten.KeyArrowRight) {
		g.azimuth += dt * 0.5
	}
	if ebiten.IsKeyPressed(ebiten.KeyW) {
		g.distance -= dt * 10
		if g.distance < 5 {
			g.distance = 5
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyS) {
		g.distance += dt * 10
	}
	if ebiten.IsKeyPressed(ebiten.KeyA) {
		g.spin -= dt * 0.2
		if g.spin < 0 {
			g.spin = 0
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyD) {
		g.spin += dt * 0.2
		if g.spin >= g.mass {
			g.spin = g.mass - 0.01
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyEqual) {
		g.fov -= dt * 20
		if g.fov < 10 {
			g.fov = 10
		}
	}
	if ebiten.IsKeyPressed(ebiten.KeyMinus) {
		g.fov += dt * 20
		if g.fov > 120 {
			g.fov = 120
		}
	}
	if inpututil.IsKeyJustPressed(ebiten.KeyR) {
		go g.saveHighRes()
	}
	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	t0 := time.Now()
	photons := g.buildPhotonArray(renderW, renderH)
	params := core.RenderBatchParams{
		M:              g.mass,
		Spin:           g.spin,
		RDiskOuter:     g.rDiskOuter,
		RMax:           g.rMax,
		LambdaMax:      2000.0,
		EnableRedshift: true,
		EnableDoppler:  true,
		EnableBeaming:  true,
	}
	core.RenderBatch(photons, renderW*renderH, params, g.pixels)

	for i := 0; i < renderH; i++ {
		for j := 0; j < renderW; j++ {
			off := (i*renderW + j) * 3
			r := clampByte(g.pixels[off])
			gr := clampByte(g.pixels[off+1])
			b := clampByte(g.pixels[off+2])
			g.img.SetRGBA(j, i, color.RGBA{R: r, G: gr, B: b, A: 255})
		}
	}

	eImg := ebiten.NewImageFromImage(g.img)
	op := &ebiten.DrawImageOptions{}
	sx := float64(windowW) / float64(renderW)
	sy := float64(windowH) / float64(renderH)
	op.GeoM.Scale(sx, sy)
	op.Filter = ebiten.FilterNearest
	screen.DrawImage(eImg, op)

	elapsed := time.Since(t0).Seconds()
	if elapsed > 0 {
		g.fps = 1.0 / elapsed
	}
	info := fmt.Sprintf("FPS: %.1f\nDist: %.1f  Inc: %.1f  Az: %.1f\nFOV: %.0f  Spin: %.3f  M: %.1f",
		g.fps, g.distance, g.inclination*180/math.Pi, g.azimuth*180/math.Pi,
		g.fov, g.spin, g.mass)
	ebitenutil.DebugPrint(screen, info)
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return windowW, windowH
}

func (g *Game) buildPhotonArray(nx, ny int) []float64 {
	camX := g.distance * math.Sin(g.inclination) * math.Cos(g.azimuth)
	camY := g.distance * math.Sin(g.inclination) * math.Sin(g.azimuth)
	camZ := g.distance * math.Cos(g.inclination)
	camPos := [3]float64{camX, camY, camZ}

	target := [3]float64{0, 0, 0}
	upHint := [3]float64{0, 0, 1}

	forward := bhmath.Normalize(bhmath.Sub(target, camPos))
	right := bhmath.Normalize(bhmath.Cross(forward, upHint))
	up := bhmath.Cross(right, forward)

	aspect := float64(nx) / float64(ny)
	fovRad := g.fov * math.Pi / 180
	halfW := math.Tan(fovRad / 2)
	halfH := halfW / aspect

	photons := make([]float64, nx*ny*6)
	for i := 0; i < ny; i++ {
		v := 1.0 - 2.0*(float64(i)+0.5)/float64(ny)
		for j := 0; j < nx; j++ {
			u := -1.0 + 2.0*(float64(j)+0.5)/float64(nx)
			dir := bhmath.Normalize(bhmath.Add(
				bhmath.Add(forward, bhmath.Scale(right, u*halfW)),
				bhmath.Scale(up, v*halfH),
			))
			r, theta, phi := bhmath.CartesianToSpherical(camPos[0], camPos[1], camPos[2])
			vr, vtheta, vphi := bhmath.CartesianVelocityToSpherical(camPos, dir)
			off := (i*nx + j) * 6
			photons[off] = r
			photons[off+1] = theta
			photons[off+2] = phi
			photons[off+3] = vr
			photons[off+4] = vtheta
			photons[off+5] = vphi
		}
	}
	return photons
}

func (g *Game) saveHighRes() {
	nx, ny := 640, 480
	photons := g.buildPhotonArray(nx, ny)
	pixels := make([]float32, nx*ny*3)
	params := core.RenderBatchParams{
		M:              g.mass,
		Spin:           g.spin,
		RDiskOuter:     g.rDiskOuter,
		RMax:           g.rMax,
		LambdaMax:      2000.0,
		EnableRedshift: true,
		EnableDoppler:  true,
		EnableBeaming:  true,
	}
	core.RenderBatch(photons, nx*ny, params, pixels)

	img := image.NewRGBA(image.Rect(0, 0, nx, ny))
	for i := 0; i < ny; i++ {
		for j := 0; j < nx; j++ {
			off := (i*nx + j) * 3
			r := clampByte(pixels[off])
			gr := clampByte(pixels[off+1])
			b := clampByte(pixels[off+2])
			img.SetRGBA(j, i, color.RGBA{R: r, G: gr, B: b, A: 255})
		}
	}

	if err := os.MkdirAll("output", 0o755); err != nil {
		log.Printf("Failed to create output dir: %v", err)
		return
	}
	fname := fmt.Sprintf("output/render_%d.png", time.Now().Unix())
	f, err := os.Create(fname)
	if err != nil {
		log.Printf("Failed to create file: %v", err)
		return
	}
	defer f.Close()
	if err := png.Encode(f, img); err != nil {
		log.Printf("Failed to encode PNG: %v", err)
		return
	}
	log.Printf("Saved high-res render to %s", fname)
}

func clampByte(v float32) uint8 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 255
	}
	return uint8(v * 255)
}

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU())
	ebiten.SetWindowSize(windowW, windowH)
	ebiten.SetWindowTitle("Hlack-Bole Interactive Black Hole Renderer")
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeEnabled)
	game := newGame()
	if err := ebiten.RunGame(game); err != nil {
		log.Fatal(err)
	}
}
