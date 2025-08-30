"""In-memory simulation state and edit application logic."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Pixel:
    """Single cell in the simulation grid."""

    material: str
    depth: float = 0.0


@dataclass
class SimState:
    """Simulation state consisting of nodes, pipes and a grid."""

    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pipes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    grid: List[List[Pixel]] = field(default_factory=list)

    def snapshot(self) -> Dict[str, Any]:
        """Return a snapshot of current nodes, pipes and grid."""
        return {
            "nodes": list(self.nodes.values()),
            "pipes": list(self.pipes.values()),
            "grid": [
                [{"material": cell.material, "depth": cell.depth} for cell in row]
                for row in self.grid
            ],
        }

    def apply_edits(self, edits: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """Apply a batch of edits atomically.

        Returns an error dict on failure, or ``None`` on success. The
        validation covers basic structural checks, including ensuring that
        pipes reference existing nodes.
        """
        new_nodes = {k: v.copy() for k, v in self.nodes.items()}
        new_pipes = {k: v.copy() for k, v in self.pipes.items()}

        for edit in edits:
            op = edit.get("op")
            if op == "add_node":
                node_id = edit.get("id")
                if not isinstance(node_id, str):
                    return {"code": "bad_request"}
                if node_id in new_nodes or node_id in new_pipes:
                    return {"code": "id_conflict"}
                new_nodes[node_id] = {
                    "id": node_id,
                    "type": edit.get("type", "junction"),
                    "params": dict(edit.get("params", {})),
                    "state": {"p": 0},
                }
            elif op == "add_pipe":
                pipe_id = edit.get("id")
                a = edit.get("a")
                b = edit.get("b")
                if (
                    not isinstance(pipe_id, str)
                    or not isinstance(a, str)
                    or not isinstance(b, str)
                ):
                    return {"code": "bad_request"}
                if pipe_id in new_pipes or pipe_id in new_nodes:
                    return {"code": "id_conflict"}
                if a not in new_nodes or b not in new_nodes:
                    return {"code": "unknown_entity"}
                new_pipes[pipe_id] = {
                    "id": pipe_id,
                    "a": a,
                    "b": b,
                    "params": dict(edit.get("params", {})),
                    "state": {"q": 0, "dir": 0},
                }
            elif op == "set_param":
                ent_id = edit.get("id")
                key = edit.get("key")
                if not isinstance(ent_id, str) or not isinstance(key, str):
                    return {"code": "bad_request"}
                value = edit.get("value")
                if ent_id in new_nodes:
                    new_nodes[ent_id]["params"][key] = value
                elif ent_id in new_pipes:
                    new_pipes[ent_id]["params"][key] = value
                else:
                    return {"code": "unknown_entity"}
            elif op == "del":
                ent_id = edit.get("id")
                if not isinstance(ent_id, str):
                    return {"code": "bad_request"}
                if ent_id in new_nodes:
                    new_nodes.pop(ent_id, None)
                elif ent_id in new_pipes:
                    new_pipes.pop(ent_id, None)
                else:
                    return {"code": "unknown_entity"}
            else:
                return {"code": "bad_request"}

        self.nodes = new_nodes
        self.pipes = new_pipes
        return None
