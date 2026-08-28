package main

import (
	"io"
	"log"
	"net/http"
	"os"
	"runtime"
	"strconv"
)

func main() {
	cpuCount, err := strconv.Atoi(os.Getenv("BSER_CPU_COUNT"))
	if err != nil || cpuCount < 1 {
		log.Fatal("BSER_CPU_COUNT must be a positive integer")
	}
	runtime.GOMAXPROCS(cpuCount)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain")
		w.Header().Set("Content-Length", "13")
		_, _ = io.WriteString(w, "Hello, World!")
	})
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
