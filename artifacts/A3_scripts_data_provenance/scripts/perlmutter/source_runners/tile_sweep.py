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
TILE_RE = re.compile(r"TILE,(.*)")


def parse_kv(line, prefix_re):
    match = prefix_re.search(line)
    if not match:
        return None
    fields = {}
    for part in match.group(1).split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key] = value
    return fields


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


def run_one(cmd, timeout):
    start = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        timeout=timeout,
    )
    elapsed = time.time() - start
    result = None
    last_tile = None
    all_tiles = []
    for line in proc.stdout.splitlines():
        tile = parse_kv(line, TILE_RE)
        if tile is not None:
            last_tile = tile
            all_tiles.append(tile)
            continue
        parsed = parse_kv(line, RESULT_RE)
        if parsed is not None:
            result = parsed
    return proc.returncode, elapsed, proc.stdout, result, last_tile, all_tiles


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    preferred = [
        "experiment", "op", "dimension", "density", "sparse_factor",
        "buffer_size", "repeat", "timing_source", "time_us", "time_ms",
        "selected_field", "gpu_tiles", "gpu_oom_backoffs",
        "gpu_host_fallback", "gpu_input_rects", "gpu_scratch_bytes",
        "tile_rows_seen", "d1", "d2", "num_nodes", "num_edges",
        "num_spaces", "num_pieces", "rc", "elapsed_s", "cmd",
        "result_json", "tile_json", "output_tail",
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


def main():
    repo = Path.cwd()
    out_dir = Path(os.environ.get(
        "REALM_TILE_SWEEP_OUT",
        repo / ".local" / ("tile_sweep_" + time.strftime("%Y%m%d_%H%M%S")),
    ))
    repeats = int(os.environ.get("REALM_TILE_SWEEP_REPEATS", "5"))
    timeout = int(os.environ.get("REALM_TILE_SWEEP_TIMEOUT", "900"))
    out_dir.mkdir(parents=True, exist_ok=True)

    binary = repo / "build_pm_deppart" / "tests" / "benchmark"
    if not binary.exists():
        raise SystemExit("missing benchmark binary: " + str(binary))

    dims = [
        ("1d", "1", "1", "1000000", "1000000"),
        ("2d", "2", "2", "1000", "1000"),
        ("3d", "3", "3", "100", "100"),
    ]
    densities = [
        ("dense", "1"),
        ("sparse", "5"),
    ]
    buffers = [100, 75, 50, 25, 10, 5, 2, 1]
    ops = ["image", "preimage"]
    policies = [
        ("cpu_source", [], "cpu_us"),
        ("gpu_source", ["-dp:noisectopt"], "gpu_us"),
    ]

    base = [
        str(binary),
        "-ll:gpu", "1",
        "-ll:cpu", "1",
        "-ll:fsize", "8192",
        "-dp:workers", "1",
        "-dp:hpool", "256",
        "-nocheck",
        "-random",
    ]

    raw_rows = []
    point_rows = []
    failures = []

    for repeat in range(1, repeats + 1):
        for op in ops:
            for dim_name, d1, d2, n, e in dims:
                for density, sparse_factor in densities:
                    for buffer_size in buffers:
                        op_args = [
                            "-d1", d1,
                            "-d2", d2,
                            op,
                            "-n", n,
                            "-e", e,
                            "-p", "1",
                            "-s", "4",
                            "-f", sparse_factor,
                            "-b", str(buffer_size),
                        ]
                        for timing_source, extra, selected_field in policies:
                            cmd = base + extra + op_args
                            print(
                                "RUN repeat=%d op=%s dim=%s density=%s b=%s source=%s"
                                % (repeat, op, dim_name, density, buffer_size, timing_source),
                                flush=True,
                            )
                            try:
                                rc, elapsed, output, parsed, tile, all_tiles = run_one(cmd, timeout)
                            except subprocess.TimeoutExpired as exc:
                                failures.append({
                                    "experiment": "tile_sweep",
                                    "op": op,
                                    "dimension": dim_name,
                                    "density": density,
                                    "sparse_factor": sparse_factor,
                                    "buffer_size": buffer_size,
                                    "repeat": repeat,
                                    "timing_source": timing_source,
                                    "rc": "timeout",
                                    "elapsed_s": timeout,
                                    "cmd": " ".join(cmd),
                                    "output_tail": (exc.stdout or "")[-4000:],
                                })
                                continue

                            raw = {
                                "experiment": "tile_sweep",
                                "op": op,
                                "dimension": dim_name,
                                "density": density,
                                "sparse_factor": sparse_factor,
                                "buffer_size": buffer_size,
                                "repeat": repeat,
                                "timing_source": timing_source,
                                "selected_field": selected_field,
                                "rc": rc,
                                "elapsed_s": "%.6f" % elapsed,
                                "cmd": " ".join(cmd),
                                "result_json": json.dumps(parsed or {}, sort_keys=True),
                                "tile_json": json.dumps(tile or {}, sort_keys=True),
                                "tile_rows_seen": len(all_tiles),
                            }
                            if parsed:
                                raw.update(parsed)
                            if tile:
                                raw.update(tile)
                            raw_rows.append(raw)

                            if rc != 0 or not parsed or selected_field not in parsed:
                                failures.append({
                                    "experiment": "tile_sweep",
                                    "op": op,
                                    "dimension": dim_name,
                                    "density": density,
                                    "sparse_factor": sparse_factor,
                                    "buffer_size": buffer_size,
                                    "repeat": repeat,
                                    "timing_source": timing_source,
                                    "rc": rc,
                                    "elapsed_s": "%.6f" % elapsed,
                                    "cmd": " ".join(cmd),
                                    "output_tail": output[-4000:],
                                })
                                continue

                            # Tile counters are GPU-only. Keep them on the GPU
                            # timing rows and leave them blank on CPU rows.
                            point = {
                                "experiment": "tile_sweep",
                                "op": op,
                                "dimension": dim_name,
                                "density": density,
                                "sparse_factor": numeric(sparse_factor),
                                "buffer_size": numeric(buffer_size),
                                "repeat": repeat,
                                "timing_source": timing_source,
                                "selected_field": selected_field,
                                "time_us": int(parsed[selected_field]),
                                "time_ms": int(parsed[selected_field]) / 1000.0,
                                "d1": numeric(parsed.get("d1")),
                                "d2": numeric(parsed.get("d2")),
                                "num_nodes": numeric(parsed.get("num_nodes")),
                                "num_edges": numeric(parsed.get("num_edges")),
                                "num_spaces": numeric(parsed.get("num_spaces")),
                                "num_pieces": numeric(parsed.get("num_pieces")),
                            }
                            if timing_source == "gpu_source" and tile:
                                for key in [
                                    "gpu_tiles", "gpu_oom_backoffs",
                                    "gpu_host_fallback", "gpu_input_rects",
                                    "gpu_scratch_bytes",
                                ]:
                                    point[key] = numeric(tile.get(key))
                                point["tile_rows_seen"] = len(all_tiles)
                            point_rows.append(point)

    grouped = defaultdict(list)
    meta = {}
    for row in point_rows:
        key = (
            row["op"], row["dimension"], row["density"],
            row["buffer_size"], row["timing_source"],
        )
        grouped[key].append(row)
        meta[key] = row

    summary_rows = []
    by_case = defaultdict(dict)
    for key, rows in grouped.items():
        op, dimension, density, buffer_size, timing_source = key
        times = sorted(row["time_us"] for row in rows)
        row0 = meta[key]
        summary = {
            "experiment": "tile_sweep",
            "op": op,
            "dimension": dimension,
            "density": density,
            "sparse_factor": row0["sparse_factor"],
            "buffer_size": buffer_size,
            "timing_source": timing_source,
            "n": len(times),
            "median_us": statistics.median(times),
            "median_ms": statistics.median(times) / 1000.0,
            "min_us": min(times),
            "max_us": max(times),
            "d1": row0["d1"],
            "d2": row0["d2"],
            "num_nodes": row0["num_nodes"],
            "num_edges": row0["num_edges"],
            "num_spaces": row0["num_spaces"],
            "num_pieces": row0["num_pieces"],
        }
        if timing_source == "gpu_source":
            for tile_key in [
                "gpu_tiles", "gpu_oom_backoffs", "gpu_host_fallback",
                "gpu_input_rects", "gpu_scratch_bytes",
            ]:
                values = [row.get(tile_key) for row in rows if row.get(tile_key) != ""]
                summary[tile_key + "_median"] = statistics.median(values) if values else ""
                summary[tile_key + "_min"] = min(values) if values else ""
                summary[tile_key + "_max"] = max(values) if values else ""
        summary_rows.append(summary)
        by_case[(op, dimension, density, buffer_size)][timing_source] = summary["median_us"]

    for row in summary_rows:
        pair = by_case[(row["op"], row["dimension"], row["density"], row["buffer_size"])]
        cpu = pair.get("cpu_source")
        gpu = pair.get("gpu_source")
        row["speedup_cpu_over_gpu"] = (cpu / gpu) if cpu and gpu else ""

    raw_path = out_dir / "tile_sweep_raw.csv"
    points_path = out_dir / "tile_sweep_points.csv"
    summary_path = out_dir / "tile_sweep_summary.csv"
    failures_path = out_dir / "tile_sweep_failures.csv"
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
        "dims": dims,
        "densities": densities,
        "buffers": buffers,
        "num_raw_rows": len(raw_rows),
        "num_point_rows": len(point_rows),
        "num_failures": len(failures),
        "policy": {
            "common_flags": base[1:],
            "cpu_source": "normal run, use cpu_us",
            "gpu_source": "-dp:noisectopt run, use gpu_us",
            "tile_join": "last TILE row before RESULT; tile counters retained on gpu_source rows",
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
