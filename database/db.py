import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reagent.db')

_conn = None


def get_conn():
    """获取数据库连接"""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def close_conn():
    """关闭数据库连接"""
    global _conn
    if _conn:
        _conn.close()
        _conn = None


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS reagent_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reagent_name TEXT NOT NULL,
            batch_no TEXT NOT NULL UNIQUE,
            specification TEXT,
            unit TEXT NOT NULL,
            total_quantity REAL NOT NULL,
            remaining_quantity REAL NOT NULL,
            production_date TEXT,
            expiry_date TEXT,
            supplier TEXT,
            storage_condition TEXT,
            is_hazardous INTEGER DEFAULT 0,
            hazard_level TEXT,
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS outbound_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            project_id INTEGER,
            project_name TEXT,
            receiver TEXT NOT NULL,
            outbound_date TEXT DEFAULT (datetime('now','localtime')),
            purpose TEXT,
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (batch_id) REFERENCES reagent_batches(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_name TEXT NOT NULL UNIQUE,
            level_rank INTEGER NOT NULL UNIQUE,
            monthly_quota REAL NOT NULL DEFAULT 0,
            hazardous_quota REAL NOT NULL DEFAULT 0,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS project_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL UNIQUE,
            level_id INTEGER NOT NULL,
            current_quota REAL NOT NULL DEFAULT 0,
            current_hazardous_quota REAL NOT NULL DEFAULT 0,
            used_quota REAL NOT NULL DEFAULT 0,
            used_hazardous_quota REAL NOT NULL DEFAULT 0,
            quota_month TEXT,
            leader TEXT,
            contact TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (level_id) REFERENCES project_levels(id)
        );

        CREATE TABLE IF NOT EXISTS level_change_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            old_level_id INTEGER,
            new_level_id INTEGER NOT NULL,
            old_quota REAL,
            new_quota REAL,
            carry_over_type TEXT NOT NULL,
            carry_over_amount REAL DEFAULT 0,
            operator TEXT,
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (project_id) REFERENCES project_groups(id)
        );

        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            operator TEXT DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS hazardous_qualifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_name TEXT,
            qualification_type TEXT NOT NULL,
            certificate_no TEXT NOT NULL,
            issue_date TEXT,
            expiry_date TEXT,
            issuing_authority TEXT,
            holder_name TEXT,
            holder_id_card TEXT,
            status TEXT DEFAULT 'valid',
            remark TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_batch_no ON reagent_batches(batch_no);
        CREATE INDEX IF NOT EXISTS idx_outbound_batch ON outbound_records(batch_id);
        CREATE INDEX IF NOT EXISTS idx_outbound_project ON outbound_records(project_id);
        CREATE INDEX IF NOT EXISTS idx_log_module ON operation_logs(module);
        CREATE INDEX IF NOT EXISTS idx_qual_project ON hazardous_qualifications(project_id);
    ''')

    conn.commit()
    _migrate_db(conn)
    _init_seed_data()


def _migrate_db(conn):
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE level_change_logs ADD COLUMN old_hazardous_quota REAL')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE level_change_logs ADD COLUMN new_hazardous_quota REAL')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE level_change_logs ADD COLUMN carry_over_hazardous_amount REAL DEFAULT 0')
    except Exception:
        pass
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outbound_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                reagent_name TEXT,
                batch_no TEXT,
                quantity REAL NOT NULL,
                unit TEXT,
                project_id INTEGER NOT NULL,
                project_name TEXT,
                receiver TEXT,
                outbound_date TEXT,
                purpose TEXT,
                remark TEXT,
                is_hazardous INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                requested_amount REAL DEFAULT 0,
                remaining_quota REAL DEFAULT 0,
                quota_shortage REAL DEFAULT 0,
                applicant TEXT,
                approval_note TEXT,
                approved_by TEXT,
                approved_at TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (batch_id) REFERENCES reagent_batches(id),
                FOREIGN KEY (project_id) REFERENCES project_groups(id)
            )
        ''')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE outbound_approvals ADD COLUMN approval_note TEXT')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE outbound_approvals ADD COLUMN approved_by TEXT')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE outbound_approvals ADD COLUMN approved_at TEXT')
    except Exception:
        pass
    conn.commit()


def _init_seed_data():
    """初始化种子数据"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM project_levels')
    count = cursor.fetchone()['count']
    if count == 0:
        levels = [
            ('A级', 1, 50000, 5000, '重点项目组，额度最高'),
            ('B级', 2, 30000, 3000, '普通项目组'),
            ('C级', 3, 15000, 1000, '新立项项目组'),
            ('D级', 4, 5000, 0, '临时项目组，无危化品额度')
        ]
        cursor.executemany(
            'INSERT INTO project_levels (level_name, level_rank, monthly_quota, hazardous_quota, description) VALUES (?, ?, ?, ?, ?)',
            levels
        )

    cursor.execute('SELECT COUNT(*) as count FROM project_groups')
    count = cursor.fetchone()['count']
    if count == 0:
        cursor.execute("SELECT id FROM project_levels WHERE level_name = 'A级'")
        level_a = cursor.fetchone()['id']
        cursor.execute("SELECT id FROM project_levels WHERE level_name = 'B级'")
        level_b = cursor.fetchone()['id']
        cursor.execute("SELECT id FROM project_levels WHERE level_name = 'C级'")
        level_c = cursor.fetchone()['id']

        projects = [
            ('肿瘤标志物检测组', level_a, 50000, 5000, '2026-06', '张博士', '13800138001'),
            ('生化免疫组', level_b, 30000, 3000, '2026-06', '李主任', '13800138002'),
            ('微生物检测组', level_b, 30000, 3000, '2026-06', '王主管', '13800138003'),
            ('分子诊断组', level_c, 15000, 1000, '2026-06', '陈研究员', '13800138004')
        ]
        cursor.executemany(
            'INSERT INTO project_groups (group_name, level_id, current_quota, current_hazardous_quota, quota_month, leader, contact) VALUES (?, ?, ?, ?, ?, ?, ?)',
            projects
        )

    conn.commit()


def add_operation_log(module, action, detail, operator='system'):
    """添加操作日志"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO operation_logs (module, action, detail, operator) VALUES (?, ?, ?, ?)',
        (module, action, detail, operator)
    )
    conn.commit()
