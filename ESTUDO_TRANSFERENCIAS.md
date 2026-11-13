# Transferências e consumo: primeira etapa

## O que já foi medido

As tabelas agregadas 6715 e 6974 do IBGE apresentam médias nacionais mensais familiares estimadas pela POF 2017-2018. As sete faixas são definidas por rendimento total **e variação patrimonial**, não por decis ou por renda individual. Os valores incorporam componentes monetários e não monetários. As estimativas publicadas pelo IBGE já consideram o desenho amostral; esta etapa usa as tabelas agregadas, não reprocessa os microdados nem estima intervalos de confiança.

Alimentação representa 23,76% das despesas de consumo na faixa até R$ 1.908 e 11,47% na faixa acima de R$ 23.850. Habitação representa, respectivamente, 42,20% e 34,37%. As proporções dividem a despesa média do item pela despesa média de consumo da mesma faixa. São médias agregadas, não a média das proporções individuais. Os valores e limites são da pesquisa e não foram atualizados para preços atuais. Habitação inclui componentes não monetários, portanto não equivale somente a contas pagas em dinheiro.

Isso mostra diferenças na composição do orçamento, não na propensão marginal a consumir (PMC). As faixas possuem diferentes tamanhos familiares e características; a classificação inclui variação patrimonial e pode refletir decisões da própria família. Não se pode inferir que uma transferência geraria a mesma proporção de gastos, nem calcular uma PMC subtraindo as médias de duas faixas. Não estimamos efeitos causais, multiplicadores ou impactos fiscais, e não usamos os indicadores para calibrar automaticamente o modelo.

## Próxima pergunta causal

Entre famílias elegíveis a uma transferência adicional bem definida, quanto aumenta o consumo nos meses seguintes por real recebido, em comparação com o que teria ocorrido sem o benefício? O tratamento deve especificar valor, duração e data de recebimento; os desfechos devem incluir consumo total e por categoria, além de endividamento e inflação enfrentada. A razão entre efeito no consumo e transferência recebida é uma PMC estimada para a população, prazo e política estudados, não uma constante universal.

Uma possibilidade a investigar é uma regra de elegibilidade com corte preexistente, comparando famílias imediatamente acima e abaixo desse limite. Isso só é válido se a regra e os dados existirem, se outras características forem contínuas ao redor do corte, se não houver manipulação relevante da variável de elegibilidade e se outras políticas não mudarem no mesmo ponto. Quando o recebimento não segue perfeitamente a regra, será necessária uma estratégia apropriada para adesão imperfeita e interpretação local. A POF agregada, sozinha, não permite executar esse desenho.

Alternativamente, uma expansão escalonada poderia permitir diferenças em diferenças, mas exigiria datas e critérios de adoção verificáveis, grupos comparáveis, tendências prévias plausíveis e cuidado com antecipação e efeitos sobre famílias não tratadas. Nenhuma regra específica ou acesso a dados vinculados foi ainda confirmado. Antes de escolher um desenho, será necessário avaliar dados administrativos e pesquisas disponíveis, documentação, acesso seguro e proteção de dados pessoais.

## Viabilidade: PNAD COVID-19 e auxílio em 2020

Os [microdados mensais públicos do IBGE](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_PNAD_COVID19/Microdados/Dados/) cobrem maio a novembro de 2020. O [dicionário de maio](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_PNAD_COVID19/Microdados/Documentacao/Dicionario_PNAD_COVID_052020_20220621.xls) identifica D0051 como recebimento de auxílios emergenciais relacionados ao coronavírus e D0053 como somatório recebido pelos moradores. Essa pergunta não distingue necessariamente o Auxílio Emergencial federal de todos os demais auxílios relacionados à pandemia. A série não pode ser interpretada como beneficiários únicos de um programa específico.

Para cada mês, selecionamos a pessoa responsável pelo domicílio (A001A = 01), verificamos unicidade por UF, UPA e V1008 e somamos o peso domiciliar V1032 dos registros com D0051 = 1. O denominador é a soma dos pesos com resposta conhecida (1 ou 2); respostas ausentes são contadas e excluídas do denominador. Os sete arquivos analisados não têm respostas ausentes entre responsáveis. Em maio, a estimativa é 26,30 milhões de domicílios e 38,67% dos domicílios com resposta conhecida; em novembro, 28,11 milhões e 40,96%. São estimativas pontuais, não valores administrativos nem contagens de pessoas.

Em uma auditoria do arquivo de maio, cada domicílio tinha exatamente um responsável e D0051 não divergia entre os moradores. Isso não substitui a estimação de incerteza com estratos, unidades primárias de amostragem e o desenho apropriado. Não calculamos intervalos, nem concluímos que diferenças entre meses sejam estatisticamente significativas. Comparações mensais tampouco identificam o efeito do auxílio: a crise e outras políticas ocorreram simultaneamente, as condições de elegibilidade mudaram e composição e não resposta podem variar.

**Decisão de viabilidade:** a PNAD COVID fornece recebimento amplo de auxílios e variáveis de trabalho e rendimento, mas não a despesa de consumo familiar necessária para estimar a PMC. Começa após o início da pandemia, e renda observada após a crise ou o auxílio não deve ser tratada automaticamente como renda anterior usada na elegibilidade. A POF 2017–2018 e a PNAD COVID não foram vinculadas em nível domiciliar. Os dados aqui obtidos não permitem estimar o contrafactual proposto.

### Regra candidata e obstáculos

