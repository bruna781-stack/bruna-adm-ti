# Referência de dados — IDH/IDHM com API do IBGE

Todos os exemplos abaixo foram testados em novembro de 2026.
Base: `https://servicodados.ibge.gov.br/api/v3/agregados`

## 1. Endpoints de apoio

```text
# lista de pesquisas e agregados (procurar por "Censo", "PNAD", "ODS")
GET /api/v3/agregados

# metadados de um agregado
GET /api/v3/agregados/{agregado}/metadados

# períodos disponíveis
GET /api/v3/agregados/{agregado}/periodos

# valores
GET /api/v3/agregados/{agregado}/periodos/{periodo}/variaveis/{variaveis}
    ?localidades={nivel}[{codigo}]
    &classificacao={id}[{categoria}]|{id2}[{categoria2}]
```

## 2. Localidades

```text
# todas as UFs
GET https://servicodados.ibge.gov.br/api/v1/localidades/estados

# municípios de uma UF (21 = Maranhão)
GET https://servicodados.ibge.gov.br/api/v1/localidades/estados/21/municipios

# um município (2111300 = São Luís)
GET https://servicodados.ibge.gov.br/api/v1/localidades/municipios/2111300
```

Códigos de nível: `N1` Brasil, `N2` região, `N3` UF, `N6` município,
`N7` mesorregião, `N14` microrregião.

## 3. Indicadores

### 3.1 População residente — Censo 2022 (agregado 4714, variável 93)

```text
https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N1[all]
https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N3[21]
https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93?localidades=N6[2111300]
```

Retorno (São Luís): `"2022": "1037775"`.

### 3.2 População estimada (agregado 6579, variável 9324)

Períodos: 2001 a 2026 (sem 2007, 2010, 2022 e 2023). Níveis N1, N2, N3, N6.
Para 2022, usar a população do Censo (agregado 4714).

```text
https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2025/variaveis/9324?localidades=N3[21]
```

### 3.3 Rendimento domiciliar per capita (agregado 7395, variável 4196)

Períodos: 2016–2019, 2021–2025 (não há 2020). Níveis N1, N2, N3, N7, N14.
Unidade: reais.

```text
https://servicodados.ibge.gov.br/api/v3/agregados/7395/periodos/2024/variaveis/4196?localidades=N3[21]
```

Retorno (Maranhão, 2024): `"2024": "1151"`.
Brasil, 2024: `"2024": "2157"`.

### 3.4 Índice de Gini (agregado 7435, variável 10681)

Períodos: 2012–2025. Níveis N1, N2, N3.

```text
https://servicodados.ibge.gov.br/api/v3/agregados/7435/periodos/2024/variaveis/10681?localidades=N3[21]
```

### 3.5 Taxa de analfabetismo 15+ (agregado 7113, variável 10267)

Períodos: 2016–2019, 2022–2025. Níveis N1, N2, N3, N7, N14.
Classificações: `2` (sexo) e `58` (grupo de idade).

```text
https://servicodados.ibge.gov.br/api/v3/agregados/7113/periodos/2024/variaveis/10267?localidades=N3[21]&classificacao=2[6794]|58[2795]
```

Retorno (Maranhão, 2024): `"2024": "11.2"` (%).

Categorias:

| Classificação | Código | Categoria |
|---|---|---|
| 2 (sexo) | 6794 | Total |
| 2 (sexo) | 4 | Homens |
| 2 (sexo) | 5 | Mulheres |
| 58 (idade) | 2795 | 15 anos ou mais |
| 58 (idade) | 108866 | 25 anos ou mais |

### 3.6 Média de anos de estudo 25+ (agregado 7126, variável 3593)

Períodos: 2016–2019, 2022–2025. Níveis N1, N2, N3, N6, N7, N14.

```text
https://servicodados.ibge.gov.br/api/v3/agregados/7126/periodos/2024/variaveis/3593?localidades=N3[21]&classificacao=2[6794]|58[108866]
```

Retorno (Maranhão, 2024): `"2024": "8.6"` (anos).

### 3.7 Esperança de vida ao nascer (agregado 1174, variável 2503)

Períodos: 2000–2014. Níveis N1, N2, N3. Unidade: anos.

```text
https://servicodados.ibge.gov.br/api/v3/agregados/1174/periodos/2014/variaveis/2503?localidades=N3[21]
```

Retorno (Maranhão, 2014): `"2014": "70.0"`.

Para anos posteriores: usar a Tábua Completa de Mortalidade do IBGE
(publicação anual) e citar a edição. O agregado 7362 traz 2018 para Brasil e
UFs; o 3825 traz por sexo até 2016.

## 4. Classificação de faixas

| Faixa | PNUD (IDH) | Atlas (IDHM) |
|---|---|---|
| Muito alto | ≥ 0,800 | 0,800–1,000 |
| Alto | 0,700–0,799 | 0,700–0,799 |
| Médio | 0,550–0,699 | 0,600–0,699 |
| Baixo | < 0,550 | 0,500–0,599 |
| Muito baixo | — | 0,000–0,499 |

## 5. Valores-âncora (conferir antes de citar)

| Indicador | Valor | Fonte | Observação |
|---|---|---|---|
| IDHM Brasil 2010 | 0,727 | Atlas Brasil 2013 | Censo 2010 |
| IDHM Brasil 2024 | 0,805 | Atlas Brasil (home, consulta em nov/2026) | Faixa muito alta; confirmar edição |
| IDH Brasil 2021 | 0,754 | PNUD — RDH 2021/2022 | Comparação internacional |

Regra: se o valor não puder ser confirmado na fonte, escrever
"dado a confirmar" em vez de estimar.

## 6. Exemplo de retorno da API

```json
[
  {
    "id": "4196",
    "variavel": "Rendimento médio mensal real domiciliar per capita",
    "unidade": "Reais",
    "resultados": [
      {
        "classificacoes": [],
        "series": [
          {
            "localidade": {
              "id": "21",
              "nivel": { "id": "N3", "nome": "Unidade da Federação" },
              "nome": "Maranhão"
            },
            "serie": { "2024": "1151" }
          }
        ]
      }
    ]
  }
]
```

O valor numérico chega como **string**. Converter para `float` antes de calcular.
Valores ausentes podem vir como `"..."`, `"-"` ou `"X"`: tratar como nulos.
