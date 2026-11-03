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
    const blob = new Blob(["\ufeff" + linhas.join("\n")], { type: "text/csv;charset=utf-8" });
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
