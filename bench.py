#!/usr/bin/env python3
"""Hello-world web server benchmark orchestrator.

For each server declared in servers.json this script:
  1. builds it (unless --no-build),
  2. starts it with PORT set and waits for the socket to accept connections,
  3. runs a warmup load, then a measured load with oha, wrk, or autocannon,
  4. samples RSS and CPU of the whole server process tree while it runs,
  5. tears the server down and writes results (JSON + Markdown) to results/.

Only the Linux /proc filesystem is used for resource sampling.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
CLK_TCK = os.sysconf("SC_CLK_TCK")


# ---------------------------------------------------------------------------
# /proc helpers (process-tree RSS and CPU)
# ---------------------------------------------------------------------------

def _stat_fields(pid):
    """Fields of /proc/<pid>/stat after the comm field, or None."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as f:
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    idx = data.rfind(")")
    if idx == -1:
        return None
    return data[idx + 2 :].split()


def proc_tree(root_pid):
    """root_pid plus all its live descendants."""
    children = {}
    try:
        entries = os.listdir("/proc")
    except OSError:
        return [root_pid]
    for entry in entries:
        if not entry.isdigit():
            continue
        fields = _stat_fields(int(entry))
        if fields is None:
            continue
        ppid = int(fields[1])
        children.setdefault(ppid, []).append(int(entry))
    pids, stack, seen = [], [root_pid], set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        pids.append(pid)
        stack.extend(children.get(pid, []))
    return pids


def rss_bytes(pid):
    try:
        with open(f"/proc/{pid}/statm") as f:
            return int(f.read().split()[1]) * PAGE_SIZE
    except OSError:
        return 0


def cpu_seconds(pid):
    fields = _stat_fields(pid)
    if fields is None:
        return 0.0
    utime, stime = int(fields[11]), int(fields[12])
    return (utime + stime) / CLK_TCK


class ResourceSampler(threading.Thread):
    """Polls RSS/CPU of a process tree; peak/avg RSS and a CPU-time counter."""

    def __init__(self, root_pid, interval=0.2):
        super().__init__(daemon=True)
        self.root_pid = root_pid
        self.interval = interval
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self.peak_rss = 0
        self.samples = []
        self.cpu = 0.0

    def run(self):
        while not self._stop.is_set():
            pids = proc_tree(self.root_pid)
            rss = sum(rss_bytes(p) for p in pids)
            cpu = sum(cpu_seconds(p) for p in pids)
            with self._lock:
                self.samples.append(rss)
                self.peak_rss = max(self.peak_rss, rss)
                self.cpu = max(self.cpu, cpu)
            self._stop.wait(self.interval)

    def snapshot(self):
        with self._lock:
            avg = sum(self.samples) / len(self.samples) if self.samples else 0
            return {"peak_rss": self.peak_rss, "avg_rss": avg, "cpu": self.cpu}

    def reset_window(self):
        with self._lock:
            self.samples = []
            self.peak_rss = 0

    def stop(self):
        self._stop.set()


# ---------------------------------------------------------------------------
# Load generators
# ---------------------------------------------------------------------------

def detect_tool():
    if shutil.which("oha"):
        return ["oha"]
    if shutil.which("wrk"):
        return ["wrk"]
    if shutil.which("autocannon"):
        return ["autocannon"]
    for runner in (["bunx", "autocannon"], ["npx", "--yes", "autocannon"]):
        if shutil.which(runner[0]):
            return runner
    return None


def resolve_tool(name):
    if name == "auto":
        tool = detect_tool()
        if tool is None:
            sys.exit(
                "error: no load generator found. Install one of: "
                "oha (cargo install oha), wrk, or autocannon (bun add -g autocannon)."
            )
        return tool
    if name == "autocannon" and not shutil.which("autocannon"):
        for runner in (["bunx", "autocannon"], ["npx", "--yes", "autocannon"]):
            if shutil.which(runner[0]):
                return runner
    if not shutil.which(name):
        sys.exit(f"error: requested tool {name!r} is not on PATH")
    return [name]


