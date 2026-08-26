#!/bin/bash
set -euo pipefail

root=$(cd "$(dirname "$0")" && pwd)
server_dir="$root/servers/vif-multicore"
output_dir=$(mktemp -d)
trap 'rm -rf "$output_dir"' EXIT

(cd "$server_dir" && dune build ./main.exe)

for run in 1 2 3 4 5; do
  python3 "$root/bench.py" \
    --servers vif-multicore \
    --duration 30 \
    --warmup 5 \
    --connections 64 \
    --tool wrk \
    --no-build \
    --fail-on-error \
    --out "$output_dir/run-$run" >/dev/null
done

python3 - "$output_dir" <<'PY'
import glob
import json
import statistics
import sys

records = []
for path in glob.glob(f"{sys.argv[1]}/run-*/*/results.json"):
    with open(path) as source:
        result = json.load(source)["results"][0]
    if result["status"] != "ok":
        raise SystemExit(f"benchmark failed: {result['status']}")
    records.append(result)

if len(records) != 5:
    raise SystemExit(f"expected 5 benchmark records, found {len(records)}")

def median(values):
    return statistics.median(values)

request_rates = [item["metrics"]["requests_per_sec"] for item in records]
p99 = [item["metrics"]["latency_ms"]["p99"] for item in records]
rss = [item["resources"]["peak_rss_bytes"] for item in records]
cpu = [item["resources"]["cpu_percent"] for item in records]
errors = [item["metrics"]["errors"] + item["metrics"]["non_2xx"] for item in records]

print(f"METRIC requests_per_sec={median(request_rates):.2f}")
print(f"METRIC p99_latency_ms={median(p99):.4f}")
print(f"METRIC peak_rss_bytes={median(rss):.0f}")
print(f"METRIC cpu_percent={median(cpu):.2f}")
print(f"METRIC errors={sum(errors)}")
print("SAMPLES requests_per_sec=" + ",".join(f"{value:.2f}" for value in request_rates))
PY
