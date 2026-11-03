#!/usr/bin/env python3
"""Gera um site HTML estatico com os dados de IDH/IDHM do repositorio.

Entradas (produzidas pelas outras skills):
  dados/idh_2025_uf.json          IDH estimado 2025 por UF (IBGE)
  dados/idhm_oficial_2024_uf.json IDHM oficial 2024 por UF (Atlas/IpeaData)

Saidas (pasta site/):
  index.html          mapa coropletico interativo + destaques
  estados.html        ranking completo, com busca e ordenacao
  comparacao.html     estimado 2025 x oficial 2024 (dispersao e divergencias)
  metodologia.html    formulas, fontes e limitacoes
  dados.html          downloads e links das fontes
  assets/estilo.css   folha de estilo unica
  assets/site.js      interacoes (mapa, tabela, camadas)
  assets/dados.js     dados embutidos (funciona tambem em file://)
  dados/*.csv|json    copias para download

O site nao usa CDN nem biblioteca externa: abre direto no navegador ou por
um servidor local (ver servir.py).

Uso:
  python .opencode/skills/site-idh-ibge/gera_site.py
"""

from __future__ import annotations

import json
import math
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DADOS = ROOT / "dados"
SITE = ROOT / "site"
ASSETS = SITE / "assets"

ARQ_ESTIMADO = DADOS / "idh_2025_uf.json"
ARQ_OFICIAL = DADOS / "idhm_oficial_2024_uf.json"

CORES_ESTIMADO = ["#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3", "#2b8cbe"]
CORES_OFICIAL = ["#eef4fa", "#d3e4f2", "#aecbe4", "#83aed3", "#5489b8", "#2a5f8f"]
ESCURO = [False, False, False, True, True, True]

OFFSETS = {
    "53": (10, -4), "33": (8, 2), "32": (9, 2), "27": (9, 2), "28": (8, 3),
    "24": (4, 4), "25": (7, 2), "26": (7, 3), "31": (-4, 2), "35": (5, 1),
    "21": (-2, 2), "16": (0, 0), "14": (0, 0),
}

VARIAVEIS = {
    "idh": ("Índice", "idh"),
    "renda": ("Renda", "renda"),
    "educacao": ("Educação", "educacao"),
    "longevidade": ("Longevidade", "longevidade"),
}

NAV = [
    ("index.html", "Visão geral"),
    ("estados.html", "Estados"),
    ("comparacao.html", "Comparação"),
    ("metodologia.html", "Metodologia"),
    ("dados.html", "Dados"),
]

CSS = """
:root {
  --azul: #0b3d6b;
  --azul-medio: #14588f;
  --azul-claro: #e8f1f8;
  --texto: #1d2733;
  --muted: #5b6b7c;
  --borda: #d9e2ea;
  --alerta: #fff4d6;
  --alerta-borda: #e0a800;
  --ok: #e7f4ec;
  --ok-borda: #2f8f5b;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: #f4f6f8; color: var(--texto);
  font-family: "Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif;
  line-height: 1.55;
}
a { color: var(--azul-medio); }
header.topo {
  background: linear-gradient(135deg, #0b3d6b 0%, #14588f 60%, #1f7a8c 100%);
  color: #fff;
}
header.topo .wrap { max-width: 1180px; margin: 0 auto; padding: 22px 20px 26px; }
header.topo .kicker {
  text-transform: uppercase; letter-spacing: .14em; font-size: 11.5px;
  opacity: .85; margin-bottom: 6px;
}
header.topo h1 { margin: 0 0 8px; font-size: clamp(23px, 3vw, 34px); line-height: 1.15; }
header.topo p { margin: 0; max-width: 880px; opacity: .93; font-size: 14.5px; }
nav.menu { background: #fff; border-bottom: 1px solid var(--borda); position: sticky; top: 0; z-index: 30; }
nav.menu .wrap { max-width: 1180px; margin: 0 auto; padding: 0 20px; display: flex; gap: 4px; overflow-x: auto; }
nav.menu a {
  padding: 12px 13px; font-size: 14px; font-weight: 600; color: var(--muted);
  text-decoration: none; border-bottom: 3px solid transparent; white-space: nowrap;
}
nav.menu a:hover { color: var(--azul); }
nav.menu a[aria-current="page"] { color: var(--azul); border-bottom-color: var(--azul); }
main { max-width: 1180px; margin: 0 auto; padding: 22px 18px 54px; }
.card {
  background: #fff; border: 1px solid var(--borda); border-radius: 10px;
  padding: 18px; margin-bottom: 18px; box-shadow: 0 1px 2px rgba(16,42,67,.05);
}
.card h2 { margin: 0 0 4px; font-size: 20px; color: var(--azul); }
.card h3 { margin: 18px 0 8px; font-size: 15px; color: var(--azul); }
.card .sub { margin: 0 0 14px; color: var(--muted); font-size: 13px; }
.alerta {
  background: var(--alerta); border-left: 5px solid var(--alerta-borda);
  padding: 14px 16px; border-radius: 6px; margin: 0 0 18px; font-size: 14px;
}
.alerta strong { color: #7a5200; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-bottom: 18px; }
.kpi { background: #fff; border: 1px solid var(--borda); border-radius: 10px; padding: 14px 16px; }
.kpi .rot { font-size: 11px; text-transform: uppercase; letter-spacing: .09em; color: var(--muted); }
.kpi .val { font-size: 28px; font-weight: 700; color: var(--azul); line-height: 1.2; }
.kpi .quem { font-size: 12.5px; color: var(--muted); }
.layout { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(260px, .75fr); gap: 18px; align-items: start; }
#mapa { width: 100%; height: auto; display: block; }
.uf { stroke: #fff; stroke-width: 1.1; cursor: pointer; transition: opacity .15s, stroke .15s; }
.uf:hover { stroke: #102a43; stroke-width: 2.2; }
.rotulo {
  font-size: 10px; font-weight: 700; fill: #102a43; text-anchor: middle;
  dominant-baseline: middle; pointer-events: none; paint-order: stroke;
  stroke: rgba(255,255,255,.85); stroke-width: 2.4px; stroke-linejoin: round;
}
.rotulo.claro { fill: #fff; stroke: rgba(16,42,67,.55); }
.controles { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.controles button {
  border: 1px solid var(--borda); background: #fff; color: var(--texto);
  padding: 8px 12px; border-radius: 999px; font-size: 13px; cursor: pointer; font-weight: 600;
}
.controles button:hover { border-color: #7fb3d5; }
.controles button.ativo { background: var(--azul); border-color: var(--azul); color: #fff; }
.controles .grupo-rot {
  width: 100%; font-size: 11px; text-transform: uppercase; letter-spacing: .09em;
  color: var(--muted); margin: 2px 0 -4px;
}
.legenda { margin-top: 12px; }
.legenda .titulo { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 6px; }
.legenda .faixas { display: grid; gap: 5px; }
.legenda .faixa { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.legenda .cor { width: 22px; height: 14px; border-radius: 3px; border: 1px solid rgba(0,0,0,.08); flex: 0 0 auto; }
.nota-mapa { font-size: 12px; color: var(--muted); margin-top: 10px; }
.destaques { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.destaque-box { background: var(--azul-claro); border-radius: 8px; padding: 10px 12px; }
.destaque-box .rotulo-peq { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.destaque-box .valor { font-size: 22px; font-weight: 700; color: var(--azul); }
.destaque-box .quem { font-size: 12px; color: var(--muted); }
.acoes { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.acoes button, .acoes a.botao {
  border: 1px solid var(--borda); background: #fff; padding: 7px 11px; border-radius: 6px;
  cursor: pointer; font-size: 12.5px; font-weight: 600; color: var(--azul); text-decoration: none;
}
.acoes button:hover, .acoes a.botao:hover { border-color: #7fb3d5; }
.filtros { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }
.filtros input, .filtros select {
  padding: 8px 10px; border: 1px solid var(--borda); border-radius: 6px;
  font-size: 13px; font-family: inherit; background: #fff;
}
.filtros input { min-width: 220px; }
.tabela-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 7px 8px; border-bottom: 1px solid #e6edf3; text-align: left; white-space: nowrap; }
th { background: #f0f5f9; color: #284b63; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
tbody tr:nth-child(even) { background: #fafcfd; }
tbody tr:hover { background: #eef6fb; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.pos { text-align: right; color: var(--muted); width: 46px; }
td.destaque { font-weight: 700; color: var(--azul); }
.chip { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; border: 1px solid rgba(0,0,0,.08); vertical-align: middle; }
.sigla { color: var(--muted); font-size: 11px; }
.grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.grid-cards a.card-link {
  display: block; background: #fff; border: 1px solid var(--borda); border-radius: 10px;
  padding: 16px; text-decoration: none; color: inherit;
}
.grid-cards a.card-link:hover { border-color: #7fb3d5; box-shadow: 0 3px 10px rgba(16,42,67,.08); }
.grid-cards .titulo { font-weight: 700; color: var(--azul); margin-bottom: 4px; }
.grid-cards .desc { font-size: 13px; color: var(--muted); }
.metodologia { font-size: 14px; }
.metodologia code { background: #f2f5f7; padding: 2px 5px; border-radius: 4px; font-size: 13px; }
.metodologia ul, .metodologia ol { padding-left: 22px; }
.metodologia li { margin-bottom: 5px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; align-items: start; }
.fontes { font-size: 13px; color: var(--muted); }
.fontes li { margin-bottom: 6px; }
.tooltip {
  position: absolute; z-index: 40; max-width: 290px; pointer-events: none;
  background: rgba(16,42,67,.96); color: #fff; padding: 10px 12px; border-radius: 8px;
  font-size: 12.5px; line-height: 1.45; box-shadow: 0 6px 18px rgba(0,0,0,.25);
  opacity: 0; transform: translateY(4px); transition: opacity .12s;
}
.tooltip.show { opacity: 1; }
.tooltip .nome { font-weight: 700; font-size: 14px; margin-bottom: 4px; }
.tooltip .linha { display: flex; justify-content: space-between; gap: 14px; }
.tooltip .linha span:last-child { font-variant-numeric: tabular-nums; }
.tooltip .divisor { height: 1px; background: rgba(255,255,255,.2); margin: 6px 0; }
.tooltip .peq { opacity: .8; font-size: 11.5px; }
.scatter-wrap { overflow-x: auto; }
#dispersao { width: 100%; max-width: 760px; height: auto; display: block; margin: 0 auto; }
.eixo { stroke: #c3cfda; stroke-width: 1; }
.eixo-texto { fill: #5b6b7c; font-size: 11px; }
.ponto { fill: #1f5f9e; opacity: .82; stroke: #fff; stroke-width: 1; }
.ponto.extremo { fill: #b3541e; }
.ponto-label { fill: #102a43; font-size: 10.5px; font-weight: 700; }
.identidade { stroke: #b3541e; stroke-width: 1.2; stroke-dasharray: 5 4; fill: none; }
footer.rodape { text-align: center; color: var(--muted); font-size: 12px; padding: 8px 18px 34px; }
.tag { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 999px; }
.tag.est { background: #e0f3db; color: #2c5f2d; }
.tag.ofi { background: #d3e4f2; color: #1d4d75; }
@media (max-width: 860px) {
  .layout, .two-col { grid-template-columns: 1fr; }
}
@media print {
  body { background: #fff; }
  nav.menu, .controles, .acoes, .tooltip, .filtros { display: none !important; }
  header.topo { background: #0b3d6b; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .card { box-shadow: none; break-inside: avoid; }
}
"""

