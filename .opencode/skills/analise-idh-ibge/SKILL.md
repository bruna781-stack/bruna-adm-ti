---
name: analise-idh-ibge
description: Use para analisar IDH e IDHM no Brasil com dados do IBGE (Censo, PNAD Contínua, Tábua de Mortalidade). Distingue IDH (PNUD) de IDHM (Atlas), coleta indicadores na API oficial, calcula variacoes e gera diagnostico com limitacoes declaradas.
---

# Análise do IDH no Brasil com dados do IBGE

Skill para transformar indicadores de desenvolvimento humano em diagnóstico
territorial, usando a API oficial do IBGE e os valores oficiais de IDH/IDHM.

## 0. Regra de ouro: quem calcula o quê

Esta distinção evita o erro mais comum em relatórios sobre o tema:

| Indicador | Quem calcula | Unidade de análise | Base |
|---|---|---|---|
| **IDH** | PNUD (Relatório de Desenvolvimento Humano) | País e, no Brasil, UF | Renda nacional bruta per capita em PPC |
| **IDHM** | Atlas do Desenvolvimento Humano no Brasil (PNUD, Ipea e FJP) | Município, UF, região, UDH | Censos 1991/2000/2010 e PNAD Contínua |
| **Insumos** (renda, longevidade, educação, população) | **IBGE** | País, região, UF, município | Censo, PNAD Contínua, Tábua de Mortalidade |

O IBGE **não publica IDH nem IDHM como agregado na API v3** (verificado em
novembro de 2026: nenhum agregado com "IDH" ou "desenvolvimento humano").
O IBGE produz os dados que alimentam os dois índices. Portanto:

1. Os **valores oficiais** de IDH/IDHM vêm do PNUD e do Atlas Brasil.
2. Os **componentes e o contexto** vêm da API do IBGE.
3. Nunca escrever "IDH do IBGE". Escrever "IDH (PNUD), calculado com dados do IBGE".

## 1. Quando usar

Use quando o usuário pedir: IDH, IDHM, desenvolvimento humano, ranking de
estados ou municípios, desigualdade regional, evolução do IDHM, ou comparação
entre territórios brasileiros.

Se o pedido for relatório formal em PDF/DOCX, combinar com `estilo-vale`:
esta skill analisa, a outra formata.

## 2. Fontes e o que cada uma responde

| Pergunta | Fonte | Onde consultar |
|---|---|---|
| Qual o IDH do país? | PNUD — RDH | `hdr.undp.org` (data center) |
| Qual o IDH das UFs? | PNUD Brasil | `pnud.org.br` e Atlas Brasil |
| Qual o IDHM do município/UF? | Atlas Brasil | `atlasbrasil.org.br/consulta` |
| Renda, educação e população | IBGE | API v3 (seção 3) |
| Esperança de vida | IBGE — Tábua de Mortalidade | agregados 1174/3825/7362 e página oficial |

Registrar sempre: **ano de referência**, **edição/fonte** e **data de coleta**.

## 3. API do IBGE: como consultar

Base: `https://servicodados.ibge.gov.br/api/v3/agregados`

```text
# 1) metadados do agregado (variáveis, categorias, níveis)
/5453/metadados

# 2) períodos disponíveis
/7395/periodos

# 3) valores
/7395/periodos/2024/variaveis/4196?localidades=N3[21]
```

### 3.1 Agregados úteis para desenvolvimento humano

| Indicador | Agregado | Variável | Níveis | Períodos |
|---|---|---|---|---|
| População residente (Censo 2022) | 4714 | 93 | N1, N2, N3, N6 | 2022 |
| População estimada | 6579 | 9324 | N1, N2, N3, N6 | 2001–2026 (sem 2007, 2010, 2022, 2023) |
| Rendimento domiciliar per capita | 7395 | 4196 | N1, N2, N3, N7, N14 | 2016–2025 (sem 2020) |
| Índice de Gini | 7435 | 10681 | N1, N2, N3 | 2012–2025 |
| Taxa de analfabetismo (15+) | 7113 | 10267 | N1, N2, N3, N7, N14 | 2016–2025 |
| Média de anos de estudo (25+) | 7126 | 3593 | N1, N2, N3, N6, N7, N14 | 2016–2025 |
| Esperança de vida ao nascer | 1174 | 2503 | N1, N2, N3 | 2000–2014 |
| Esperança de vida por sexo | 3825 | 2503 | N1, N2, N3 | 2000–2016 |
| Esperança + mortalidade infantil | 7362 | 2503, 1940 | N1, N2, N3 | 2018 |

