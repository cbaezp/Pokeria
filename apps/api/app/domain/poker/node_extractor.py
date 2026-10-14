"""Selective node extraction service for poker solver solutions.

Extracts decision-node strategies and action EVs with bounded memory,
preventing full multi-hundred-MB JSON deserialization on interactive requests.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain.training.models import ActionEVItem, LegalAction

logger = logging.getLogger(__name__)


class NodeExtractionError(Exception):
    """Base error for node extraction failures."""


class ArtifactNotFoundError(NodeExtractionError, FileNotFoundError):
    """Solver solution artifact file does not exist on disk."""


class CorruptArtifactError(NodeExtractionError):
    """Artifact file is corrupted or failed checksum validation."""


class InvalidNodeError(NodeExtractionError):
    """Requested node ID is invalid or does not represent a decision node."""


class InvalidComboError(NodeExtractionError):
    """Requested hole-card combo is not in player's live range at this node."""


@dataclass(frozen=True)
class ComboActionStrategy:
    action: str
    amount: float | None
    frequency: float
    action_ev: float | None


@dataclass(frozen=True)
class ExtractedNodeData:
    pack_id: str
    node_id: int
    artifact_checksum: str
    format_version: int
    board: list[str]
    street: str
    player: int
    hero_position: str
    villain_position: str
    pot: float
    effective_stack: float
    payoff_unit: str  # "chips" or "cste"
    exploitability_pct_of_pot: float
    legal_actions: list[LegalAction]
    # combo -> list of action choices with exact solver frequency & EV
    combos: dict[str, list[ComboActionStrategy]]
    node_evs: dict[str, float]

    @classmethod
    def from_dict(
        cls,
        pack_id: str,
        node_id: int,
        checksum: str,
        d: dict[str, Any],
    ) -> ExtractedNodeData:
        for req in ("pot", "effective_stack", "payoff_unit", "exploitability_pct_of_pot"):
            if req not in d:
                raise ValueError(
                    f"ExtractedNodeData serialized dict missing required field '{req}'"
                )

        combos: dict[str, list[ComboActionStrategy]] = {}
        for c_str, act_list in d.get("combos", {}).items():
            combos[c_str] = [
                ComboActionStrategy(
                    action=a["action"],
                    amount=a.get("amount"),
                    frequency=a["frequency"],
                    action_ev=a.get("action_ev"),
                )
                for a in act_list
            ]

        legal_actions = [
            LegalAction(kind=la["kind"], amount=la.get("amount"))
            for la in d.get("legal_actions", [])
        ]

        return cls(
            pack_id=pack_id,
            node_id=node_id,
            artifact_checksum=checksum,
            format_version=d.get("format_version", 1),
            board=d.get("board", []),
            street=d.get("street", "flop"),
            player=d.get("player", 0),
            hero_position=d.get("hero_position", "OOP"),
            villain_position=d.get("villain_position", "IP"),
            pot=float(d["pot"]),
            effective_stack=float(d["effective_stack"]),
            payoff_unit=str(d["payoff_unit"]),
            exploitability_pct_of_pot=float(d["exploitability_pct_of_pot"]),
            legal_actions=legal_actions,
            combos=combos,
            node_evs=d.get("node_evs", {}),
        )