JS = """
(function () {
  const D = window.DADOS_SITE;
  if (!D) return;

  let camada = "estimado";
  let variavel = "idh";

  const fmt = (v, c = 3) => Number(v).toLocaleString("pt-BR", { minimumFractionDigits: c, maximumFractionDigits: c });
  const fmtInt = (v) => Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 0 });

  function classe(valor, cortes) {
    if (valor <= cortes[0]) return 0;
    if (valor >= cortes[cortes.length - 1]) return cortes.length - 2;
    for (let i = 0; i < cortes.length - 1; i++) {
      if (valor >= cortes[i] && valor < cortes[i + 1]) return i;
    }
    return cortes.length - 2;
  }

  function cam() { return D.camadas[camada]; }

  /* ---------- mapa ---------- */
  function pintarMapa() {
    const c = cam();
    document.querySelectorAll("path.uf").forEach(function (path) {
      const item = c.ufs[path.dataset.cod];
      if (!item) return;
      const k = classe(item[variavel], c.cortes[variavel]);
      path.setAttribute("fill", c.cores[k]);
      const rot = document.querySelector('text.rotulo[data-cod="' + path.dataset.cod + '"]');
      if (rot) rot.classList.toggle("claro", c.escuro[k]);
    });
    const faixas = document.getElementById("legenda-faixas");
    if (faixas) {
      const cortes = c.cortes[variavel];
      faixas.innerHTML = cortes.slice(0, -1).map(function (inf, i) {
        return '<div class="faixa"><span class="cor" style="background:' + c.cores[i] + '"></span>' +
          '<span>' + fmt(inf) + " – " + fmt(cortes[i + 1]) + "</span></div>";
      }).join("");
    }
    const titulo = document.getElementById("legenda-titulo");
    if (titulo) titulo.textContent = c.titulos[variavel];
    const nota = document.getElementById("nota-mapa");
    if (nota) nota.textContent = c.notas[variavel];
    document.querySelectorAll("[data-tag-camada]").forEach(function (el) {
      el.textContent = c.rotulo;
    });
  }

  /* ---------- tooltip ---------- */
  function mostrar(ev, cod) {
    const el = document.getElementById("tooltip");
    if (!el) return;
    const c = cam();
    const d = c.ufs[cod];
    if (!d) return;
    let html = '<div class="nome">' + d.nome + " (" + d.sigla + ")</div>" +
      '<div class="linha"><span>' + c.rotulo + '</span><span><strong>' + fmt(d.idh) +
      "</strong> · " + d.posicao + 'º</span></div><div class="divisor"></div>' +
      '<div class="linha"><span>Renda</span><span>' + fmt(d.renda) + "</span></div>" +
      '<div class="linha"><span>Educação</span><span>' + fmt(d.educacao) + "</span></div>" +
      '<div class="linha"><span>Longevidade</span><span>' + fmt(d.longevidade) + "</span></div>";
    if (camada === "estimado") {
      html += '<div class="divisor"></div>' +
        '<div class="linha peq"><span>Renda per capita</span><span>R$ ' + fmtInt(d.renda_per_capita) + "</span></div>" +
        '<div class="linha peq"><span>Anos de estudo (25+)</span><span>' + fmt(d.anos_estudo, 1) + "</span></div>" +
        '<div class="linha peq"><span>Esperança de vida</span><span>' + fmt(d.esperanca_vida, 1) + " anos</span></div>";
    } else {
      html += '<div class="divisor"></div><div class="linha peq"><span>Fonte</span><span>Atlas 2024 · IpeaData</span></div>';
    }
    el.innerHTML = html;
    el.classList.add("show");
    mover(ev);
  }
  function mover(ev) {
    const el = document.getElementById("tooltip");
    if (!el) return;
    const m = 14;
    let x = ev.pageX + m, y = ev.pageY + m;
    if (x + el.offsetWidth > window.scrollX + document.documentElement.clientWidth - 8) x = ev.pageX - el.offsetWidth - m;
    if (y + el.offsetHeight > window.scrollY + window.innerHeight - 8) y = ev.pageY - el.offsetHeight - m;
    el.style.left = x + "px";
    el.style.top = y + "px";
  }
  function esconder() {
    const el = document.getElementById("tooltip");
    if (el) el.classList.remove("show");
  }
  document.querySelectorAll("path.uf").forEach(function (path) {
    path.addEventListener("mouseenter", function (ev) { mostrar(ev, path.dataset.cod); });
    path.addEventListener("mousemove", mover);
    path.addEventListener("mouseleave", esconder);
  });

  /* ---------- destaques ---------- */
  function renderDestaques() {
    const box = document.getElementById("destaques");
    if (!box) return;
    const c = cam();
    const lista = Object.values(c.ufs).sort(function (a, b) { return b.idh - a.idh; });
    const topo = lista[0], base = lista[lista.length - 1];
    const media = lista.reduce(function (s, d) { return s + d.idh; }, 0) / lista.length;
    const itens = [
      ["Maior índice", fmt(topo.idh), topo.nome + " (" + topo.sigla + ")"],
      ["Menor índice", fmt(base.idh), base.nome + " (" + base.sigla + ")"],
      ["Gap absoluto", fmt(topo.idh - base.idh), "maior menos menor"],
      ["Razão maior/menor", fmt(topo.idh / base.idh, 2) + "×", "desigualdade relativa"],
      ["Média simples das UFs", fmt(media), "não ponderada por população"]
    ];
    box.innerHTML = itens.map(function (i) {
      return '<div class="destaque-box"><div class="rotulo-peq">' + i[0] + '</div><div class="valor">' +
        i[1] + '</div><div class="quem">' + i[2] + "</div></div>";
    }).join("");
  }

  /* ---------- tabela ---------- */
  function renderTabela() {
    const corpo = document.getElementById("corpo-tabela");
    if (!corpo) return;
    const c = cam();
    const busca = (document.getElementById("busca") || {}).value || "";
    const ordem = (document.getElementById("ordem") || {}).value || "posicao";
    const q = busca.trim().toLowerCase();
    let lista = Object.values(c.ufs).filter(function (d) {
      return !q || d.nome.toLowerCase().indexOf(q) >= 0 || d.sigla.toLowerCase().indexOf(q) >= 0;
    });
    if (ordem === "posicao") lista.sort(function (a, b) { return a.posicao - b.posicao; });
    else if (ordem === "nome") lista.sort(function (a, b) { return a.nome.localeCompare(b.nome, "pt-BR"); });
    else lista.sort(function (a, b) { return b[ordem] - a[ordem]; });

    const extra = camada === "estimado";
    document.querySelectorAll("[data-col-extra]").forEach(function (el) {
      el.style.display = extra ? "" : "none";
    });

    corpo.innerHTML = lista.map(function (d) {
      const k = classe(d.idh, c.cortes.idh);
      let linha = "<tr>" +
        '<td class="pos">' + d.posicao + "º</td>" +
        '<td><span class="chip" style="background:' + c.cores[k] + '"></span>' + d.nome +
        ' <span class="sigla">' + d.sigla + "</span></td>" +
        '<td class="num destaque">' + fmt(d.idh) + "</td>" +
        '<td class="num">' + fmt(d.renda) + "</td>" +
        '<td class="num">' + fmt(d.educacao) + "</td>" +
        '<td class="num">' + fmt(d.longevidade) + "</td>";
      if (extra) {
        linha += '<td class="num" data-col-extra>R$ ' + fmtInt(d.renda_per_capita) + "</td>" +
          '<td class="num" data-col-extra>' + fmt(d.anos_estudo, 1) + "</td>" +
          '<td class="num" data-col-extra>' + fmt(d.esperanca_vida, 1) + "</td>";
      }
      return linha + "</tr>";
    }).join("");
  }

  /* ---------- csv ---------- */
  function baixarCsv() {
    const c = cam();
    const est = camada === "estimado";
    const cab = ["posicao", "uf", "nome", "indice", "renda", "educacao", "longevidade"];
    if (est) cab.push("renda_per_capita", "anos_estudo", "analfabetismo", "esperanca_vida");
    const linhas = [cab.join(";")];
    Object.values(c.ufs).sort(function (a, b) { return a.posicao - b.posicao; }).forEach(function (d) {
      const l = [d.posicao, d.sigla, d.nome, d.idh, d.renda, d.educacao, d.longevidade];
      if (est) l.push(d.renda_per_capita, d.anos_estudo, d.analfabetismo, d.esperanca_vida);
      linhas.push(l.join(";"));
    });
    const blob = new Blob(["\\ufeff" + linhas.join("\\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "idh_" + camada + "_uf.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ---------- eventos ---------- */
  document.querySelectorAll("[data-camada]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      camada = btn.dataset.camada;
      document.querySelectorAll("[data-camada]").forEach(function (b) { b.classList.remove("ativo"); });
      btn.classList.add("ativo");
      pintarMapa(); renderDestaques(); renderTabela();
    });
  });
  document.querySelectorAll("[data-var]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      variavel = btn.dataset.var;
      document.querySelectorAll("[data-var]").forEach(function (b) { b.classList.remove("ativo"); });
      btn.classList.add("ativo");
      pintarMapa();
    });
  });
  const busca = document.getElementById("busca");
  if (busca) busca.addEventListener("input", renderTabela);
  const ordem = document.getElementById("ordem");
  if (ordem) ordem.addEventListener("change", renderTabela);
  const csv = document.getElementById("btn-csv");
  if (csv) csv.addEventListener("click", baixarCsv);
  const imprimir = document.getElementById("btn-print");
  if (imprimir) imprimir.addEventListener("click", function () { window.print(); });

  pintarMapa();
  renderDestaques();
  renderTabela();
})();
"""


