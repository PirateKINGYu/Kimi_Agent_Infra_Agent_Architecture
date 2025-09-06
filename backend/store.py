# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3
import os
import json
from typing import Dict, Any, List


_DB = "agent_obs.db"


def init_db():
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS runs(
    run_id TEXT PRIMARY KEY,
    task TEXT, model TEXT, policy TEXT, created_at TEXT,
    status TEXT DEFAULT 'running', final_answer TEXT, metrics_json TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS steps(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT, step_no INTEGER,
    thought TEXT, action TEXT, action_input TEXT, observation TEXT,
    error TEXT, latency_s REAL, model_usage_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()


def insert_run(run: Dict[str, Any]):
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO runs(run_id,task,model,policy,created_at) VALUES(?,?,?,?,?)",
              (run['run_id'], run['task'], run['model'], run['policy'], run['created_at']))
    conn.commit()
    conn.close()


def insert_step(run_id: str, step: Dict[str, Any]):
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO steps(run_id, step_no, thought, action, action_input, observation, error, latency_s, model_usage_json)
    VALUES(?,?,?,?,?,?,?,?,?)
    """, (run_id, step['step_no'], step['thought'], step.get('action'), step.get('action_input'), step.get('observation'),
          step.get('error'), float(step['latency_s']), json.dumps(step.get('model_usage') or {}, ensure_ascii=False)))
    conn.commit()
    conn.close()


def finalize_run(run_id: str, final_answer: str, metrics: Dict[str, Any]):
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    c.execute("UPDATE runs SET status='done', final_answer=?, metrics_json=? WHERE run_id=?",
              (final_answer, json.dumps(metrics, ensure_ascii=False), run_id))
    conn.commit()
    conn.close()


def list_runs() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    rows = c.execute("SELECT run_id,task,model,policy,created_at,status FROM runs ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(run_id=r[0], task=r[1], model=r[2], policy=r[3], created_at=r[4], status=r[5]) for r in rows]


def get_run(run_id: str) -> Dict[str, Any]:
    conn = sqlite3.connect(_DB)
    c = conn.cursor()
    r = c.execute("SELECT run_id,task,model,policy,created_at,status,final_answer,metrics_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
    steps = c.execute("SELECT step_no,thought,action,action_input,observation,error,latency_s,model_usage_json,created_at FROM steps WHERE run_id=? ORDER BY step_no", (run_id,)).fetchall()
    conn.close()
    if not r:
        return {}
    return {
        "run": dict(run_id=r[0], task=r[1], model=r[2], policy=r[3], created_at=r[4], status=r[5], final_answer=r[6], metrics_json=r[7]),
        "steps": [dict(step_no=s[0], thought=s[1], action=s[2], action_input=s[3], observation=s[4], error=s[5], latency_s=s[6], model_usage_json=s[7], created_at=s[8]) for s in steps]
    }