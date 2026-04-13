import sqlite3
from decimal import Decimal

from contabilidade.db.import_log import has_movimentacao, log_import
from contabilidade.models.movimentacao import MovimentacaoReport, MovimentacaoRow


def save_movimentacao_report(
    conn: sqlite3.Connection, report: MovimentacaoReport
) -> None:
    year = report.year
    conn.execute("BEGIN")
    try:
        conn.execute("DELETE FROM movimentacao WHERE year = ?", (year,))
        conn.execute(
            "DELETE FROM import_log WHERE year = ? AND source_type = 'movimentacao'",
            (year,),
        )

        conn.executemany(
            "INSERT INTO movimentacao"
            " (year, entrada_saida, data, movimentacao, produto, instituicao,"
            "  quantidade, preco_unitario, valor_operacao)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (
                    year,
                    r.entrada_saida,
                    r.data,
                    r.movimentacao,
                    r.produto,
                    r.instituicao,
                    str(r.quantidade) if r.quantidade is not None else None,
                    str(r.preco_unitario) if r.preco_unitario is not None else None,
                    str(r.valor_operacao) if r.valor_operacao is not None else None,
                )
                for r in report.rows
            ],
        )

        log_import(conn, year, "movimentacao")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def load_movimentacao_report(
    conn: sqlite3.Connection, year: int
) -> MovimentacaoReport | None:
    if not has_movimentacao(conn, year):
        return None

    rows = [
        MovimentacaoRow(
            entrada_saida=str(r["entrada_saida"]),
            data=str(r["data"]),
            movimentacao=str(r["movimentacao"]),
            produto=str(r["produto"]),
            instituicao=str(r["instituicao"]),
            quantidade=(
                Decimal(str(r["quantidade"])) if r["quantidade"] is not None else None
            ),
            preco_unitario=(
                Decimal(str(r["preco_unitario"]))
                if r["preco_unitario"] is not None
                else None
            ),
            valor_operacao=(
                Decimal(str(r["valor_operacao"]))
                if r["valor_operacao"] is not None
                else None
            ),
        )
        for r in conn.execute(
            "SELECT * FROM movimentacao WHERE year = ? ORDER BY rowid", (year,)
        ).fetchall()
    ]

    return MovimentacaoReport(year=year, rows=rows)
