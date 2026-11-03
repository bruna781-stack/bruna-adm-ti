#!/usr/bin/env python3
"""Gera um mapa coropletico do IDH estimado 2025 por UF, com dados do IBGE.

O script NAO produz o IDH oficial. Ele calcula uma estimativa propria, com
metodologia inspirada no IDH/IDHM, usando apenas dados de 2025 do IBGE:

  - renda: PNAD Continua, agregado 7395 (rendimento domiciliar per capita)
  - educacao: PNAD Continua, agregados 7126 (anos de estudo) e 7138
    (taxa de escolarizacao por grupo de idade)
  - longevidade: Projecoes da Populacao 2024, esperanca de vida projetada 2025

A camada oficial (IDHM 2024, Atlas/IpeaData) e o site com as duas camadas
ficam no skill site-idh-ibge.

Saidas:
  dados/idh_2025_uf.json
  dados/idh_2025_uf.csv
  mapa-idh-2025.html

Uso:
  python .opencode/skills/analise-idh-ibge/gera_mapa_idh.py
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DADOS = ROOT / "dados"
HTML_SAIDA = ROOT / "mapa-idh-2025.html"

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
MALHA = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
)
PROJECOES_XLSX = (
    "https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/"
    "projecoes_2024_tab4_indicadores.xlsx"
)
PPP_WORLD_BANK = (
    "https://api.worldbank.org/v2/country/BRA/indicator/PA.NUS.PPP"
    "?format=json&per_page=5&date=2025"
)
USER_AGENT = "analise-idh-ibge/1.0 (mapa IDH 2025)"

# Plano B caso o download das projecoes falhe (valores extraidos do xlsx oficial).
E0_FALLBACK = {
    "RO": 76.2252, "AC": 76.0814, "AM": 75.7119, "RR": 74.6072, "PA": 76.4718,
    "AP": 74.5821, "TO": 76.8830, "MA": 75.8473, "PI": 77.1606, "CE": 77.4513,
    "RN": 78.0117, "PB": 77.0250, "PE": 75.7526, "AL": 74.6542, "SE": 76.5768,
    "BA": 76.0363, "MG": 77.7012, "ES": 77.3812, "RJ": 75.8537, "SP": 77.2214,
    "PR": 77.0523, "SC": 78.4371, "RS": 77.3574, "MS": 75.6237, "MT": 75.9425,
    "GO": 76.9837, "DF": 79.8933,
}
E0_BRASIL_FALLBACK = 76.8177
PPP_FALLBACK = 2.5544

# Paleta sequencial (claro -> escuro), 6 classes.
CORES = ["#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3", "#2b8cbe"]
CORES_ESCURAS = [False, False, False, True, True, True]

UF_NOMES = {
    "11": ("RO", "Rondônia"), "12": ("AC", "Acre"), "13": ("AM", "Amazonas"),
    "14": ("RR", "Roraima"), "15": ("PA", "Pará"), "16": ("AP", "Amapá"),
    "17": ("TO", "Tocantins"), "21": ("MA", "Maranhão"), "22": ("PI", "Piauí"),
    "23": ("CE", "Ceará"), "24": ("RN", "Rio Grande do Norte"),
    "25": ("PB", "Paraíba"), "26": ("PE", "Pernambuco"), "27": ("AL", "Alagoas"),
    "28": ("SE", "Sergipe"), "29": ("BA", "Bahia"), "31": ("MG", "Minas Gerais"),
    "32": ("ES", "Espírito Santo"), "33": ("RJ", "Rio de Janeiro"),
    "35": ("SP", "São Paulo"), "41": ("PR", "Paraná"),
    "42": ("SC", "Santa Catarina"), "43": ("RS", "Rio Grande do Sul"),
    "50": ("MS", "Mato Grosso do Sul"), "51": ("MT", "Mato Grosso"),
    "52": ("GO", "Goiás"), "53": ("DF", "Distrito Federal"),
}

# Pequenos deslocamentos para os rotulos dos estados menores.
OFFSETS = {
    "53": (10, -4), "33": (8, 2), "32": (9, 2), "27": (9, 2), "28": (8, 3),
    "24": (4, 4), "25": (7, 2), "26": (7, 3), "31": (-4, 2), "35": (5, 1),
    "21": (-2, 2), "16": (0, 0), "14": (0, 0),
}


def encode(url: str) -> str:
    return url.replace("[", "%5B").replace("]", "%5D").replace("|", "%7C")


def get_json(url: str, timeout: int = 90):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, */*"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        bruto = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip":
            bruto = gzip.decompress(bruto)
        return json.loads(bruto.decode("utf-8"))


def get_bytes(url: str, timeout: int = 180) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def serie_por_uf(agregado: int, variavel: int, periodo: int, filtro: str = "") -> dict[str, float]:
    url = (
        f"{BASE}/{agregado}/periodos/{periodo}/variaveis/{variavel}"
        f"?localidades=N3[all]{filtro}"
    )
    payload = get_json(encode(url))
    valores: dict[str, float] = {}
    for var in payload:
        for resultado in var.get("resultados", []):
            for serie in resultado.get("series", []):
                bruto = serie.get("serie", {}).get(str(periodo))
                if bruto in (None, "", "...", "-", "X"):
                    continue
                try:
                    valores[serie["localidade"]["id"]] = float(bruto)
                except (TypeError, ValueError):
                    continue
    return valores


def serie_brasil(agregado: int, variavel: int, periodo: int, filtro: str = "") -> float | None:
    url = (
        f"{BASE}/{agregado}/periodos/{periodo}/variaveis/{variavel}"
        f"?localidades=N1[all]{filtro}"
    )
    payload = get_json(encode(url))
    for var in payload:
        for resultado in var.get("resultados", []):
            for serie in resultado.get("series", []):
                bruto = serie.get("serie", {}).get(str(periodo))
                try:
                    return float(bruto)
                except (TypeError, ValueError):
                    return None
    return None


def inpc_medio(ano: int) -> float:
    meses = ",".join(f"{ano}{mes:02d}" for mes in range(1, 13))
    url = f"{BASE}/1736/periodos/{meses}/variaveis/2289?localidades=N1[all]"
    payload = get_json(url)
    serie = payload[0]["resultados"][0]["series"][0]["serie"]
    valores = [float(v) for k, v in sorted(serie.items()) if v not in ("", "...", "-")]
    if not valores:
        raise RuntimeError(f"INPC sem valores para {ano}")
    return sum(valores) / len(valores)


def esperanca_vida_2025() -> tuple[dict[str, float], float, str]:
    """Le a esperanca de vida projetada para 2025 no xlsx das projecoes."""
    destino = DADOS / "projecoes_2024_tab4_indicadores.xlsx"
    try:
        if not destino.exists():
            DADOS.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(get_bytes(PROJECOES_XLSX))
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(destino, read_only=True, data_only=True)
        ws = wb["4) INDICADORES"]
        por_sigla: dict[str, float] = {}
        brasil = None
        for row in ws.iter_rows(min_row=8, values_only=True):
            if str(row[0]) != "2025":
                continue
            sigla = str(row[2]).strip() if row[2] else ""
            cod = str(row[1]).strip() if row[1] else ""
            e0 = row[20]
            if e0 is None:
                continue
            if cod == "0":
                brasil = float(e0)
            elif sigla in E0_FALLBACK:
                por_sigla[sigla] = float(e0)
        if len(por_sigla) == 27:
            return por_sigla, brasil or E0_BRASIL_FALLBACK, str(destino)
    except Exception as erro:  # noqa: BLE001
        print(f"[aviso] projecoes: usando plano B ({erro})", file=sys.stderr)
    return dict(E0_FALLBACK), E0_BRASIL_FALLBACK, "valores embutidos no script"


def ppp_brasil() -> tuple[float, str]:
    try:
        payload = get_json(PPP_WORLD_BANK)
        valor = payload[1][0]["value"]
        if valor:
            return float(valor), "World Bank, PA.NUS.PPP (2025)"
    except Exception as erro:  # noqa: BLE001
        print(f"[aviso] PPP: usando plano B ({erro})", file=sys.stderr)
    return PPP_FALLBACK, "valor de referencia 2025 (World Bank)"


def calcular(
    renda: dict[str, float],
    analfabetismo: dict[str, float],
    anos_estudo: dict[str, float],
    escolar_614: dict[str, float],
    escolar_1517: dict[str, float],
    escolar_1824: dict[str, float],
    e0: dict[str, float],
    inpc2010: float,
    inpc2025: float,
    ppp: float,
) -> dict[str, dict]:
    resultado: dict[str, dict] = {}
    for cod, (sigla, nome) in UF_NOMES.items():
        r = renda[cod]
        renda_ppp = (r * 12) / ppp
        i_renda = (math.log(renda_ppp) - math.log(100)) / (math.log(75000) - math.log(100))
        i_renda = max(0.0, min(1.0, i_renda))

        anos_esperados = (
            9 * escolar_614[cod] / 100
            + 3 * escolar_1517[cod] / 100
            + 7 * escolar_1824[cod] / 100
        )
        anos_esperados = max(0.0, min(15.0, anos_esperados))
        i_educacao = (
            min(18.0, anos_estudo[cod]) / 18 + anos_esperados / 15
        ) / 2

        i_longevidade = (e0[sigla] - 20) / (85 - 20)
        i_longevidade = max(0.0, min(1.0, i_longevidade))

        idh = (i_renda * i_educacao * i_longevidade) ** (1 / 3)
        resultado[cod] = {
            "codigo": cod,
            "sigla": sigla,
            "nome": nome,
            "idh": idh,
            "renda": i_renda,
            "educacao": i_educacao,
            "longevidade": i_longevidade,
            "renda_per_capita": r,
            "renda_ppp": renda_ppp,
            "anos_estudo": anos_estudo[cod],
            "analfabetismo": analfabetismo[cod],
            "anos_esperados": anos_esperados,
            "esperanca_vida": e0[sigla],
            "inpc2010": inpc2010,
            "inpc2025": inpc2025,
        }
    ordenado = sorted(resultado.values(), key=lambda x: x["idh"], reverse=True)
    for posicao, item in enumerate(ordenado, start=1):
        resultado[item["codigo"]]["posicao"] = posicao
    return resultado


def classes(valores: list[float], n: int = 6) -> list[float]:
    lo, hi = min(valores), max(valores)
    if hi == lo:
        return [lo] * (n + 1)
    passo = (hi - lo) / n
    return [lo + i * passo for i in range(n + 1)]


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


def carregar_malha() -> dict:
    destino = DADOS / "malha_uf.geojson"
    if destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    DADOS.mkdir(parents=True, exist_ok=True)
    payload = get_json(MALHA, timeout=120)
    destino.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def projetar(lon: float, lat: float) -> tuple[float, float]:
    x = math.radians(lon)
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def gerar_svg(malha: dict, dados: dict[str, dict]) -> tuple[str, dict[str, tuple[float, float]]]:
    largura, altura, margem = 760, 760, 18
    pontos: list[tuple[float, float]] = []
    aneis_por_uf: dict[str, list[list[tuple[float, float]]]] = {}

    for feature in malha["features"]:
        cod = str(feature["properties"]["codarea"])
        geom = feature["geometry"]
        poligonos = (
            [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        )
        aneis: list[list[tuple[float, float]]] = []
        for poligono in poligonos:
            for anel in poligono:
                convertido = [projetar(lon, lat) for lon, lat in anel]
                aneis.append(convertido)
                pontos.extend(convertido)
        aneis_por_uf[cod] = aneis

    minx = min(p[0] for p in pontos)
    maxx = max(p[0] for p in pontos)
    miny = min(p[1] for p in pontos)
    maxy = max(p[1] for p in pontos)
    escala = min(
        (largura - 2 * margem) / (maxx - minx),
        (altura - 2 * margem) / (maxy - miny),
    )
    sobra_x = (largura - (maxx - minx) * escala) / 2
    sobra_y = (altura - (maxy - miny) * escala) / 2

    def tela(p: tuple[float, float]) -> tuple[float, float]:
        return (
            sobra_x + (p[0] - minx) * escala,
            sobra_y + (maxy - p[1]) * escala,
        )

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
            partes.append(
                "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in tela_anel) + " Z"
            )
            area = 0.0
            cx = cy = 0.0
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
        d = " ".join(partes)
        paths.append(
            f'<path class="uf" data-cod="{cod}" d="{d}" fill-rule="evenodd"></path>'
        )
        centroides[cod] = centro

    svg = (
        f'<svg id="mapa" viewBox="0 0 {largura} {altura}" '
        f'role="img" aria-label="Mapa do IDH estimado 2025 por unidade da federação">'
        + "".join(paths)
        + '<g id="rotulos"></g></svg>'
    )
    return svg, centroides


def fmt(valor: float, casas: int = 3) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def gerar_tabela(dados: dict[str, dict], cortes_idh: list[float]) -> str:
    linhas = []
    for item in sorted(dados.values(), key=lambda x: x["posicao"]):
        classe = classe_de(item["idh"], cortes_idh)
        renda_txt = f'{item["renda_per_capita"]:,.0f}'.replace(",", ".")
        linhas.append(
            "<tr>"
            f'<td class="pos">{item["posicao"]}º</td>'
            f'<td class="uf-nome"><span class="chip" style="background:{CORES[classe]}"></span>'
            f'{item["nome"]} <span class="sigla">{item["sigla"]}</span></td>'
            f'<td class="num destaque">{fmt(item["idh"])}</td>'
            f'<td class="num">{fmt(item["renda"])}</td>'
            f'<td class="num">{fmt(item["educacao"])}</td>'
            f'<td class="num">{fmt(item["longevidade"])}</td>'
            f'<td class="num">R$ {renda_txt}</td>'
            f'<td class="num">{fmt(item["anos_estudo"], 1)}</td>'
            f'<td class="num">{fmt(item["esperanca_vida"], 1)}</td>'
            "</tr>"
        )
    return "\n".join(linhas)


def gerar_html(
    dados: dict[str, dict],
    svg: str,
    centroides: dict[str, tuple[float, float]],
    brasil: dict,
    fontes: dict,
) -> str:
    cortes = {
        "idh": classes([d["idh"] for d in dados.values()]),
        "renda": classes([d["renda"] for d in dados.values()]),
        "educacao": classes([d["educacao"] for d in dados.values()]),
        "longevidade": classes([d["longevidade"] for d in dados.values()]),
    }
    tabela = gerar_tabela(dados, cortes["idh"])

    top = sorted(dados.values(), key=lambda x: x["idh"], reverse=True)
    gap = top[0]["idh"] - top[-1]["idh"]
    razao = top[0]["idh"] / top[-1]["idh"]
    agora = datetime.now().strftime("%d/%m/%Y")

    rotulos = []
    for cod, (x, y) in centroides.items():
        sigla = dados[cod]["sigla"]
        dx, dy = OFFSETS.get(cod, (0, 0))
        rotulos.append(
            f'<text x="{x + dx:.1f}" y="{y + dy:.1f}" class="rotulo" '
            f'data-cod="{cod}">{sigla}</text>'
        )
    svg = svg.replace('<g id="rotulos"></g>', "<g id=\"rotulos\">" + "".join(rotulos) + "</g>")

    dados_js = {
        cod: {
            "sigla": d["sigla"],
            "nome": d["nome"],
            "idh": round(d["idh"], 4),
            "renda": round(d["renda"], 4),
            "educacao": round(d["educacao"], 4),
            "longevidade": round(d["longevidade"], 4),
            "renda_per_capita": round(d["renda_per_capita"], 0),
            "anos_estudo": round(d["anos_estudo"], 1),
            "analfabetismo": round(d["analfabetismo"], 1),
            "esperanca_vida": round(d["esperanca_vida"], 1),
            "posicao": d["posicao"],
        }
        for cod, d in dados.items()
    }

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IDH estimado 2025 por UF — dados do IBGE</title>
<style>
  :root {{
    --azul: #0b3d6b;
    --azul-claro: #e8f1f8;
    --texto: #1d2733;
    --muted: #5b6b7c;
    --borda: #d9e2ea;
    --alerta: #fff4d6;
    --alerta-borda: #e0a800;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: #f4f6f8; color: var(--texto);
    font-family: "Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif;
    line-height: 1.5;
  }}
  header {{
    background: linear-gradient(135deg, #0b3d6b 0%, #14588f 60%, #1f7a8c 100%);
    color: #fff; padding: 34px 24px 30px;
  }}
  header .wrap {{ max-width: 1180px; margin: 0 auto; }}
  header .kicker {{
    text-transform: uppercase; letter-spacing: .14em; font-size: 12px;
    opacity: .85; margin-bottom: 8px;
  }}
  header h1 {{ margin: 0 0 8px; font-size: clamp(24px, 3.2vw, 38px); line-height: 1.15; }}
  header p {{ margin: 0; max-width: 900px; opacity: .92; font-size: 15px; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 22px 18px 50px; }}
  .alerta {{
    background: var(--alerta); border-left: 5px solid var(--alerta-borda);
    padding: 14px 16px; border-radius: 6px; margin: 0 0 18px; font-size: 14px;
  }}
  .alerta strong {{ color: #7a5200; }}
  .card {{
    background: #fff; border: 1px solid var(--borda); border-radius: 10px;
    padding: 18px; margin-bottom: 18px; box-shadow: 0 1px 2px rgba(16,42,67,.05);
  }}
  .card h2 {{ margin: 0 0 4px; font-size: 20px; color: var(--azul); }}
  .card h3 {{ margin: 18px 0 8px; font-size: 15px; color: var(--azul); }}
  .card .sub {{ margin: 0 0 14px; color: var(--muted); font-size: 13px; }}
  .layout {{ display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(260px, .75fr); gap: 18px; align-items: start; }}
  #mapa {{ width: 100%; height: auto; display: block; }}
  .uf {{ stroke: #fff; stroke-width: 1.1; cursor: pointer; transition: opacity .15s, stroke .15s; }}
  .uf:hover {{ stroke: #102a43; stroke-width: 2.2; }}
  .rotulo {{
    font-size: 10px; font-weight: 700; fill: #102a43; text-anchor: middle;
    dominant-baseline: middle; pointer-events: none; paint-order: stroke;
    stroke: rgba(255,255,255,.85); stroke-width: 2.4px; stroke-linejoin: round;
  }}
  .rotulo.claro {{ fill: #fff; stroke: rgba(16,42,67,.55); }}
  .controles {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
  .controles button {{
    border: 1px solid var(--borda); background: #fff; color: var(--texto);
    padding: 8px 12px; border-radius: 999px; font-size: 13px; cursor: pointer;
    font-weight: 600;
  }}
  .controles button:hover {{ border-color: #7fb3d5; }}
  .controles button.ativo {{ background: var(--azul); border-color: var(--azul); color: #fff; }}
  .legenda {{ margin-top: 12px; }}
  .legenda .titulo {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 6px; }}
  .legenda .faixas {{ display: grid; gap: 5px; }}
  .legenda .faixa {{ display: flex; align-items: center; gap: 8px; font-size: 12px; }}
  .legenda .cor {{ width: 22px; height: 14px; border-radius: 3px; border: 1px solid rgba(0,0,0,.08); flex: 0 0 auto; }}
  .nota-mapa {{ font-size: 12px; color: var(--muted); margin-top: 10px; }}
  .destaques {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 4px 0 2px; }}
  .destaque-box {{ background: var(--azul-claro); border-radius: 8px; padding: 10px 12px; }}
  .destaque-box .rotulo-peq {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
  .destaque-box .valor {{ font-size: 22px; font-weight: 700; color: var(--azul); }}
  .destaque-box .quem {{ font-size: 12px; color: var(--muted); }}
  .tabela-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 7px 8px; border-bottom: 1px solid #e6edf3; text-align: left; white-space: nowrap; }}
  th {{ background: #f0f5f9; color: #284b63; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; position: sticky; top: 0; }}
  tbody tr:nth-child(even) {{ background: #fafcfd; }}
  tbody tr:hover {{ background: #eef6fb; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.pos {{ text-align: right; color: var(--muted); width: 46px; }}
  td.destaque {{ font-weight: 700; color: var(--azul); }}
  .chip {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; border: 1px solid rgba(0,0,0,.08); vertical-align: middle; }}
  .sigla {{ color: var(--muted); font-size: 11px; }}
  .metodologia {{ font-size: 14px; }}
  .metodologia code {{ background: #f2f5f7; padding: 2px 5px; border-radius: 4px; font-size: 13px; }}
  .metodologia ol, .metodologia ul {{ padding-left: 22px; }}
  .metodologia li {{ margin-bottom: 5px; }}
  .fontes {{ font-size: 13px; color: var(--muted); }}
  .fontes a {{ color: #14588f; }}
  .tooltip {{
    position: absolute; z-index: 20; max-width: 290px; pointer-events: none;
    background: rgba(16,42,67,.96); color: #fff; padding: 10px 12px; border-radius: 8px;
    font-size: 12.5px; line-height: 1.45; box-shadow: 0 6px 18px rgba(0,0,0,.25);
    opacity: 0; transform: translateY(4px); transition: opacity .12s;
  }}
  .tooltip.show {{ opacity: 1; }}
  .tooltip .nome {{ font-weight: 700; font-size: 14px; margin-bottom: 4px; }}
  .tooltip .linha {{ display: flex; justify-content: space-between; gap: 14px; }}
  .tooltip .linha span:last-child {{ font-variant-numeric: tabular-nums; }}
  .tooltip .divisor {{ height: 1px; background: rgba(255,255,255,.2); margin: 6px 0; }}
  .tooltip .peq {{ opacity: .8; font-size: 11.5px; }}
  .acoes {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
  .acoes button {{
    border: 1px solid var(--borda); background: #fff; padding: 7px 11px;
    border-radius: 6px; cursor: pointer; font-size: 12.5px; font-weight: 600; color: var(--azul);
  }}
  footer {{ text-align: center; color: var(--muted); font-size: 12px; padding: 0 18px 30px; }}
  @media (max-width: 860px) {{
    .layout {{ grid-template-columns: 1fr; }}
  }}
  @media print {{
    body {{ background: #fff; }}
    header {{ background: #0b3d6b; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .controles, .acoes, .tooltip {{ display: none !important; }}
    .card {{ box-shadow: none; break-inside: avoid; }}
    .layout {{ grid-template-columns: 1.4fr .8fr; }}
  }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="kicker">Administração de TI · Análise territorial</div>
    <h1>IDH estimado por Unidade da Federação — 2025</h1>
    <p>Mapa coroplético construído com dados de 2025 da API do IBGE. O índice é uma
    <strong>estimativa própria</strong>, inspirada na metodologia do IDH/IDHM, e não um
    valor oficial do PNUD ou do Atlas do Desenvolvimento Humano.</p>
  </div>
</header>

<main>
  <div class="alerta">
    <strong>Leia antes de citar:</strong> o IBGE não calcula nem publica IDH/IDHM, e
    não existe IDH oficial de 2025. O último IDHM nacional publicado pelo Atlas é
    <strong>0,805 (2024)</strong>. Este mapa usa os componentes oficiais do IBGE de 2025
    para produzir um índice aproximado, adequado para <strong>comparar os estados
    brasileiros entre si</strong> — não para comparar com o IDH de outros países.
  </div>

  <section class="card">
    <h2>Mapa</h2>
    <p class="sub">Passe o mouse sobre um estado para ver o índice e os componentes. Use os botões para trocar a dimensão analisada.</p>
    <div class="controles" id="controles">
      <button data-var="idh" class="ativo">IDH estimado</button>
      <button data-var="renda">Renda</button>
      <button data-var="educacao">Educação</button>
      <button data-var="longevidade">Longevidade</button>
    </div>
    <div class="layout">
      <div>
        {svg}
        <p class="nota-mapa" id="nota-mapa">Cor mais escura = maior valor. Escala ajustada ao intervalo observado entre os estados.</p>
      </div>
      <div>
        <div class="legenda">
          <div class="titulo" id="legenda-titulo">IDH estimado 2025</div>
          <div class="faixas" id="legenda-faixas"></div>
        </div>
        <div class="acoes">
          <button id="btn-csv">Baixar CSV</button>
          <button id="btn-print">Imprimir / PDF</button>
        </div>
      </div>
    </div>
  </section>

  <section class="card">
    <h2>Destaques</h2>
    <div class="destaques">
      <div class="destaque-box">
        <div class="rotulo-peq">Maior índice</div>
        <div class="valor">{fmt(top[0]["idh"])}</div>
        <div class="quem">{top[0]["nome"]} ({top[0]["sigla"]})</div>
      </div>
      <div class="destaque-box">
        <div class="rotulo-peq">Menor índice</div>
        <div class="valor">{fmt(top[-1]["idh"])}</div>
        <div class="quem">{top[-1]["nome"]} ({top[-1]["sigla"]})</div>
      </div>
      <div class="destaque-box">
        <div class="rotulo-peq">Gap absoluto</div>
        <div class="valor">{fmt(gap)}</div>
        <div class="quem">maior menos menor</div>
      </div>
      <div class="destaque-box">
        <div class="rotulo-peq">Razão maior/menor</div>
        <div class="valor">{fmt(razao, 2)}×</div>
        <div class="quem">desigualdade relativa</div>
      </div>
      <div class="destaque-box">
        <div class="rotulo-peq">Média simples das UFs</div>
        <div class="valor">{fmt(sum(d["idh"] for d in dados.values()) / len(dados))}</div>
        <div class="quem">não ponderada por população</div>
      </div>
    </div>
  </section>

  <section class="card">
    <h2>Ranking por estado</h2>
    <p class="sub">Ordenado pelo IDH estimado. Os componentes também variam de 0 a 1.</p>
    <div class="tabela-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th><th>Unidade da Federação</th><th>IDH est.</th>
            <th>Renda</th><th>Educação</th><th>Longevidade</th>
            <th>Renda per capita</th><th>Anos de estudo</th><th>Esperança de vida</th>
          </tr>
        </thead>
        <tbody>
        {tabela}
        </tbody>
      </table>
    </div>
  </section>

  <section class="card metodologia">
    <h2>Como o índice foi calculado</h2>
    <p class="sub">Metodologia inspirada no IDH (PNUD) e no IDHM (Atlas), adaptada à disponibilidade dos dados do IBGE para 2025.</p>

    <h3>1. Dimensão renda</h3>
    <p>Rendimento médio mensal real domiciliar per capita (PNAD Contínua, agregado 7395,
    variável 4196, 2025), anualizado e convertido para dólares de paridade de poder de compra
    pelo fator <code>{fmt(fontes["ppp"], 4)}</code> (Banco Mundial, PA.NUS.PPP, 2025).</p>
    <p><code>I_renda = [ln(renda PPC) − ln(100)] / [ln(75.000) − ln(100)]</code></p>

    <h3>2. Dimensão educação</h3>
    <p>Média de anos de estudo das pessoas de 25 anos ou mais (agregado 7126, variável 3593)
    e taxa de escolarização por grupo de idade (agregado 7138, variável 10276), usada para
    estimar os anos esperados de estudo:</p>
    <p><code>anos esperados = 9 × escolarização(6–14) + 3 × escolarização(15–17) + 7 × escolarização(18–24)</code></p>
    <p><code>I_educação = [min(anos de estudo, 18) / 18 + min(anos esperados, 15) / 15] / 2</code></p>
    <p>A taxa de escolarização substitui os anos esperados de estudo do IDH, que não são
    publicados para 2025 na API do IBGE.</p>

    <h3>3. Dimensão longevidade</h3>
    <p>Esperança de vida ao nascer projetada para 2025 nas Projeções da População —
    Revisão 2024 (IBGE).</p>
    <p><code>I_longevidade = (esperança de vida − 20) / (85 − 20)</code></p>

    <h3>4. Índice final</h3>
    <p><code>IDH estimado = (I_renda × I_educação × I_longevidade)^(1/3)</code></p>
    <p>Média geométrica, como no IDH. O resultado é uma estimativa própria: não é o IDH
    do PNUD nem o IDHM do Atlas.</p>

    <h3>Limitações</h3>
    <ul>
      <li>O IDH usa <strong>RNB per capita em PPC</strong>; aqui usamos renda domiciliar per capita, que tende a ser menor. Por isso o índice estimado fica abaixo do IDHM oficial.</li>
      <li>A esperança de vida de 2025 é <strong>projetada</strong>, não observada.</li>
      <li>A educação usa uma <strong>aproximação</strong> para os anos esperados de estudo.</li>
      <li>A PNAD Contínua é amostral: diferenças pequenas entre estados podem não ser estatisticamente significativas.</li>
      <li>O índice serve para comparação interna entre UFs, não para ranking internacional.</li>
    </ul>
  </section>

  <section class="card fontes">
    <h2>Fontes</h2>
    <ul>
      <li>IBGE. <em>PNAD Contínua</em> — agregados 7395 (renda), 7113 (analfabetismo), 7126 (anos de estudo) e 7138 (escolarização), 2025. API v3: <a href="https://servicodados.ibge.gov.br/api/docs/agregados?versao=3">servicodados.ibge.gov.br/api/docs/agregados?versao=3</a>.</li>
      <li>IBGE. <em>Projeções da População — Revisão 2024</em> — esperança de vida ao nascer, 2025. <a href="https://www.ibge.gov.br/estatisticas/sociais/populacao/9109-projecao-da-populacao.html">Página oficial</a>.</li>
      <li>IBGE. <em>Malha territorial</em> — API v3 de malhas, qualidade mínima, Unidades da Federação.</li>
      <li>Banco Mundial. <em>PPP conversion factor, GDP (LCU per international $)</em> — PA.NUS.PPP, Brasil, 2025.</li>
      <li>PNUD/Ipea/FJP. <em>Atlas do Desenvolvimento Humano no Brasil</em> — referência metodológica do IDHM e valor nacional de 2024 (0,805).</li>
    </ul>
    <p>Dados extraídos em {agora}. Script gerador: <code>.opencode/skills/analise-idh-ibge/gera_mapa_idh.py</code>.
    JSON bruto: <code>dados/idh_2025_uf.json</code>.</p>
  </section>
</main>

<footer>
  Elaboração própria com dados do IBGE. Este mapa não substitui os valores oficiais de IDH (PNUD) ou IDHM (Atlas).
</footer>

<div class="tooltip" id="tooltip"></div>

<script>
const DADOS = {json.dumps(dados_js, ensure_ascii=False)};
const CORES = {json.dumps(CORES)};
const ESCURO = {json.dumps(CORES_ESCURAS)};
const CORTES = {json.dumps({k: [round(x, 4) for x in v] for k, v in cortes.items()}, ensure_ascii=False)};
const TITULOS = {{
  idh: "IDH estimado 2025",
  renda: "Dimensão renda (0 a 1)",
  educacao: "Dimensão educação (0 a 1)",
  longevidade: "Dimensão longevidade (0 a 1)"
}};
const CAMPOS = {{ idh: "idh", renda: "renda", educacao: "educacao", longevidade: "longevidade" }};
let variavel = "idh";

function fmt(v, casas = 3) {{
  return Number(v).toLocaleString("pt-BR", {{ minimumFractionDigits: casas, maximumFractionDigits: casas }});
}}
function fmtInt(v) {{ return Number(v).toLocaleString("pt-BR", {{ maximumFractionDigits: 0 }}); }}

function classe(valor, cortes) {{
  if (valor <= cortes[0]) return 0;
  if (valor >= cortes[cortes.length - 1]) return cortes.length - 2;
  for (let i = 0; i < cortes.length - 1; i++) {{
    if (valor >= cortes[i] && valor < cortes[i + 1]) return i;
  }}
  return cortes.length - 2;
}}

function aplicarCores() {{
  document.querySelectorAll("path.uf").forEach(path => {{
    const cod = path.dataset.cod;
    const item = DADOS[cod];
    if (!item) return;
    const c = classe(item[CAMPOS[variavel]], CORTES[variavel]);
    path.setAttribute("fill", CORES[c]);
    const rotulo = document.querySelector(`text.rotulo[data-cod="${{cod}}"]`);
    if (rotulo) rotulo.classList.toggle("claro", ESCURO[c]);
  }});
  const cortes = CORTES[variavel];
  const faixas = document.getElementById("legenda-faixas");
  faixas.innerHTML = cortes.slice(0, -1).map((inf, i) => {{
    const sup = cortes[i + 1];
    const casas = variavel === "idh" ? 3 : 3;
    return `<div class="faixa"><span class="cor" style="background:${{CORES[i]}}"></span>
      <span>${{fmt(inf, casas)}} – ${{fmt(sup, casas)}}</span></div>`;
  }}).join("");
  document.getElementById("legenda-titulo").textContent = TITULOS[variavel];
  document.getElementById("nota-mapa").textContent =
    variavel === "idh"
      ? "Cor mais escura = maior IDH estimado. Escala ajustada ao intervalo observado entre os estados."
      : "Cor mais escura = maior valor do componente. Escala ajustada ao intervalo observado entre os estados.";
}}

function mostrarTooltip(ev, cod) {{
  const d = DADOS[cod];
  if (!d) return;
  const el = document.getElementById("tooltip");
  el.innerHTML = `
    <div class="nome">${{d.nome}} (${{d.sigla}})</div>
    <div class="linha"><span>IDH estimado</span><span><strong>${{fmt(d.idh)}}</strong> · ${{d.posicao}}º</span></div>
    <div class="divisor"></div>
    <div class="linha"><span>Renda</span><span>${{fmt(d.renda)}}</span></div>
    <div class="linha"><span>Educação</span><span>${{fmt(d.educacao)}}</span></div>
    <div class="linha"><span>Longevidade</span><span>${{fmt(d.longevidade)}}</span></div>
    <div class="divisor"></div>
    <div class="linha peq"><span>Renda per capita</span><span>R$ ${{fmtInt(d.renda_per_capita)}}</span></div>
    <div class="linha peq"><span>Anos de estudo (25+)</span><span>${{fmt(d.anos_estudo, 1)}}</span></div>
    <div class="linha peq"><span>Esperança de vida</span><span>${{fmt(d.esperanca_vida, 1)}} anos</span></div>
  `;
  el.classList.add("show");
  moverTooltip(ev);
}}

function moverTooltip(ev) {{
  const el = document.getElementById("tooltip");
  const margem = 14;
  let x = ev.pageX + margem;
  let y = ev.pageY + margem;
  const largura = el.offsetWidth;
  const altura = el.offsetHeight;
  if (x + largura > window.scrollX + document.documentElement.clientWidth - 8) {{
    x = ev.pageX - largura - margem;
  }}
  if (y + altura > window.scrollY + window.innerHeight - 8) {{
    y = ev.pageY - altura - margem;
  }}
  el.style.left = x + "px";
  el.style.top = y + "px";
}}

function esconderTooltip() {{
  document.getElementById("tooltip").classList.remove("show");
}}

document.querySelectorAll("path.uf").forEach(path => {{
  path.addEventListener("mouseenter", ev => mostrarTooltip(ev, path.dataset.cod));
  path.addEventListener("mousemove", moverTooltip);
  path.addEventListener("mouseleave", esconderTooltip);
}});

document.querySelectorAll("#controles button").forEach(btn => {{
  btn.addEventListener("click", () => {{
    document.querySelectorAll("#controles button").forEach(b => b.classList.remove("ativo"));
    btn.classList.add("ativo");
    variavel = btn.dataset.var;
    aplicarCores();
  }});
}});

document.getElementById("btn-print").addEventListener("click", () => window.print());
document.getElementById("btn-csv").addEventListener("click", () => {{
  const linhas = [["posicao","uf","idh_estimado","renda","educacao","longevidade","renda_per_capita","anos_estudo","analfabetismo","esperanca_vida"]];
  Object.values(DADOS).sort((a,b) => a.posicao - b.posicao).forEach(d => {{
    linhas.push([d.posicao, d.sigla, d.idh, d.renda, d.educacao, d.longevidade, d.renda_per_capita, d.anos_estudo, d.analfabetismo, d.esperanca_vida]);
  }});
  const csv = linhas.map(l => l.join(";")).join("\\n");
  const blob = new Blob(["\\ufeff" + csv], {{ type: "text/csv;charset=utf-8" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "idh_estimado_2025_uf.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}});

aplicarCores();
</script>
</body>
</html>
"""


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    DADOS.mkdir(parents=True, exist_ok=True)
    periodo = 2025

    print("Coletando PNAD Contínua 2025...")
    renda = serie_por_uf(7395, 4196, periodo)
    analfabetismo = serie_por_uf(7113, 10267, periodo, "&classificacao=2[6794]|58[2795]")
    anos_estudo = serie_por_uf(7126, 3593, periodo, "&classificacao=2[6794]|58[108866]")
    esc614 = serie_por_uf(7138, 10276, periodo, "&classificacao=2[6794]|58[31615]")
    esc1517 = serie_por_uf(7138, 10276, periodo, "&classificacao=2[6794]|58[2792]")
    esc1824 = serie_por_uf(7138, 10276, periodo, "&classificacao=2[6794]|58[100052]")

    print("Coletando INPC e PPP...")
    inpc2010 = inpc_medio(2010)
    inpc2025 = inpc_medio(2025)
    ppp, fonte_ppp = ppp_brasil()

    print("Lendo esperança de vida projetada 2025...")
    e0, e0_brasil, fonte_e0 = esperanca_vida_2025()

    # Brasil (referência), com os mesmos cálculos.
    renda_br = serie_brasil(7395, 4196, periodo)
    analf_br = serie_brasil(7113, 10267, periodo, "&classificacao=2[6794]|58[2795]")
    anos_br = serie_brasil(7126, 3593, periodo, "&classificacao=2[6794]|58[108866]")
    e614_br = serie_brasil(7138, 10276, periodo, "&classificacao=2[6794]|58[31615]")
    e1517_br = serie_brasil(7138, 10276, periodo, "&classificacao=2[6794]|58[2792]")
    e1824_br = serie_brasil(7138, 10276, periodo, "&classificacao=2[6794]|58[100052]")

    dados = calcular(
        renda, analfabetismo, anos_estudo, esc614, esc1517, esc1824,
        e0, inpc2010, inpc2025, ppp,
    )

    renda_ppp_br = (renda_br * 12) / ppp
    i_renda_br = (math.log(renda_ppp_br) - math.log(100)) / (math.log(75000) - math.log(100))
    anos_esp_br = min(15.0, 9 * e614_br / 100 + 3 * e1517_br / 100 + 7 * e1824_br / 100)
    i_educ_br = (min(18.0, anos_br) / 18 + anos_esp_br / 15) / 2
    i_long_br = (e0_brasil - 20) / 65
    brasil = {
        "idh": (i_renda_br * i_educ_br * i_long_br) ** (1 / 3),
        "renda": i_renda_br,
        "educacao": i_educ_br,
        "longevidade": i_long_br,
        "renda_per_capita": renda_br,
        "anos_estudo": anos_br,
        "esperanca_vida": e0_brasil,
    }

    fontes = {
        "periodo": periodo,
        "inpc2010": inpc2010,
        "inpc2025": inpc2025,
        "ppp": ppp,
        "fonte_ppp": fonte_ppp,
        "fonte_esperanca": fonte_e0,
    }

    saida = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "titulo": "IDH estimado 2025 por Unidade da Federação",
        "aviso": (
            "Estimativa propria. O IBGE nao calcula nem publica IDH/IDHM. "
            "Nao existe IDH oficial de 2025. Indice adequado para comparacao "
            "interna entre UFs, nao para comparacao internacional."
        ),
        "metodologia": {
            "renda": "PNUD: ln(renda PPC)-ln(100) / ln(75000)-ln(100)",
            "educacao": "PNUD adaptado: (min(anos_estudo,18)/18 + min(anos_esperados,15)/15)/2",
            "longevidade": "PNUD: (esperanca_vida-20)/(85-20)",
            "indice": "media geometrica dos tres subindices",
            "anos_esperados": "9*escolarizacao_6_14 + 3*escolarizacao_15_17 + 7*escolarizacao_18_24",
        },
        "fontes": fontes,
        "brasil_referencia": {k: round(v, 4) if isinstance(v, float) else v for k, v in brasil.items()},
        "ufs": {cod: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()} for cod, d in dados.items()},
    }
    (DADOS / "idh_2025_uf.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (DADOS / "idh_2025_uf.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        campos = [
            "posicao", "codigo", "sigla", "nome", "idh", "renda", "educacao",
            "longevidade", "renda_per_capita", "anos_estudo", "analfabetismo",
            "anos_esperados", "esperanca_vida",
        ]
        escritor = csv.DictWriter(fh, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        for item in sorted(dados.values(), key=lambda x: x["posicao"]):
            escritor.writerow({k: (round(item[k], 4) if isinstance(item[k], float) else item[k]) for k in campos})

    print("Gerando malha e SVG...")
    malha = carregar_malha()
    svg, centroides = gerar_svg(malha, dados)

    html = gerar_html(dados, svg, centroides, brasil, fontes)
    HTML_SAIDA.write_text(html, encoding="utf-8")

    print(f"OK: {HTML_SAIDA}")
    print(f"OK: {DADOS / 'idh_2025_uf.json'}")
    print(f"OK: {DADOS / 'idh_2025_uf.csv'}")
    print(f"Brasil (referencia): IDH estimado {brasil['idh']:.4f}")
    print(f"Min: {min(d['idh'] for d in dados.values()):.4f} | Max: {max(d['idh'] for d in dados.values()):.4f}")


if __name__ == "__main__":
    main()
