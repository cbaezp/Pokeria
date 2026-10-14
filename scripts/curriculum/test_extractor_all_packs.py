import json
import time
from pathlib import Path

from app.domain.poker.node_extractor import (
    ArtifactNotFoundError,
    CorruptArtifactError,
    InvalidComboError,
    InvalidNodeError,
    SelectiveNodeExtractor,
)

extractor = SelectiveNodeExtractor()
manifest_path = Path("data/solutions/manifest.json")
with open(manifest_path) as f:
    packs = json.load(f)

print(f"Testing extraction across {len(packs)} packs...")

benchmarks = []

for pack in packs:
    pid = pack["id"]
    pname = pack["name"]
    art_path = Path("data/solutions") / Path(pack["artifact_path"]).name
    checksum = pack["artifact_checksum"]

    # Cold extraction
    t0 = time.perf_counter()
    extracted = extractor.extract_node(pid, 0, art_path, expected_checksum=checksum)
    t1 = time.perf_counter()
    cold_ms = (t1 - t0) * 1000

    # Warm extraction
    t2 = time.perf_counter()
    warm_extracted = extractor.extract_node(pid, 0, art_path, expected_checksum=checksum)
    t3 = time.perf_counter()
    warm_ms = (t3 - t2) * 1000

    # Get combo actions
    first_combo = next(iter(extracted.combos.keys()))
    combo_actions = extractor.get_combo_actions(
        pid, 0, first_combo, art_path, expected_checksum=checksum
    )

    has_evs = any(a.action_ev is not None for a in combo_actions)

    benchmarks.append(
        {
            "pack_id": pid,
            "name": pname,
            "street": extracted.street,
            "board": extracted.board,
            "combos_count": len(extracted.combos),
            "legal_actions": [la.kind for la in extracted.legal_actions],
            "cold_ms": round(cold_ms, 2),
            "warm_ms": round(warm_ms, 4),
            "sample_combo": first_combo,
            "sample_strategy": [(a.action, a.frequency, a.action_ev) for a in combo_actions],
            "has_evs": has_evs,
        }
    )
    print(
        f"Pack {pid} ({extracted.street}): Cold {cold_ms:.2f}ms | Warm {warm_ms:.4f}ms | Combos: {len(extracted.combos)} | Has EVs: {has_evs}"
    )

# Adversarial error tests
print("\n--- Testing Adversarial Rejections ---")

# 1. Checksum mismatch
try:
    extractor.extract_node(
        "test",
        0,
        "data/solutions/632c34943e011ef5_eeb2c59a3c21cd7c.json",
        expected_checksum="badchecksum",
    )
    print("FAIL: Checksum mismatch was not rejected!")
except CorruptArtifactError:
    print("PASS: Checksum mismatch successfully rejected.")

# 2. Invalid node
try:
    extractor.extract_node(
        "632c34943e011ef5", 99999, "data/solutions/632c34943e011ef5_eeb2c59a3c21cd7c.json"
    )
    print("FAIL: Invalid node 99999 was not rejected!")
except InvalidNodeError:
    print("PASS: Invalid node ID successfully rejected.")

# 3. Nonexistent artifact
try:
    extractor.extract_node("fake", 0, "data/solutions/does_not_exist.json")
    print("FAIL: Missing artifact was not rejected!")
except ArtifactNotFoundError:
    print("PASS: Missing artifact successfully rejected.")

# 4. Invalid combo
art_path = "data/solutions/632c34943e011ef5_eeb2c59a3c21cd7c.json"
try:
    extractor.get_combo_actions("632c34943e011ef5", 0, "2s2c", art_path)  # 2c is on the board!
    print("FAIL: Dead/impossible combo was not rejected!")
except InvalidComboError:
    print("PASS: Dead/impossible combo successfully rejected.")

print("\nSummary Results:")
for b in benchmarks:
    print(
        f"  [{b['street'].upper():<5}] {b['pack_id']} {b['name']}: {b['combos_count']} combos, actions: {b['legal_actions']}, sample: {b['sample_combo']} -> {b['sample_strategy']}"
    )
