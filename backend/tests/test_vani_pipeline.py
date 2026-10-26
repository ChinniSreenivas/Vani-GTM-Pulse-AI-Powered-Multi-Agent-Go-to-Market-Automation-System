import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.agents import run_pipeline


async def fake_search_web(query, num_results=5):
    return {
        "results": [
            {
                "title": "Solution Consultant Careers — Client-facing communication",
                "url": "https://example.com/careers/solution-consultant",
                "description": (
                    "The role supports client-facing conversations, stakeholder "
                    "expectations, and sales enablement."
                ),
            },
            {
                "title": "Company news",
                "url": "https://example.com/news",
                "description": "A general company announcement.",
            },
        ]
    }


class VaniPipelineTests(unittest.TestCase):
    def setUp(self):
        self.prospect = SimpleNamespace(
            company="Example Consulting Group",
            industry="Consulting / Professional Services",
            location="India",
            product="Vani communication fitness and coaching platform",
            target_role="Head of Learning & Development",
            company_size="Enterprise",
            pain_points=["client-facing communication consistency"],
            signals=["client-facing hiring"],
            notes="",
        )

    def test_four_agents_return_vani_specific_reviewable_result(self):
        with patch("app.agents.search_web", new=fake_search_web):
            result = run_pipeline(self.prospect)

        self.assertEqual(result["demand_sensing"]["agent"], "Demand Sensing Agent")
        self.assertEqual(result["customer_profiling"]["agent"], "Customer Profiling Agent")
        self.assertEqual(result["outbound"]["agent"], "Outbound Strategy Agent")
        self.assertEqual(result["manager"]["agent"], "Managing Agent")
        self.assertGreaterEqual(result["customer_profiling"]["lead_score"], 0)
        self.assertLessEqual(result["customer_profiling"]["lead_score"], 100)
        self.assertTrue(result["demand_sensing"]["relevant_research_results"])
        self.assertIn("Vani", result["outbound"]["body"])
        self.assertEqual(result["outbound"]["send_status"], "Draft only — not sent")
        self.assertFalse(result["manager"]["validation_checks"]["external_message_sent"])
        self.assertEqual(result["manager"]["decision"], "pending_human_review")

    def test_research_error_does_not_claim_verified_buying_intent(self):
        async def fail_search(query, num_results=5):
            raise RuntimeError("test network error")

        with patch("app.agents.search_web", new=fail_search):
            result = run_pipeline(self.prospect)

        self.assertEqual(result["demand_sensing"]["status"], "needs_review")
        self.assertFalse(result["customer_profiling"]["evidence_sources"])
        self.assertIn("not independently", result["outbound"]["body"])
        self.assertEqual(result["manager"]["decision"], "blocked_needs_research")
        self.assertFalse(result["manager"]["validation_checks"]["public_source_candidate_available"])


if __name__ == "__main__":
    unittest.main()
