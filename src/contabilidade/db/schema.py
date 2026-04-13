import sqlite3

CURRENT_VERSION: int = 1

_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS import_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        year        INTEGER NOT NULL,
        source_type TEXT NOT NULL,
        imported_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS acoes (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        year                  INTEGER NOT NULL,
        produto               TEXT NOT NULL,
        instituicao           TEXT NOT NULL,
        conta                 TEXT NOT NULL,
        codigo_negociacao     TEXT NOT NULL,
        cnpj_empresa          TEXT NOT NULL,
        codigo_isin           TEXT NOT NULL,
        tipo                  TEXT NOT NULL,
        escriturador          TEXT NOT NULL,
        quantidade            TEXT NOT NULL,
        quantidade_disponivel TEXT NOT NULL,
        preco_fechamento      TEXT NOT NULL,
        valor_atualizado      TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS emprestimos (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        year             INTEGER NOT NULL,
        produto          TEXT NOT NULL,
        instituicao      TEXT NOT NULL,
        natureza         TEXT NOT NULL,
        numero_contrato  TEXT NOT NULL,
        taxa             TEXT NOT NULL,
        data_registro    TEXT NOT NULL,
        data_vencimento  TEXT NOT NULL,
        quantidade       TEXT NOT NULL,
        valor_atualizado TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS etfs (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        year              INTEGER NOT NULL,
        produto           TEXT NOT NULL,
        instituicao       TEXT NOT NULL,
        conta             TEXT NOT NULL,
        codigo_negociacao TEXT NOT NULL,
        cnpj_fundo        TEXT NOT NULL,
        codigo_isin       TEXT NOT NULL,
        tipo              TEXT NOT NULL,
        quantidade        TEXT NOT NULL,
        preco_fechamento  TEXT NOT NULL,
        valor_atualizado  TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fundos (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        year              INTEGER NOT NULL,
        produto           TEXT NOT NULL,
        instituicao       TEXT NOT NULL,
        conta             TEXT NOT NULL,
        codigo_negociacao TEXT NOT NULL,
        cnpj_fundo        TEXT NOT NULL,
        codigo_isin       TEXT NOT NULL,
        tipo              TEXT NOT NULL,
        administrador     TEXT NOT NULL,
        quantidade        TEXT NOT NULL,
        preco_fechamento  TEXT NOT NULL,
        valor_atualizado  TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS renda_fixa (
        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
        year                   INTEGER NOT NULL,
        produto                TEXT NOT NULL,
        instituicao            TEXT NOT NULL,
        emissor                TEXT NOT NULL,
        codigo                 TEXT NOT NULL,
        indexador              TEXT NOT NULL,
        tipo_regime            TEXT NOT NULL,
        data_emissao           TEXT NOT NULL,
        vencimento             TEXT NOT NULL,
        quantidade             TEXT NOT NULL,
        valor_atualizado_curva TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tesouro_direto (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        year             INTEGER NOT NULL,
        produto          TEXT NOT NULL,
        instituicao      TEXT NOT NULL,
        codigo_isin      TEXT NOT NULL,
        indexador        TEXT NOT NULL,
        vencimento       TEXT NOT NULL,
        quantidade       TEXT NOT NULL,
        valor_aplicado   TEXT NOT NULL,
        valor_atualizado TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS proventos (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        year          INTEGER NOT NULL,
        produto       TEXT NOT NULL,
        tipo_evento   TEXT NOT NULL,
        valor_liquido TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reembolsos (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        year          INTEGER NOT NULL,
        produto       TEXT NOT NULL,
        tipo_evento   TEXT NOT NULL,
        valor_liquido TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movimentacao (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        year           INTEGER NOT NULL,
        entrada_saida  TEXT NOT NULL,
        data           TEXT NOT NULL,
        movimentacao   TEXT NOT NULL,
        produto        TEXT NOT NULL,
        instituicao    TEXT NOT NULL,
        quantidade     TEXT,
        preco_unitario TEXT,
        valor_operacao TEXT
    )
    """,
]


def ensure_schema(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if row is None:
        # Fresh database — run all DDL
        for ddl in _DDL:
            conn.execute(ddl)
        conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)", (CURRENT_VERSION,)
        )
        conn.commit()
        return

    version_row = conn.execute("SELECT version FROM schema_version").fetchone()
    current = int(version_row["version"]) if version_row else 0

    if current < CURRENT_VERSION:
        # Run DDL idempotently (CREATE TABLE IF NOT EXISTS is safe)
        for ddl in _DDL:
            conn.execute(ddl)
        conn.execute("UPDATE schema_version SET version = ?", (CURRENT_VERSION,))
        conn.commit()