def run_load(tool, url, duration, connections, threads, capture=True):
    """Run one load; returns normalized metrics (None when capture=False)."""
    kind = "autocannon" if "autocannon" in tool[-1] else tool[0]
    if kind == "oha":
        cmd = tool + ["--no-tui", "-j", "-z", f"{duration}s", "-c", str(connections), url]
    elif kind == "wrk":
        cmd = tool + [f"-t{threads}", f"-c{connections}", f"-d{duration}s", "--latency", url]
    else:  # autocannon
        cmd = tool + ["-c", str(connections), "-d", str(duration), "-j", url]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"load generator failed ({' '.join(cmd)}):\n{proc.stderr.strip() or proc.stdout.strip()}"
        )
    if not capture:
        return None
    if kind == "oha":
        return parse_oha(proc.stdout)
    if kind == "wrk":
        return parse_wrk(proc.stdout)
    return parse_autocannon(proc.stdout)


def parse_oha(output):
    data = json.loads(output)
    summary = data["summary"]
    pct = data.get("latencyPercentiles", {})
    status = data.get("statusCodeDistribution", {})
    total_2xx = sum(v for k, v in status.items() if k.startswith("2"))
    total = sum(status.values())
    errors = sum(data.get("errorDistribution", {}).values())
    return {
        "tool": "oha",
        "requests_per_sec": summary["requestsPerSec"],
        "total_requests": total,
        "latency_ms": {
            "avg": summary["average"] * 1000,
            "p50": pct.get("p50", 0) * 1000,
            "p90": pct.get("p90", 0) * 1000,
            "p99": pct.get("p99", 0) * 1000,
            "max": summary["slowest"] * 1000,
        },
        "throughput_bytes_per_sec": summary.get("sizePerSec", 0),
        "errors": errors,
        "non_2xx": total - total_2xx,
        "raw": data,
    }


_WRK_UNITS = {"us": 1e-3, "ms": 1.0, "s": 1e3, "m": 60e3}
_WRK_SIZES = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}


def _wrk_ms(value):
    m = re.match(r"([\d.]+)(us|ms|s|m)", value)
    return float(m.group(1)) * _WRK_UNITS[m.group(2)] if m else 0.0


def _wrk_bytes(value):
    m = re.match(r"([\d.]+)(B|KB|MB|GB)", value)
    return float(m.group(1)) * _WRK_SIZES[m.group(2)] if m else 0.0


def parse_wrk(output):
    def search(pattern, default=""):
        m = re.search(pattern, output, re.M)
        return m.group(1) if m else default

    latency = {}
    for pct, key in (("50", "p50"), ("90", "p90"), ("99", "p99")):
        latency[key] = _wrk_ms(search(rf"^\s*{pct}%\s+(\S+)", ""))
    non_2xx = int(search(r"Non-2xx or 3xx responses:\s+(\d+)", "0"))
    errors_m = re.search(
        r"Socket errors: connect (\d+), read (\d+), write (\d+), timeout (\d+)", output
    )
    errors = sum(int(g) for g in errors_m.groups()) if errors_m else 0
    return {
        "tool": "wrk",
        "requests_per_sec": float(search(r"Requests/sec:\s+([\d.]+)", "0")),
        "total_requests": int(search(r"(\d+) requests in", "0")),
        "latency_ms": {
            "avg": _wrk_ms(search(r"Latency\s+(\S+)", "")),
            "max": _wrk_ms(search(r"Latency\s+\S+\s+\S+\s+(\S+)", "")),
            **latency,
        },
        "throughput_bytes_per_sec": _wrk_bytes(search(r"Transfer/sec:\s+(\S+)", "")),
        "errors": errors,
        "non_2xx": non_2xx,
        "raw": output,
    }


def parse_autocannon(output):
    data = json.loads(output)
    lat = data.get("latency", {})
    return {
        "tool": "autocannon",
        "requests_per_sec": data.get("requests", {}).get("average", 0),
        "total_requests": data.get("requests", {}).get("total", 0),
        "latency_ms": {
            "avg": lat.get("average", 0),
            "p50": lat.get("p50", 0),
            "p90": lat.get("p90", lat.get("p97_5")),
            "p99": lat.get("p99", 0),
            "max": lat.get("max", 0),
        },
        "throughput_bytes_per_sec": data.get("throughput", {}).get("average", 0),
        "errors": data.get("errors", 0) + data.get("timeouts", 0),
        "non_2xx": data.get("non2xx", 0),
        "raw": data,
    }


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def wait_port(host, port, timeout, proc=None):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            return False
        if port_open(host, port):
            return True
        time.sleep(0.1)
    return False


