import json
import subprocess
import time
from pathlib import Path

SOLVER_BIN = Path("/Users/cbz/Desktop/Pokeria/apps/solver/target/release/solver")
BENCH_DIR = Path("/Users/cbz/Desktop/Pokeria/data/benchmarks")
OUT_DIR = BENCH_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

benchmarks = [
    ("Simple River (1-size)", BENCH_DIR / "bench_simple_river.toml"),
    ("Multi-node River (multi-size)", BENCH_DIR / "bench_multinode_river.toml"),
    ("Variable Stack 20bb", BENCH_DIR / "bench_variable_stack_20.toml"),
    ("Variable Stack 200bb", BENCH_DIR / "bench_variable_stack_200.toml"),
    ("Rake Configuration (5% cap 3)", BENCH_DIR / "bench_rake.toml"),
    ("Tournament ICM (6-seat 3-paid)", BENCH_DIR / "bench_tournament.toml"),
    ("Turn (48 river chance transitions)", BENCH_DIR / "bench_turn.toml"),
    ("Flop (49 turn * 48 river transitions)", BENCH_DIR / "bench_flop.toml"),
]

results = []

for name, cfg_path in benchmarks:
    print(f"=== Running {name} ===")
    out_file = OUT_DIR / f"{cfg_path.stem}.sol"
    cmd = [
        "/usr/bin/time",
        "-l",
        str(SOLVER_BIN),
        "solve",
        "--config",
        str(cfg_path),
        "--out",
        str(out_file),
    ]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    t1 = time.perf_counter()
    wall_clock = t1 - t0

    stdout = proc.stdout
    stderr = proc.stderr

    # Parse peak memory from /usr/bin/time -l (maximum resident set size)
    peak_rss_bytes = 0
    for line in stderr.splitlines():
        if "maximum resident set size" in line:
            parts = line.strip().split()
            if parts:
                peak_rss_bytes = int(parts[0])
                break

    artifact_size = out_file.stat().st_size if out_file.exists() else 0

    # Extract tree and final report
    res_entry = {
        "benchmark": name,
        "config": cfg_path.name,
        "exit_code": proc.returncode,
        "wall_clock_python_s": round(wall_clock, 4),
        "peak_rss_bytes": peak_rss_bytes,
        "peak_rss_mb": round(peak_rss_bytes / (1024 * 1024), 2),
        "artifact_bytes": artifact_size,
        "stdout": stdout,
        "stderr_time": stderr,
    }
    results.append(res_entry)
    print(
        f"Done in {wall_clock:.4f}s | Peak RSS: {res_entry['peak_rss_mb']} MB | Artifact: {artifact_size} bytes"
    )
    print(stdout.strip())
    print("-" * 50)

with open(BENCH_DIR / "results.json", "w") as f:
    json.dump(results, f, indent=2)

print("All benchmarks finished successfully.")