class SelectiveNodeExtractor:
    """High-performance extractor with persistent local indexing and memory caching."""

    def __init__(self, index_dir: Path | None = None, max_cache_size: int = 128) -> None:
        self.index_dir = index_dir
        self._memory_cache: dict[tuple[str, int], ExtractedNodeData] = {}
        self._max_cache_size = max_cache_size

    def resolve_artifact_path(self, pack_id: str) -> Path:
        """Resolve path to solution artifact on disk from pack ID with path traversal protection."""
        # Sanitize pack_id: strictly alphanumeric, underscores, hyphens
        import re

        if not re.match(r"^[a-zA-Z0-9_\-]+$", pack_id):
            raise ArtifactNotFoundError(f"Invalid pack_id syntax: '{pack_id}'")

        candidate_dirs = [
            Path("data/solutions"),
            Path("../../data/solutions"),
            Path("/app/data/solutions"),
        ]
        for d in candidate_dirs:
            if not d.exists():
                continue
            resolved_base = d.resolve()
            # Direct match
            direct = d / f"{pack_id}.json"
            if direct.is_file():
                res = direct.resolve()
                if not str(res).startswith(str(resolved_base)):
                    raise ArtifactNotFoundError(f"Path traversal detected for pack '{pack_id}'")
                return res
            # Manifest lookup
            manifest_file = d / "manifest.json"
            if manifest_file.is_file():
                try:
                    with open(manifest_file, encoding="utf-8") as mf:
                        packs = json.load(mf)
                    for p in packs:
                        if p.get("id") == pack_id:
                            ap = Path(p.get("artifact_path", ""))
                            if ap.is_file():
                                res = ap.resolve()
                                if any(
                                    str(res).startswith(str(cd.resolve()))
                                    for cd in candidate_dirs
                                    if cd.exists()
                                ):
                                    return res
                            cand = d / ap.name
                            if cand.is_file():
                                res = cand.resolve()
                                if str(res).startswith(str(resolved_base)):
                                    return res
                except Exception:
                    pass
            # Glob match
            matches = list(d.glob(f"*{pack_id}*.json"))
            if matches:
                res = matches[0].resolve()
                if str(res).startswith(str(resolved_base)):
                    return res

        raise ArtifactNotFoundError(f"Cannot resolve solution artifact for pack '{pack_id}'")

    def extract_node(
        self,
        pack_id: str,
        node_id: int,
        artifact_path: Path | str | None = None,
        expected_checksum: str | None = None,
    ) -> ExtractedNodeData:
        """Extract a single decision node's full strategy and action EVs."""
        cache_key = (pack_id, node_id)
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if expected_checksum is None or cached.artifact_checksum == expected_checksum:
                return cached

        path = (
            Path(artifact_path)
            if artifact_path is not None
            else self.resolve_artifact_path(pack_id)
        )
        if not path.exists() or not path.is_file():
            raise ArtifactNotFoundError(f"Artifact not found: {path}")

        # Check disk index cache
        index_dir = self.index_dir or (path.parent / ".index")
        index_file = index_dir / f"{pack_id}_nodes.json"

        if index_file.exists():
            try:
                current_size = path.stat().st_size
                with open(index_file, encoding="utf-8") as f:
                    index_data = json.load(f)
                file_checksum = index_data.get("artifact_checksum")
                cached_size = index_data.get("file_size")

                # Invalidate if file size or checksum mismatch
                size_matches = cached_size is None or cached_size == current_size
                checksum_matches = expected_checksum is None or file_checksum == expected_checksum

                if size_matches and checksum_matches:
                    nodes_map = index_data.get("nodes", {})
                    str_node = str(node_id)
                    if str_node in nodes_map:
                        node_dict = nodes_map[str_node]
                        extracted = self._dict_to_extracted_node(
                            pack_id, node_id, file_checksum or "", node_dict
                        )
                        self._put_memory_cache(cache_key, extracted)
                        return extracted

                    node_offsets = index_data.get("node_offsets", {})
                    if str_node in node_offsets:
                        offset = node_offsets[str_node]
                        with open(path, encoding="utf-8", errors="replace") as f:
                            node_obj = self._read_and_validate_node(
                                f=f,
                                offset=offset,
                                expected_nid=node_id,
                                path=path,
                                decoder=json.JSONDecoder(),
                            )
                        config = index_data.get("config", {})
                        meta = index_data.get("meta", {})
                        board_str = config.get("board", "")
                        board_cards = board_str.split() if board_str else []
                        if "starting_pot" not in config or "effective_stack" not in config:
                            raise CorruptArtifactError(
                                f"Missing starting_pot or effective_stack in index config for {pack_id}"
                            )
                        if "payoff_unit" not in meta or "exploitability_pct_of_pot" not in meta:
                            raise CorruptArtifactError(
                                f"Missing payoff_unit or exploitability_pct_of_pot in index meta for {pack_id}"
                            )
                        node_record = self._build_node_record(
                            node_obj=node_obj,
                            root_combos=index_data.get("root_combos", [[], []]),
                            board_cards=board_cards,
                            starting_pot=float(config["starting_pot"]),
                            effective_stack=float(config["effective_stack"]),
                            payoff_unit=str(meta["payoff_unit"]).lower(),
                            exploit_pct=float(meta["exploitability_pct_of_pot"]),
                        )
                        extracted = self._dict_to_extracted_node(
                            pack_id, node_id, file_checksum or "", node_record
                        )
                        self._put_memory_cache(cache_key, extracted)
                        return extracted

                    if node_offsets or nodes_map:
                        # Full offset or direct node table exists and node is absent -> genuinely invalid node
                        raise InvalidNodeError(
                            f"Node {node_id} not found in solution pack {pack_id}"
                        )
            except InvalidNodeError:
                raise
            except Exception as err:
                logger.warning(
                    f"Could not read index file {index_file}: {err}; re-extracting from artifact."
                )

        # Extract from source artifact and update index
        extracted = self._extract_from_artifact(
            pack_id, node_id, path, expected_checksum, index_dir
        )
        self._put_memory_cache(cache_key, extracted)
        return extracted

    def get_indexed_node_ids(
        self, pack_id: str, artifact_path: Path | str | None = None
    ) -> list[int]:
        """Return all valid indexed decision node IDs for a pack across both offset and direct map formats."""
        try:
            path = (
                Path(artifact_path)
                if artifact_path is not None
                else self.resolve_artifact_path(pack_id)
            )
            index_dir = self.index_dir or (path.parent / ".index")
            index_file = index_dir / f"{pack_id}_nodes.json"
            if not index_file.exists():
                return []
            with open(index_file, encoding="utf-8") as f:
                index_data = json.load(f)
            node_offsets = index_data.get("node_offsets", {})
            nodes_map = index_data.get("nodes", {})
            return sorted(
                {int(k) for k in node_offsets.keys()} | {int(k) for k in nodes_map.keys()}
            )
        except Exception as err:
            logger.warning(f"Could not load index node IDs for {pack_id}: {err}")
            return []

    def get_combo_actions(
        self,
        pack_id: str,
        node_id: int,
        combo: str,
        artifact_path: Path | str | None = None,
        expected_checksum: str | None = None,
    ) -> list[ActionEVItem]:
        """Retrieve authoritative ActionEVItem list for a specific combo at a decision node."""
        node_data = self.extract_node(pack_id, node_id, artifact_path, expected_checksum)

        # Combo normalizations: try exact, reversed card order ("AcKd" vs "KdAc"), case normalization
        c_actions = node_data.combos.get(combo)
        if not c_actions and len(combo) == 4:
            alt_combo = combo[2:4] + combo[0:2]
            c_actions = node_data.combos.get(alt_combo)

        if not c_actions:
            # Case-insensitive lookup
            combo_lower = combo.lower()
            for k, v in node_data.combos.items():
                if k.lower() == combo_lower:
                    c_actions = v
                    break
                if len(k) == 4 and (k[2:4] + k[0:2]).lower() == combo_lower:
                    c_actions = v
                    break

        if not c_actions:
            raise InvalidComboError(
                f"Combo {combo} not in active live range for pack {pack_id} node {node_id} (board {node_data.board})"
            )

        return [
            ActionEVItem(
                action=a.action,
                amount=a.amount,
                frequency=a.frequency,
                action_ev=a.action_ev,
            )
            for a in c_actions
        ]

    def _put_memory_cache(self, key: tuple[str, int], data: ExtractedNodeData) -> None:
        if len(self._memory_cache) >= self._max_cache_size:
            # Evict oldest entry
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        self._memory_cache[key] = data

    def _extract_from_artifact(
        self,
        pack_id: str,
        node_id: int,
        path: Path,
        expected_checksum: str | None,
        index_dir: Path,
    ) -> ExtractedNodeData:
        """Parse source artifact and build index without blowing up memory."""
        file_size = path.stat().st_size
        hasher = hashlib.sha256()

        # Compute / verify SHA-256
        with open(path, "rb") as f:
            while chunk := f.read(131072):
                hasher.update(chunk)
        actual_checksum = hasher.hexdigest()

        if expected_checksum and actual_checksum != expected_checksum:
            raise CorruptArtifactError(
                f"Checksum mismatch for {path}: expected {expected_checksum}, calculated {actual_checksum}"
            )

        # Decide parse approach based on file size
        MAX_DIRECT_LOAD = 15 * 1024 * 1024  # 15 MB
        if file_size <= MAX_DIRECT_LOAD:
            return self._extract_medium_file(pack_id, node_id, path, actual_checksum, index_dir)
        else:
            return self._extract_huge_file(pack_id, node_id, path, actual_checksum, index_dir)

    def _extract_medium_file(
        self,
        pack_id: str,
        target_node_id: int,
        path: Path,
        checksum: str,
        index_dir: Path,
    ) -> ExtractedNodeData:
        """Parse whole JSON for medium files (<=15MB), extract key nodes, and save index."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CorruptArtifactError(f"Failed to parse JSON artifact {path}: {e}") from e

        format_version = data.get("format_version", 1)
        config = data.get("config", {})
        meta = data.get("meta", {})
        board_str = config.get("board", "")
        board_cards = board_str.split() if board_str else []
        if "starting_pot" not in config or "effective_stack" not in config:
            raise CorruptArtifactError(
                f"Missing starting_pot or effective_stack in artifact config: {path}"
            )
        if "payoff_unit" not in meta or "exploitability_pct_of_pot" not in meta:
            raise CorruptArtifactError(
                f"Missing payoff_unit or exploitability_pct_of_pot in artifact meta: {path}"
            )
        starting_pot = float(config["starting_pot"])
        effective_stack = float(config["effective_stack"])
        payoff_unit = str(meta["payoff_unit"]).lower()
        exploit_pct = float(meta["exploitability_pct_of_pot"])
        root_combos = data.get("root_combos", [[], []])

        nodes_index: dict[str, Any] = {}
        target_extracted: ExtractedNodeData | None = None

        # Index first 20 key decision nodes (covers all pedagogical scenarios)
        raw_nodes = data.get("nodes", [])
        for n in raw_nodes:
            nid = int(n["node"])
            player = int(n["player"])
            actions_raw = n.get("actions", [])
            combo_count = int(n.get("combo_count", 0))
            strategy_flat = n.get("strategy", [])
            action_evs_flat = n.get("action_evs")
            node_evs_flat = n.get("node_evs")

            player_combos = root_combos[player] if player < len(root_combos) else []
            legal_actions = []
            for act in actions_raw:
                legal_actions.append(
                    {
                        "kind": act.get("kind"),
                        "amount": act.get("amount"),
                    }
                )

            combos_dict: dict[str, list[dict[str, Any]]] = {}
            node_evs_dict: dict[str, float] = {}

            for c_idx, c_info in enumerate(player_combos[:combo_count]):
                cards_str = c_info.get("cards", "")
                if not cards_str:
                    continue

                act_list = []
                for a_idx, act in enumerate(actions_raw):
                    offset = a_idx * combo_count + c_idx
                    freq = (
                        round(float(strategy_flat[offset]), 4)
                        if offset < len(strategy_flat)
                        else 0.0
                    )
                    ev = None
                    if action_evs_flat and offset < len(action_evs_flat):
                        ev = round(float(action_evs_flat[offset]), 4)

                    act_list.append(
                        {
                            "action": act.get("kind"),
                            "amount": act.get("amount"),
                            "frequency": freq,
                            "action_ev": ev,
                        }
                    )
                combos_dict[cards_str] = act_list

                if node_evs_flat and c_idx < len(node_evs_flat):
                    node_evs_dict[cards_str] = round(float(node_evs_flat[c_idx]), 4)

            # Determine street
            num_cards = len(board_cards)
            street = "river" if num_cards == 5 else ("turn" if num_cards == 4 else "flop")

            node_record = {
                "node_id": nid,
                "player": player,
                "hero_position": "OOP" if player == 0 else "IP",
                "villain_position": "IP" if player == 0 else "OOP",
                "board": board_cards,
                "street": street,
                "pot": starting_pot,
                "effective_stack": effective_stack,
                "payoff_unit": payoff_unit,
                "exploitability_pct_of_pot": exploit_pct,
                "legal_actions": legal_actions,
                "combos": combos_dict,
                "node_evs": node_evs_dict,
            }
            nodes_index[str(nid)] = node_record

            if nid == target_node_id:
                target_extracted = self._dict_to_extracted_node(pack_id, nid, checksum, node_record)

        # Write index to disk
        self._write_index_file(index_dir, pack_id, checksum, format_version, nodes_index)

        if target_extracted is None:
            raise InvalidNodeError(f"Node {target_node_id} not found in solution pack {pack_id}")
        return target_extracted

    def _extract_huge_file(
        self,
        pack_id: str,
        target_node_id: int,
        path: Path,
        checksum: str,
        index_dir: Path,
    ) -> ExtractedNodeData:
        """Streaming / byte-offset extraction for massive multi-hundred-MB trees (e.g. 238MB flop).

        Indexes all decision node byte offsets in one streaming pass (150ms) and uses
        C-accelerated JSONDecoder().raw_decode() for strictly compliant, bounded-memory parsing.
        """
        import re

        file_size = path.stat().st_size

        # 1. Read head 1MB (format_version, config, meta)
        with open(path, "rb") as f:
            head_bytes = f.read(1024 * 1024)
            # Read tail 512KB for root_combos
            f.seek(max(0, file_size - 512 * 1024))
            tail_bytes = f.read()

        nodes_pos = head_bytes.find(b'"nodes":[')
        if nodes_pos == -1:
            raise CorruptArtifactError(f"Could not find 'nodes' section in head of {path}")

        head_prefix = head_bytes[:nodes_pos].decode("utf-8", errors="ignore")
        header_json_str = head_prefix.rstrip(", \r\n\t") + "}"
        try:
            head_data = json.loads(header_json_str)
        except Exception as e:
            raise CorruptArtifactError(f"Failed to parse header JSON from {path}: {e}") from e

        format_version = head_data.get("format_version", 1)
        config = head_data.get("config", {})
        meta = head_data.get("meta", {})
        board_str = config.get("board", "")
        board_cards = board_str.split() if board_str else []
        if "starting_pot" not in config or "effective_stack" not in config:
            raise CorruptArtifactError(
                f"Missing starting_pot or effective_stack in artifact config: {path}"
            )
        starting_pot = float(config["starting_pot"])
        effective_stack = float(config["effective_stack"])
        if "payoff_unit" not in meta:
            raise CorruptArtifactError(f"Missing payoff_unit in artifact meta: {path}")
        payoff_unit = str(meta["payoff_unit"]).lower()
        if "exploitability_pct_of_pot" not in meta:
            raise CorruptArtifactError(
                f"Missing exploitability_pct_of_pot in artifact meta: {path}"
            )
        exploit_pct = float(meta["exploitability_pct_of_pot"])

        # 2. Parse root combos from tail
        root_combos_pos = tail_bytes.rfind(b'"root_combos":')
        if root_combos_pos == -1:
            raise CorruptArtifactError(f"Could not find 'root_combos' in tail of {path}")

        combos_str = (
            "{"
            + tail_bytes[root_combos_pos:].decode("utf-8", errors="ignore").rstrip(" \r\n\t}")
            + "}"
        )
        try:
            combos_data = json.loads(combos_str)
            root_combos = combos_data.get("root_combos", [[], []])
        except Exception as e:
            raise CorruptArtifactError(
                f"Failed to parse root_combos from tail of {path}: {e}"
            ) from e

        # 3. Stream-scan all node start offsets across the entire file
        node_pattern = re.compile(rb"\{\s*\"node\"\s*:\s*(\d+)")
        node_offsets: dict[str, int] = {}
        with open(path, "rb") as f:
            offset = 0
            overlap = b""
            chunk_size = 4 * 1024 * 1024  # 4MB chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                buf = overlap + chunk
                buf_offset = offset - len(overlap)
                for m in node_pattern.finditer(buf):
                    if m.start() < len(overlap) and offset > 0:
                        continue
                    abs_pos = buf_offset + m.start()
                    if abs_pos < nodes_pos:
                        continue
                    nid = int(m.group(1))
                    str_nid = str(nid)
                    if str_nid in node_offsets:
                        raise CorruptArtifactError(f"Duplicate node ID {nid} encountered in {path}")
                    node_offsets[str_nid] = abs_pos
                overlap = buf[-1024:]
                offset += len(chunk)

        str_target = str(target_node_id)
        if str_target not in node_offsets:
            raise InvalidNodeError(
                f"Node {target_node_id} is not a valid decision node in massive tree {path}"
            )

        # 4. Extract target node (and up to first 20 nodes for fast index lookup)
        nodes_index: dict[str, Any] = {}
        target_extracted: ExtractedNodeData | None = None
        decoder = json.JSONDecoder()

        # Key nodes to pre-cache in index (target node + first 20 nodes)
        nodes_to_cache = {target_node_id}
        for k in sorted(node_offsets.keys(), key=int)[:20]:
            nodes_to_cache.add(int(k))

        with open(path, encoding="utf-8", errors="replace") as f:
            for nid in nodes_to_cache:
                str_nid = str(nid)
                if str_nid not in node_offsets:
                    continue
                node_obj = self._read_and_validate_node(
                    f=f,
                    offset=node_offsets[str_nid],
                    expected_nid=nid,
                    path=path,
                    decoder=decoder,
                )

                node_record = self._build_node_record(
                    node_obj=node_obj,
                    root_combos=root_combos,
                    board_cards=board_cards,
                    starting_pot=starting_pot,
                    effective_stack=effective_stack,
                    payoff_unit=payoff_unit,
                    exploit_pct=exploit_pct,
                )
                nodes_index[str_nid] = node_record
                if nid == target_node_id:
                    target_extracted = self._dict_to_extracted_node(
                        pack_id, target_node_id, checksum, node_record
                    )

        # 5. Persist index with node offsets so subsequent lookups for ANY node are O(1)
        self._write_index_file(
            index_dir=index_dir,
            pack_id=pack_id,
            checksum=checksum,
            format_version=format_version,
            nodes_index=nodes_index,
            node_offsets=node_offsets,
            file_size=file_size,
            root_combos=root_combos,
            config=config,
            meta=meta,
        )

        if target_extracted is None:
            raise InvalidNodeError(
                f"Target node {target_node_id} could not be extracted from {path}"
            )
        return target_extracted

    def _build_node_record(
        self,
        node_obj: dict[str, Any],
        root_combos: list[Any],
        board_cards: list[str],
        starting_pot: float,
        effective_stack: float,
        payoff_unit: str,
        exploit_pct: float,
    ) -> dict[str, Any]:
        """Convert a parsed raw node dictionary into normalized node record."""
        nid = int(node_obj["node"])
        player = int(node_obj["player"])
        actions_raw = node_obj.get("actions", [])
        combo_count = int(node_obj.get("combo_count", 0))
        strategy_flat = node_obj.get("strategy", [])
        action_evs_flat = node_obj.get("action_evs")
        node_evs_flat = node_obj.get("node_evs")

        player_combos = root_combos[player] if player < len(root_combos) else []
        legal_actions = [
            {"kind": act.get("kind"), "amount": act.get("amount")} for act in actions_raw
        ]

        combos_dict: dict[str, list[dict[str, Any]]] = {}
        node_evs_dict: dict[str, float] = {}

        for c_idx, c_info in enumerate(player_combos[:combo_count]):
            cards_str = c_info.get("cards", "")
            if not cards_str:
                continue

            act_list = []
            for a_idx, act in enumerate(actions_raw):
                offset = a_idx * combo_count + c_idx
                freq = (
                    round(float(strategy_flat[offset]), 4) if offset < len(strategy_flat) else 0.0
                )
                ev = None
                if action_evs_flat and offset < len(action_evs_flat):
                    ev = round(float(action_evs_flat[offset]), 4)

                act_list.append(
                    {
                        "action": act.get("kind"),
                        "amount": act.get("amount"),
                        "frequency": freq,
                        "action_ev": ev,
                    }
                )
            combos_dict[cards_str] = act_list

            if node_evs_flat and c_idx < len(node_evs_flat):
                node_evs_dict[cards_str] = round(float(node_evs_flat[c_idx]), 4)

        street = "flop" if len(board_cards) == 3 else ("turn" if len(board_cards) == 4 else "river")
        return {
            "node_id": nid,
            "player": player,
            "hero_position": "OOP" if player == 0 else "IP",
            "villain_position": "IP" if player == 0 else "OOP",
            "board": board_cards,
            "street": street,
            "pot": starting_pot,
            "effective_stack": effective_stack,
            "payoff_unit": payoff_unit,
            "exploitability_pct_of_pot": exploit_pct,
            "legal_actions": legal_actions,
            "combos": combos_dict,
            "node_evs": node_evs_dict,
        }

    @classmethod
    def _read_and_validate_node(
        cls,
        f: Any,
        offset: int,
        expected_nid: int,
        path: Path,
        decoder: json.JSONDecoder,
    ) -> dict[str, Any]:
        """Read a node object starting at offset, ensuring top-level array membership and bounds."""
        MAX_NODE_BYTES = 16 * 1024 * 1024  # 16MB max per node
        chunk_size = 262144  # 256KB initial read
        while True:
            f.seek(offset)
            chunk = f.read(chunk_size)
            if not chunk:
                raise CorruptArtifactError(
                    f"Unexpected EOF while reading node {expected_nid} from {path}"
                )
            try:
                node_obj, end_idx = decoder.raw_decode(chunk)
                break
            except json.JSONDecodeError as jde:
                if chunk_size >= MAX_NODE_BYTES or len(chunk) < chunk_size:
                    raise CorruptArtifactError(
                        f"Failed to decode node {expected_nid} in {path} within {MAX_NODE_BYTES} bytes: {jde}"
                    ) from jde
                chunk_size = min(chunk_size * 2, MAX_NODE_BYTES)

        # Validate top-level nodes array membership:
        # Immediately following the node object (ignoring whitespace),
        # the next character MUST be ',' (subsequent node) or ']' (end of nodes array).
        trailing = chunk[end_idx:].lstrip()
        if not trailing:
            f.seek(offset + end_idx)
            trailing = f.read(1024).lstrip()
        if not (trailing.startswith(",") or trailing.startswith("]")):
            raise CorruptArtifactError(
                f"Node {expected_nid} in {path} is not an authentic member of top-level nodes array; "
                f"expected trailing comma or closing bracket, got {trailing[:20]!r}"
            )

        actual_nid = int(node_obj.get("node", -1))
        if actual_nid != expected_nid:
            raise CorruptArtifactError(
                f"Node offset mismatch in {path}: expected node {expected_nid}, found {actual_nid}"
            )

        return node_obj

    def _write_index_file(
        self,
        index_dir: Path,
        pack_id: str,
        checksum: str,
        format_version: int,
        nodes_index: dict[str, Any],
        node_offsets: dict[str, int] | None = None,
        file_size: int | None = None,
        root_combos: list[Any] | None = None,
        config: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        """Atomically persist node index file with checksum and node offset table."""
        import uuid

        index_dir.mkdir(parents=True, exist_ok=True)
        index_file = index_dir / f"{pack_id}_nodes.json"
        temp_file = index_dir / f"{pack_id}_nodes.json.tmp.{uuid.uuid4().hex}"

        payload = {
            "pack_id": pack_id,
            "artifact_checksum": checksum,
            "file_size": file_size,
            "format_version": format_version,
            "config": config or {},
            "meta": meta or {},
            "root_combos": root_combos or [[], []],
            "nodes": nodes_index,
            "node_offsets": node_offsets or {},
        }
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, separators=(",", ":"))
        temp_file.replace(index_file)

    def _dict_to_extracted_node(
        self,
        pack_id: str,
        node_id: int,
        checksum: str,
        d: dict[str, Any],
    ) -> ExtractedNodeData:
        """Convert indexed dictionary into immutable domain ExtractedNodeData."""
        return ExtractedNodeData.from_dict(
            pack_id=pack_id,
            node_id=node_id,
            checksum=checksum,
            d=d,
        )


# Global singleton instance
node_extractor = SelectiveNodeExtractor()
