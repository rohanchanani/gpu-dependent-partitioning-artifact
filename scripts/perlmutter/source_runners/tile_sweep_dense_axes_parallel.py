#!/usr/bin/env python3
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from tile_sweep_dense_axes import (
    LINEAR_BUFFERS,
    LOG_BUFFERS,
    RESULT_RE,
    TILE_RE,
    numeric,
    parse_kv,
    summarize,
    write_csv,
)


def run_one(cmd, timeout, gpu_id):
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    start = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        timeout=timeout,
        env=env,
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


def main():
    repo = Path.cwd()
    out_dir = Path(os.environ.get(
        "REALM_TILE_SWEEP_OUT",
        repo / ".local" / ("tile_sweep_dense_axes_parallel_" + time.strftime("%Y%m%d_%H%M%S")),
    ))
    repeats = int(os.environ.get("REALM_TILE_SWEEP_REPEATS", "5"))
    timeout = int(os.environ.get("REALM_TILE_SWEEP_TIMEOUT", "900"))
    workers = int(os.environ.get("REALM_TILE_SWEEP_WORKERS", "4"))
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
    buffers = sorted(set(LOG_BUFFERS) | set(LINEAR_BUFFERS))
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
    lock = threading.Lock()
    tasks = queue.Queue()

    raw_path = out_dir / "tile_sweep_dense_axes_raw.csv"
    points_path = out_dir / "tile_sweep_dense_axes_points.csv"
    all_summary_path = out_dir / "tile_sweep_dense_axes_summary_all_buffers.csv"
    log_summary_path = out_dir / "tile_sweep_dense_axes_summary_log_axis.csv"
    linear_summary_path = out_dir / "tile_sweep_dense_axes_summary_linear_axis.csv"
    failures_path = out_dir / "tile_sweep_dense_axes_failures.csv"
    manifest_path = out_dir / "manifest.json"

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
                            tasks.put({
                                "repeat": repeat,
                                "op": op,
                                "dimension": dim_name,
                                "density": density,
                                "sparse_factor": sparse_factor,
                                "buffer_size": buffer_size,
                                "timing_source": timing_source,
                                "selected_field": selected_field,
                                "cmd": base + extra + op_args,
                            })

    total_tasks = tasks.qsize()
    completed = 0

    def checkpoint():
        write_csv(raw_path, raw_rows)
        write_csv(points_path, point_rows)
        write_csv(failures_path, failures)

    def worker(gpu_id):
        nonlocal completed
        while True:
            try:
                task = tasks.get_nowait()
            except queue.Empty:
                return

            print(
                "RUN worker=%d repeat=%d op=%s dim=%s density=%s b=%s source=%s"
                % (
                    gpu_id,
                    task["repeat"],
                    task["op"],
                    task["dimension"],
                    task["density"],
                    task["buffer_size"],
                    task["timing_source"],
                ),
                flush=True,
            )
            try:
                rc, elapsed, output, parsed, tile, all_tiles = run_one(
                    task["cmd"], timeout, gpu_id
                )
            except subprocess.TimeoutExpired as exc:
                with lock:
                    failures.append({
                        "experiment": "tile_sweep_dense_axes",
                        "op": task["op"],
                        "dimension": task["dimension"],
                        "density": task["density"],
                        "sparse_factor": task["sparse_factor"],
                        "buffer_size": task["buffer_size"],
                        "repeat": task["repeat"],
                        "timing_source": task["timing_source"],
                        "worker": gpu_id,
                        "rc": "timeout",
                        "elapsed_s": timeout,
                        "cmd": " ".join(task["cmd"]),
                        "output_tail": (exc.stdout or "")[-4000:],
                    })
                    completed += 1
                    if completed % 25 == 0:
                        checkpoint()
                tasks.task_done()
                continue

            raw = {
                "experiment": "tile_sweep_dense_axes",
                "op": task["op"],
                "dimension": task["dimension"],
                "density": task["density"],
                "sparse_factor": task["sparse_factor"],
                "buffer_size": task["buffer_size"],
                "repeat": task["repeat"],
                "timing_source": task["timing_source"],
                "selected_field": task["selected_field"],
                "worker": gpu_id,
                "rc": rc,
                "elapsed_s": "%.6f" % elapsed,
                "cmd": " ".join(task["cmd"]),
                "result_json": json.dumps(parsed or {}, sort_keys=True),
                "tile_json": json.dumps(tile or {}, sort_keys=True),
                "tile_rows_seen": len(all_tiles),
            }
            if parsed:
                raw.update(parsed)
            if tile:
                raw.update(tile)

            point = None
            if rc == 0 and parsed and task["selected_field"] in parsed:
                point = {
                    "experiment": "tile_sweep_dense_axes",
                    "op": task["op"],
                    "dimension": task["dimension"],
                    "density": task["density"],
                    "sparse_factor": numeric(task["sparse_factor"]),
                    "buffer_size": numeric(task["buffer_size"]),
                    "repeat": task["repeat"],
                    "timing_source": task["timing_source"],
                    "selected_field": task["selected_field"],
                    "time_us": int(parsed[task["selected_field"]]),
                    "time_ms": int(parsed[task["selected_field"]]) / 1000.0,
                    "d1": numeric(parsed.get("d1")),
                    "d2": numeric(parsed.get("d2")),
                    "num_nodes": numeric(parsed.get("num_nodes")),
                    "num_edges": numeric(parsed.get("num_edges")),
                    "num_spaces": numeric(parsed.get("num_spaces")),
                    "num_pieces": numeric(parsed.get("num_pieces")),
                    "worker": gpu_id,
                }
                if task["timing_source"] == "gpu_source" and tile:
                    for key in [
                        "gpu_tiles", "gpu_oom_backoffs",
                        "gpu_host_fallback", "gpu_input_rects",
                        "gpu_scratch_bytes",
                    ]:
                        point[key] = numeric(tile.get(key))
                    point["tile_rows_seen"] = len(all_tiles)
            else:
                failures.append({
                    "experiment": "tile_sweep_dense_axes",
                    "op": task["op"],
                    "dimension": task["dimension"],
                    "density": task["density"],
                    "sparse_factor": task["sparse_factor"],
                    "buffer_size": task["buffer_size"],
                    "repeat": task["repeat"],
                    "timing_source": task["timing_source"],
                    "worker": gpu_id,
                    "rc": rc,
                    "elapsed_s": "%.6f" % elapsed,
                    "cmd": " ".join(task["cmd"]),
                    "output_tail": output[-4000:],
                })

            with lock:
                raw_rows.append(raw)
                if point:
                    point_rows.append(point)
                completed += 1
                print(
                    "DONE worker=%d completed=%d/%d rc=%s"
                    % (gpu_id, completed, total_tasks, rc),
                    flush=True,
                )
                if completed % 25 == 0:
                    checkpoint()
            tasks.task_done()

    threads = []
    for gpu_id in range(workers):
        thread = threading.Thread(target=worker, args=(gpu_id,), daemon=True)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

    all_summary = summarize(point_rows, "all_buffers")
    log_summary = summarize(point_rows, "log_axis", set(LOG_BUFFERS))
    linear_summary = summarize(point_rows, "linear_axis", set(LINEAR_BUFFERS))

    checkpoint()
    write_csv(all_summary_path, all_summary)
    write_csv(log_summary_path, log_summary)
    write_csv(linear_summary_path, linear_summary)

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "repo": str(repo),
        "binary": str(binary),
        "repeats": repeats,
        "workers": workers,
        "timeout_s": timeout,
        "ops": ops,
        "dims": dims,
        "densities": densities,
        "buffers_all": buffers,
        "buffers_log_axis": LOG_BUFFERS,
        "buffers_linear_axis": LINEAR_BUFFERS,
        "num_raw_rows": len(raw_rows),
        "num_point_rows": len(point_rows),
        "num_summary_all_rows": len(all_summary),
        "num_summary_log_rows": len(log_summary),
        "num_summary_linear_rows": len(linear_summary),
        "num_failures": len(failures),
        "policy": {
            "parallelism": "one benchmark worker per GPU using CUDA_VISIBLE_DEVICES",
            "common_flags": base[1:],
            "cpu_source": "normal run, use cpu_us",
            "gpu_source": "-dp:noisectopt run, use gpu_us",
            "tile_join": "last TILE row before RESULT; tile counters retained on gpu_source rows",
            "collection": "run the union of log-axis and linear-axis buffer values once",
        },
        "outputs": {
            "raw": str(raw_path),
            "points": str(points_path),
            "summary_all": str(all_summary_path),
            "summary_log_axis": str(log_summary_path),
            "summary_linear_axis": str(linear_summary_path),
            "failures": str(failures_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