N1 = Brasil, N2 = Grande Região, N3 = UF, N6 = município.
Códigos de UF: use `https://servicodados.ibge.gov.br/api/v1/localidades/estados`.

### 3.2 Filtros de classificação (pegadinha)

O filtro por categoria funciona como **query param**, não como caminho:

```text
# CERTO
.../7113/periodos/2024/variaveis/10267?localidades=N3[21]&classificacao=2[6794]|58[2795]

# ERRADO (retorna 404)
.../7113/periodos/2024/variaveis/10267/classificacoes/2/categorias/6794?localidades=N3[21]
```

Categorias usadas com mais frequência:

- Sexo (classificação 2): `6794` Total, `4` Homens, `5` Mulheres.
- Grupo de idade (classificação 58): `2795` 15 anos ou mais; `108866` 25 anos ou mais.

### 3.3 Erros que a API devolve

- Período inexistente (ex.: `2022` no agregado 1174) → **404**.
- Localidade incompatível com o nível (ex.: `N3[33]` no agregado 5453) → **500**.
- Sempre conferir `/periodos` e `/metadados` antes de montar a URL.
- Salvar o JSON bruto: sem ele a análise não é reproduzível.

### 3.4 Coleta automatizada

`coleta_ibge.py` (nesta pasta, só biblioteca padrão) baixa os indicadores da
seção 3.1 para uma UF e salva o JSON bruto:

```bash
python .opencode/skills/analise-idh-ibge/coleta_ibge.py --uf MA --ano 2024
python .opencode/skills/analise-idh-ibge/coleta_ibge.py --uf 21 --saida dados/
```

- `--uf` aceita sigla (`MA`) ou código IBGE (`21`).
- `--ano` é opcional; sem ele usa o período mais recente de cada agregado.
- Se o ano não existir no agregado, usa o mais recente até o ano pedido e
  registra o ajuste em `observacoes`.
- O script **não** calcula IDH/IDHM: apenas coleta componentes e contexto.

## 4. Indicadores mínimos por tipo de análise

| Análise | Indicadores |
|---|---|
| Retrato de um território | IDH/IDHM, renda per capita, esperança de vida, analfabetismo/anos de estudo, Gini, população |
| Ranking | IDH/IDHM de todos os territórios + população para ponderar |
| Evolução | IDH/IDHM em 2+ anos + componentes nos mesmos anos |
| Desigualdade regional | maior vs menor, gap absoluto, razão, Gini |
| Relação com ODS | IDH/IDHM + indicadores ODS (agregados da pesquisa C2) |

## 5. Fórmulas e cálculos

### 5.1 IDH (metodologia PNUD, 2010 em diante)

```text
I_saúde   = (esperança de vida - 20) / (85 - 20)
I_educação = [(média de anos de estudo / 18) + (anos esperados de estudo / 15)] / 2
I_renda   = [ln(RNB per capita) - ln(100)] / [ln(75.000) - ln(100)]

IDH = (I_saúde × I_educação × I_renda)^(1/3)
```

Limites: média de anos de estudo até 18; anos esperados até 15; RNB per capita
em dólares de PPC de 2017, até 75.000. Média geométrica, não aritmética.

### 5.2 Cálculos de apoio

```text
Variação absoluta = IDH(t) - IDH(t-1)
Variação relativa (%) = [(IDH(t) / IDH(t-1)) - 1] × 100
Gap = maior IDH - menor IDH
Razão = maior IDH / menor IDH
Distância até a faixa seguinte = limite da faixa - IDH atual
```

### 5.3 Faixas: cuidado, as escalas são diferentes

| Faixa | PNUD (IDH) | Atlas (IDHM) |
|---|---|---|
| Muito alto | ≥ 0,800 | 0,800–1,000 |
| Alto | 0,700–0,799 | 0,700–0,799 |
| Médio | 0,550–0,699 | **0,600–0,699** |
| Baixo | < 0,550 | **0,500–0,599** |
| Muito baixo | — | **0,000–0,499** |

Nunca classificar IDHM com a régua do PNUD nem o contrário.

### 5.4 Quando é legítimo recalcular

Só recalcule o índice quando **todas** as condições valerem:

