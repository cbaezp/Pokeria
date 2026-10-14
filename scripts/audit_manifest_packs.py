import hashlib
import json
from pathlib import Path


def main():
    manifest_path = Path("data/solutions/manifest.json")
    with open(manifest_path) as f:
        packs = json.load(f)

    print(f"Auditing all {len(packs)} packs in data/solutions/manifest.json:\n")
    all_ok = True
    for p in packs:
        pid = p["id"]
        name = p.get("name")
        path_str = p["artifact_path"]
        path = Path(path_str)
        exists = path.exists()
        size = path.stat().st_size if exists else 0

        if exists:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    h.update(chunk)
            calc_sha = h.hexdigest()
        else:
            calc_sha = "MISSING"

        man_sha = p.get("artifact_checksum")
        sha_ok = calc_sha == man_sha
        size_ok = size == p.get("artifact_bytes")
        if not (exists and sha_ok and size_ok):
            all_ok = False

        print(f"Pack ID: {pid}")
        print(f"  Name: {name}")
        print(f"  File: {path_str} (exists: {exists})")
        print(f"  Bytes: manifest={p.get('artifact_bytes')} disk={size} (match: {size_ok})")
        print(f"  SHA-256: {calc_sha} (match: {sha_ok})")
        print(
            f"  Manifest Nodes: {p.get('node_count')} | Exploitability: {p.get('exploitability_pct_of_pot'):.4f}% pot"
        )
        print()

    print(f"OVERALL INVENTORY INTEGRITY: {'100% MATCH' if all_ok else 'FAILED'}")


if __name__ == "__main__":
    main()
