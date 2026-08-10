"""
PostgreSQL & SQLite Database persistence module for AutoTester
"""
import os
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("DATABASE")

# PostgreSQL Configuration from Environment
DATABASE_URL = os.getenv("DATABASE_URL", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432")))
POSTGRES_DB = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "autotester"))
POSTGRES_USER = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))


def get_postgres_conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        cursor_factory=RealDictCursor
    )


def get_db_connection():
    """
    Get PostgreSQL connection if available/configured, otherwise fallback to SQLite.
    Returns tuple: (db_type, connection_object)
    """
    # Check if PostgreSQL is configured or explicitly requested
    if DATABASE_URL or os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or os.getenv("USE_POSTGRES") == "true":
        try:
            conn = get_postgres_conn()
            return ("postgres", conn)
        except Exception as e:
            logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite.")

    # SQLite Fallback
    conn = sqlite3.connect("autotester.db")
    conn.row_factory = sqlite3.Row
    return ("sqlite", conn)


def init_db():
    """Initialize PostgreSQL or SQLite database schemas if needed."""
    try:
        db_type, conn = get_db_connection()
        cursor = conn.cursor()

        if db_type == "postgres":
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                run_id VARCHAR(255) PRIMARY KEY,
                task_id VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                suite VARCHAR(255) DEFAULT 'Authentication',
                env VARCHAR(255) DEFAULT 'Staging',
                browser VARCHAR(255) DEFAULT 'Chromium',
                status VARCHAR(50) NOT NULL,
                duration VARCHAR(50) DEFAULT '0.0s',
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
                case_id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                template_name VARCHAR(255),
                target_url TEXT,
                steps_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        else:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                run_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                name TEXT NOT NULL,
                suite TEXT DEFAULT 'Authentication',
                env TEXT DEFAULT 'Staging',
                browser TEXT DEFAULT 'Chromium',
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
        logger.info(f"Database initialized successfully using {db_type.upper()}")
    except Exception as e:
        logger.error(f"Database init error: {e}")


def save_test_run(run_data: Dict[str, Any]) -> str:
    """Save or update a test run in PostgreSQL or SQLite."""
    init_db()
    db_type, conn = get_db_connection()
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

    if db_type == "postgres":
        cursor.execute("""
        INSERT INTO test_runs (
            run_id, task_id, name, suite, env, browser, status, duration,
            passed_steps, failed_steps, report_path, task_prompt, steps_json, logs_json, interactions_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            status = EXCLUDED.status,
            duration = EXCLUDED.duration,
            passed_steps = EXCLUDED.passed_steps,
            failed_steps = EXCLUDED.failed_steps,
            report_path = EXCLUDED.report_path,
            steps_json = EXCLUDED.steps_json,
            logs_json = EXCLUDED.logs_json,
            interactions_json = EXCLUDED.interactions_json
        """, (
            run_id, task_id, name, suite, env, browser, status, duration,
            passed_steps, failed_steps, report_path, task_prompt, steps_json, logs_json, interactions_json
        ))
    else:
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
    db_type, conn = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("SELECT * FROM test_runs ORDER BY created_at DESC LIMIT %s", (limit,))
    else:
        cursor.execute("SELECT * FROM test_runs ORDER BY created_at DESC LIMIT ?", (limit,))

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
    db_type, conn = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgres":
        cursor.execute("SELECT * FROM test_runs WHERE run_id = %s OR task_id = %s", (run_id, run_id))
    else:
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