# ---------------------------------------------------------------------------
# dados
# ---------------------------------------------------------------------------


def carregar() -> tuple[dict, dict]:
    faltando = [p for p in (ARQ_ESTIMADO, ARQ_OFICIAL) if not p.exists()]
    if faltando:
        nomes = ", ".join(str(p.relative_to(ROOT)) for p in faltando)
        raise SystemExit(
            f"Faltam arquivos de dados: {nomes}\n"
            "Rode primeiro:\n"
            "  python .opencode/skills/analise-idh-ibge/coleta_ipea.py\n"
            "  python .opencode/skills/analise-idh-ibge/gera_mapa_idh.py"
        )
    est = json.loads(ARQ_ESTIMADO.read_text(encoding="utf-8"))
    ofi = json.loads(ARQ_OFICIAL.read_text(encoding="utf-8"))
    return est, ofi


def classes(valores: list[float], n: int = 6) -> list[float]:
    lo, hi = min(valores), max(valores)
    if hi == lo:
        return [lo] * (n + 1)
    passo = (hi - lo) / n
    return [round(lo + i * passo, 4) for i in range(n + 1)]


def classe_de(valor: float, cortes: list[float]) -> int:
    n = len(cortes) - 1
    if valor <= cortes[0]:
        return 0
    if valor >= cortes[-1]:
        return n - 1
    for i in range(n):
        if cortes[i] <= valor < cortes[i + 1]:
            return i
    return n - 1


