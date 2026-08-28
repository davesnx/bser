.PHONY: first deps lock build bench smoke list clean

BUN_SERVERS = elysia-bun bun-fetch-native hono-bun h3-bun node-http-bun express-bun fastify-bun
NPM_SERVERS = node-http-scriptc
OCAML_BASE_SERVERS = dream opium vif trail httpcats cohttp-eio cohttp-lwt httpun-eio httpun-lwt httpaf tiny-httpd tiny-httpd-moonpool
OCAML_FLAMBDA_SERVERS = dream-flambda httpcats-flambda cohttp-eio-flambda httpaf-flambda tiny-httpd-flambda
OCAML_MULTICORE_SERVERS = vif-multicore httpcats-multicore cohttp-eio-multicore httpun-eio-multicore
OCAML_SERVERS = $(OCAML_BASE_SERVERS) $(OCAML_FLAMBDA_SERVERS) $(OCAML_MULTICORE_SERVERS)

# Start here: get a single OCaml server (dream) locked, built, and benchmarked
# in a short run next to the Bun baseline. Needs a recent dune (>= 3.24) with
# package management: curl -fsSL https://get.dune.build/install | sh
first:
	cd servers/dream && ([ -d dune.lock ] || dune pkg lock) && dune build ./main.exe
	cd servers/elysia-bun && bun install --frozen-lockfile
	python3 bench.py --servers elysia-bun,dream --duration 5 --warmup 2 --connections 32

# Install/resolve dependencies for all servers (Bun packages + dune locks).
deps: lock
	@for s in $(BUN_SERVERS); do \
	  echo "== bun install: $$s"; \
	  (cd servers/$$s && bun install --frozen-lockfile) || exit 1; \
	done
	@for s in $(NPM_SERVERS); do \
	  echo "== npm ci: $$s"; \
	  (cd servers/$$s && npm ci) || exit 1; \
	done

# (Re)generate each OCaml server's own dune.lock. Each server is a standalone
# dune project, so dependency versions are solved per server and never collide.
lock:
	@for s in $(OCAML_SERVERS); do \
	  echo "== dune pkg lock: $$s"; \
	  (cd servers/$$s && dune pkg lock) || exit 1; \
	done
	python3 patch-trail-lock.py

# Build every server without running the benchmark.
build:
	@for s in $(BUN_SERVERS); do \
	  echo "== bun install: $$s"; \
	  (cd servers/$$s && bun install --frozen-lockfile) || exit 1; \
	done
	@for s in $(NPM_SERVERS); do \
	  echo "== npm build: $$s"; \
	  (cd servers/$$s && npm ci && npm run build) || exit 1; \
	done
	python3 patch-trail-lock.py
	@for s in $(OCAML_SERVERS); do \
	  echo "== dune build: $$s"; \
	  (cd servers/$$s && ([ -d dune.lock ] || dune pkg lock) && dune build ./main.exe) || exit 1; \
	done

# Full benchmark run with the defaults from servers.json.
bench:
	python3 bench.py

# Quick pipeline check: short runs, small concurrency.
smoke:
	python3 bench.py --duration 3 --warmup 1 --connections 16

list:
	python3 bench.py --list

clean:
	@for s in $(BUN_SERVERS); do rm -rf servers/$$s/node_modules; done
	@for s in $(NPM_SERVERS); do rm -rf servers/$$s/node_modules servers/$$s/_build; done
	rm -rf results
	@for s in $(OCAML_SERVERS); do rm -rf servers/$$s/_build; done
