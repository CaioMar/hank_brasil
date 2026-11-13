# Transferências e consumo: primeira etapa

## O que já foi medido

As tabelas agregadas 6715 e 6974 do IBGE apresentam médias nacionais mensais familiares estimadas pela POF 2017-2018. As sete faixas são definidas por rendimento total **e variação patrimonial**, não por decis ou por renda individual. Os valores incorporam componentes monetários e não monetários. As estimativas publicadas pelo IBGE já consideram o desenho amostral; esta etapa usa as tabelas agregadas, não reprocessa os microdados nem estima intervalos de confiança.

Alimentação representa 23,76% das despesas de consumo na faixa até R$ 1.908 e 11,47% na faixa acima de R$ 23.850. Habitação representa, respectivamente, 42,20% e 34,37%. As proporções dividem a despesa média do item pela despesa média de consumo da mesma faixa. São médias agregadas, não a média das proporções individuais. Os valores e limites são da pesquisa e não foram atualizados para preços atuais. Habitação inclui componentes não monetários, portanto não equivale somente a contas pagas em dinheiro.

Isso mostra diferenças na composição do orçamento, não na propensão marginal a consumir (PMC). As faixas possuem diferentes tamanhos familiares e características; a classificação inclui variação patrimonial e pode refletir decisões da própria família. Não se pode inferir que uma transferência geraria a mesma proporção de gastos, nem calcular uma PMC subtraindo as médias de duas faixas. Não estimamos efeitos causais, multiplicadores ou impactos fiscais, e não usamos os indicadores para calibrar automaticamente o modelo.

## Próxima pergunta causal

Entre famílias elegíveis a uma transferência adicional bem definida, quanto aumenta o consumo nos meses seguintes por real recebido, em comparação com o que teria ocorrido sem o benefício? O tratamento deve especificar valor, duração e data de recebimento; os desfechos devem incluir consumo total e por categoria, além de endividamento e inflação enfrentada. A razão entre efeito no consumo e transferência recebida é uma PMC estimada para a população, prazo e política estudados, não uma constante universal.

Uma possibilidade a investigar é uma regra de elegibilidade com corte preexistente, comparando famílias imediatamente acima e abaixo desse limite. Isso só é válido se a regra e os dados existirem, se outras características forem contínuas ao redor do corte, se não houver manipulação relevante da variável de elegibilidade e se outras políticas não mudarem no mesmo ponto. Quando o recebimento não segue perfeitamente a regra, será necessária uma estratégia apropriada para adesão imperfeita e interpretação local. A POF agregada, sozinha, não permite executar esse desenho.

Alternativamente, uma expansão escalonada poderia permitir diferenças em diferenças, mas exigiria datas e critérios de adoção verificáveis, grupos comparáveis, tendências prévias plausíveis e cuidado com antecipação e efeitos sobre famílias não tratadas. Nenhuma regra específica ou acesso a dados vinculados foi ainda confirmado. Antes de escolher um desenho, será necessário avaliar dados administrativos e pesquisas disponíveis, documentação, acesso seguro e proteção de dados pessoais.

## Critérios antes de simular políticas

- Definir o contrafactual, os critérios de elegibilidade, a população e o horizonte antes da estimação.
- Documentar dados, pesos, amostragem, disponibilidade temporal, perda de observações, incerteza e fontes potenciais de viés.
- Examinar equilíbrio nas características anteriores, eventuais efeitos antecipados, manipulação do corte ou tendências prévias, conforme o desenho escolhido; testar especificações e grupos alternativos.
- Distinguir estimativa local de efeito nacional e avaliar limites para sua aplicação a outras populações e períodos.
- Comparar cenários com e sem transferência em um modelo com balanços e mecanismos estimados, reportando também inflação, emprego, arrecadação e dívida; uma PMC isolada não é o multiplicador fiscal.

## Reprodução

```bash
python -m src.etl.pof
MPLBACKEND=Agg python -m src.relatorio.grafico_pof
```

As tabelas oficiais podem ser consultadas em [SIDRA 6715](https://sidra.ibge.gov.br/tabela/6715) e [SIDRA 6974](https://sidra.ibge.gov.br/tabela/6974). O coletor consulta a API de agregados do IBGE e produz `docs/pof-2017-2018.csv`; o gráfico é salvo em `docs/grafico-pof.png`. O arquivo HTML contém valores textuais que devem ser conferidos novamente se a fonte for revisada.