def fmt(valor: float, casas: int = 3) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def fmt_int(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def projetar(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon)
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def gerar_mapa(malha: dict, est: dict, cortes_idh: list[float]) -> tuple[str, dict]:
    largura = altura = 760
    margem = 18
    pontos: list[tuple[float, float]] = []
    aneis_por_uf: dict[str, list[list[tuple[float, float]]]] = {}

    for feature in malha["features"]:
        cod = str(feature["properties"]["codarea"])
        geom = feature["geometry"]
        poligonos = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        aneis = []
        for poligono in poligonos:
            for anel in poligono:
                convertido = [projetar(lon, lat) for lon, lat in anel]
                aneis.append(convertido)
                pontos.extend(convertido)
        aneis_por_uf[cod] = aneis

    minx, maxx = min(p[0] for p in pontos), max(p[0] for p in pontos)
    miny, maxy = min(p[1] for p in pontos), max(p[1] for p in pontos)
    escala = min((largura - 2 * margem) / (maxx - minx), (altura - 2 * margem) / (maxy - miny))
    sobra_x = (largura - (maxx - minx) * escala) / 2
    sobra_y = (altura - (maxy - miny) * escala) / 2

    def tela(p: tuple[float, float]) -> tuple[float, float]:
        return sobra_x + (p[0] - minx) * escala, sobra_y + (maxy - p[1]) * escala

    paths: list[str] = []
    centroides: dict[str, tuple[float, float]] = {}
    for cod, aneis in aneis_por_uf.items():
        partes = []
        maior_area = -1.0
        centro = (largura / 2, altura / 2)
        for anel in aneis:
            if len(anel) < 3:
                continue
            tela_anel = [tela(p) for p in anel]
            partes.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in tela_anel) + " Z")
            area = cx = cy = 0.0
            for i in range(len(tela_anel) - 1):
                x1, y1 = tela_anel[i]
                x2, y2 = tela_anel[i + 1]
                cruz = x1 * y2 - x2 * y1
                area += cruz
                cx += (x1 + x2) * cruz
                cy += (y1 + y2) * cruz
            area_abs = abs(area) / 2
            if area_abs > maior_area and area != 0:
                maior_area = area_abs
                centro = (cx / (3 * area), cy / (3 * area))
        item = est["ufs"].get(cod)
        cor = CORES_ESTIMADO[classe_de(item["idh"], cortes_idh)] if item else "#cccccc"
        paths.append(
            f'<path class="uf" data-cod="{cod}" d="{" ".join(partes)}" '
            f'fill="{cor}" fill-rule="evenodd"></path>'
        )
        centroides[cod] = centro

    rotulos = []
    for cod, (x, y) in centroides.items():
        item = est["ufs"].get(cod)
        if not item:
            continue
        dx, dy = OFFSETS.get(cod, (0, 0))
        rotulos.append(
            f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" class="rotulo" '
            f'data-cod="{cod}">{item["sigla"]}</text>'
        )

    svg = (
        f'<svg id="mapa" viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="Mapa do IDH por unidade da federação">'
        + "".join(paths)
        + '<g id="rotulos">' + "".join(rotulos) + "</g></svg>"
    )
    return svg, centroides


def cortes_para(ufs: dict, chaves: tuple[str, ...]) -> dict[str, list[float]]:
    return {chave: classes([d[chave] for d in ufs.values()]) for chave in chaves}


def dados_js(est: dict, ofi: dict) -> dict:
    chaves = ("idh", "renda", "educacao", "longevidade")

    def limpar(ufs: dict, extra: tuple[str, ...]) -> dict:
        saida = {}
        for cod, d in ufs.items():
            item = {k: d[k] for k in ("sigla", "nome", "posicao") + chaves}
            for k in extra:
                item[k] = d[k]
            saida[cod] = item
        return saida

    camadas = {
        "estimado": {
            "rotulo": "IDH estimado 2025",
            "ano": 2025,
            "fonte": "IBGE (estimativa própria)",
            "ufs": limpar(
                est["ufs"],
                ("renda_per_capita", "anos_estudo", "analfabetismo", "esperanca_vida"),
            ),
            "cortes": cortes_para(est["ufs"], chaves),
            "cores": CORES_ESTIMADO,
            "escuro": ESCURO,
            "titulos": {
                "idh": "IDH estimado 2025",
                "renda": "Dimensão renda (0 a 1)",
                "educacao": "Dimensão educação (0 a 1)",
                "longevidade": "Dimensão longevidade (0 a 1)",
            },
            "notas": {
                "idh": "Cor mais escura = maior IDH estimado. Escala ajustada ao intervalo dos estados.",
                "renda": "Cor mais escura = maior subíndice de renda.",
                "educacao": "Cor mais escura = maior subíndice de educação.",
                "longevidade": "Cor mais escura = maior subíndice de longevidade.",
            },
        },
        "oficial": {
            "rotulo": "IDHM oficial 2024",
            "ano": 2024,
            "fonte": "Atlas do Desenvolvimento Humano · IpeaData",
            "ufs": limpar(ofi["ufs"], ()),
            "cortes": cortes_para(ofi["ufs"], chaves),
            "cores": CORES_OFICIAL,
            "escuro": ESCURO,
            "titulos": {
                "idh": "IDHM oficial 2024",
                "renda": "Dimensão renda (oficial)",
                "educacao": "Dimensão educação (oficial)",
                "longevidade": "Dimensão longevidade (oficial)",
            },
            "notas": {
                "idh": "Cor mais escura = maior IDHM oficial de 2024 (Atlas/IpeaData).",
                "renda": "Cor mais escura = maior subíndice oficial de renda.",
                "educacao": "Cor mais escura = maior subíndice oficial de educação.",
                "longevidade": "Cor mais escura = maior subíndice oficial de longevidade.",
            },
        },
    }
    return {"camadas": camadas, "brasil": {"estimado": est["brasil_referencia"], "oficial": ofi["brasil"]}}


# ---------------------------------------------------------------------------
# estatistica
# ---------------------------------------------------------------------------


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    return cov / math.sqrt(vx * vy)


def ranks(valores: list[float]) -> list[float]:
    ordem = sorted(range(len(valores)), key=lambda i: valores[i])
    saida = [0.0] * len(valores)
    i = 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and valores[ordem[j + 1]] == valores[ordem[i]]:
            j += 1
        posicao = (i + j) / 2 + 1
        for k in range(i, j + 1):
            saida[ordem[k]] = posicao
        i = j + 1
    return saida


def comparar(est: dict, ofi: dict) -> dict:
    codigos = sorted(ofi["ufs"])
    xs = [ofi["ufs"][c]["idh"] for c in codigos]
    ys = [est["ufs"][c]["idh"] for c in codigos]
    difs = [y - x for x, y in zip(xs, ys)]
    abs_difs = [abs(d) for d in difs]
    linha = []
    for cod, x, y, d in zip(codigos, xs, ys, difs):
        linha.append({
            "cod": cod,
            "sigla": ofi["ufs"][cod]["sigla"],
            "nome": ofi["ufs"][cod]["nome"],
            "oficial": x,
            "estimado": y,
            "diff": d,
            "pos_est": est["ufs"][cod]["posicao"],
            "pos_ofi": ofi["ufs"][cod]["posicao"],
        })
    linha.sort(key=lambda r: abs(r["diff"]), reverse=True)
    return {
        "r": pearson(xs, ys),
        "rho": pearson(ranks(xs), ranks(ys)),
        "media_abs": sum(abs_difs) / len(abs_difs),
        "max_abs": max(abs_difs),
        "max_nome": linha[0]["sigla"],
        "n": len(codigos),
        "linhas": linha,
        "xs": xs,
        "ys": ys,
        "codigos": codigos,
    }


