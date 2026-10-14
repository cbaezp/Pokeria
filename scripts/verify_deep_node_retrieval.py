import sys
import time
from pathlib import Path

# Add apps/api to sys.path
sys.path.insert(0, str(Path("apps/api").resolve()))

from app.domain.poker.node_extractor import SelectiveNodeExtractor


def test_pack_retrieval(pack_id: str, artifact_path: str):
    p = Path(artifact_path).resolve()
    assert p.exists(), f"Artifact not found: {p}"

    ext = SelectiveNodeExtractor()
    idx_file = p.parent / ".index" / f"{pack_id}_nodes.json"
    assert idx_file.exists(), f"Index file not found: {idx_file}"

    all_nids = ext.get_indexed_node_ids(pack_id, p)
    total_nodes = len(all_nids)
    print(f"Pack {pack_id} ({p.name}, {p.stat().st_size / (1024 * 1024):.2f} MB):")
    print(f"  Total indexed decision nodes: {total_nodes}")

    # Pick root (0), quarter (25%), middle (50%), three-quarter (75%), and deep leaf (-1)
    sample_indices = [
        ("Root", 0),
        ("Quarter", len(all_nids) // 4),
        ("Middle", len(all_nids) // 2),
        ("Three-Quarter", (3 * len(all_nids)) // 4),
        ("Deepest", len(all_nids) - 1),
    ]

    for label, idx_pos in sample_indices:
        nid = all_nids[idx_pos]
        t0 = time.time()
        node = ext.extract_node(pack_id, nid, p)
        elapsed_ms = (time.time() - t0) * 1000
        legal_kinds = [a.kind for a in node.legal_actions]
        num_combos = len(node.combos)
        print(
            f"  {label:<13} Node {nid:<7} ({node.street}, player {node.player}): {elapsed_ms:6.2f}ms | Combos: {num_combos:<3} | Actions: {legal_kinds}"
        )
    print()


def main():
    print("=== TESTING ROOT, MIDDLE, AND DEEP DECISION RETRIEVAL ===\n")
    targets = [
        ("5d56f96898377bb6", "data/solutions/5d56f96898377bb6_e6b2984760c31d8c.json"),
        ("64bf1668d802a75d", "data/solutions/64bf1668d802a75d_cac95130a5a522a1.json"),
        ("330d29b8bd559335", "data/solutions/330d29b8bd559335_90c36fe585fe473f.json"),
        (
            "cert_cash_flop_cbet_ae73a18d60ad9965",
            "data/solutions/cert_cash_flop_cbet_ae73a18d60ad9965.json",
        ),
        (
            "cert_cash_turn_barrel_dd24266c0d7fdbc0",
            "data/solutions/cert_cash_turn_barrel_dd24266c0d7fdbc0.json",
        ),
    ]

    for pid, apath in targets:
        test_pack_retrieval(pid, apath)

    print("=== ALL LARGE FLOP & TURN SOLUTIONS RETRIEVE DEEP NODES CLEANLY ===")


if __name__ == "__main__":
    main()
