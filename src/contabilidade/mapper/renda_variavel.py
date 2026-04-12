from contabilidade.models.b3 import EmprestimoPosition
from contabilidade.models.dirpf import RendaVariavelNota


def map_renda_variavel(
    emprestimos: list[EmprestimoPosition], year: int
) -> list[RendaVariavelNota]:
    notas: list[RendaVariavelNota] = []

    notas.append(
        RendaVariavelNota(
            mensagem=(
                "ATENÇÃO: O relatório consolidado anual da B3 contém apenas a posição em "
                "31/12 do ano. Ele NÃO contém o histórico de compras e vendas realizadas "
                "durante o ano.\n\n"
                "Para preencher a seção de Renda Variável na DIRPF, você precisará do "
                "extrato mensal de operações (Nota de Corretagem) ou do demonstrativo de "
                "operações da sua corretora.\n\n"
                "Regras gerais para Renda Variável (Ações):\n"
                "  - Ganho mensal líquido tributado à alíquota de 15% (operações comuns)\n"
                "  - Day Trade: tributado à alíquota de 20%\n"
                "  - Isenção: vendas de ações cujo total no mês não ultrapasse R$ 20.000,00\n"
                "  - Prejuízos podem ser compensados com ganhos de meses seguintes\n"
                "  - IRRF de 0,005% (operações normais) e 1% (day trade) é compensável"
            )
        )
    )

    doador_positions = [e for e in emprestimos if "doador" in e.natureza.lower()]
    if doador_positions:
        linhas = []
        for pos in doador_positions:
            ticker, _ = _ticker_from_produto(pos.produto)
            linhas.append(
                f"  - {ticker}: {pos.quantidade} cotas emprestadas, "
                f"vencimento {pos.data_vencimento}, taxa {pos.taxa}% a.m."
            )
        posicoes_str = "\n".join(linhas)
        notas.append(
            RendaVariavelNota(
                mensagem=(
                    f"Posições em Empréstimo (BTC) como Doador em 31/12/{year}:\n"
                    f"{posicoes_str}\n\n"
                    "Nota: Estas ações continuam sendo suas e devem ser declaradas em "
                    "Bens e Direitos. Os reembolsos recebidos pelo aluguel estão listados "
                    "na seção de Rendimentos Exclusivos."
                )
            )
        )

    return notas


def _ticker_from_produto(produto: str) -> tuple[str, str]:
    parts = produto.split(" - ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return produto.strip(), produto.strip()