def dispersao_svg(comp: dict) -> str:
    largura, altura = 760, 430
    esq, dir_, topo, base = 62, 22, 22, 54
    xs, ys = comp["xs"], comp["ys"]
    lo = min(min(xs), min(ys)) - 0.006
    hi = max(max(xs), max(ys)) + 0.006

    def px(v: float) -> float:
        return esq + (v - lo) / (hi - lo) * (largura - esq - dir_)

    def py(v: float) -> float:
        return altura - base - (v - lo) / (hi - lo) * (altura - topo - base)

    ticks = []
    t = math.ceil(lo * 100) / 100
    while t <= hi:
        ticks.append(round(t, 2))
        t += 0.02

    partes = []
    for v in ticks:
        partes.append(f'<line class="eixo" x1="{px(v):.1f}" y1="{py(lo):.1f}" x2="{px(v):.1f}" y2="{py(hi):.1f}"/>')
        partes.append(f'<line class="eixo" x1="{px(lo):.1f}" y1="{py(v):.1f}" x2="{px(hi):.1f}" y2="{py(v):.1f}"/>')
        partes.append(f'<text class="eixo-texto" x="{px(v):.1f}" y="{altura - base + 16:.1f}" text-anchor="middle">{v:.2f}</text>')
        partes.append(f'<text class="eixo-texto" x="{esq - 8:.1f}" y="{py(v) + 4:.1f}" text-anchor="end">{v:.2f}</text>')

    partes.append(f'<line class="identidade" x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}"/>')

    extremos = {"53", "21", "35", "42"}
    for cod, x, y in zip(comp["codigos"], xs, ys):
        sigla = comp_uf_sigla(comp, cod)
        cls = "ponto extremo" if cod in extremos else "ponto"
        partes.append(f'<circle class="{cls}" cx="{px(x):.1f}" cy="{py(y):.1f}" r="4.6"><title>{sigla}: oficial {fmt(x)} · estimado {fmt(y)}</title></circle>')
        if cod in extremos:
            partes.append(f'<text class="ponto-label" x="{px(x) + 7:.1f}" y="{py(y) - 6:.1f}">{sigla}</text>')

    partes.append(f'<text class="eixo-texto" x="{(esq + largura - dir_) / 2:.1f}" y="{altura - 14:.1f}" text-anchor="middle">IDHM oficial 2024 (Atlas/IpeaData)</text>')
    partes.append(f'<text class="eixo-texto" transform="rotate(-90 14 {(altura - base + topo) / 2:.1f})" x="14" y="{(altura - base + topo) / 2:.1f}" text-anchor="middle">IDH estimado 2025 (IBGE)</text>')
    return (
        f'<svg id="dispersao" viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="Dispersão entre IDHM oficial e IDH estimado">'
        + "".join(partes)
        + "</svg>"
    )


def comp_uf_sigla(comp: dict, cod: str) -> str:
    for r in comp["linhas"]:
        if r["cod"] == cod:
            return r["sigla"]
    return cod


# ---------------------------------------------------------------------------
# paginas
# ---------------------------------------------------------------------------


def nav_html(pagina: str) -> str:
    itens = []
    for href, rotulo in NAV:
        atual = ' aria-current="page"' if href == pagina else ""
        itens.append(f'<a href="{href}"{atual}>{rotulo}</a>')
    return '<nav class="menu"><div class="wrap">' + "".join(itens) + "</div></nav>"


def pagina(titulo: str, pagina_atual: str, corpo: str, subtitulo: str = "") -> str:
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<link rel="stylesheet" href="assets/estilo.css">
</head>
<body>
<header class="topo">
  <div class="wrap">
    <div class="kicker">Desenvolvimento humano · Análise territorial</div>
    <h1>{titulo}</h1>
    {sub}
  </div>
</header>
{nav_html(pagina_atual)}
<main>
{corpo}
</main>
<footer class="rodape">
  Elaboração própria. IDH estimado 2025 (IBGE) e IDHM oficial 2024 (Atlas/IpeaData) são
  indicadores distintos — compare apenas dentro da mesma camada.
</footer>
<div class="tooltip" id="tooltip"></div>
<script src="assets/dados.js"></script>
<script src="assets/site.js"></script>
</body>
</html>
"""


def legenda_html(cortes: list[float], cores: list[str], titulo: str) -> str:
    faixas = []
    for i in range(len(cortes) - 1):
        faixas.append(
            f'<div class="faixa"><span class="cor" style="background:{cores[i]}"></span>'
            f"<span>{fmt(cortes[i])} – {fmt(cortes[i + 1])}</span></div>"
        )
    return (
        '<div class="legenda"><div class="titulo" id="legenda-titulo">'
        + titulo
        + '</div><div class="faixas" id="legenda-faixas">'
        + "".join(faixas)
        + "</div></div>"
    )


def destaques_html(ufs: dict) -> str:
    lista = sorted(ufs.values(), key=lambda d: d["idh"], reverse=True)
    topo, base = lista[0], lista[-1]
    media = sum(d["idh"] for d in lista) / len(lista)
    itens = [
        ("Maior índice", fmt(topo["idh"]), f'{topo["nome"]} ({topo["sigla"]})'),
        ("Menor índice", fmt(base["idh"]), f'{base["nome"]} ({base["sigla"]})'),
        ("Gap absoluto", fmt(topo["idh"] - base["idh"]), "maior menos menor"),
        ("Razão maior/menor", fmt(topo["idh"] / base["idh"], 2) + "×", "desigualdade relativa"),
        ("Média simples das UFs", fmt(media), "não ponderada por população"),
    ]
    return "".join(
        f'<div class="destaque-box"><div class="rotulo-peq">{r}</div>'
        f'<div class="valor">{v}</div><div class="quem">{q}</div></div>'
        for r, v, q in itens
    )


def linhas_tabela(ufs: dict, cortes: list[float], cores: list[str], extra: bool) -> str:
    linhas = []
    for d in sorted(ufs.values(), key=lambda x: x["posicao"]):
        k = classe_de(d["idh"], cortes)
        linha = (
            "<tr>"
            f'<td class="pos">{d["posicao"]}º</td>'
            f'<td><span class="chip" style="background:{cores[k]}"></span>{d["nome"]} '
            f'<span class="sigla">{d["sigla"]}</span></td>'
            f'<td class="num destaque">{fmt(d["idh"])}</td>'
            f'<td class="num">{fmt(d["renda"])}</td>'
            f'<td class="num">{fmt(d["educacao"])}</td>'
            f'<td class="num">{fmt(d["longevidade"])}</td>'
        )
        if extra:
            linha += (
                f'<td class="num" data-col-extra>R$ {fmt_int(d["renda_per_capita"])}</td>'
                f'<td class="num" data-col-extra">{fmt(d["anos_estudo"], 1)}</td>'
                f'<td class="num" data-col-extra">{fmt(d["esperanca_vida"], 1)}</td>'
            )
        linhas.append(linha + "</tr>")
    return "\n".join(linhas)


def pagina_index(est: dict, ofi: dict, svg: str) -> str:
    cortes = classes([d["idh"] for d in est["ufs"].values()])
    br_e = est["brasil_referencia"]
    br_o = ofi["brasil"]
    topo = max(ofi["ufs"].values(), key=lambda d: d["idh"])
    base = min(ofi["ufs"].values(), key=lambda d: d["idh"])

    corpo = f"""
