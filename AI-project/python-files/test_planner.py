import unittest

from app import BOOKS_BY_ID, GRAPH, NODES
from multi_book_agent import plan_collection_route


def books(*ids):
    return [BOOKS_BY_ID[book_id] for book_id in ids]


class TestMultiBookPlanner(unittest.TestCase):
    def plan(self, book_ids, limit=999, authorized=False, closed_sections=None, optimize="distance"):
        return plan_collection_route(
            GRAPH,
            NODES,
            "Entrance",
            books(*book_ids),
            optimize_for=optimize,
            time_limit=limit,
            authorized=authorized,
            closed_sections=closed_sections,
        )

    def test_priority_order_is_high_medium_low(self):
        result = self.plan(["148", "146", "101"])
        self.assertTrue(result["found"])
        self.assertEqual(
            [book["priority"] for book in result["collected"]],
            ["High", "Medium", "Low"],
        )
        self.assertEqual([book["id"] for book in result["collected"]], ["101", "146", "148"])

    def test_stable_order_inside_same_priority_group(self):
        forward = self.plan(["101", "138"], limit=999)
        backward = self.plan(["138", "101"], limit=999)
        self.assertEqual([book["id"] for book in forward["collected"]], ["101", "138"])
        self.assertEqual([book["id"] for book in backward["collected"]], ["138", "101"])

    def test_empty_collection(self):
        result = self.plan([])
        self.assertTrue(result["found"])
        self.assertEqual(result["path"], ["Entrance"])
        self.assertEqual(result["total_cost"], 0)
        self.assertEqual(result["legs"], [])
        self.assertEqual(result["collected"], [])
        self.assertEqual(result["missed"], [])
        self.assertIn("empty", result["message"].lower())

    def test_limit_sweep_is_monotonic_and_never_exceeded(self):
        book_ids = ["101", "138", "186", "146", "148"]
        previous_count = -1
        for limit in (0, 5, 10, 20, 30, 100, 999):
            result = self.plan(book_ids, limit=limit)
            self.assertLessEqual(result["total_cost"], limit + 1e-9)
            collected_count = len(result["collected"])
            self.assertGreaterEqual(collected_count, previous_count)
            previous_count = collected_count
            for missed in result["missed"]:
                self.assertIn(missed["reason"], {
                    "Book unavailable", "Restricted access", "Closed section",
                    "Unreachable shelf", "Limit exceeded", "Closed section blocks route",
                    "Restricted access required",
                })

    def test_limit_exceeded_reports_required_cost_and_remaining(self):
        result = self.plan(["101"], limit=7)
        self.assertFalse(result["found"])
        self.assertEqual(len(result["missed"]), 1)
        missed = result["missed"][0]
        self.assertEqual(missed["reason"], "Limit exceeded")
        self.assertEqual(missed["required_cost"], 8.0)
        self.assertEqual(missed["remaining_limit"], 7.0)

    def test_same_shelf_second_book_has_zero_cost(self):
        result = self.plan(["101", "108"], limit=999)
        self.assertEqual(len(result["collected"]), 2)
        self.assertEqual(result["legs"][1]["cost"], 0)
        self.assertEqual(result["legs"][1]["path"], ["CS_Section"])
        self.assertEqual(result["legs"][1]["cumulative_cost"], result["legs"][0]["cumulative_cost"])

    def test_unavailable_book_is_missed(self):
        result = self.plan(["135"])
        self.assertFalse(result["found"])
        self.assertEqual(result["collected"], [])
        self.assertEqual(result["missed"][0]["reason"], "Book unavailable")
        self.assertEqual(result["legs"], [])

    def test_medium_priority_is_supported(self):
        result = self.plan(["146", "101"])
        self.assertEqual([book["priority"] for book in result["collected"]], ["High", "Medium"])

    def test_restricted_book_requires_authorization(self):
        denied = self.plan(["117"], authorized=False)
        granted = self.plan(["117"], authorized=True)
        self.assertFalse(denied["found"])
        self.assertEqual(denied["missed"][0]["reason"], "Restricted access")
        self.assertTrue(granted["found"])
        self.assertEqual(granted["collected"][0]["id"], "117")
        self.assertIn("Restricted_Archive", granted["path"])

    def test_closed_target_is_missed_with_closed_reason(self):
        result = self.plan(["101"], closed_sections=["CS_Section"])
        self.assertFalse(result["found"])
        self.assertEqual(result["missed"][0]["reason"], "Closed section")

    def test_closed_route_reports_closed_section_reason(self):
        blocked = sorted(GRAPH["AI_Section"].keys())
        result = self.plan(["138"], closed_sections=blocked)
        self.assertFalse(result["found"])
        self.assertEqual(result["missed"][0]["reason"], "Closed section blocks route")

    def test_unreachable_shelf_reason(self):
        graph = {"Entrance": {}, "Island": {}}
        nodes = {
            "Entrance": {"id": "Entrance", "x": 0, "y": 0, "restricted": False, "crowd": "Low"},
            "Island": {"id": "Island", "x": 10, "y": 10, "restricted": False, "crowd": "Low"},
        }
        book = {
            "id": "x1", "title": "Island Book", "author": "A", "category": "Test",
            "shelf": "Island", "available": True, "priority": "High",
        }
        result = plan_collection_route(graph, nodes, "Entrance", [book], time_limit=999)
        self.assertFalse(result["found"])
        self.assertEqual(result["missed"][0]["reason"], "Unreachable shelf")

    def test_legs_contain_required_details(self):
        result = self.plan(["101", "138", "146"], limit=999)
        self.assertEqual(len(result["legs"]), 3)
        required = {
            "from", "to", "book_id", "title", "shelf", "priority", "cost",
            "cumulative_cost", "remaining_limit", "path", "edge_count", "explored_count",
        }
        for leg in result["legs"]:
            self.assertTrue(required.issubset(leg.keys()))
        cumulative = [leg["cumulative_cost"] for leg in result["legs"]]
        self.assertEqual(cumulative, sorted(cumulative))
        self.assertAlmostEqual(result["legs"][-1]["cumulative_cost"], result["total_cost"], places=6)
        self.assertGreaterEqual(result["remaining_limit"], 0)

    def test_time_mode_uses_weighted_time(self):
        result = self.plan(["105"], optimize="time")
        self.assertTrue(result["found"])
        self.assertAlmostEqual(result["total_cost"], 12.5, places=6)


if __name__ == "__main__":
    unittest.main()
