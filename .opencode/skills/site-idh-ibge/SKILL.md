---
name: site-idh-ibge
description: Use para publicar os dados de IDH/IDHM como site HTML navegável. Gera páginas estáticas (mapa, ranking, comparação, metodologia e dados) a partir dos JSON/CSV do repositório, sem CDN, e sobe um servidor local para visualizar.
---

# Site HTML de IDH/IDHM

Transforma os dados já coletados em um site estático de cinco páginas, pronto
para abrir no navegador (`file://`) ou servir em `http://localhost`.

O site **não recalcula nada**: consome os arquivos de `dados/` produzidos pelo
skill `analise-idh-ibge`. A separação entre valor **estimado** e **oficial** é
mantida em todas as páginas.

## 1. Quando usar

Use quando o pedido for:

- "quero um site/página para mostrar esses dados";
- "publicar o mapa com tabela e comparação";
- "rodar localmente um HTML com os dados de IDH";
- uma versão navegável do relatório, com ranking e downloads.

Para um único mapa autocontido, use `analise-idh-ibge` (gera
`mapa-idh-2025.html`). Este skill gera o site completo.

## 2. Pré-requisitos

Os dados precisam existir em `dados/`:

| Arquivo | Origem | Comando |
|---|---|---|
| `idh_2025_uf.json` e `.csv` | IBGE, estimativa 2025 | `gera_mapa_idh.py` |
| `idhm_oficial_2024_uf.json` e `.csv` | Atlas/IpeaData | `coleta_ipea.py` |
| `idh_oficial_pnud_brasil.csv` | PNUD/IpeaData | `coleta_ipea.py` |
| `malha_uf.geojson` | API de malhas do IBGE | `gera_mapa_idh.py` |

Na raiz do repositório:

```bash
python .opencode/skills/analise-idh-ibge/coleta_ipea.py
python .opencode/skills/analise-idh-ibge/gera_mapa_idh.py
```

O gerador do site falha com mensagem explícita se algum arquivo faltar.

## 3. Gerar o site

```bash
python .opencode/skills/site-idh-ibge/gera_site.py
```

Saída em `site/`:

```text
site/
├── index.html          mapa interativo + KPIs + destaques
├── estados.html        ranking com busca, ordenação e as duas camadas
├── comparacao.html     dispersão, correlação e divergências
├── metodologia.html    fórmulas, faixas e limitações
├── dados.html          downloads, fontes e comandos
├── assets/
│   ├── estilo.css      estilo único, responsivo e com regras de impressão
│   ├── site.js         mapa, tooltip, camadas, tabela e CSV
│   └── dados.js        dados embutidos (permite abrir via file://)
└── dados/              cópias dos CSV/JSON para download
```

Abrir direto: clique duas vezes em `site/index.html`.
Como os dados estão embutidos em `assets/dados.js`, não há `fetch()` e o site
funciona sem servidor.

## 4. Servir localmente

```bash
python .opencode/skills/site-idh-ibge/servir.py
python .opencode/skills/site-idh-ibge/servir.py --port 8080 --no-browser
```

- Escuta apenas em `127.0.0.1` (não expõe na rede).
- Se a porta estiver ocupada, tenta as 20 seguintes.
- Abre o navegador padrão, salvo `--no-browser`.
- Encerra com `Ctrl+C`.

## 5. O que cada página contém

### `index.html`
- Quatro KPIs: IDH estimado 2025 e IDHM oficial 2024 do Brasil, maior e menor UF.
- Mapa SVG com duas camadas e quatro dimensões (índice, renda, educação,
  longevidade).
- Tooltip com índice, posição, dimensões e insumos (na camada estimada).
- Destaques calculados sobre a camada ativa: maior, menor, gap, razão e média.

### `estados.html`
- Tabela das 27 UFs nas duas camadas.
- Busca por nome/sigla e ordenação por posição, nome ou qualquer dimensão.
- Colunas extras (renda per capita, anos de estudo, esperança de vida) aparecem
  só na camada estimada.