<div class="alerta">
  <strong>Leia antes de citar:</strong> o IBGE não calcula nem publica IDH/IDHM. O
  <strong>IDH estimado 2025</strong> é uma estimativa própria, feita com componentes
  oficiais do IBGE, adequada para comparar estados entre si. O <strong>IDHM oficial 2024</strong>
  vem do Atlas do Desenvolvimento Humano (PNUD/Ipea/FJP), obtido pela API do IpeaData.
  São índices diferentes: não compare um valor da camada estimada com um valor oficial.
</div>

<div class="kpis">
  <div class="kpi"><div class="rot">IDH estimado 2025 · Brasil</div>
    <div class="val">{fmt(br_e["idh"])}</div><div class="quem">estimativa própria com dados do IBGE</div></div>
  <div class="kpi"><div class="rot">IDHM oficial 2024 · Brasil</div>
    <div class="val">{fmt(br_o["idh"])}</div><div class="quem">Atlas do Desenvolvimento Humano</div></div>
  <div class="kpi"><div class="rot">Maior UF no IDHM oficial</div>
    <div class="val">{fmt(topo["idh"])}</div><div class="quem">{topo["nome"]} ({topo["sigla"]})</div></div>
  <div class="kpi"><div class="rot">Menor UF no IDHM oficial</div>
    <div class="val">{fmt(base["idh"])}</div><div class="quem">{base["nome"]} ({base["sigla"]})</div></div>
</div>

<section class="card">
  <h2>Mapa por unidade da federação</h2>
  <p class="sub">Escolha a camada e a dimensão. Passe o mouse sobre um estado para ver os valores.</p>
  <div class="controles">
    <span class="grupo-rot">Camada</span>
    <button data-camada="estimado" class="ativo">IDH estimado 2025 · IBGE</button>
    <button data-camada="oficial">IDHM oficial 2024 · Atlas/Ipea</button>
  </div>
  <div class="controles">
    <span class="grupo-rot">Dimensão</span>
    <button data-var="idh" class="ativo">Índice</button>
    <button data-var="renda">Renda</button>
    <button data-var="educacao">Educação</button>
    <button data-var="longevidade">Longevidade</button>
  </div>
  <div class="layout">
    <div>
      {svg}
      <p class="nota-mapa" id="nota-mapa">Cor mais escura = maior IDH estimado. Escala ajustada ao intervalo dos estados.</p>
    </div>
    <div>
      {legenda_html(cortes, CORES_ESTIMADO, "IDH estimado 2025")}
      <div class="acoes">
        <button id="btn-csv">Baixar CSV da camada</button>
        <button id="btn-print">Imprimir / PDF</button>
      </div>
      <p class="nota-mapa">Camada ativa: <strong data-tag-camada>IDH estimado 2025</strong></p>
    </div>
  </div>
</section>

<section class="card">
  <h2>Destaques</h2>
  <p class="sub">Calculados sobre a camada ativa do mapa.</p>
  <div class="destaques" id="destaques">
    {destaques_html(est["ufs"])}
  </div>
</section>

<section class="card">
  <h2>Explore</h2>
  <div class="grid-cards">
    <a class="card-link" href="estados.html">
      <div class="titulo">Ranking por estado</div>
      <div class="desc">Tabela completa das 27 UFs, com busca, ordenação e as duas camadas.</div>
    </a>
    <a class="card-link" href="comparacao.html">
      <div class="titulo">Estimado × oficial</div>
      <div class="desc">Dispersão, correlação e as maiores divergências entre as duas camadas.</div>
    </a>
    <a class="card-link" href="metodologia.html">
      <div class="titulo">Metodologia</div>
      <div class="desc">Fórmulas, insumos do IBGE, série oficial do IpeaData e limitações.</div>
    </a>
    <a class="card-link" href="dados.html">
      <div class="titulo">Dados</div>
      <div class="desc">Downloads em CSV e JSON, fontes e comandos para reproduzir.</div>
    </a>
  </div>
</section>
"""
    return pagina(
        "IDH no Brasil — mapa interativo",
        "index.html",
        corpo,
        "Duas camadas: IDH estimado 2025 com dados do IBGE e IDHM oficial 2024 do Atlas, "
        "obtido pela API do IpeaData.",
    )


def pagina_estados(est: dict, ofi: dict) -> str:
    cortes_e = classes([d["idh"] for d in est["ufs"].values()])
    cortes_o = classes([d["idh"] for d in ofi["ufs"].values()])

    corpo = f"""
<section class="card">
  <h2>Ranking por unidade da federação</h2>
  <p class="sub">Use a busca e a ordenação. A camada <strong>estimada</strong> inclui os insumos
  do IBGE; a <strong>oficial</strong> traz o IDHM e as dimensões do Atlas.</p>
  <div class="controles">
    <span class="grupo-rot">Camada</span>
    <button data-camada="estimado" class="ativo">IDH estimado 2025</button>
    <button data-camada="oficial">IDHM oficial 2024</button>
  </div>
  <div class="filtros">
    <input id="busca" type="search" placeholder="Buscar UF ou estado…" aria-label="Buscar UF">
    <select id="ordem" aria-label="Ordenar por">
      <option value="posicao">Ordenar por posição</option>
      <option value="nome">Ordenar por nome</option>
      <option value="idh">Ordenar por índice</option>
      <option value="renda">Ordenar por renda</option>
      <option value="educacao">Ordenar por educação</option>
      <option value="longevidade">Ordenar por longevidade</option>
    </select>
    <button id="btn-csv" class="botao" style="border:1px solid var(--borda);background:#fff;padding:8px 11px;border-radius:6px;cursor:pointer;font-weight:600;color:var(--azul);">Baixar CSV</button>
  </div>
  <div class="tabela-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th><th>Unidade da Federação</th><th>Índice</th>
          <th>Renda</th><th>Educação</th><th>Longevidade</th>
          <th data-col-extra>Renda per capita</th><th data-col-extra>Anos de estudo</th>
          <th data-col-extra>Esperança de vida</th>
        </tr>
      </thead>
      <tbody id="corpo-tabela">
        {linhas_tabela(est["ufs"], cortes_e, CORES_ESTIMADO, True)}
      </tbody>
    </table>
  </div>
  <p class="nota-mapa">Valores de índice e dimensões variam de 0 a 1. Renda per capita em reais
  correntes de 2025. Camada ativa: <strong data-tag-camada>IDH estimado 2025</strong>.</p>
</section>

<section class="card">
  <h2>Como ler a tabela</h2>
  <div class="two-col">
    <div>
      <h3>Camada estimada (2025)</h3>
      <p>Índice calculado neste repositório com renda domiciliar per capita, anos de estudo,
      escolarização e esperança de vida projetada. Serve para comparar UFs no mesmo ano.</p>
    </div>
    <div>
      <h3>Camada oficial (2024)</h3>
      <p>IDHM e dimensões publicados pelo Atlas do Desenvolvimento Humano e reproduzidos pela
      API do IpeaData. É o valor oficial mais recente disponível por UF.</p>
    </div>
  </div>
