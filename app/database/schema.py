"""SQLite şema tanımları.

Kamera şifreleri bu şemada SAKLANMAZ: yalnızca kullanıcı adı ve bağlantı
bilgileri tutulur, parola app.utils.credentials üzerinden işletim
sisteminin kimlik bilgisi deposuna (Windows Credential Manager / Linux
geliştirmede şifreli dosya yedeği) yazılır.
"""

SCHEMA_STATEMENTS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        host TEXT NOT NULL,
        port INTEGER NOT NULL DEFAULT 554,
        main_path TEXT NOT NULL DEFAULT '',
        sub_path TEXT NOT NULL DEFAULT '',
        username TEXT NOT NULL DEFAULT '',
        credential_ref TEXT NOT NULL,
        transport TEXT NOT NULL DEFAULT 'tcp',
        location TEXT NOT NULL DEFAULT '',
        enabled INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'disconnected',
        last_status_at TEXT,
        last_error TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS authorized_vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_normalized TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL DEFAULT '',
        permission_status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_id INTEGER NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
        plate_raw TEXT NOT NULL,
        plate_normalized TEXT NOT NULL,
        detection_confidence REAL NOT NULL,
        ocr_confidence REAL NOT NULL,
        image_path TEXT,
        is_authorized INTEGER NOT NULL DEFAULT 0,
        needs_review INTEGER NOT NULL DEFAULT 0,
        review_status TEXT NOT NULL DEFAULT 'pending',
        detected_at TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_detections_plate ON detections(plate_normalized)",
    "CREATE INDEX IF NOT EXISTS idx_detections_camera ON detections(camera_id)",
    "CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at)",
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'operator',
        full_name TEXT NOT NULL DEFAULT '',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_login_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS application_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL DEFAULT '',
        entity_id TEXT NOT NULL DEFAULT '',
        details TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)",
]
