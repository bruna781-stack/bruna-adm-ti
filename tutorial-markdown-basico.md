# Tutorial Básico de Markdown

> Arquivo exemplificativo para a disciplina de Administração de TI.
> Use este arquivo como referência rápida e como modelo para seus relatórios e entregas.

## 1. O que é Markdown?

Markdown é uma linguagem simples para formatar texto. Você escreve em texto puro e ele é convertido para HTML, PDF, slides, etc.

É muito usado no GitHub, Notion, Discord, e nos roteiros da disciplina (`roteiro-moduloN.md`).

## 2. Títulos

Use `#` no início da linha. Quanto mais `#`, menor o nível:

```markdown
# Título 1
## Título 2
### Título 3
#### Título 4
```

Resultado:

# Título 1
## Título 2
### Título 3
#### Título 4

## 3. Parágrafos e quebras de linha

Escreva normalmente. Para novo parágrafo, deixe **uma linha em branco**.

Para quebra de linha dentro do mesmo parágrafo, termine a linha com dois espaços
assim.

## 4. Ênfase

```markdown
*itálico* ou _itálico_
**negrito** ou __negrito__
***negrito e itálico***
~~riscado~~
```

*itálico* ou _itálico_
**negrito** ou __negrito__
***negrito e itálico***
~~riscado~~

Exemplo da Administração: o **lucro líquido** cresceu *12%* no trimestre.

## 5. Listas

### Lista não ordenada

```markdown
- Planejamento
- Organização
  - Recursos humanos
  - Recursos financeiros
- Controle
```

- Planejamento
- Organização
  - Recursos humanos
  - Recursos financeiros
- Controle

### Lista ordenada

```markdown
1. Levantar requisitos
2. Analisar dados
3. Apresentar proposta
```

1. Levantar requisitos
2. Analisar dados
3. Apresentar proposta

### Lista de tarefas (checkbox)

```markdown
- [x] Criar conta no GitHub
- [x] Instalar Python
- [ ] Entregar atividade A1
```

- [x] Criar conta no GitHub
- [x] Instalar Python
- [ ] Entregar atividade A1

## 6. Links e imagens

```markdown
[Site da UFMA](https://www.ufma.br)
[Programa da disciplina](./decc0294-tic-administracao/README.md)
```

[Site da UFMA](https://www.ufma.br)
[Programa da disciplina](./decc0294-tic-administracao/README.md)

Imagem:

```markdown
![Legenda da imagem](https://via.placeholder.com/300x100)
```

## 7. Citações

```markdown
> A quarta revolução industrial está transformando a gestão.
> — Klaus Schwab
```

> A quarta revolução industrial está transformando a gestão.
> — Klaus Schwab

## 8. Código

No meio da frase, use crase: o comando `python atividade_modulo1.py conferir` valida a entrega.

Bloco de código com três crases + linguagem:

```python
receita = 15000
custo = 9000
lucro = receita - custo
print(f"Lucro: R$ {lucro}")
```

```bash
python atividade_modulo1.py iniciar
python atividade_modulo1.py conferir
```

## 9. Tabelas

Muito usadas em Administração para comparar indicadores:

```markdown
| Indicador | 2024 | 2025 | Variação |
|---|---|---|---|
| Receita | 100 mil | 120 mil | +20% |
| Custo | 60 mil | 70 mil | +16% |
| Lucro | 40 mil | 50 mil | +25% |
```

| Indicador | 2024 | 2025 | Variação |
|---|---|---|---|
| Receita | 100 mil | 120 mil | +20% |
| Custo | 60 mil | 70 mil | +16% |
| Lucro | 40 mil | 50 mil | +25% |

Dica: alinhe com `|:---|` (esquerda), `|:---:|` (centro), `|---:|` (direita).

## 10. Linha horizontal e divisões

Use três hífens, asteriscos ou underlines:

```markdown
---
```

---

## 11. Exemplo completo: mini-relatório

> Copie e adapte este modelo para suas entregas:

```markdown
# Relatório - Análise de Vendas

**Aluno:** Maria Silva
**Data:** 06/10/2026

## Objetivo
Analisar a variação das vendas no 3º trimestre.

## Resultados
- Receita total: **R$ 120 mil**
- Melhor mês: *setembro*
- Crescimento: +20% vs. trimestre anterior

## Próximos passos
1. Investigar causa da queda em julho
2. Propor plano de ação

> Fonte: planilha `vendas.csv` da pasta `dados/`
```

## 12. Como visualizar

1. No **VS Code**: abra o arquivo e pressione `Ctrl+Shift+V` para pré-visualizar.
2. No **GitHub**: basta abrir o arquivo `.md` no navegador, ele já renderiza sozinho.
3. No **navegador**: arraste o arquivo para extensões como Markdown Viewer.

## 13. Exercício rápido

1. Edite este arquivo
2. Troque o nome do aluno no exemplo acima pelo seu
3. Crie uma tabela com 3 disciplinas e suas notas
4. Crie uma lista de tarefas com o que falta para a próxima entrega

---
*Arquivo criado como material de apoio — Administração de TI / UFMA*