A [redação original da Lei 13.982/2020, art. 2º](https://www2.camara.leg.br/legin/fed/lei/2020/lei-13982-2-abril-2020-789931-publicacaooriginal-160250-pl.html), previa R$ 600 mensais inicialmente por três meses para trabalhadores que satisfizessem requisitos cumulativos, incluindo idade, trabalho, benefícios recebidos e renda tributável em 2018. A condição de renda familiar era de até meio salário mínimo por pessoa **ou** até três salários mínimos no total. A lei limitava o recebimento a dois membros por família, previa duas cotas para mulher provedora de família monoparental e substituição do Bolsa Família quando mais vantajoso. O texto previa aferição via CadÚnico ou autodeclaração, conforme o caso. Essa é a redação original, não uma afirmação de que permaneceu inalterada em todos os meses ou de que a implementação seguiu perfeitamente a regra.

A alternativa entre os dois limites é essencial: ultrapassar meio salário mínimo por pessoa não necessariamente interrompe a elegibilidade quando a renda total ainda está dentro de três salários mínimos. A definição legal de família pode diferir do domicílio observado; outras condições, valores por família, substituição de benefícios e regras posteriores também importam. Um corte somente seria candidato a uma descontinuidade se fosse efetivamente restritivo para o grupo estudado e se a elegibilidade e o recebimento mudassem ali. Não há demonstração disso nos dados disponíveis.

O próximo passo é documentar a redação aplicável à data e sua implementação efetiva, e localizar dados que associem elegibilidade anterior, recebimento específico e consumo. Um corte só será usado depois de verificar que realmente determina o tratamento, que não há outras políticas simultâneas no mesmo limiar e que os dados possibilitam os testes previstos acima. Até lá, a hipótese causal permanece aberta.

## Alternativa pública: painel por unidade da federação

O [Portal da Transparência](https://portaldatransparencia.gov.br/download-de-dados/auxilio-emergencial) anuncia downloads abertos do Auxílio Emergencial, mas seu dicionário não ficou acessível nesta consulta. Não verificamos os arquivos, campos, datas, privacidade ou possibilidade de vínculo. Uma base que conecte elegibilidade anterior, pagamento específico e consumo familiar, assim como as autorizações necessárias para acessá-la, continua não confirmada; não se deve tentar identificar pessoas usando os dados publicados aqui.

Como alternativa exploratória, a [Pesquisa Mensal de Comércio, tabela 3416](https://sidra.ibge.gov.br/tabela/3416), fornece índice de volume de vendas do varejo por unidade da federação para janeiro de 2019 a novembro de 2020. Usamos a série com ajuste sazonal, base 2014 = 100, encerrada em janeiro de 2022. O índice não representa todo o consumo familiar, pode incluir compradores que não receberam o benefício e está sujeito a revisões e a ajuste sazonal retrospectivo. Não é uma base em tempo real.

Ligamos os dados da PNAD COVID por código de UF e mês, usando a resposta domiciliar D0051 e peso V1032. O painel contém 621 linhas (27 UFs por 23 meses), das quais 189 têm auxílio observado entre maio e novembro de 2020. Dados anteriores de auxílio permanecem nulos. A soma dos pesos estaduais reproduziu as estimativas nacionais em todos os sete meses dentro do erro numérico. Os percentuais estaduais são estimativas amostrais: o painel inclui os tamanhos de amostra e respostas ausentes, mas não calcula erros-padrão ou intervalos.

Para o gráfico, dividimos cada índice estadual pelo índice do próprio estado em fevereiro de 2020 e multiplicamos por 100. A linha mostra a mediana não ponderada das 27 trajetórias e a faixa mostra os quartis 25 e 75, interpolados linearmente. A mediana é 78,19 em abril e 106,99 em novembro. Não é o índice nacional; a unidade mediana pode mudar a cada mês.

**Decisão de identificação:** este painel não estabelece causalidade. A proporção de auxílio já é medida depois do começo da crise, pode responder à perda de renda e não identifica exclusivamente o programa federal. Estados também diferem em restrições sanitárias, estrutura econômica e exposição à pandemia. Comparar proporções ou ajustar uma regressão não identifica a resposta de vendas ao auxílio sem uma estratégia adicional e controles/condições críveis definidos antes da análise. Os dados anteriores do comércio permitem examinar tendências, mas por si só não provam tendências paralelas. Há apenas 27 unidades agregadas, e inferência, efeitos comuns, seleção e defasagens exigem tratamento cuidadoso. Mesmo uma estimativa regional válida não seria uma PMC individual.

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
python -m src.etl.pnad_covid
MPLBACKEND=Agg python -m src.relatorio.grafico_pnad_covid
python -m src.etl.comercio_regional
python -m src.etl.painel_regional
MPLBACKEND=Agg python -m src.relatorio.grafico_painel_regional
```

As tabelas oficiais podem ser consultadas em [SIDRA 6715](https://sidra.ibge.gov.br/tabela/6715) e [SIDRA 6974](https://sidra.ibge.gov.br/tabela/6974). O coletor consulta a API de agregados do IBGE e produz `docs/pof-2017-2018.csv`; o gráfico é salvo em `docs/grafico-pof.png`. O arquivo HTML contém valores textuais que devem ser conferidos novamente se a fonte for revisada.

O segundo coletor baixa sete arquivos mensais do IBGE em memória, sem gravar os microdados no repositório, e gera `docs/pnad-covid-auxilios.csv` e `docs/grafico-pnad-covid.png`. Se as fontes forem revisadas, a tabela e a narrativa HTML também precisam ser conferidas.

O coletor de comércio gera `docs/comercio-estadual-2019-2020.csv`; o painel relê os sete arquivos da PNAD em memória e gera `docs/painel-regional-2019-2020.csv`. O último comando gera `docs/resumo-comercio-estadual.csv` e `docs/grafico-comercio-estadual.png`. Os números textuais da página não são atualizados automaticamente.