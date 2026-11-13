# Plano para tornar o modelo mais convincente

O objetivo é construir um modelo que possa **ganhar ou perder uma comparação justa**, não apenas confirmar uma tese. O trabalho está organizado em cinco etapas, com resultados verificáveis em cada uma.

## Progresso

- **Diagnóstico parcialmente concluído:** relatórios e auditorias mensais para [2015–2018](data/sgs/diagnostico.md) e [2023–2025](data/sgs_2023_2025/diagnostico.md), com erros, gráficos e decomposição da dívida simulada. As janelas usam Selic realizada, portanto não são testes fora da amostra.
- **Contabilidade em andamento:** um [protótipo SFC separado](ESTUDO_SFC.md) fecha os fluxos agregados de uma economia fechada simplificada sem normalizar a riqueza. Ainda não há setores bancário e externo, limites de crédito nem balanços completos; o motor original continua com os problemas identificados na auditoria.
- **Microdados, calibração estrutural e comparação com Focus pendentes:** dependem de fontes e critérios de identificação, datas de divulgação, balanços corrigidos e protocolo de validação comparável.
- **Primeira evidência distributiva:** tabelas agregadas da POF 2017–2018 mostram a composição do consumo por faixa familiar. O [protocolo de transferências](ESTUDO_TRANSFERENCIAS.md) separa esse resultado descritivo da futura identificação causal; microdados e uma regra de elegibilidade verificável ainda não foram obtidos.

## 1. Diagnóstico do protótipo

- Gerar um relatório do exercício 2015–2018 com gráficos, erros mensais e decomposição da dívida entre juros, resultado primário e crescimento nominal.
- Auditar os fluxos entre famílias e governo, incluindo impostos, transferências e juros. Identificar os ajustes que hoje impedem o fechamento contábil.
- Registrar hipóteses, unidades e limitações, distinguindo valores observados de parâmetros arbitrados.

**Critério de saída:** qualquer resultado pode ser reproduzido e suas diferenças contábeis estão medidas e explicadas.

## 2. Dados e microeconomia

- Organizar séries históricas de atividade, preços, juros, contas públicas e câmbio, com fonte, frequência, revisões e datas de divulgação.
- Incorporar microdados do IBGE com pesos amostrais e documentação das transformações.
- Estimar a heterogeneidade de renda e consumo sem confundir consumo observado com PMC: a resposta a uma renda adicional exige identificação específica ou hipóteses explícitas.

**Critério de saída:** conjuntos de dados versionados e calibrações reproduzíveis, com incertezas documentadas.

## 3. Modelo e calibração

- Corrigir os problemas contábeis identificados antes de ajustar parâmetros; manter o núcleo vetorizado e diferenciável.
- Calibrar apenas parâmetros identificáveis pelos dados disponíveis. Para os demais, usar faixas explícitas e análise de sensibilidade.
- Testar cenários de juros, gastos e tributação, incluindo hipóteses alternativas para câmbio e reservas.

**Critério de saída:** balanços fecham dentro de tolerância definida e os resultados não dependem de uma única escolha arbitrária de parâmetros.

## 4. Validação justa

- Separar períodos de calibração e teste; usar apenas informações disponíveis na data de cada previsão.
- Comparar horizontes e variáveis equivalentes com o Focus e com referências simples, como a última observação disponível.
- Reportar erros médios, viés, incerteza e desempenho por período. Usar Diebold–Mariano quando houver observações suficientes e suas condições forem adequadas.

**Critério de saída:** uma tabela reproduzível mostra onde o modelo melhora, empata ou piora em relação às referências.

## 5. Conclusões públicas

- Apresentar multiplicadores, trajetórias da dívida e efeitos distributivos como **estimativas condicionais**, com intervalos e premissas.
- Separar resultados empíricos, cenários hipotéticos e posições normativas.
- Publicar também os testes que contrariem a hipótese inicial.

## Primeira entrega

Produzir o **relatório diagnóstico e a auditoria contábil de 2015–2018**. Eles mostram o que precisa ser corrigido antes de investir em calibração mais sofisticada.