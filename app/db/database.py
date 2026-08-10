"""
SQLite Database storage for AutoTester test runs, cases, and logs
"""
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = os.getenv("DATABASE_PATH", "autotester.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_runs (
        run_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        name TEXT NOT NULL,
        suite TEXT DEFAULT 'Authentication',
        env TEXT DEFAULT 'Staging (test.com)',
        browser TEXT DEFAULT 'Chromium v124',
        status TEXT NOT NULL,
        duration TEXT DEFAULT '0.0s',
        passed_steps INTEGER DEFAULT 0,
        failed_steps INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        report_path TEXT,
        task_prompt TEXT,
        steps_json TEXT,
        logs_json TEXT,
        interactions_json TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        case_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        template_name TEXT,
        target_url TEXT,
        steps_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


def save_test_run(run_data: Dict[str, Any]):
    """Save or update a test run in the database."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    run_id = run_data.get("run_id", f"RUN-{int(datetime.now().timestamp())}")
    task_id = run_data.get("task_id", "")
    name = run_data.get("name", "Automated UI Test")
    suite = run_data.get("suite", "E2E Test Suite")
    env = run_data.get("env", "Staging")
    browser = run_data.get("browser", "Chromium")
    status = run_data.get("status", "completed")
    duration = run_data.get("duration", "0.0s")
    passed_steps = run_data.get("passed_steps", 0)
    failed_steps = run_data.get("failed_steps", 0)
    report_path = run_data.get("report_path", "")
    task_prompt = run_data.get("task_prompt", "")
    steps_json = json.dumps(run_data.get("steps", []))
    logs_json = json.dumps(run_data.get("logs", []))
    interactions_json = json.dumps(run_data.get("interactions", []))

    cursor.execute("""
    INSERT OR REPLACE INTO test_runs (
        run_id, task_id, name, suite, env, browser, status, duration,
        passed_steps, failed_steps, report_path, task_prompt, steps_json, logs_json, interactions_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, task_id, name, suite, env, browser, status, duration,
        passed_steps, failed_steps, report_path, task_prompt, steps_json, logs_json, interactions_json
    ))

    conn.commit()
    conn.close()
    return run_id


def get_all_test_runs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve test runs sorted by created_at DESC."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM test_runs ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    runs = []
    for row in rows:
        item = dict(row)
        item["steps"] = json.loads(item["steps_json"]) if item.get("steps_json") else []
        item["logs"] = json.loads(item["logs_json"]) if item.get("logs_json") else []
        item["interactions"] = json.loads(item["interactions_json"]) if item.get("interactions_json") else []
        runs.append(item)
    return runs


def get_test_run_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed record for a specific test run."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_runs WHERE run_id = ? OR task_id = ?", (run_id, run_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    item = dict(row)
    item["steps"] = json.loads(item["steps_json"]) if item.get("steps_json") else []
    item["logs"] = json.loads(item["logs_json"]) if item.get("logs_json") else []
    item["interactions"] = json.loads(item["interactions_json"]) if item.get("interactions_json") else []
    return item


# Initialize database on import
init_db()
