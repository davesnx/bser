#!/usr/bin/env python3
"""Render a standalone HTML report from benchmark results.json."""

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "report-template.html")
DATA_TOKEN = "__REPORT_DATA__"


def write_report(payload, output_path):
    with open(TEMPLATE_PATH) as template_file:
        template = template_file.read()
    if template.count(DATA_TOKEN) != 1:
        raise ValueError(f"expected one {DATA_TOKEN} token in {TEMPLATE_PATH}")

    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    data = data.replace("</", "<\\/")
    with open(output_path, "w") as output_file:
        output_file.write(template.replace(DATA_TOKEN, data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", help="path to results.json")
    parser.add_argument("--out", help="output path; defaults to report.html beside results")
    args = parser.parse_args()

    with open(args.results) as results_file:
        payload = json.load(results_file)
    output_path = args.out or os.path.join(os.path.dirname(args.results), "report.html")
    write_report(payload, output_path)
    print(output_path)


if __name__ == "__main__":
    main()
