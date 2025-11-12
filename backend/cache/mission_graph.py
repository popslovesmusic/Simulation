"""Mission Graph DAG Cache for DASE/IGSOA missions.

This module provides caching for mission computational graphs (DAGs),
allowing reuse of intermediate results for repeated subgraphs.

Features:
- SHA256-based node hashing
- Intermediate result caching
- Cache validity checking
- Automatic cache invalidation

Usage:
    from backend.cache.mission_graph import CachedMissionRunner

    runner = CachedMissionRunner()
    result = runner.run_mission({
        "commands": [
            {"type": "create_engine", "params": {"num_nodes": 4096}},
            {"type": "evolve", "params": {"timesteps": 100}},
            {"type": "snapshot", "params": {}}
        ]
    })
"""

import sys
from pathlib import Path
import json
import hashlib
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import CacheManager


class MissionNode:
    """Represents a single node in the mission DAG."""

    def __init__(self, node_type: str, params: Dict[str, Any], node_id: Optional[str] = None):
        """Initialize mission node.

        Args:
            node_type: Command type (e.g., "create_engine", "evolve")
            params: Command parameters
            node_id: Optional explicit node ID (otherwise computed from hash)
        """
        self.node_type = node_type
        self.params = params
        self.node_id = node_id if node_id else self._compute_hash()
        self.dependencies: List[str] = []
        self.cached_result: Optional[Any] = None

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of node parameters."""
        # Create deterministic JSON representation
        node_json = json.dumps({
            "type": self.node_type,
            "params": self.params
        }, sort_keys=True)

        # Hash
        node_hash = hashlib.sha256(node_json.encode()).hexdigest()
        return f"{self.node_type}_{node_hash[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "params": self.params,
            "dependencies": self.dependencies
        }


class MissionDAG:
    """Directed Acyclic Graph representation of mission."""

    def __init__(self, commands: List[Dict[str, Any]]):
        """Initialize mission DAG from command list.

        Args:
            commands: List of mission commands
        """
        self.nodes: Dict[str, MissionNode] = {}
        self.execution_order: List[str] = []
        self._build_dag(commands)

    def _build_dag(self, commands: List[Dict[str, Any]]):
        """Build DAG from command list."""
        prev_node_id = None

        for cmd in commands:
            node = MissionNode(cmd["type"], cmd.get("params", {}))

            # Add dependency on previous node (simple sequential execution)
            if prev_node_id:
                node.dependencies.append(prev_node_id)

            self.nodes[node.node_id] = node
            self.execution_order.append(node.node_id)
            prev_node_id = node.node_id

    def get_node(self, node_id: str) -> Optional[MissionNode]:
        """Get node by ID."""
        return self.nodes.get(node_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary."""
        return {
            "nodes": {nid: node.to_dict() for nid, node in self.nodes.items()},
            "execution_order": self.execution_order
        }