</section>
"""
    return pagina(
        "Ranking por estado",
        "estados.html",
        corpo,
        "As 27 unidades da federação nas duas camadas, com os componentes de cada índice.",
    )


def pagina_comparacao(est: dict, ofi: dict, comp: dict) -> str:
    divergencias = comp["linhas"][:8]
    linhas = []
    for r in divergencias:
        sinal = "+" if r["diff"] >= 0 else "−"
        delta_pos = r["pos_ofi"] - r["pos_est"]
        pos = "=" if delta_pos == 0 else (f"+{delta_pos}" if delta_pos > 0 else str(delta_pos))
        linhas.append(
            "<tr>"
            f'<td>{r["nome"]} <span class="sigla">{r["sigla"]}</span></td>'
            f'<td class="num">{fmt(r["oficial"])}</td>'
            f'<td class="num">{fmt(r["estimado"])}</td>'
            f'<td class="num">{sinal}{fmt(abs(r["diff"]))}</td>'
            f'<td class="num">{r["pos_ofi"]}º</td>'
            f'<td class="num">{r["pos_est"]}º</td>'
            f'<td class="num">{pos}</td>'
            "</tr>"
        )

    corpo = f"""
<div class="kpis">
  <div class="kpi"><div class="rot">Correlação de Pearson</div><div class="val">{fmt(comp["r"], 3)}</div>
    <div class="quem">entre as duas camadas (n = {comp["n"]})</div></div>
  <div class="kpi"><div class="rot">Correlação de Spearman</div><div class="val">{fmt(comp["rho"], 3)}</div>
    <div class="quem">ordenação das UFs</div></div>
  <div class="kpi"><div class="rot">Diferença média absoluta</div><div class="val">{fmt(comp["media_abs"], 3)}</div>
    <div class="quem">estimado menos oficial</div></div>
  <div class="kpi"><div class="rot">Maior divergência</div><div class="val">{fmt(comp["max_abs"], 3)}</div>
    <div class="quem">{comp["max_nome"]}</div></div>
</div>

<section class="card">
  <h2>Dispersão: IDHM oficial × IDH estimado</h2>
  <p class="sub">Cada ponto é uma UF. A linha tracejada é a identidade (y = x). Pontos abaixo dela
  indicam estimativa menor que o valor oficial.</p>
  <div class="scatter-wrap">{dispersao_svg(comp)}</div>
</section>

<section class="card">
  <h2>Maiores divergências</h2>
  <p class="sub">Ordenadas pela diferença absoluta. Posição 1º = maior índice.</p>
  <div class="tabela-wrap">
    <table>
      <thead>
        <tr><th>UF</th><th>IDHM 2024</th><th>IDH est. 2025</th><th>Diferença</th>
        <th>Pos. oficial</th><th>Pos. estimada</th><th>Δ posição</th></tr>
      </thead>
      <tbody>
        {''.join(linhas)}
      </tbody>
    </table>
  </div>
</section>

<section class="card">
  <h2>Por que os níveis são diferentes</h2>
  <p>As duas camadas medem desenvolvimento humano, mas não são a mesma coisa:</p>
  <ul>
    <li><strong>Renda:</strong> o IDHM usa a renda municipal per capita em reais de 2010; o IDH
    estimado usa renda domiciliar per capita de 2025 convertida por paridade de poder de compra.
    Conceitos e anos diferentes explicam a maior parte do nível mais baixo da estimativa.</li>
    <li><strong>Educação:</strong> o IDHM usa anos de estudo e anos esperados de estudo; aqui os
    anos esperados são aproximados pela taxa de escolarização por grupo de idade.</li>
    <li><strong>Longevidade:</strong> o IDHM usa a esperança de vida do período do Atlas; aqui é a
    projeção do IBGE para 2025.</li>
    <li><strong>Ano:</strong> 2024 no oficial e 2025 na estimativa. Não é uma série temporal.</li>
  </ul>
  <p>A correlação alta mostra que a estimativa preserva a <strong>ordenação relativa</strong> dos
  estados. O nível absoluto, porém, não deve ser comparado entre camadas.</p>
</section>
"""
    return pagina(
        "Estimado × oficial",
        "comparacao.html",
        corpo,
        "Onde a estimativa de 2025 acompanha — e onde se afasta — do IDHM oficial de 2024.",
    )


def pagina_metodologia(est: dict, ofi: dict) -> str:
    fontes = est.get("fontes", {})
    ppp = fmt(fontes.get("ppp", 0), 4)
    ano_ofi = ofi.get("ano", 2024)
    serie = ofi.get("serie_idh_pnud_brasil", {})
    ultimo_ano = max(serie) if serie else None
    ultimo_valor = serie[ultimo_ano] if ultimo_ano else None

    corpo = f"""
<section class="card metodologia">
  <h2>Camada 1 — IDH estimado 2025</h2>
  <p class="sub">Estimativa própria com insumos oficiais do IBGE. Não é o IDH do PNUD nem o IDHM do Atlas.</p>

  <h3>Renda</h3>
  <p>Rendimento médio mensal real domiciliar per capita (PNAD Contínua, agregado 7395,
  variável 4196, 2025), anualizado e convertido para dólares de paridade de poder de compra
  pelo fator <code>{ppp}</code> (Banco Mundial, PA.NUS.PPP, 2025).</p>
  <p><code>I_renda = [ln(renda PPC) − ln(100)] / [ln(75.000) − ln(100)]</code></p>

  <h3>Educação</h3>
  <p>Média de anos de estudo das pessoas de 25 anos ou mais (agregado 7126, variável 3593) e
  taxa de escolarização por grupo de idade (agregado 7138, variável 10276), usada para estimar
  os anos esperados de estudo:</p>
  <p><code>anos esperados = 9 × escolarização(6–14) + 3 × escolarização(15–17) + 7 × escolarização(18–24)</code></p>
  <p><code>I_educação = [min(anos de estudo, 18) / 18 + min(anos esperados, 15) / 15] / 2</code></p>

  <h3>Longevidade</h3>
  <p>Esperança de vida ao nascer projetada para 2025 nas Projeções da População — Revisão 2024
  (IBGE).</p>
  <p><code>I_longevidade = (esperança de vida − 20) / (85 − 20)</code></p>

  <h3>Índice final</h3>
  <p><code>IDH estimado = (I_renda × I_educação × I_longevidade)^(1/3)</code></p>
</section>

<section class="card metodologia">
  <h2>Camada 2 — IDHM oficial {ano_ofi}</h2>
  <p class="sub">Atlas do Desenvolvimento Humano no Brasil (PNUD, Ipea e FJP), via API do IpeaData.</p>
  <p>O IDHM é o IDH adaptado à realidade municipal brasileira. Para as UFs, o valor más recente
  publicado é <strong>{ano_ofi}</strong>. As séries usadas são:</p>
  <ul>
    <li><code>IDHM</code> — índice completo;</li>
    <li><code>IDHMED</code> — dimensão educação;</li>
    <li><code>IDHMLO</code> — dimensão longevidade;</li>
    <li><code>IDHMRE</code> — dimensão renda.</li>
  </ul>
  <p>Endpoint: <code>http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='IDHM')</code>,
  filtrando <code>NIVNOME = "Estados"</code> e o ano {ano_ofi}.</p>
  <p>O IDH global do PNUD para o Brasil é outra série (<code>PNUD_IDH</code>), com último valor
  <strong>{fmt(ultimo_valor) if ultimo_valor else "n/d"}</strong> em {ultimo_ano or "n/d"}.
  Não usar o IDH global no lugar do IDHM.</p>
</section>

