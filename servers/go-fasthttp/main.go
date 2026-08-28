package main

import (
	"log"
	"os"
	"runtime"
	"strconv"

	"github.com/valyala/fasthttp"
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

	handler := func(ctx *fasthttp.RequestCtx) {
		ctx.SetContentType("text/plain")
		ctx.Response.Header.SetContentLength(13)
		ctx.SetBodyString("Hello, World!")
	}
	log.Fatal(fasthttp.ListenAndServe(":"+port, handler))
}
