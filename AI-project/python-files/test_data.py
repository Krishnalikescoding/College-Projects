import copy
import json
import os
import unittest

from data_validation import LibraryDataError, build_adjacency, validate_library_data

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "..", "JSON", "library_data.json")

with open(DATA_PATH, "r", encoding="utf-8") as handle:
    LIBRARY_DATA = json.load(handle)


class TestLibraryData(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(LIBRARY_DATA)

    def test_real_data_is_valid_and_expanded(self):
        summary = validate_library_data(self.data)
        self.assertGreaterEqual(summary["node_count"], 17)
        self.assertGreaterEqual(summary["edge_count"], 20)
        self.assertGreaterEqual(summary["book_count"], 100)
        self.assertGreaterEqual(len(summary["restricted_nodes"]), 2)
        self.assertGreater(summary["unavailable_books"], 0)
        self.assertGreater(summary["priorities"]["Medium"], 0)
        self.assertGreater(summary["priorities"]["High"], 0)
        self.assertGreater(summary["priorities"]["Low"], 0)

    def test_all_nodes_have_coordinates_restricted_flag_and_crowd(self):
        for node_id, node in self.data["nodes"].items():
            self.assertEqual(node["id"], node_id)
            self.assertIn("label", node)
            self.assertIn("x", node)
            self.assertIn("y", node)
            self.assertIsInstance(node["restricted"], bool)
            self.assertIn(node["crowd"], {"Low", "Medium", "High"})

    def test_all_books_reference_real_shelves(self):
        for book in self.data["books"]:
            self.assertIn(book["shelf"], self.data["nodes"])
            self.assertIn(book["priority"], {"High", "Medium", "Low"})
            self.assertIsInstance(book["available"], bool)

    def test_time_differs_from_distance_on_some_edges(self):
        self.assertTrue(any(edge["time"] != edge["distance"] for edge in self.data["edges"]))

    def test_graph_is_connected(self):
        adjacency = build_adjacency(self.data["nodes"], self.data["edges"])
        visited = {"Entrance"}
        stack = ["Entrance"]
        while stack:
            current = stack.pop()
            for neighbour in adjacency[current]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    stack.append(neighbour)
        self.assertEqual(visited, set(self.data["nodes"]))

    def test_duplicate_book_id_is_rejected(self):
        self.data["books"][1]["id"] = self.data["books"][0]["id"]
        with self.assertRaisesRegex(LibraryDataError, "Duplicate book id"):
            validate_library_data(self.data)

    def test_unknown_book_shelf_is_rejected(self):
        self.data["books"][0]["shelf"] = "No_Such_Shelf"
        with self.assertRaisesRegex(LibraryDataError, "unknown shelf"):
            validate_library_data(self.data)

    def test_invalid_priority_is_rejected(self):
        self.data["books"][0]["priority"] = "Urgent"
        with self.assertRaisesRegex(LibraryDataError, "invalid priority"):
            validate_library_data(self.data)

    def test_invalid_availability_is_rejected(self):
        self.data["books"][0]["available"] = "yes"
        with self.assertRaisesRegex(LibraryDataError, "boolean 'available'"):
            validate_library_data(self.data)

    def test_unknown_edge_endpoint_is_rejected(self):
        self.data["edges"][0]["to"] = "No_Such_Node"
        with self.assertRaisesRegex(LibraryDataError, "unknown target node"):
            validate_library_data(self.data)

    def test_short_edge_distance_is_rejected(self):
        self.data["edges"][0]["distance"] = 0.1
        with self.assertRaisesRegex(LibraryDataError, "shorter than"):
            validate_library_data(self.data)

    def test_non_positive_time_is_rejected(self):
        self.data["edges"][0]["time"] = 0
        with self.assertRaisesRegex(LibraryDataError, "positive 'time'"):
            validate_library_data(self.data)

    def test_self_loop_is_rejected(self):
        self.data["edges"][0]["to"] = self.data["edges"][0]["from"]
        with self.assertRaisesRegex(LibraryDataError, "self-loop"):
            validate_library_data(self.data)

    def test_duplicate_undirected_edge_is_rejected(self):
        edge = self.data["edges"][0]
        self.data["edges"].append({
            "from": edge["to"],
            "to": edge["from"],
            "distance": edge["distance"],
            "time": edge["time"],
        })
        with self.assertRaisesRegex(LibraryDataError, "duplicates"):
            validate_library_data(self.data)

    def test_disconnected_graph_is_rejected(self):
        target = "Quiet_Study"
        self.data["edges"] = [
            edge for edge in self.data["edges"]
            if edge["from"] != target and edge["to"] != target
        ]
        with self.assertRaisesRegex(LibraryDataError, "disconnected"):
            validate_library_data(self.data)

    def test_missing_node_coordinate_is_rejected(self):
        del self.data["nodes"]["Entrance"]["x"]
        with self.assertRaisesRegex(LibraryDataError, "invalid 'x'"):
            validate_library_data(self.data)

    def test_missing_node_restricted_flag_is_rejected(self):
        del self.data["nodes"]["Entrance"]["restricted"]
        with self.assertRaisesRegex(LibraryDataError, "boolean 'restricted'"):
            validate_library_data(self.data)

    def test_invalid_crowd_level_is_rejected(self):
        self.data["nodes"]["Entrance"]["crowd"] = "Packed"
        with self.assertRaisesRegex(LibraryDataError, "invalid crowd"):
            validate_library_data(self.data)


if __name__ == "__main__":
    unittest.main()
