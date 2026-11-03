# Modelo de relatório — Desenvolvimento humano no Brasil

Use este esqueleto como ponto de partida. Trocar o que está entre colchetes.
Não deixar nenhum número sem fonte.

---

# [Título: Desenvolvimento humano em [território], [ano]]

**Território:** [Brasil / UF / município]
**Ano de referência:** [ano]
**Fonte dos índices:** [PNUD / Atlas Brasil — edição]
**Data de coleta dos dados do IBGE:** [dd/mm/aaaa]

## 1. Sumário executivo

[3 a 5 achados, cada um com número, ano e fonte. Exemplo:]

1. O IDHM de [território] foi de **[0,000]** em [ano], na faixa **[faixa]**
   (Atlas Brasil, [edição]).
2. A dimensão que mais limita o índice é **[renda/educação/longevidade]**:
   [valor] contra [valor] da média nacional (IBGE, [agregado], [ano]).
3. A renda domiciliar per capita foi de **R$ [valor]** em [ano], [x]% abaixo
   da média nacional (IBGE, agregado 7395).
4. O Gini foi de **[valor]**, indicando [leitura em uma frase].
5. [Achado territorial: gap, ranking ou evolução.]

## 2. Metodologia

- Índice utilizado: [IDH (PNUD) / IDHM (Atlas)].
- Ano e edição: [ano/edição].
- Componentes: [renda, longevidade, educação] — fontes e agregados.
- Fórmula: [fórmula aplicada ou "valores publicados, sem recálculo"].
- Data de extração da API: [dd/mm/aaaa].
- Arquivo bruto: `dados/[arquivo].json`.

## 3. Nível de desenvolvimento

| Indicador | Território | Brasil | Fonte | Ano |
|---|---:|---:|---|---|
| IDH/IDHM | 0,000 | 0,000 | [fonte] | [ano] |
| Renda domiciliar per capita (R$) | 0 | 0 | IBGE 7395 | [ano] |
| Esperança de vida (anos) | 0,0 | 0,0 | IBGE 1174 / Tábua | [ano] |
| Anos de estudo (25+) | 0,0 | 0,0 | IBGE 7126 | [ano] |
| Analfabetismo (15+) (%) | 0,0 | 0,0 | IBGE 7113 | [ano] |
| Gini | 0,000 | 0,000 | IBGE 7435 | [ano] |

**Leitura:** [1 parágrafo. O que o conjunto diz? O índice está acima ou abaixo
da média? Qual dimensão explica a posição?]

## 4. Evolução

| Ano | IDH/IDHM | Variação absoluta | Variação relativa |
|---|---:|---:|---:|
| [t-2] | 0,000 | — | — |
| [t-1] | 0,000 | +0,000 | +0,0% |
| [t] | 0,000 | +0,000 | +0,0% |

**Leitura:** [ritmo de melhora, aceleração/desaceleração, comparação com o
Brasil. Mostrar a conta.]

## 5. Desigualdade territorial

| Território | IDH/IDHM | População | Posição |
|---|---:|---:|---:|
| [maior] | 0,000 | 0 | 1º |
| ... | 0,000 | 0 | ... |
| [menor] | 0,000 | 0 | ... |

- Gap absoluto: **[0,000]**
- Razão maior/menor: **[x,x]**
- Distância do menor até a faixa seguinte: **[0,000]**

**Leitura:** [o gap é grande ou pequeno para o porte do território? Citar a
limitação de comparar municípios de portes diferentes.]

## 6. Implicações para a gestão

1. **[Ação]** — responsável: [área]; prazo: [prazo]; indicador de acompanhamento:
   [indicador].
2. **[Ação]** — ...
3. **[Ação]** — ...

[As ações devem decorrer dos achados. Não propor ação genérica.]

## 7. Limitações

- [Ano do índice x ano dos componentes.]
- [IDHM municipal decenal; PNAD Contínua amostral.]
- [IDH e IDHM usam réguas de renda diferentes.]
- [Dados não disponíveis para o ano pedido.]
- [Recorte territorial e período.]

## 8. Fontes

- PNUD. *Relatório de Desenvolvimento Humano [ano]*. [link, acesso em dd/mm/aaaa].
- PNUD/Ipea/FJP. *Atlas do Desenvolvimento Humano no Brasil [edição]*. [link].
- IBGE. *Censo Demográfico 2022* — agregado 4714. [link da API].
- IBGE. *PNAD Contínua* — agregados 7395, 7435, 7113, 7126.
- IBGE. *Tábua Completa de Mortalidade [ano]*.

---

*Relatório produzido com a skill `analise-idh-ibge`. Números conferidos na API
em [data].*