1. Os três componentes vêm da mesma fonte e do mesmo ano.
2. A metodologia está documentada (PNUD ou Atlas).
3. O resultado é rotulado como "estimativa própria", não como valor oficial.

Se a renda disponível for domiciliar per capita (IBGE) e não RNB per capita em
PPC, **não** apresente o resultado como IDH: é uma aproximação, e a comparação
internacional fica inválida.

## 6. Roteiro de análise (7 passos)

1. **Pergunta e recorte**: país, UF ou município; ano; comparação desejada.
2. **Coleta oficial**: IDH/IDHM publicado (PNUD/Atlas) com ano e edição.
3. **Coleta IBGE**: componentes e contexto via API; salvar JSON bruto.
4. **Validação**: conferir período, nível, denominador e coeficiente de variação.
5. **Decomposição**: qual dimensão puxa o índice para baixo? Compare com a
   média nacional e com a faixa seguinte.
6. **Interpretação**: o que o número significa para gestão pública/privada;
   separar fato, hipótese e julgamento.
7. **Entrega**: relatório com fonte em cada número e seção de limitações.

## 7. Modelo de saída

Seguir `modelo-relatorio.md`. Ordem mínima:

1. Título + território + ano.
2. Sumário executivo com 3 a 5 achados (cada um com número e fonte).
3. Metodologia (fonte, período, data de coleta, fórmula usada).
4. Análise em 3 blocos: nível, evolução, desigualdade.
5. Comparação territorial (ranking ou gap).
6. Implicações para gestão (3 recomendações).
7. Limitações.
8. Fontes e referências.

## 8. Regras fixas

- Nunca escrever que o IBGE calcula ou publica IDH/IDHM.
- Nunca apresentar IDH/IDHM sem ano, fonte e unidade territorial.
- Nunca comparar IDH de país com IDHM municipal como se fossem o mesmo índice.
- Nunca usar IDHM de 2010 para descrever 2024 sem dizer que o dado é de 2010.
- Nunca recalcular o índice e chamar o resultado de oficial.
- Nunca inferir causalidade a partir de correlação.
- Nunca arredondar dois territórios para o mesmo valor quando a diferença for
  menor que a margem de arredondamento; usar 3 casas e dizer o critério.
- Nunca esconder que PNAD Contínua é amostral: citar o coeficiente de variação
  quando a diferença entre territórios for pequena.
- Se a API falhar, registrar a falha e usar o valor publicado com a data de
  consulta; não preencher lacuna com estimativa não declarada.
- Se não houver dado para o ano pedido, escrever "não disponível" e informar o
  ano mais recente disponível.

## 9. Checklist antes de entregar

- [ ] Cada número tem fonte, ano e território.
- [ ] A distinção IDH/IDHM está explícita no texto.
- [ ] As faixas usadas correspondem ao índice correto.
- [ ] As contas de variação e gap estão visíveis.
- [ ] O JSON bruto foi salvo em `dados/`.
- [ ] As limitações estão declaradas (amostra, ano, metodologia).
- [ ] Nenhuma frase afirma causalidade sem evidência.

## 10. Integração com outras skills

- `estilo-vale`: relatório institucional em HTML/PDF/DOCX.
- `analise-turnover`: quando o recorte for mercado de trabalho e rotatividade.

## 11. Limitações conhecidas

- Na API v3, a esperança de vida por UF para no agregado 1174 (2014). Para anos
  recentes, usar a Tábua de Mortalidade publicada pelo IBGE e citar a edição.
- O IDHM municipal é decenal (Censo); as atualizações anuais do Atlas cobrem
  UFs com PNAD Contínua. Não misturar as duas granularidades.
- IDH e IDHM usam réguas de renda diferentes (RNB per capita PPC x renda
  domiciliar per capita). Os valores não são diretamente comparáveis.
- PNAD Contínua tem plano amostral complexo: valores municipais exigem cuidado.

## 12. Referências

- PNUD. *Relatório de Desenvolvimento Humano* — notas metodológicas do IDH.
- PNUD/Ipea/FJP. *Atlas do Desenvolvimento Humano no Brasil* — metodologia do IDHM.
- IBGE. *API de Agregados v3* — `servicodados.ibge.gov.br/api/docs/agregados?versao=3`.
- IBGE. *Tábua Completa de Mortalidade* — página de População.
- IBGE. *Censo Demográfico 2022* e *PNAD Contínua* — agregados citados na seção 3.
