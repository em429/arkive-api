CREATE TABLE webpage (
    [timestamp] DATE DEFAULT (datetime('now', 'utc')),
    [url] TEXT UNIQUE NOT NULL,
    [wayback_url] TEXT DEFAULT NULL
    -- [original_title] TEXT NOT NULL,
    -- [freeze_dried?] BOOLEAN NOT NULL CHECK (solo in (0, 1)),
    -- [freezedry_path] TEXT DEFAULT NULL,
);
