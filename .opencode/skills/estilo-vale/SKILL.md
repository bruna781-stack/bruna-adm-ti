---
name: estilo-vale
description: Use when creating Vale-style corporate documents, relatorios, propostas ou apresentacoes. Aplica paleta, tipografia e tom institucional da Vale.
---

# Estilo Vale para Criação de Documentos

Skill para gerar documentos com identidade institucional da Vale (mineradora).

## 1. Paleta oficial

| Nome | HEX | Uso |
|---|---|---|
| Verde Vale | `#007E7A` | Títulos, cabeçalhos, barras, destaques principais |
| Amarelo Vale | `#ECB11F` | Detalhes, filetes, gráficos de destaque, chamadas |
| Cinza Vale | `#747678` | Texto secundário, legendas, rodapés |
| Branco | `#FFFFFF` | Fundo preferencial |
| Cinza-escuro digital | `#555555` | Texto corrido no digital (no lugar do preto puro) |

Regra: fundo branco ou claro sempre que possível. Verde Vale para títulos sobre branco; branco sobre fundo verde.

## 2. Tipografia

- Títulos, chamadas e destaques: Caecilia Light (fallback: Georgia, serif). Grandes e leves.
- Subtítulos e corpo: Myriad Pro Light/Regular, Bold só em destaques (fallback: Arial, Verdana, sans-serif).
- Digital: nunca usar preto puro `#000000`; usar cinza-escuro `#555555`.

## 3. Tom de voz

- Institucional, sóbrio e direto. Frases completas, sem gírias.
- Valores a transmitir: segurança, sustentabilidade, respeito às pessoas e excelência operacional.
- Números sempre com fonte (ex: "Produção de 310 Mt em 2024, segundo Relato Integrado Vale 2024").
- Nunca inventar dado: se não houver fonte, escrever "dado a confirmar".

## 4. Estrutura padrão do documento

1. Capa: título em Verde Vale, subtítulo em cinza, filete amarelo, data e autor.
2. Sumário ou objetivo (3–5 linhas).
3. Desenvolvimento em seções numeradas com títulos em Verde Vale.
4. Tabelas e gráficos com cabeçalho verde e destaque amarelo no dado principal.
5. Conclusão + próximos passos (lista numerada).
6. Fontes e referências no rodapé em cinza.

## 5. Modelo Markdown

```markdown
# Título do Documento (Verde Vale)

> Objetivo em até 5 linhas.

## 1. Contexto

Texto em cinza-escuro, frase completa.

| Indicador | 2024 | Fonte |
|---|---|---|
| Exemplo | — | dado a confirmar |

## 2. Análise

- Ponto 1
- Ponto 2

## 3. Próximos passos

1. Ação + responsável + prazo.

---
*Documento em estilo Vale — Verde #007E7A, Amarelo #ECB11F. Fontes: ___*
```

## 6. Modelo HTML (quando pedir página)

- Fundo branco, `h1/h2` em `#007E7A`, filete superior de 4px em `#ECB11F`.
- Corpo em `#555555`, fonte sistema (Verdana/Arial).
- Rodapé em `#747678` com fontes.

## 7. Referências da marca

- Manual da Marca Fundação Vale (2025): Verde Vale Pantone 328 `#007E7A`, Amarelo Vale `#ECB11F`.
- Guia Rápido da Marca Vale (2007): títulos Caecilia, corpo Myriad Pro, logo V-coração verde/amarelo.
