# bruna-adm-ti

Repositório de conteúdos de Administração de TI, incluindo materiais educacionais sobre Inteligência Artificial e Large Language Models (LLMs).

## Conteúdo

- `site/` — Site HTML navegável com os dados de IDH/IDHM: mapa interativo, ranking, comparação entre estimativa e valor oficial, metodologia e downloads.
- `mapa-idh-2025.html` — Mapa coroplético autocontido do IDH estimado 2025 por UF.
- `llm-explicacao.html` — Página interativa explicando o que é um LLM, com design responsivo e visual moderno.
- `vocabulario-ingles.html` — Site de vocabulário em inglês com imagens, filtros por categoria e pronúncia por áudio.
- `tutorial-markdown-basico.md` — Tutorial básico de Markdown com exemplos da Administração.

## Skills do OpenCode

- `.opencode/skills/analise-idh-ibge/` — Analisa IDH/IDHM no Brasil com dados do IBGE: distingue os índices, coleta indicadores na API oficial e gera relatório com limitações declaradas.
- `.opencode/skills/site-idh-ibge/` — Gera um site HTML estático com mapa, ranking, comparação e downloads a partir dos dados coletados, e sobe um servidor local.

## Como gerar o site

```bash
python .opencode/skills/analise-idh-ibge/coleta_ipea.py
python .opencode/skills/analise-idh-ibge/gera_mapa_idh.py
python .opencode/skills/site-idh-ibge/gera_site.py
python .opencode/skills/site-idh-ibge/servir.py
```

Abra `site/index.html` diretamente ou acesse `http://localhost:8000`.

## Como visualizar

Abra os arquivos `.html` diretamente no navegador. Para o Markdown, abra o `.md` no VS Code (`Ctrl+Shift+V`) ou no GitHub.

## Tecnologias

- HTML5
- CSS3 (Gradientes, Glassmorphism, Responsivo)
