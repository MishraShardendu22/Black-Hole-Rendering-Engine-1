.PHONY: build-go build-interactive run run-interactive clean

build-go:
	cd gocore && go build -o ../librender.so -buildmode=c-shared .

build-interactive:
	cd gocore && go build -o ../hlack-bole-live ./cmd/interactive/

run:
	python main.py --resolution 320x240

run-interactive:
	./hlack-bole-live

clean:
	rm -f librender.so librender.h hlack-bole-live