<section class="card metodologia">
  <h2>Faixas de classificação</h2>
  <p>As réguas do IDH (PNUD) e do IDHM (Atlas) são diferentes no intervalo médio e baixo.</p>
  <div class="tabela-wrap">
    <table>
      <thead><tr><th>Faixa</th><th>IDH (PNUD)</th><th>IDHM (Atlas)</th></tr></thead>
      <tbody>
        <tr><td>Muito alto</td><td class="num">≥ 0,800</td><td class="num">0,800 – 1,000</td></tr>
        <tr><td>Alto</td><td class="num">0,700 – 0,799</td><td class="num">0,700 – 0,799</td></tr>
        <tr><td>Médio</td><td class="num">0,550 – 0,699</td><td class="num">0,600 – 0,699</td></tr>
        <tr><td>Baixo</td><td class="num">&lt; 0,550</td><td class="num">0,500 – 0,599</td></tr>
        <tr><td>Muito baixo</td><td class="num">—</td><td class="num">0,000 – 0,499</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="card metodologia">
  <h2>Limitações</h2>
  <ul>
    <li>O IDH usa RNB per capita em PPC; aqui usamos renda domiciliar per capita, que tende a ser menor.</li>
    <li>A esperança de vida de 2025 é projetada, não observada.</li>
    <li>A educação usa aproximação para os anos esperados de estudo.</li>
    <li>A PNAD Contínua é amostral: diferenças pequenas entre estados podem não ser significativas.</li>
    <li>O IDHM oficial é de {ano_ofi}; a estimativa é de 2025. Não formar série temporal com as duas.</li>
    <li>Correlação entre as camadas não implica causalidade.</li>
  </ul>
</section>
"""
    return pagina(
        "Metodologia",
        "metodologia.html",
        corpo,
        "Como cada camada é construída, quais insumos entram e o que não pode ser comparado.",
    )


def pagina_dados(est: dict, ofi: dict) -> str:
    fontes = est.get("fontes", {})
    corpo = f"""
<section class="card">
  <h2>Downloads</h2>
  <p class="sub">Arquivos usados nas páginas, em CSV (separador ponto e vírgula, UTF-8 com BOM)
  e JSON.</p>
  <div class="tabela-wrap">
    <table>
      <thead><tr><th>Arquivo</th><th>Conteúdo</th><th>Formato</th></tr></thead>
      <tbody>
        <tr><td><a href="dados/idh_2025_uf.csv">idh_2025_uf.csv</a></td>
          <td>IDH estimado 2025 por UF, com os três subíndices e insumos</td><td>CSV</td></tr>
        <tr><td><a href="dados/idh_2025_uf.json">idh_2025_uf.json</a></td>
          <td>Mesmos dados + metodologia e fontes</td><td>JSON</td></tr>
        <tr><td><a href="dados/idhm_oficial_2024_uf.csv">idhm_oficial_2024_uf.csv</a></td>
          <td>IDHM oficial 2024 por UF e dimensões</td><td>CSV</td></tr>
        <tr><td><a href="dados/idhm_oficial_2024_uf.json">idhm_oficial_2024_uf.json</a></td>
          <td>IDHM oficial + Brasil + série do IDH global</td><td>JSON</td></tr>
        <tr><td><a href="dados/idh_oficial_pnud_brasil.csv">idh_oficial_pnud_brasil.csv</a></td>
          <td>Série do IDH global do Brasil (PNUD), 1990–2023</td><td>CSV</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="card">
  <h2>Fontes</h2>
  <ul class="fontes">
    <li>IBGE. <em>PNAD Contínua</em> — agregados 7395, 7113, 7126 e 7138, 2025.
      <a href="https://servicodados.ibge.gov.br/api/docs/agregados?versao=3">API de Agregados v3</a>.</li>
    <li>IBGE. <em>Projeções da População — Revisão 2024</em> — esperança de vida ao nascer, 2025.
      <a href="https://www.ibge.gov.br/estatisticas/sociais/populacao/9109-projecao-da-populacao.html">Página oficial</a>.</li>
    <li>IBGE. <em>Malha territorial</em> — API v3 de malhas, UFs.</li>
    <li>Banco Mundial. <em>PPP conversion factor, GDP (LCU per international $)</em> — PA.NUS.PPP, Brasil, 2025.</li>
    <li>PNUD/Ipea/FJP. <em>Atlas do Desenvolvimento Humano no Brasil</em> — IDHM oficial.
      <a href="https://www.atlasbrasil.org.br/">atlasbrasil.org.br</a>.</li>
    <li>Ipea. <em>IpeaData</em> — séries IDHM, IDHMED, IDHMLO, IDHMRE e PNUD_IDH.
      <a href="http://www.ipeadata.gov.br/api/odata4/">API OData v4</a>.</li>
  </ul>
</section>

<section class="card metodologia">
  <h2>Reproduzir</h2>
  <p>Na raiz do repositório:</p>
  <pre><code>python .opencode/skills/analise-idh-ibge/coleta_ipea.py
python .opencode/skills/analise-idh-ibge/gera_mapa_idh.py
python .opencode/skills/site-idh-ibge/gera_site.py
python .opencode/skills/site-idh-ibge/servir.py</code></pre>
  <p>O primeiro comando baixa o IDHM oficial; o segundo coleta o IBGE e gera o mapa
  autocontido; o terceiro monta este site; o quarto sobe um servidor local em
  <code>http://localhost:8000</code>.</p>
  <p>Parâmetros da estimativa: INPC médio de 2010 = {fmt(fontes.get("inpc2010", 0), 2)},
  INPC médio de 2025 = {fmt(fontes.get("inpc2025", 0), 2)}, PPP = {fmt(fontes.get("ppp", 0), 4)}.
  Dados gerados em {est.get("gerado_em", "n/d")[:10]}.</p>
</section>
"""
    return pagina(
        "Dados e fontes",
        "dados.html",
        corpo,
        "Arquivos para download, links das fontes e comandos para reconstruir o site.",
    )


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


def copiar_dados() -> None:
    destino = SITE / "dados"
    destino.mkdir(parents=True, exist_ok=True)
    for nome in (
        "idh_2025_uf.csv",
        "idh_2025_uf.json",
        "idhm_oficial_2024_uf.csv",
        "idhm_oficial_2024_uf.json",
        "idh_oficial_pnud_brasil.csv",
    ):
        origem = DADOS / nome
        if origem.exists():
            shutil.copy2(origem, destino / nome)


def main() -> None:
    est, ofi = carregar()
    ASSETS.mkdir(parents=True, exist_ok=True)
    SITE.mkdir(parents=True, exist_ok=True)

    malha = json.loads((DADOS / "malha_uf.geojson").read_text(encoding="utf-8"))
    cortes = classes([d["idh"] for d in est["ufs"].values()])
    svg, _ = gerar_mapa(malha, est, cortes)

    comp = comparar(est, ofi)

    (ASSETS / "estilo.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (ASSETS / "site.js").write_text(JS.strip() + "\n", encoding="utf-8")
    (ASSETS / "dados.js").write_text(
        "window.DADOS_SITE = " + json.dumps(dados_js(est, ofi), ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    paginas = {
        "index.html": pagina_index(est, ofi, svg),
        "estados.html": pagina_estados(est, ofi),
        "comparacao.html": pagina_comparacao(est, ofi, comp),
        "metodologia.html": pagina_metodologia(est, ofi),
        "dados.html": pagina_dados(est, ofi),
    }
    for nome, html in paginas.items():
        (SITE / nome).write_text(html, encoding="utf-8")

    copiar_dados()

    hoje = datetime.now().strftime("%d/%m/%Y")
    print(f"Site gerado em {SITE} ({hoje})")
    for nome in paginas:
        print(f"  - {nome}")
    print(f"  - assets/estilo.css, assets/site.js, assets/dados.js")
    print(f"  - dados/ (CSVs e JSONs para download)")
    print(f"Correlação estimado x oficial: r={comp['r']:.3f} | rho={comp['rho']:.3f}")
    print("Abra site/index.html ou rode: python .opencode/skills/site-idh-ibge/servir.py")


if __name__ == "__main__":
    main()