def wait_port_free(host, port, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not port_open(host, port):
            return True
        time.sleep(0.1)
    return False


def stop_process(proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.wait()


def tail(path, lines=20):
    try:
        with open(path, errors="replace") as f:
            return "".join(f.readlines()[-lines:])
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Benchmark loop
# ---------------------------------------------------------------------------

def bench_server(server, cfg, tool, log_dir, no_build):
    name = server["name"]
    cwd = os.path.join(HERE, server["cwd"])
    port = cfg["port"]
    url = f"http://127.0.0.1:{port}{cfg['path']}"
    result = {"name": name, "runtime": server.get("runtime", ""), "status": "ok"}

    print(f"\n=== {name} ({server.get('runtime', '')}) ===")

    if server.get("build") and not no_build:
        print(f"  building: {server['build']}")
        build = subprocess.run(
            server["build"], shell=True, cwd=cwd, capture_output=True, text=True
        )
        if build.returncode != 0:
            print(f"  BUILD FAILED for {name}")
            sys.stdout.write(build.stderr[-2000:] if build.stderr else build.stdout[-2000:])
            result.update(status="build_failed", error=build.stderr[-2000:])
            return result

    if port_open("127.0.0.1", port):
        result.update(status="port_busy", error=f"port {port} already in use")
        print(f"  SKIPPED: port {port} already in use")
        return result

    log_path = os.path.join(log_dir, f"{name}.log")
    log = open(log_path, "w")
    proc = subprocess.Popen(
        server["run"],
        shell=True,
        cwd=cwd,
        env={**os.environ, "PORT": str(port)},
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    sampler = None
    try:
        print(f"  starting: {server['run']} (pid {proc.pid})")
        if not wait_port("127.0.0.1", port, timeout=60, proc=proc):
            result.update(status="start_failed", error=tail(log_path))
            print(f"  START FAILED for {name}; log tail:\n{tail(log_path)}")
            return result

        sampler = ResourceSampler(proc.pid)
        sampler.start()

        if cfg["warmup"] > 0:
            print(f"  warmup: {cfg['warmup']}s")
            run_load(tool, url, cfg["warmup"], cfg["connections"], cfg["threads"], capture=False)

        sampler.reset_window()
        cpu_before = sampler.snapshot()["cpu"]
        print(
            f"  measuring: {cfg['duration']}s, {cfg['connections']} connections "
            f"({'/'.join(tool)})"
        )
        started = time.monotonic()
        metrics = run_load(tool, url, cfg["duration"], cfg["connections"], cfg["threads"])
        elapsed = time.monotonic() - started

        res = sampler.snapshot()
        cpu_used = max(0.0, res["cpu"] - cpu_before)
        result.update(
            metrics=metrics,
            resources={
                "peak_rss_bytes": res["peak_rss"],
                "avg_rss_bytes": res["avg_rss"],
                "cpu_seconds": cpu_used,
                "cpu_percent": (cpu_used / elapsed * 100) if elapsed else 0,
            },
        )
        print(
            f"  done: {metrics['requests_per_sec']:,.0f} req/s, "
            f"p99 {metrics['latency_ms']['p99']:.2f} ms, "
            f"peak RSS {res['peak_rss'] / 1e6:.1f} MB"
        )
    except Exception as exc:  # noqa: BLE001 - record and continue with next server
        result.update(status="error", error=str(exc))
        print(f"  ERROR for {name}: {exc}")
    finally:
        if sampler:
            sampler.stop()
        stop_process(proc)
        log.close()
        if not wait_port_free("127.0.0.1", port):
            print(f"  warning: port {port} still busy after shutdown")
    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def fmt_table(results, cfg, tool):
    header = [
        "Server", "Req/s", "Avg (ms)", "p50 (ms)", "p90 (ms)", "p99 (ms)",
        "Throughput (MB/s)", "Peak RSS (MB)", "CPU (%)", "Errors",
    ]
    rows = []
    ok = [r for r in results if r["status"] == "ok"]
    ok.sort(key=lambda r: r["metrics"]["requests_per_sec"], reverse=True)
    for r in ok:
        m, res = r["metrics"], r["resources"]
        lat = m["latency_ms"]

        def ms(v):
            return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

        rows.append([
            r["name"],
            f"{m['requests_per_sec']:,.0f}",
            ms(lat.get("avg")), ms(lat.get("p50")), ms(lat.get("p90")), ms(lat.get("p99")),
            f"{m['throughput_bytes_per_sec'] / 1e6:.2f}",
            f"{res['peak_rss_bytes'] / 1e6:.1f}",
            f"{res['cpu_percent']:.0f}",
            str(m["errors"] + m["non_2xx"]),
        ])
    for r in results:
        if r["status"] != "ok":
            rows.append([r["name"], f"({r['status']})"] + ["-"] * 8)

    md = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    md += ["| " + " | ".join(row) + " |" for row in rows]

    widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]
    txt = ["  ".join(h.ljust(widths[i]) for i, h in enumerate(header))]
    txt += ["  ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) for row in rows]

    note = (
        f"\nTool: {'/'.join(tool)} — {cfg['duration']}s @ {cfg['connections']} connections "
        f"(warmup {cfg['warmup']}s), path {cfg['path']}"
    )
    return "\n".join(md) + note, "\n".join(txt) + note


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", default=os.path.join(HERE, "servers.json"))
    parser.add_argument("--servers", help="comma-separated subset of server names")
    parser.add_argument("--duration", type=int, help="measured seconds per server")
    parser.add_argument("--warmup", type=int, help="warmup seconds per server")
    parser.add_argument("--connections", type=int, help="concurrent connections")
    parser.add_argument("--threads", type=int, help="load generator threads (wrk)")
    parser.add_argument("--port", type=int, help="port servers listen on")
    parser.add_argument(
        "--tool", default="auto", choices=["auto", "oha", "wrk", "autocannon"]
    )
    parser.add_argument("--no-build", action="store_true", help="skip build steps")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="exit non-zero if any server failed to build, start, or bench (for CI)",
    )
    parser.add_argument("--list", action="store_true", help="list servers and exit")
    parser.add_argument("--out", default=os.path.join(HERE, "results"))
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)
    cfg = dict(manifest["defaults"])
    for key in ("duration", "warmup", "connections", "threads", "port"):
        value = getattr(args, key)
        if value is not None:
            cfg[key] = value

    servers = manifest["servers"]
    if args.list:
        for s in servers:
            print(f"{s['name']:<12} {s.get('runtime', '')}")
        return
    if args.servers:
        wanted = [w.strip() for w in args.servers.split(",")]
        by_name = {s["name"]: s for s in servers}
        unknown = [w for w in wanted if w not in by_name]
        if unknown:
            sys.exit(f"error: unknown server(s): {', '.join(unknown)}")
        servers = [by_name[w] for w in wanted]

    tool = resolve_tool(args.tool)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = os.path.join(args.out, stamp)
    os.makedirs(out_dir, exist_ok=True)

    results = [bench_server(s, cfg, tool, out_dir, args.no_build) for s in servers]

    env = {
        "timestamp": stamp,
        "tool": " ".join(tool),
        "config": cfg,
        "cpu_count": os.cpu_count(),
        "uname": " ".join(os.uname()),
    }
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump({"environment": env, "results": results}, f, indent=2, default=str)

    md, txt = fmt_table(results, cfg, tool)
    with open(os.path.join(out_dir, "results.md"), "w") as f:
        f.write(f"# Hello-world benchmark — {stamp}\n\n{md}\n")

    print(f"\n{txt}\n\nResults written to {out_dir}")

    failed = [r["name"] for r in results if r["status"] != "ok"]
    if args.fail_on_error and failed:
        sys.exit(f"error: {len(failed)} server(s) did not complete: {', '.join(failed)}")


if __name__ == "__main__":
    main()
