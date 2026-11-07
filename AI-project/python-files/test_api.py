import json
import unittest

import app as app_module


class TestFlaskApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.config["TESTING"] = True
        cls.client = app_module.app.test_client()

    def assert_json(self, response, status=200):
        self.assertEqual(response.status_code, status, msg=response.get_data(as_text=True))
        self.assertTrue(response.headers["Content-Type"].startswith("application/json"))
        return response.get_json()

    def assert_error(self, response, status=400):
        data = self.assert_json(response, status)
        self.assertIn("message", data)
        self.assertIn("error", data)
        return data

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Library AI Agent", response.data)

    def test_data_route(self):
        data = self.assert_json(self.client.get("/api/data"))
        self.assertGreaterEqual(len(data["nodes"]), 17)
        self.assertGreaterEqual(len(data["edges"]), 20)
        self.assertGreaterEqual(len(data["books"]), 100)
        self.assertIn("stats", data)
        self.assertEqual(data["stats"]["node_count"], len(data["nodes"]))

    def test_navigate_all_algorithms(self):
        for algorithm in ("BFS", "DFS", "A*"):
            data = self.assert_json(self.client.post("/api/navigate", json={
                "target": "Physics_Section",
                "algorithm": algorithm,
            }))
            self.assertTrue(data["found"])
            self.assertEqual(data["algorithm"], algorithm)
            self.assertEqual(data["target"], "Physics_Section")
            for key in ("path", "cost", "edge_count", "explored_count", "visited", "found", "message"):
                self.assertIn(key, data)
            self.assertNotIn("Infinity", json.dumps(data))
            self.assertNotIn("NaN", json.dumps(data))

    def test_bfs_and_astar_differ_through_api(self):
        bfs_data = self.assert_json(self.client.post("/api/navigate", json={
            "target": "Physics_Section", "algorithm": "BFS",
        }))
        astar_data = self.assert_json(self.client.post("/api/navigate", json={
            "target": "Physics_Section", "algorithm": "A*",
        }))
        self.assertLess(bfs_data["edge_count"], astar_data["edge_count"])
        self.assertGreater(bfs_data["cost"], astar_data["cost"])

    def test_restricted_access_for_all_algorithms(self):
        for algorithm in ("BFS", "DFS", "A*"):
            denied = self.assert_json(self.client.post("/api/navigate", json={
                "target": "Restricted_Archive",
                "algorithm": algorithm,
                "authorized": False,
            }))
            granted = self.assert_json(self.client.post("/api/navigate", json={
                "target": "Restricted_Archive",
                "algorithm": algorithm,
                "authorized": True,
            }))
            self.assertFalse(denied["found"])
            self.assertIsNone(denied["cost"])
            self.assertIn("restricted", denied["message"].lower())
            self.assertTrue(granted["found"])
            self.assertEqual(granted["path"][-1], "Restricted_Archive")

    def test_closed_section_through_api(self):
        data = self.assert_json(self.client.post("/api/navigate", json={
            "target": "Physics_Section",
            "algorithm": "A*",
            "closed_sections": ["Physics_Section"],
        }))
        self.assertFalse(data["found"])
        self.assertIsNone(data["cost"])
        self.assertIn("closed", data["message"].lower())

    def test_no_path_returns_null_cost_not_infinity(self):
        blocked = sorted(app_module.GRAPH["AI_Section"].keys())
        response = self.client.post("/api/navigate", json={
            "target": "AI_Section",
            "algorithm": "A*",
            "closed_sections": blocked,
        })
        raw = response.get_data(as_text=True)
        self.assertNotIn("Infinity", raw)
        self.assertNotIn("NaN", raw)
        data = response.get_json()
        self.assertFalse(data["found"])
        self.assertIsNone(data["cost"])
        self.assertEqual(data["path"], [])

    def test_compare_route(self):
        data = self.assert_json(self.client.post("/api/compare", json={
            "target": "Physics_Section",
            "optimize": "distance",
        }))
        self.assertEqual([row["algorithm"] for row in data["results"]], ["BFS", "DFS", "A*"])
        self.assertTrue(all("path" in row for row in data["results"]))
        self.assertTrue(any(row["found"] for row in data["results"]))

    def test_navigate_input_validation(self):
        invalid_payloads = [
            {},
            {"target": None},
            {"target": "No_Such_Node"},
            {"target": "Physics_Section", "algorithm": "DIJKSTRA"},
            {"target": "Physics_Section", "optimize": "fuel"},
            {"target": "Physics_Section", "closed_sections": "Math_Section"},
            {"target": "Physics_Section", "closed_sections": ["No_Such_Node"]},
            {"target": "Physics_Section", "authorized": "true"},
            {"target": "Physics_Section", "start": "No_Such_Node"},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_error(self.client.post("/api/navigate", json=payload))

    def test_malformed_json_is_a_json_error(self):
        response = self.client.post("/api/navigate", data="{bad json", content_type="application/json")
        self.assert_error(response)

    def test_missing_content_type_is_a_json_error(self):
        response = self.client.post("/api/navigate", data='{"target": "Physics_Section"}')
        self.assert_error(response)

    def test_unknown_api_route_is_json(self):
        self.assert_error(self.client.get("/api/does-not-exist"), status=404)

    def test_wrong_method_is_json(self):
        self.assert_error(self.client.get("/api/navigate"), status=405)

    def test_multi_route_success(self):
        data = self.assert_json(self.client.post("/api/multi_route", json={
            "books": ["101", "138", "146"],
            "time_limit": 999,
        }))
        self.assertTrue(data["found"])
        self.assertEqual(len(data["legs"]), 3)
        self.assertEqual(data["requested_books"], ["101", "138", "146"])
        self.assertIn("remaining_limit", data)
        for book in data["collected"]:
            self.assertIn("title", book)

    def test_multi_route_accepts_full_book_objects(self):
        data = self.assert_json(self.client.post("/api/multi_route", json={
            "books": [app_module.BOOKS_BY_ID["101"]],
            "time_limit": 999,
        }))
        self.assertTrue(data["found"])
        self.assertEqual(data["collected"][0]["id"], "101")

    def test_multi_route_empty_collection(self):
        data = self.assert_json(self.client.post("/api/multi_route", json={
            "books": [],
            "time_limit": 50,
        }))
        self.assertTrue(data["found"])
        self.assertEqual(data["legs"], [])
        self.assertEqual(data["total_cost"], 0)

    def test_multi_route_limit_validation(self):
        invalid_payloads = [
            {"books": []},
            {"books": [], "time_limit": None},
            {"books": [], "time_limit": ""},
            {"books": [], "time_limit": "50"},
            {"books": [], "time_limit": True},
            {"books": [], "time_limit": -1},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_error(self.client.post("/api/multi_route", json=payload))

    def test_multi_route_book_validation(self):
        invalid_payloads = [
            {"books": "101", "time_limit": 50},
            {"books": ["nope"], "time_limit": 50},
            {"books": ["101", "101"], "time_limit": 50},
            {"books": [{"id": "nope"}], "time_limit": 50},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_error(self.client.post("/api/multi_route", json=payload))

    def test_multi_route_option_validation(self):
        invalid_payloads = [
            {"books": [], "time_limit": 50, "optimize": "fuel"},
            {"books": [], "time_limit": 50, "authorized": "yes"},
            {"books": [], "time_limit": 50, "closed_sections": "CS_Section"},
            {"books": [], "time_limit": 50, "closed_sections": ["Nope"]},
        ]
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                self.assert_error(self.client.post("/api/multi_route", json=payload))

    def test_multi_route_restricted_and_limit_reasons(self):
        denied = self.assert_json(self.client.post("/api/multi_route", json={
            "books": ["117"], "time_limit": 999, "authorized": False,
        }))
        limited = self.assert_json(self.client.post("/api/multi_route", json={
            "books": ["101"], "time_limit": 7,
        }))
        self.assertEqual(denied["missed"][0]["reason"], "Restricted access")
        self.assertEqual(limited["missed"][0]["reason"], "Limit exceeded")

    def test_multi_route_closed_section_reason(self):
        data = self.assert_json(self.client.post("/api/multi_route", json={
            "books": ["101"],
            "time_limit": 999,
            "closed_sections": ["CS_Section"],
        }))
        self.assertEqual(data["missed"][0]["reason"], "Closed section")

    def test_compare_input_validation(self):
        self.assert_error(self.client.post("/api/compare", json={}))
        self.assert_error(self.client.post("/api/compare", json={"target": "Nope"}))


if __name__ == "__main__":
    unittest.main()
