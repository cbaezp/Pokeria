import json
from pathlib import Path

p = Path("data/solutions/5d56f96898377bb6_e6b2984760c31d8c.json")
file_size = p.stat().st_size
print(f"Reading flop pack {p.name}, size: {file_size} bytes")

# Read head chunk (500 KB) to extract config, meta, and root decision nodes
with open(p, "rb") as f:
    head_bytes = f.read(500 * 1024)

# Read tail chunk (100 KB) to extract root_combos
with open(p, "rb") as f:
    f.seek(max(0, file_size - 100 * 1024))
    tail_bytes = f.read()

# Extract root_combos from tail
root_combos_idx = tail_bytes.rfind(b'"root_combos":')
if root_combos_idx != -1:
    tail_str = tail_bytes[root_combos_idx:].decode("utf-8", errors="ignore")
    # Wrap in dict to parse
    combos_json_str = "{" + tail_str.rstrip(" \r\n\t")
    combos_data = json.loads(combos_json_str)
    root_combos = combos_data["root_combos"]
    print(f"Extracted root_combos: OOP={len(root_combos[0])}, IP={len(root_combos[1])}")
    print("Sample OOP combos:", [c["cards"] for c in root_combos[0][:5]])
    print("Sample IP combos:", [c["cards"] for c in root_combos[1][:5]])
else:
    print("root_combos not found in tail")

# Parse Node 0 from head
nodes_start = head_bytes.find(b'"nodes":[')
if nodes_start != -1:
    # Find first node object
    first_node_start = head_bytes.find(b'{"node":0,', nodes_start)
    if first_node_start != -1:
        # Find closing brace of first node
        brace_count = 0
        end_idx = first_node_start
        for i in range(first_node_start, len(head_bytes)):
            if head_bytes[i : i + 1] == b"{":
                brace_count += 1
            elif head_bytes[i : i + 1] == b"}":
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        node0_str = head_bytes[first_node_start:end_idx].decode("utf-8")
        node0 = json.loads(node0_str)
        print("Node 0 extracted successfully:")
        print("  node:", node0["node"])
        print("  player:", node0["player"])
        print("  actions:", node0["actions"])
        print("  combo_count:", node0["combo_count"])
        print("  has action_evs:", "action_evs" in node0 and node0["action_evs"] is not None)
        print("  strategy len:", len(node0["strategy"]))
        if "action_evs" in node0 and node0["action_evs"]:
            print("  action_evs len:", len(node0["action_evs"]))