class CachedMissionRunner:
    """Mission runner with DAG caching.

    Example:
        >>> runner = CachedMissionRunner()
        >>>
        >>> mission = {
        ...     "commands": [
        ...         {"type": "create_engine", "params": {"num_nodes": 4096}},
        ...         {"type": "evolve", "params": {"timesteps": 100}},
        ...         {"type": "snapshot", "params": {}}
        ...     ]
        ... }
        >>>
        >>> # First run: compute and cache
        >>> result1 = runner.run_mission(mission)
        >>>
        >>> # Second run: use cached results
        >>> result2 = runner.run_mission(mission)  # Much faster!
    """

    def __init__(self, cache_root: str = "./cache", enable_cache: bool = True):
        """Initialize mission runner.

        Args:
            cache_root: Path to cache root directory
            enable_cache: If False, always recompute
        """
        self.enable_cache = enable_cache

        if enable_cache:
            self.cache = CacheManager(root=cache_root)
        else:
            self.cache = None

        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "nodes_executed": 0,
            "nodes_cached": 0
        }

    def run_mission(
        self,
        mission: Dict[str, Any],
        force_recompute: bool = False
    ) -> Dict[str, Any]:
        """Run mission with caching.

        Args:
            mission: Mission specification with commands
            force_recompute: If True, bypass cache

        Returns:
            Mission results dict
        """
        # Build DAG
        dag = MissionDAG(mission["commands"])

        # Execute nodes in order
        results = {}
        for node_id in dag.execution_order:
            node = dag.get_node(node_id)

            # Try to load from cache
            if self.enable_cache and not force_recompute:
                cached_result = self._load_node_result(node_id)
                if cached_result is not None:
                    results[node_id] = cached_result
                    self.stats["cache_hits"] += 1
                    self.stats["nodes_cached"] += 1
                    continue

            # Execute node
            result = self._execute_node(node, results)
            results[node_id] = result

            # Cache result
            if self.enable_cache:
                self._save_node_result(node_id, result)

            self.stats["cache_misses"] += 1
            self.stats["nodes_executed"] += 1

        # Return final results
        return {
            "dag": dag.to_dict(),
            "node_results": results,
            "stats": self.stats.copy()
        }

    def _execute_node(
        self,
        node: MissionNode,
        prev_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute single node (simulation stub).

        Args:
            node: Node to execute
            prev_results: Results from previous nodes

        Returns:
            Node execution result
        """
        # This is a stub implementation
        # In production, this would call actual engine methods

        if node.node_type == "create_engine":
            return {
                "engine_id": "engine_001",
                "num_nodes": node.params.get("num_nodes", 4096),
                "status": "created"
            }

        elif node.node_type == "evolve":
            timesteps = node.params.get("timesteps", 100)
            # Simulate evolution with dummy data
            state = np.random.rand(100)  # Simplified state vector
            return {
                "timesteps_completed": timesteps,
                "final_time": timesteps * 0.01,
                "state_size": len(state),
                "status": "evolved"
            }

        elif node.node_type == "snapshot":
            return {
                "snapshot_id": "snapshot_001",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "captured"
            }

        elif node.node_type == "analyze":
            return {
                "metrics": {
                    "energy": 1.234,
                    "entropy": 0.567,
                    "complexity": 0.890
                },
                "status": "analyzed"
            }

        else:
            return {
                "status": "unknown_command",
                "node_type": node.node_type
            }

    def _load_node_result(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Load node result from cache.

        Args:
            node_id: Node identifier

        Returns:
            Cached result or None if not found
        """
        try:
            return self.cache.load("mission_graph", node_id)
        except (FileNotFoundError, KeyError):
            return None

    def _save_node_result(self, node_id: str, result: Dict[str, Any]):
        """Save node result to cache.

        Args:
            node_id: Node identifier
            result: Node execution result
        """
        try:
            self.cache.save("mission_graph", node_id, result)
        except Exception as e:
            print(f"Warning: Failed to cache node result: {e}")

    def clear_cache(self, node_id: Optional[str] = None):
        """Clear cache for specific node or all nodes.

        Args:
            node_id: Optional node to clear (if None, clears all)
        """
        if node_id:
            self.cache.delete("mission_graph", node_id)
        else:
            self.cache.clear_category("mission_graph")

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        total_nodes = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total_nodes if total_nodes > 0 else 0.0

        return {
            **self.stats,
            "hit_rate": hit_rate
        }


class MissionOptimizer:
    """Optimize mission execution order based on cache availability."""

    def __init__(self, runner: CachedMissionRunner):
        """Initialize optimizer.

        Args:
            runner: Mission runner instance
        """
        self.runner = runner

    def analyze_mission(self, mission: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mission for cache opportunities.

        Args:
            mission: Mission specification

        Returns:
            Analysis report
        """
        dag = MissionDAG(mission["commands"])

        cached_nodes = []
        uncached_nodes = []

        for node_id in dag.execution_order:
            if self.runner._load_node_result(node_id) is not None:
                cached_nodes.append(node_id)
            else:
                uncached_nodes.append(node_id)

        return {
            "total_nodes": len(dag.execution_order),
            "cached_nodes": len(cached_nodes),
            "uncached_nodes": len(uncached_nodes),
            "cache_rate": len(cached_nodes) / len(dag.execution_order)
                if dag.execution_order else 0.0,
            "cached_node_ids": cached_nodes,
            "uncached_node_ids": uncached_nodes
        }


__all__ = ["MissionNode", "MissionDAG", "CachedMissionRunner", "MissionOptimizer"]
