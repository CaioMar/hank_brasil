# Simulação HANK Brasil

## Instalação e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
MPLBACKEND=Agg python simulacao_hank_brasil.py
```

O script executa dois cenários de 48 meses com um milhão de agentes e gera `comparativo_hank_brasil.png`.

## Página de resultados

A página estática em `docs/index.html` apresenta o exercício histórico e suas limitações. Para atualizar o gráfico depois de gerar o backtest:

```bash
MPLBACKEND=Agg python src/relatorio/grafico_divida.py
```

Os valores textuais da página descrevem a execução de 2015–2018 com 100 mil agentes e devem ser atualizados separadamente se a janela ou os resultados mudarem.

Para reproduzir os gráficos e o CSV das contas públicas de 2015–2025:

```bash
MPLBACKEND=Agg python -m src.relatorio.grafico_contas_publicas
```

O comando baixa as séries SGS 5793, 5760 e 5727 (necessidades de financiamento do setor público consolidado, sem desvalorização cambial, acumuladas em 12 meses como % do PIB), 432 (meta Selic) e 1207 (PIB anual em reais), além da tabela 2.1 da série histórica do Tesouro de julho de 2026 (receita líquida e despesa primária do governo central, em R$ milhões). Divide esses valores pelo PIB anual, verifica a identidade entre resultado nominal, primário e juros e gera os gráficos e o CSV em `docs/`. Os recortes e métodos do Tesouro e do Banco Central são diferentes e não devem ser somados. Séries históricas podem ser revisadas; a narrativa e a tabela HTML precisam ser atualizadas separadamente após regenerar os dados.

A primeira análise descritiva das famílias usa tabelas agregadas da POF 2017–2018, não microdados nem estimativas causais. Fontes, reprodução e protocolo para uma futura avaliação de transferências estão em [ESTUDO_TRANSFERENCIAS.md](ESTUDO_TRANSFERENCIAS.md).

## Calibração e comparação histórica

```bash
python -m src.etl.sgs --inicio 2015-01 --fim 2018-12 --agentes 100000 --saida data/sgs
MPLBACKEND=Agg python -m src.relatorio.diagnostico --dados data/sgs --agentes 100000 --saida data/sgs
python -m unittest discover -s tests
```

O módulo consulta a API pública do SGS por ano. Usa a última observação de cada mês para a Selic meta anual (% a.a., série 432), PTAX de venda (R$/US$, 1) e reservas internacionais no conceito de liquidez (US$ milhões, 13621); usa o IPCA mensal (%, 433) e a dívida bruta do governo geral (% do PIB, 13762) mensal. Exige meses encerrados, dados completos e onze meses anteriores de IPCA para compor a inflação de 12 meses. Os arquivos `historico_bruto.parquet` (incluindo os meses anteriores de IPCA), `historico_mensal.parquet`, `parametros.json` e `backtest.parquet` são sobrescritos no diretório de saída.

O primeiro mês fixa o estado inicial: PIB real = 100, dívida e riqueza financeira agregada iguais à dívida/PIB, Selic em fração anual, IPCA acumulado em 12 meses em fração, câmbio em R$/US$ e reservas em US$ bilhões. Na ausência de série para o custo efetivo legado, assume-se a Selic inicial para ele; a referência cambial inicial também é a Selic inicial. As demais elasticidades, distribuição sintética, participação de LFT de 55% e política fiscal inicial continuam sendo hipóteses do modelo, não parâmetros estimados pelo SGS.

A simulação começa no mês seguinte e usa a trajetória histórica de Selic, sem choques de gastos, impostos ou uso de reservas. O resultado compara a dívida/PIB, a inflação anualizada instantânea do modelo e o câmbio com a dívida observada, IPCA acumulado em 12 meses e PTAX. Essas medidas de inflação não são idênticas. Não se trata de previsão fora da amostra: usa Selic futura realizada e dados atuais do SGS, sujeitos a revisões. Observações mensais são associadas ao mês de referência, mas suas datas de divulgação não são verificadas; não há garantia de disponibilidade em tempo real no mês inicial. A comparação é exploratória, não estima elasticidades nem valida causalidade ou consistência fluxo-estoque do motor.

O diagnóstico reproduz a simulação salva, verifica parâmetros e número de agentes, e gera relatório, gráficos e auditoria mensal. A auditoria evidencia ajustes artificiais de riqueza e fluxos sem contrapartida explícita: o motor atual **não demonstra consistência fluxo-estoque**.

## Protótipo contábil experimental

O módulo separado `src/models/sfc.py` testa identidades de uma economia fechada simplificada, sem reescalar ativos. As premissas, resultados, limitações e comandos para reproduzir duas hipóteses estão em [ESTUDO_SFC.md](ESTUDO_SFC.md). Ele ainda não substitui nem valida o motor original.