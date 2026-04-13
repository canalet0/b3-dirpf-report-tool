import sqlite3
from decimal import Decimal

from contabilidade.db.import_log import has_b3_report, log_import
from contabilidade.models.b3 import (
    AcaoPosition,
    B3Report,
    EmprestimoPosition,
    EtfPosition,
    FundoPosition,
    Provento,
    Reembolso,
    RendaFixaPosition,
    TesouroDiretoPosition,
)

_B3_TABLES = [
    "acoes",
    "emprestimos",
    "etfs",
    "fundos",
    "renda_fixa",
    "tesouro_direto",
    "proventos",
    "reembolsos",
]


def save_b3_report(conn: sqlite3.Connection, report: B3Report) -> None:
    year = report.year
    conn.execute("BEGIN")
    try:
        for table in _B3_TABLES:
            conn.execute(f"DELETE FROM {table} WHERE year = ?", (year,))
        conn.execute(
            "DELETE FROM import_log WHERE year = ? AND source_type = 'b3_report'",
            (year,),
        )

        conn.executemany(
            "INSERT INTO acoes (year, produto, instituicao, conta, codigo_negociacao,"
            " cnpj_empresa, codigo_isin, tipo, escriturador, quantidade,"
            " quantidade_disponivel, preco_fechamento, valor_atualizado)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    a.produto,
                    a.instituicao,
                    a.conta,
                    a.codigo_negociacao,
                    a.cnpj_empresa,
                    a.codigo_isin,
                    a.tipo,
                    a.escriturador,
                    str(a.quantidade),
                    str(a.quantidade_disponivel),
                    str(a.preco_fechamento),
                    str(a.valor_atualizado),
                )
                for a in report.acoes
            ],
        )

        conn.executemany(
            "INSERT INTO emprestimos (year, produto, instituicao, natureza, numero_contrato,"
            " taxa, data_registro, data_vencimento, quantidade, valor_atualizado)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    e.produto,
                    e.instituicao,
                    e.natureza,
                    e.numero_contrato,
                    str(e.taxa),
                    e.data_registro,
                    e.data_vencimento,
                    str(e.quantidade),
                    str(e.valor_atualizado),
                )
                for e in report.emprestimos
            ],
        )

        conn.executemany(
            "INSERT INTO etfs (year, produto, instituicao, conta, codigo_negociacao,"
            " cnpj_fundo, codigo_isin, tipo, quantidade, preco_fechamento, valor_atualizado)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    e.produto,
                    e.instituicao,
                    e.conta,
                    e.codigo_negociacao,
                    e.cnpj_fundo,
                    e.codigo_isin,
                    e.tipo,
                    str(e.quantidade),
                    str(e.preco_fechamento),
                    str(e.valor_atualizado),
                )
                for e in report.etfs
            ],
        )

        conn.executemany(
            "INSERT INTO fundos (year, produto, instituicao, conta, codigo_negociacao,"
            " cnpj_fundo, codigo_isin, tipo, administrador, quantidade,"
            " preco_fechamento, valor_atualizado)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    f.produto,
                    f.instituicao,
                    f.conta,
                    f.codigo_negociacao,
                    f.cnpj_fundo,
                    f.codigo_isin,
                    f.tipo,
                    f.administrador,
                    str(f.quantidade),
                    str(f.preco_fechamento),
                    str(f.valor_atualizado),
                )
                for f in report.fundos
            ],
        )

        conn.executemany(
            "INSERT INTO renda_fixa (year, produto, instituicao, emissor, codigo,"
            " indexador, tipo_regime, data_emissao, vencimento, quantidade,"
            " valor_atualizado_curva)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    r.produto,
                    r.instituicao,
                    r.emissor,
                    r.codigo,
                    r.indexador,
                    r.tipo_regime,
                    r.data_emissao,
                    r.vencimento,
                    str(r.quantidade),
                    str(r.valor_atualizado_curva),
                )
                for r in report.renda_fixa
            ],
        )

        conn.executemany(
            "INSERT INTO tesouro_direto (year, produto, instituicao, codigo_isin,"
            " indexador, vencimento, quantidade, valor_aplicado, valor_atualizado)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    t.produto,
                    t.instituicao,
                    t.codigo_isin,
                    t.indexador,
                    t.vencimento,
                    str(t.quantidade),
                    str(t.valor_aplicado),
                    str(t.valor_atualizado),
                )
                for t in report.tesouro_direto
            ],
        )

        conn.executemany(
            "INSERT INTO proventos (year, produto, tipo_evento, valor_liquido)"
            " VALUES (?,?,?,?)",
            [
                (year, p.produto, p.tipo_evento, str(p.valor_liquido))
                for p in report.proventos
            ],
        )

        conn.executemany(
            "INSERT INTO reembolsos (year, produto, tipo_evento, valor_liquido)"
            " VALUES (?,?,?,?)",
            [
                (year, r.produto, r.tipo_evento, str(r.valor_liquido))
                for r in report.reembolsos
            ],
        )

        log_import(conn, year, "b3_report")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def load_b3_report(conn: sqlite3.Connection, year: int) -> B3Report | None:
    if not has_b3_report(conn, year):
        return None

    acoes = [
        AcaoPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            conta=str(r["conta"]),
            codigo_negociacao=str(r["codigo_negociacao"]),
            cnpj_empresa=str(r["cnpj_empresa"]),
            codigo_isin=str(r["codigo_isin"]),
            tipo=str(r["tipo"]),
            escriturador=str(r["escriturador"]),
            quantidade=Decimal(str(r["quantidade"])),
            quantidade_disponivel=Decimal(str(r["quantidade_disponivel"])),
            preco_fechamento=Decimal(str(r["preco_fechamento"])),
            valor_atualizado=Decimal(str(r["valor_atualizado"])),
        )
        for r in conn.execute(
            "SELECT * FROM acoes WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    emprestimos = [
        EmprestimoPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            natureza=str(r["natureza"]),
            numero_contrato=str(r["numero_contrato"]),
            taxa=Decimal(str(r["taxa"])),
            data_registro=str(r["data_registro"]),
            data_vencimento=str(r["data_vencimento"]),
            quantidade=Decimal(str(r["quantidade"])),
            valor_atualizado=Decimal(str(r["valor_atualizado"])),
        )
        for r in conn.execute(
            "SELECT * FROM emprestimos WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    etfs = [
        EtfPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            conta=str(r["conta"]),
            codigo_negociacao=str(r["codigo_negociacao"]),
            cnpj_fundo=str(r["cnpj_fundo"]),
            codigo_isin=str(r["codigo_isin"]),
            tipo=str(r["tipo"]),
            quantidade=Decimal(str(r["quantidade"])),
            preco_fechamento=Decimal(str(r["preco_fechamento"])),
            valor_atualizado=Decimal(str(r["valor_atualizado"])),
        )
        for r in conn.execute(
            "SELECT * FROM etfs WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    fundos = [
        FundoPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            conta=str(r["conta"]),
            codigo_negociacao=str(r["codigo_negociacao"]),
            cnpj_fundo=str(r["cnpj_fundo"]),
            codigo_isin=str(r["codigo_isin"]),
            tipo=str(r["tipo"]),
            administrador=str(r["administrador"]),
            quantidade=Decimal(str(r["quantidade"])),
            preco_fechamento=Decimal(str(r["preco_fechamento"])),
            valor_atualizado=Decimal(str(r["valor_atualizado"])),
        )
        for r in conn.execute(
            "SELECT * FROM fundos WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    renda_fixa = [
        RendaFixaPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            emissor=str(r["emissor"]),
            codigo=str(r["codigo"]),
            indexador=str(r["indexador"]),
            tipo_regime=str(r["tipo_regime"]),
            data_emissao=str(r["data_emissao"]),
            vencimento=str(r["vencimento"]),
            quantidade=Decimal(str(r["quantidade"])),
            valor_atualizado_curva=Decimal(str(r["valor_atualizado_curva"])),
        )
        for r in conn.execute(
            "SELECT * FROM renda_fixa WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    tesouro_direto = [
        TesouroDiretoPosition(
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            codigo_isin=str(r["codigo_isin"]),
            indexador=str(r["indexador"]),
            vencimento=str(r["vencimento"]),
            quantidade=Decimal(str(r["quantidade"])),
            valor_aplicado=Decimal(str(r["valor_aplicado"])),
            valor_atualizado=Decimal(str(r["valor_atualizado"])),
        )
        for r in conn.execute(
            "SELECT * FROM tesouro_direto WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    proventos = [
        Provento(
            produto=str(r["produto"]),
            tipo_evento=str(r["tipo_evento"]),
            valor_liquido=Decimal(str(r["valor_liquido"])),
        )
        for r in conn.execute(
            "SELECT * FROM proventos WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    reembolsos = [
        Reembolso(
            produto=str(r["produto"]),
            tipo_evento=str(r["tipo_evento"]),
            valor_liquido=Decimal(str(r["valor_liquido"])),
        )
        for r in conn.execute(
            "SELECT * FROM reembolsos WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    return B3Report(
        year=year,
        acoes=acoes,
        emprestimos=emprestimos,
        etfs=etfs,
        fundos=fundos,
        renda_fixa=renda_fixa,
        tesouro_direto=tesouro_direto,
        proventos=proventos,
        reembolsos=reembolsos,
    )
