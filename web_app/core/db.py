import sqlite3
import os
import json
from sqlalchemy import create_engine
from pathlib import Path

def _app_data_dir() -> Path:
    configured = os.environ.get("EPI_VISION_DATA_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    candidates.append(Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "EPI-Vision-Web")
    candidates.append(Path(__file__).resolve().parent.parent / "scratch" / "EPI-Vision-Web")

    for d in candidates:
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return d
        except OSError:
            continue

    raise RuntimeError("No writable data directory is available for EPI-Vision")

def get_db_path() -> str:
    return str(_app_data_dir() / "optical_data_web.db")

def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def get_engine():
    # Use 4 slashes for absolute path on Windows in SQLAlchemy
    db_path = get_db_path().replace("\\", "/")
    return create_engine(f"sqlite:///{db_path}")

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # 1. 实验数据表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ExperimentalData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material TEXT,
            angle REAL,
            wavenumber REAL,
            reflectance REAL
        )
    """)
    # 2. 定制材料映射表 (解耦折射率)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            n_film REAL,
            n_sub REAL
        )
    """)
    # 3. 分析历史表 (快照)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS AnalysisHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            dataset_name TEXT,
            method TEXT,
            n_film REAL,
            n_sub REAL,
            thickness REAL,
            fit_confidence REAL,
            mse REAL,
            parameters_json TEXT, 
            result_json TEXT 
        )
    """)
    
    # 插入默认参考材料如果不存在
    presets = [
        ('SiC', 2.60, 2.55),
        ('Si', 3.40, 3.55),
        ('GaN', 2.35, 2.30),
        ('GaAs', 3.30, 3.45)
    ]
    for p in presets:
        cur.execute("INSERT OR IGNORE INTO Materials (name, n_film, n_sub) VALUES (?, ?, ?)", p)

    conn.commit()
    conn.close()

def get_materials():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Materials ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_or_update_material(name, n_film, n_sub):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO Materials (name, n_film, n_sub) 
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET n_film=excluded.n_film, n_sub=excluded.n_sub
    """, (name, n_film, n_sub))
    conn.commit()
    conn.close()

def delete_material(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Materials WHERE name=?", (name,))
    conn.commit()
    conn.close()

def save_history(dataset_name, method, n_film, n_sub, thickness, fit_confidence, mse, parameters, result):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO AnalysisHistory 
        (dataset_name, method, n_film, n_sub, thickness, fit_confidence, mse, parameters_json, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dataset_name, method, n_film, n_sub, thickness, fit_confidence, mse, 
        json.dumps(parameters), json.dumps(result)
    ))
    history_id = cur.lastrowid
    conn.commit()
    conn.close()
    return history_id

def get_history_list():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, dataset_name, method, thickness, fit_confidence FROM AnalysisHistory ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_history_detail(history_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM AnalysisHistory WHERE id=?", (history_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['parameters_json'] = json.loads(d['parameters_json']) if d['parameters_json'] else {}
        d['result_json'] = json.loads(d['result_json']) if d['result_json'] else {}
        return d
    return None

def get_datasets():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT material, angle FROM ExperimentalData ORDER BY material, angle")
    records = cur.fetchall()
    conn.close()
    return [{"material": r["material"], "angle": r["angle"], "name": f"{r['material']} - {r['angle']}度"} for r in records]
