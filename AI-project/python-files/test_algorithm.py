import unittest
from algorithms import bfs, dfs, astar

class TestLibraryAlgorithms(unittest.TestCase):
    def setUp(self):
        # A simple test graph representing library sections
        self.graph = {
            "Entrance": {"CS": {'distance': 10}, "Math": {'distance': 5}},
            "Math": {"Entrance": {'distance': 5}, "AI": {'distance': 10}},
            "CS": {"Entrance": {'distance': 10}, "AI": {'distance': 5}},
            "AI": {"Math": {'distance': 10}, "CS": {'distance': 5}, "Restricted": {'distance': 5}},
            "Restricted": {"AI": {'distance': 5}}
        }
        self.nodes_data = {
            "Entrance": {"x": 0, "y": 0, "restricted": False},
            "Math": {"x": 5, "y": 0, "restricted": False},
            "CS": {"x": 0, "y": 10, "restricted": False},
            "AI": {"x": 5, "y": 10, "restricted": False},
            "Restricted": {"x": 10, "y": 10, "restricted": True}
        }

    def test_bfs_finds_path(self):
        path, _ = bfs(self.graph, "Entrance", "AI", closed_sections=[], authorized=False)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], "Entrance")
        self.assertEqual(path[-1], "AI")

    def test_astar_finds_optimal_path(self):
        # A* should prefer Entrance -> CS -> AI (10+5=15) over Entrance -> Math -> AI (5+10=15)
        # depending on heuristic, but both are valid. Let's test cost.
        path, cost, _ = astar(self.graph, self.nodes_data, "Entrance", "AI", 'distance')
        self.assertEqual(cost, 15)
        self.assertEqual(path[-1], "AI")

    def test_closed_sections_avoided(self):
        # Close CS. The only way to AI is through Math.
        path, cost, _ = astar(self.graph, self.nodes_data, "Entrance", "AI", 'distance', closed_sections=["CS"])
        self.assertIn("Math", path)
        self.assertNotIn("CS", path)

    def test_restricted_access_denied(self):
        # Unauthorized access to Restricted section should return None
        path, cost, _ = astar(self.graph, self.nodes_data, "Entrance", "Restricted", 'distance', authorized=False)
        self.assertIsNone(path)

    def test_restricted_access_granted(self):
        # Authorized access should find a path
        path, cost, _ = astar(self.graph, self.nodes_data, "Entrance", "Restricted", 'distance', authorized=True)
        self.assertIsNotNone(path)
        self.assertEqual(path[-1], "Restricted")

if __name__ == '__main__':
    unittest.main()