- Botão de download do CSV da camada ativa.

### `comparacao.html`
- Pearson e Spearman entre as camadas.
- Diferença média absoluta e maior divergência.
- Dispersão com linha de identidade e rótulos nos extremos.
- Tabela das oito maiores divergências, com deslocamento de posição no ranking.
- Explicação de por que os níveis diferem (renda, educação, longevidade, ano).

### `metodologia.html`
- Fórmulas da camada estimada e insumos do IBGE.
- Séries oficiais usadas no IpeaData (`IDHM`, `IDHMED`, `IDHMLO`, `IDHMRE`,
  `PNUD_IDH`).
- Réguas de classificação do IDH e do IDHM, lado a lado.
- Limitações.

### `dados.html`
- Links para os CSV/JSON em `site/dados/`.
- Fontes com URLs.
- Comandos para reproduzir todo o pipeline.

## 6. Personalização

| O que mudar | Onde |
|---|---|
| Paleta das camadas | `CORES_ESTIMADO` / `CORES_OFICIAL` em `gera_site.py` |
| Número de classes do mapa | `classes(..., n=6)` em `gera_site.py` |
| Itens do menu | lista `NAV` em `gera_site.py` |
| Cores e tipografia | `CSS` em `gera_site.py` |
| Rótulos do mapa | dicionário `OFFSETS` em `gera_site.py` |

Depois de editar, rode `gera_site.py` novamente. Não edite `site/` à mão: é
saída gerada.

## 7. Regras

- Nunca publicar o valor estimado como oficial. O site usa os rótulos
  "IDH estimado 2025" e "IDHM oficial 2024".
- Nunca somar ou comparar diretamente valores das duas camadas; elas estão em
  anos e conceitos diferentes.
- Não usar CDN, fonte externa ou biblioteca de gráficos: o site precisa
  funcionar offline.
- Não colocar dado sensível ou credencial em `assets/dados.js` (ele é público).
- Ao alterar a metodologia, atualizar `metodologia.html` e `dados.html` no mesmo
  commit.
- Se um número não existir, exibir "n/d" — nunca preencher lacuna.

## 8. Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| "Faltam arquivos de dados" | pipeline anterior não rodou | rodar `coleta_ipea.py` e `gera_mapa_idh.py` |
| Mapa cinza | código da UF fora de `dados.js` | conferir `codarea` da malha e o JSON |
| Página sem estilo | `assets/` não copiado | rodar `gera_site.py` de novo |
| Tabela vazia | `dados.js` não carregou | abrir o console; conferir caminho relativo |
| Porta ocupada | outro processo | `--port 8080` |
| CSV com acentos quebrados | abrir sem UTF-8 | o arquivo tem BOM; usar Excel ou UTF-8 |

## 9. Verificação rápida

```bash
python .opencode/skills/site-idh-ibge/gera_site.py
python .opencode/skills/site-idh-ibge/servir.py --no-browser --port 8765
```

Depois, no navegador:

1. O mapa tem 27 estados pintados e legenda com 6 faixas.
2. Trocar para "IDHM oficial 2024" muda cores, legenda e destaques.
3. `estados.html` lista 27 linhas e a busca filtra por "santa".
4. `comparacao.html` mostra 27 pontos e a correlação (≈ 0,97).
5. Os cinco links de download respondem 200.

## 10. Integração

- `analise-idh-ibge`: coleta e cálculo dos dados; gera o mapa autocontido.
- `estilo-vale`: quando o site precisar seguir a identidade visual institucional.

## 11. Limitações

- O site é estático: não há filtro temporal nem consulta à API em tempo real.
- A camada oficial é a mais recente disponível por UF (2024); não é 2025.
- A dispersão e as correlações são descritivas, não causais.
- Sem backend: atualizar dados exige rodar o pipeline e regerar o site.
