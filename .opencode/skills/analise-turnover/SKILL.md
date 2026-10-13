---
name: analise-turnover
description: Use para calcular e interpretar turnover (rotatividade) a partir de admissoes, desligamentos e quadro ativo. Calcula taxa geral e de desligamentos, classifica risco e gera plano de reducao.
---

# Análise de Turnover para Administração / RH

Skill para estudante de Administração transformar dados de RH em diagnóstico de rotatividade.

## Quando usar

Use quando o usuário pedir: turnover, rotatividade, calcular desligamentos, reter talentos, analisar RH, relatório de RH.

Se pedir relatório formal estilo Vale, combinar com `estilo-vale`: esta skill calcula, estilo-vale formata.

## 1. Inputs necessários

Pedir sempre, não assumir:

1. `admissoes` — nº contratados no período (int >=0)
2. `desligamentos` — nº que saíram no período (int >=0)
3. `quadro_ativo` ou `quadro_medio` — total funcionários ativos (int >0)
4. `periodo` — mensal, trimestral, semestral, anual + datas
5. Opcional: `voluntarios` (pediram demissão), `departamento`, `setor`

Se vier CSV como `decc0294-tic-administracao/dados/29-9/simulacao_rh_30_funcionarios.csv`, avisar: esse arquivo é foto atual (30 ativos), não tem histórico. Pedir admissões/desligamentos do período à parte.

## 2. Fórmulas oficiais

Fórmula padrão (Ticket / Catho / Qulture.Rocks):

```text
Turnover geral (%) = [(Admissões + Desligamentos) / 2] / Quadro Ativo * 100
Taxa de desligamentos (%) = Desligamentos / Quadro Médio * 100
Turnover voluntário (%) = Desligamentos voluntários / Quadro Médio * 100
```

Exemplo de validação: 6 admissões, 8 desligamentos, 60 ativos = [(6+8)/2]/60*100 = 11,6%

Manter mesmo critério ao comparar meses.

## 3. Passo a passo de execução

1. Validar inputs (quadro >0, período definido).
2. Rodar `calculadora.py` ou calcular manual.
3. Classificar faixa:
   - <10% ano: ok / saudável
   - 10-15% ano: atenção
   - >15% ano: crítico
   - Mensal >2-3%: investigar (regra prática, não universal)
4. Separar tipos:
   - voluntário (funcionário sai) x involuntário (empresa desliga)
   - funcional (sai baixo desempenho = baixo impacto) x disfuncional (sai talento = alto impacto)
   - evitável (salário, liderança, clima) x inevitável (mudança cidade, saúde, aposentadoria)
5. Levantar 3 causas prováveis: remuneração, liderança, falta de crescimento, recrutamento falho, clima, condições trabalho, onboarding fraco.
6. Propor 3-5 ações das 8 base: refinar contratação/fit cultural, remuneração+benefícios competitivos, plano carreira, capacitar liderança/feedback, clima positivo, reconhecimento, escuta ativa/pesquisa clima, onboarding 90 dias.
7. Declarar limitação: sem benchmark do setor, sem série histórica, sem entrevista desligamento = diagnóstico parcial.

## 4. Modelo de saída

Sempre entregar nesta ordem:

```markdown
## Resultado Turnover - [período]
- Admissões: X | Desligamentos: Y | Quadro: Z
- Turnover geral: __%
- Taxa desligamentos: __%
- Faixa: ok / atenção / crítico

## Interpretação
1 frase: o que o número significa.

## Tipos prováveis
- Voluntário vs involuntário: ...
- Risco disfuncional: ...

## Causas a investigar
1. ...
2. ...
3. ...

## Plano 30-60-90 dias
1. Ação + responsável + prazo
2. ...

## Limitações e próximos dados
- Falta: ...
- Fonte: Ticket 2026 + dados informados pelo usuário
```

## 5. Regras fixas

- Nunca inventar admissões, desligamentos ou benchmark setorial. Se não souber, escrever "dado a confirmar".
- Nunca apresentar % sem mostrar conta e período.
- Nunca prometer causa definitiva sem pesquisa de clima/entrevista desligamento.
- Números sempre com fonte (ex: "11,6% cálculo próprio a partir de dados informados em 13/10/2026").
- Linguagem técnica de ADM, frases curtas, termo definido na 1ª ocorrência.

## 6. Integração estilo-vale

Se usuário pedir PDF/relatório Vale:
- Títulos em Verde Vale `#007E7A`, filete Amarelo `#ECB11F`, corpo `#555555`
- Tabela com cabeçalho verde, destaque amarelo no % principal
- Rodapé cinza `#747678` com fontes

## 7. Referências

- Ticket Blog (2026): O que é turnover? Como calcular e reduzir - fórmula 3 passos
- Catho Empresas (2026): Turnover - impactos e como reduzir
- Qulture.Rocks (2024): Turnover - tipos e cálculo
