import hashlib
import json
from pathlib import Path

packs = [
    ("Turn Single-Raised", Path("data/solutions/64bf1668d802a75d_cac95130a5a522a1.json")),
    ("Turn Wet Draw-Heavy", Path("data/solutions/330d29b8bd559335_90c36fe585fe473f.json")),
]

for name, p in packs:
    print(f"=== {name} ({p.name}) ===")
    content = p.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    print(f"File size: {len(content)} bytes | SHA256: {sha256}")
    data = json.loads(content)
    print("Format version:", data.get("format_version"))
    print("Meta:", data.get("meta"))
    print("Board:", data.get("config", {}).get("board"))
    print("Effective stack:", data.get("config", {}).get("effective_stack"))
    print("Starting pot:", data.get("config", {}).get("starting_pot"))
    nodes = data.get("nodes", [])
    print("Total decision nodes:", len(nodes))
    for i in range(min(5, len(nodes))):
        n = nodes[i]
        has_evs = n.get("action_evs") is not None
        print(
            f"  Node {n.get('node')}: player {n.get('player')} combos {n.get('combo_count')} actions {n.get('actions')} has_evs={has_evs}"
        )
    root_combos = data.get("root_combos", [[], []])
    print(f"Root combos count: OOP={len(root_combos[0])}, IP={len(root_combos[1])}")
    print("Sample OOP combos:", [c["cards"] for c in root_combos[0][:5]])
    print("Sample IP combos:", [c["cards"] for c in root_combos[1][:5]])
    print("-" * 50)
