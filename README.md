# contabilidade

Ferramenta de linha de comando que lê o **Relatório Consolidado Anual** da B3 (baixado em [investidor.b3.com.br](https://www.investidor.b3.com.br)) e gera um relatório em Markdown com as instruções exatas de preenchimento da **DIRPF** (Declaração de Imposto de Renda Pessoa Física).

## Pré-requisitos

- Python 3.11+
- `make`

## Instalação

```bash
make install
```

## Uso

```bash
python -m contabilidade report YEAR --file PATH [--output PATH]
```

**Exemplos:**

```bash
# Exibe o relatório no terminal
python -m contabilidade report 2024 --file samples/relatorio-consolidado-anual-2024.xlsx

# Salva o relatório em arquivo
python -m contabilidade report 2024 \
  --file samples/relatorio-consolidado-anual-2024.xlsx \
  --output relatorio-dirpf-2024.md
```

## O que o relatório gera

O relatório é organizado nas seções da DIRPF:

### Bens e Direitos

Para cada ativo em carteira, o relatório informa o **Grupo**, o **Código** e a **Discriminação** prontos para copiar no programa da Receita Federal:

| Tipo de ativo | Grupo | Código |
|---|---|---|
| Ações | 03 | 01 |
| ETFs (Fundos de Índice) | 07 | 09 |
| Fundos de Investimento / FII | 07 | 03 |
| CDB, LCI, LCA, LIG | 04 | 02 |
| Debêntures | 04 | 03 |
| Tesouro Direto | 04 | 04 |

> **Situação em 31/12 do ano anterior** é sempre marcada como `[PREENCHER COM O VALOR DECLARADO NA DIRPF DO ANO ANTERIOR]` — o relatório consolidado da B3 contém apenas o saldo atual, sem dados do ano anterior.

### Rendimentos Isentos e Não Tributáveis

- **Linha 09** — Dividendos recebidos (acumulados por ticker)
- **Linha 26** — Rendimentos de FII (isentos para pessoa física conforme Lei 9.779/99)

### Rendimentos Sujeitos à Tributação Exclusiva/Definitiva

- **Linha 10** — Juros sobre Capital Próprio (IR já retido na fonte a 15%)
- Reembolsos do programa de aluguel de ações (BTC)

### Renda Variável

Orientações sobre como preencher a seção de Renda Variável, incluindo as posições abertas no programa de aluguel (BTC) como Doador.

> O relatório consolidado anual **não contém histórico de operações**. Para calcular o ganho de capital mensal é necessário o extrato de operações (notas de corretagem) da corretora.

## Exemplo de saída

```markdown
## BENS E DIREITOS

### Grupo 03, Código 01 — Ações

> Em Bens e Direitos, adicione um item para cada entrada abaixo selecionando Grupo 03 > Código 01.

---
**CNPJ:** 61.532.644/0001-15
**Discriminação:**
> QUANTIDADE: 143.85 ações de ITAUSA S.A. (ITSA4 PN), CNPJ 61.532.644/0001-15,
> custodiadas em INTER DISTRIBUIDORA DE TITULOS E VALORES MOBILIARIOS LTDA, conta 1534751.
> Código ISIN: BRITSAACNPR7. Preço de fechamento em 31/12/2024: R$ 8,83.
> Valor de mercado em 31/12/2024: R$ 1.270,19.

- Situação em 31/12/2023: R$ 0,00  *(preencher com valor da DIRPF anterior)*
- Situação em 31/12/2024: **R$ 1.270,19**

...

## RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS

### Linha 09 — Lucros e dividendos recebidos

| Produto | Valor Líquido |
|---------|---------------|
| ITSA4   | R$ 41,16      |
| VALE3   | R$ 19,16      |
| **TOTAL** | **R$ 60,32** |
```

## Avisos

- Este relatório é uma **guia** baseada nos dados exportados da B3. Verifique os valores com seu contador antes de enviar a DIRPF.
- Os valores de **Situação em 31/12 do ano anterior** precisam ser preenchidos manualmente com os valores declarados na DIRPF do exercício anterior.
- Arquivos `.xlsx` de anos anteriores a 2021 podem estar vazios ou incompletos.

## Desenvolvimento

```bash
make test        # roda todos os testes
make test-unit   # apenas testes unitários
make lint        # black + pylint + mypy
```
