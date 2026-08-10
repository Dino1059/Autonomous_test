"""
Unit tests for SQLite Database persistence module
"""
import os
import unittest
from app.db.database import save_test_run, get_all_test_runs, get_test_run_by_id


class TestDatabaseModule(unittest.TestCase):

    def test_save_and_retrieve_test_run(self):
        run_data = {
            "task_id": "test_task_123",
            "name": "Login Test Run",
            "suite": "Authentication",
            "env": "Staging",
            "browser": "Chromium v124",
            "status": "Passed",
            "duration": "14.2s",
            "passed_steps": 5,
            "failed_steps": 0,
            "report_path": "demo_reports/TEST_123",
            "task_prompt": "Test login feature"
        }
        run_id = save_test_run(run_data)
        self.assertIsNotNone(run_id)

        retrieved = get_test_run_by_id(run_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["task_id"], "test_task_123")
        self.assertEqual(retrieved["status"], "Passed")

        all_runs = get_all_test_runs(limit=10)
        self.assertTrue(len(all_runs) > 0)


if __name__ == "__main__":
    unittest.main()
