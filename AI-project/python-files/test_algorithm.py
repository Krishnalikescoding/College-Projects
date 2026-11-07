import math
import unittest

from algorithms import CROWD_MULTIPLIERS, astar, bfs, dfs, effective_edge_cost, heuristic
from app import GRAPH, NODES


class TestLibraryAlgorithms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = GRAPH
        cls.nodes = NODES
        cls.algorithms = (("BFS", bfs), ("DFS", dfs), ("A*", astar))

    def assert_result_shape(self, result, algorithm):
        for key in ("path", "cost", "edge_count", "explored_count", "visited", "found", "message"):
            self.assertIn(key, result)
        self.assertIsInstance(result["path"], list)
        self.assertIsInstance(result["edge_count"], int)
        self.assertIsInstance(result["explored_count"], int)
        self.assertIsInstance(result["visited"], list)
        self.assertIsInstance(result["found"], bool)
        self.assertIsInstance(result["message"], str)
        self.assertIn(algorithm, result["message"])
        if result["cost"] is not None:
            self.assertTrue(math.isfinite(result["cost"]))
            self.assertNotIsInstance(result["cost"], bool)

    def test_real_library_has_expected_expansion(self):
        self.assertGreaterEqual(len(self.nodes), 17)
        self.assertGreaterEqual(len(self.graph), 17)

    def test_bfs_finds_path(self):
        result = bfs(self.graph, self.nodes, "Entrance", "AI_Section")
        self.assert_result_shape(result, "BFS")
        self.assertTrue(result["found"])
        self.assertEqual(result["path"][0], "Entrance")
        self.assertEqual(result["path"][-1], "AI_Section")
        self.assertEqual(result["edge_count"], len(result["path"]) - 1)
        self.assertGreater(result["explored_count"], 0)

    def test_dfs_finds_path_deterministically(self):
        first = dfs(self.graph, self.nodes, "Entrance", "History")
        second = dfs(self.graph, self.nodes, "Entrance", "History")
        self.assert_result_shape(first, "DFS")
        self.assertTrue(first["found"])
        self.assertEqual(first["path"], second["path"])
        self.assertEqual(first["visited"], second["visited"])
        self.assertEqual(first["path"][-1], "History")

    def test_astar_finds_least_distance_path(self):
        result = astar(self.graph, self.nodes, "Entrance", "Physics_Section", "distance")
        self.assert_result_shape(result, "A*")
        self.assertTrue(result["found"])
        self.assertEqual(result["path"], ["Entrance", "Math_Section", "Physics_Section"])
        self.assertEqual(result["cost"], 12.0)

    def test_bfs_fewest_edges_is_not_least_distance(self):
        bfs_result = bfs(self.graph, self.nodes, "Entrance", "Physics_Section", "distance")
        astar_result = astar(self.graph, self.nodes, "Entrance", "Physics_Section", "distance")
        self.assertEqual(bfs_result["edge_count"], 1)
        self.assertEqual(astar_result["edge_count"], 2)
        self.assertGreater(bfs_result["cost"], astar_result["cost"])
        self.assertEqual(bfs_result["path"], ["Entrance", "Physics_Section"])
        self.assertEqual(astar_result["path"], ["Entrance", "Math_Section", "Physics_Section"])

    def test_astar_time_mode_uses_crowd_aware_time(self):
        distance_result = astar(self.graph, self.nodes, "Entrance", "Physics_Section", "distance")
        time_result = astar(self.graph, self.nodes, "Entrance", "Physics_Section", "time")
        self.assertTrue(time_result["found"])
        self.assertNotEqual(distance_result["path"], time_result["path"])
        self.assertEqual(time_result["path"], ["Entrance", "Physics_Section"])
        expected = 10 * CROWD_MULTIPLIERS["Medium"]
        self.assertAlmostEqual(time_result["cost"], expected, places=6)

    def test_distance_mode_ignores_crowd_penalty(self):
        self.assertEqual(
            effective_edge_cost(self.graph, self.nodes, "Entrance", "Physics_Section", "distance"),
            40.0,
        )
        self.assertEqual(
            effective_edge_cost(self.graph, self.nodes, "Entrance", "Physics_Section", "time"),
            12.5,
        )

    def test_astar_is_not_worse_than_bfs_on_distance(self):
        targets = [node for node in self.nodes if not self.nodes[node]["restricted"]]
        for target in targets:
            bfs_result = bfs(self.graph, self.nodes, "Entrance", target, "distance")
            astar_result = astar(self.graph, self.nodes, "Entrance", target, "distance")
            if bfs_result["found"] and astar_result["found"]:
                self.assertLessEqual(
                    astar_result["cost"], bfs_result["cost"] + 1e-9,
                    msg=f"A* cost exceeded BFS weighted distance for {target}",
                )

    def test_heuristic_is_admissible_for_every_edge(self):
        for source, neighbours in self.graph.items():
            for target in neighbours:
                straight_line = heuristic(source, target, self.nodes)
                self.assertLessEqual(straight_line, neighbours[target]["distance"] + 1e-9)

    def test_all_algorithms_handle_unreachable_target(self):
        blocked_neighbours = sorted(self.graph["AI_Section"].keys())
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "AI_Section",
                closed_sections=blocked_neighbours,
            )
            self.assert_result_shape(result, algorithm)
            self.assertFalse(result["found"], msg=f"{algorithm} should not reach the target")
            self.assertIsNone(result["cost"])
            self.assertEqual(result["path"], [])
            self.assertEqual(result["edge_count"], 0)
            self.assertGreater(len(result["visited"]), 0)

    def test_all_algorithms_respect_closed_target(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "Physics_Section",
                closed_sections=["Physics_Section"],
            )
            self.assertFalse(result["found"])
            self.assertIsNone(result["cost"])
            self.assertIn("closed", result["message"].lower())

    def test_closed_section_reroutes(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "AI_Section",
                closed_sections=["CS_Section"],
            )
            self.assert_result_shape(result, algorithm)
            self.assertTrue(result["found"], msg=f"{algorithm} should find an alternative route")
            self.assertNotIn("CS_Section", result["path"])

    def test_restricted_access_denied_for_all_algorithms(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "Restricted_Archive",
                authorized=False,
            )
            self.assert_result_shape(result, algorithm)
            self.assertFalse(result["found"])
            self.assertIsNone(result["cost"])
            self.assertIn("restricted", result["message"].lower())

    def test_restricted_access_granted_for_all_algorithms(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "Restricted_Archive",
                authorized=True,
            )
            self.assert_result_shape(result, algorithm)
            self.assertTrue(result["found"], msg=f"{algorithm} should reach the archive")
            self.assertEqual(result["path"][-1], "Restricted_Archive")

    def test_restricted_node_not_entered_without_authorization(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "Research_Archive",
                authorized=False,
            )
            self.assertFalse(result["found"])
            self.assertNotIn("Restricted_Archive", result["path"])

    def test_start_equals_goal(self):
        for algorithm, function in self.algorithms:
            result = function(self.graph, self.nodes, "Entrance", "Entrance")
            self.assertTrue(result["found"])
            self.assertEqual(result["path"], ["Entrance"])
            self.assertEqual(result["cost"], 0)
            self.assertEqual(result["edge_count"], 0)
            self.assertEqual(result["visited"], ["Entrance"])

    def test_visited_order_has_no_duplicates(self):
        for algorithm, function in self.algorithms:
            result = function(self.graph, self.nodes, "Entrance", "Chemistry_Section")
            self.assertEqual(len(result["visited"]), len(set(result["visited"])))
            for node in result["path"]:
                self.assertIn(node, result["visited"])

    def test_no_algorithm_returns_invalid_number(self):
        for algorithm, function in self.algorithms:
            result = function(self.graph, self.nodes, "Entrance", "Restricted_Archive")
            self.assertFalse(result["found"])
            self.assertIsNone(result["cost"])
            self.assertNotIn("Infinity", str(result))
            self.assertNotIn("NaN", str(result))
            if result["cost"] is not None:
                self.assertTrue(math.isfinite(result["cost"]))

    def test_start_closed_returns_clean_failure(self):
        for algorithm, function in self.algorithms:
            result = function(
                self.graph, self.nodes, "Entrance", "AI_Section",
                closed_sections=["Entrance"],
            )
            self.assertFalse(result["found"])
            self.assertIsNone(result["cost"])
            self.assertIn("start", result["message"].lower())


if __name__ == "__main__":
    unittest.main()
