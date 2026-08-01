#!/usr/bin/env python3
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


RESULT_RE = re.compile(r"RESULT,(.*)")


def parse_result(output):
    result = None
    for line in output.splitlines():
        match = RESULT_RE.search(line)
        if not match:
            continue
        fields = {}
        for part in match.group(1).split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        result = fields
    return result


def numeric(value):
    if value is None or value == "":
        return ""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    preferred = [
        "experiment", "op", "sparse_factor", "repeat", "timing_source",
        "time_us", "time_ms", "selected_field", "rc", "elapsed_s",
        "d1", "d2", "num_nodes", "num_edges", "num_spaces", "num_pieces",
        "buffer_size", "cmd", "result_json", "output_tail",
    ]
    keys = []
    seen = set()
    for key in preferred:
        if any(key in row for row in rows):
            keys.append(key)
            seen.add(key)
    for row in rows:
        for key in row:
            if key not in seen:
                keys.append(key)
                seen.add(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_one(cmd, timeout):
    start = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        timeout=timeout,
    )
    return proc.returncode, time.time() - start, proc.stdout, parse_result(proc.stdout)


def main():
    repo = Path.cwd()
    out_dir = Path(os.environ.get(
        "REALM_SPARSITY_OUT",
        repo / ".local" / ("sparsity_calibration_" + time.strftime("%Y%m%d_%H%M%S")),
    ))
    repeats = int(os.environ.get("REALM_SPARSITY_REPEATS", "5"))
    timeout = int(os.environ.get("REALM_SPARSITY_TIMEOUT", "900"))
    out_dir.mkdir(parents=True, exist_ok=True)

    binary = repo / "build_pm_deppart" / "tests" / "benchmark"
    if not binary.exists():
        raise SystemExit(f"missing benchmark binary: {binary}")

    base = [
        str(binary),
        "-ll:gpu", "1",
        "-ll:cpu", "1",
        "-ll:fsize", "8192",
        "-dp:workers", "1",
        "-dp:hpool", "256",
        "-nocheck",
        "-random",
        "-d1", "2",
        "-d2", "2",
    ]
    policies = [
        ("cpu_source", [], "cpu_us"),
        ("gpu_source", ["-dp:noisectopt"], "gpu_us"),
    ]
    sparse_factors = [1, 2, 5, 10, 25, 50]
    ops = ["image", "preimage"]

    raw_rows = []
    point_rows = []
    failures = []

    for repeat in range(1, repeats + 1):
        for op in ops:
            for sparse_factor in sparse_factors:
                op_args = [
                    op,
                    "-n", "1000",
                    "-e", "1000",
                    "-p", "1",
                    "-s", "4",
                    "-f", str(sparse_factor),
                    "-b", "100",
                ]
                for timing_source, extra, selected_field in policies:
                    cmd = base + extra + op_args
                    print(
                        f"RUN repeat={repeat} op={op} f={sparse_factor} source={timing_source}",
                        flush=True,
                    )
                    try:
                        rc, elapsed, output, parsed = run_one(cmd, timeout)
                    except subprocess.TimeoutExpired as exc:
                        failures.append({
                            "experiment": "sparsity_calibration",
                            "op": op,
                            "sparse_factor": sparse_factor,
                            "repeat": repeat,
                            "timing_source": timing_source,
                            "rc": "timeout",
                            "elapsed_s": timeout,
                            "cmd": " ".join(cmd),
                            "output_tail": (exc.stdout or "")[-4000:],
                        })
                        continue

                    raw = {
                        "experiment": "sparsity_calibration",
                        "op": op,
                        "sparse_factor": sparse_factor,
                        "repeat": repeat,
                        "timing_source": timing_source,
                        "selected_field": selected_field,
                        "rc": rc,
                        "elapsed_s": f"{elapsed:.6f}",
                        "cmd": " ".join(cmd),
                        "result_json": json.dumps(parsed or {}, sort_keys=True),
                    }
                    if parsed:
                        raw.update(parsed)
                    raw_rows.append(raw)

                    if rc != 0 or not parsed or selected_field not in parsed:
                        failures.append({
                            "experiment": "sparsity_calibration",
                            "op": op,
                            "sparse_factor": sparse_factor,
                            "repeat": repeat,
                            "timing_source": timing_source,
                            "rc": rc,
                            "elapsed_s": f"{elapsed:.6f}",
                            "cmd": " ".join(cmd),
                            "output_tail": output[-4000:],
                        })
                        continue

                    time_us = int(parsed[selected_field])
                    point_rows.append({
                        "experiment": "sparsity_calibration",
                        "op": op,
                        "sparse_factor": sparse_factor,
                        "repeat": repeat,
                        "timing_source": timing_source,
                        "time_us": time_us,
                        "time_ms": time_us / 1000.0,
                        "selected_field": selected_field,
                        "d1": numeric(parsed.get("d1")),
                        "d2": numeric(parsed.get("d2")),
                        "num_nodes": numeric(parsed.get("num_nodes")),
                        "num_edges": numeric(parsed.get("num_edges")),
                        "num_spaces": numeric(parsed.get("num_spaces")),
                        "num_pieces": numeric(parsed.get("num_pieces")),
                        "buffer_size": numeric(parsed.get("buffer_size")),
                        "cmd": " ".join(cmd),
                    })

    grouped = defaultdict(list)
    meta = {}
    for row in point_rows:
        key = (row["op"], row["sparse_factor"], row["timing_source"])
        grouped[key].append(row["time_us"])
        meta[key] = row

    summary_rows = []
    by_case = defaultdict(dict)
    for key, values in grouped.items():
        op, sparse_factor, timing_source = key
        values = sorted(values)
        row0 = meta[key]
        summary = {
            "experiment": "sparsity_calibration",
            "op": op,
            "sparse_factor": sparse_factor,
            "timing_source": timing_source,
            "n": len(values),
            "median_us": statistics.median(values),
            "median_ms": statistics.median(values) / 1000.0,
            "min_us": min(values),
            "max_us": max(values),
            "d1": row0["d1"],
            "d2": row0["d2"],
            "num_nodes": row0["num_nodes"],
            "num_edges": row0["num_edges"],
            "num_spaces": row0["num_spaces"],
            "num_pieces": row0["num_pieces"],
            "buffer_size": row0["buffer_size"],
        }
        summary_rows.append(summary)
        by_case[(op, sparse_factor)][timing_source] = summary["median_us"]

    for row in summary_rows:
        pair = by_case[(row["op"], row["sparse_factor"])]
        cpu = pair.get("cpu_source")
        gpu = pair.get("gpu_source")
        row["speedup_cpu_over_gpu"] = (cpu / gpu) if cpu and gpu else ""

    raw_path = out_dir / "sparsity_calibration_raw.csv"
    points_path = out_dir / "sparsity_calibration_points.csv"
    summary_path = out_dir / "sparsity_calibration_summary.csv"
    failures_path = out_dir / "sparsity_calibration_failures.csv"
    manifest_path = out_dir / "manifest.json"

    write_csv(raw_path, raw_rows)
    write_csv(points_path, point_rows)
    write_csv(summary_path, summary_rows)
    write_csv(failures_path, failures)

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo": str(repo),
        "binary": str(binary),
        "repeats": repeats,
        "timeout_s": timeout,
        "ops": ops,
        "sparse_factors": sparse_factors,
        "num_raw_rows": len(raw_rows),
        "num_point_rows": len(point_rows),
        "num_failures": len(failures),
        "policy": {
            "common_flags": base[1:],
            "cpu_source": "normal run, use cpu_us",
            "gpu_source": "-dp:noisectopt run, use gpu_us",
            "fixed_problem": "2D->2D, -n 1000, -e 1000, -p 1, -s 4, -b 100",
        },
        "outputs": {
            "raw": str(raw_path),
            "points": str(points_path),
            "summary": str(summary_path),
            "failures": str(failures_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
