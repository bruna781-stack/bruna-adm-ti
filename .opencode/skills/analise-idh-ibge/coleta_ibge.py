#!/usr/bin/env python3
"""Coleta indicadores de desenvolvimento humano na API oficial do IBGE.

Uso:
    python coleta_ibge.py --uf MA
    python coleta_ibge.py --uf 21 --ano 2024
    python coleta_ibge.py --uf SP --ano 2024 --saida dados/

O script nao calcula IDH/IDHM: baixa os componentes e o contexto territorial.
Os valores oficiais dos indices devem vir do PNUD / Atlas Brasil.

Saida: JSON com metadados de cada consulta (agregado, variavel, periodo, URL).
Apenas biblioteca padrao, sem dependencias externas.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
USER_AGENT = "analise-idh-ibge/1.0 (skill OpenCode)"

INDICADORES = {
    "renda_domiciliar_per_capita": {
        "agregado": 7395,
        "variavel": 4196,
        "unidade": "R$",
        "filtro": "",
    },
    "indice_gini": {
        "agregado": 7435,
        "variavel": 10681,
        "unidade": "indice",
        "filtro": "",
    },
    "analfabetismo_15_mais": {
        "agregado": 7113,
        "variavel": 10267,
        "unidade": "%",
        "filtro": "&classificacao=2[6794]|58[2795]",
    },
    "anos_de_estudo_25_mais": {
        "agregado": 7126,
        "variavel": 3593,
        "unidade": "anos",
        "filtro": "&classificacao=2[6794]|58[108866]",
    },
    "populacao_estimada": {
        "agregado": 6579,
        "variavel": 9324,
        "unidade": "pessoas",
        "filtro": "",
    },
    "populacao_censo_2022": {
        "agregado": 4714,
        "variavel": 93,
        "unidade": "pessoas",
        "filtro": "",
        "periodo_fixo": 2022,
    },
    "esperanca_de_vida": {
        "agregado": 1174,
        "variavel": 2503,
        "unidade": "anos",
        "filtro": "",
    },
}


def _encode(url: str) -> str:
    """Codifica colchetes e barra vertical usados nos filtros da API."""
    return url.replace("[", "%5B").replace("]", "%5D").replace("|", "%7C")


def obter_json(url: str) -> list | dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        bruto = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip":
            bruto = gzip.decompress(bruto)
        return json.loads(bruto.decode("utf-8"))


def resolver_uf(valor: str) -> dict:
    """Aceita sigla (MA) ou codigo IBGE (21) e devolve codigo, sigla e nome."""
    estados = obter_json(f"{LOCALIDADES}/estados")
    alvo = valor.strip().upper()
    for estado in estados:
        if str(estado["id"]) == alvo or estado["sigla"] == alvo:
            return {"codigo": estado["id"], "sigla": estado["sigla"], "nome": estado["nome"]}
    raise SystemExit(f"UF nao encontrada: {valor}. Use sigla (MA) ou codigo IBGE (21).")


def periodos(agregado: int) -> list[int]:
    dados = obter_json(f"{BASE}/{agregado}/periodos")
    return sorted(int(item["id"]) for item in dados)


def escolher_periodo(disponiveis: list[int], ano: int | None) -> tuple[int, bool]:
    """Retorna (periodo, foi_ajustado)."""
    if ano is None:
        return disponiveis[-1], False
    if ano in disponiveis:
        return ano, False
    anteriores = [p for p in disponiveis if p <= ano]
    return (anteriores[-1] if anteriores else disponiveis[-1]), True


def extrair_valor(payload: list) -> float | None:
    for variavel in payload:
        for resultado in variavel.get("resultados", []):
            for serie in resultado.get("series", []):
                for bruto in serie.get("serie", {}).values():
                    try:
                        return float(bruto)
                    except (TypeError, ValueError):
                        continue
    return None


def coletar(uf: dict, ano: int | None) -> dict:
    indicadores: dict[str, dict] = {}
    observacoes: list[str] = []

    for nome, config in INDICADORES.items():
        agregado = config["agregado"]
        try:
            disponiveis = periodos(agregado)
            periodo, ajustado = escolher_periodo(disponiveis, ano)
            if "periodo_fixo" in config:
                periodo, ajustado = config["periodo_fixo"], False
            url = (
                f"{BASE}/{agregado}/periodos/{periodo}/variaveis/{config['variavel']}"
                f"?localidades=N3[{uf['codigo']}]{config['filtro']}"
            )
            payload = obter_json(_encode(url))
            valor = extrair_valor(payload)
            if valor is None:
                observacoes.append(f"{nome}: sem valor para {periodo}.")
            if ajustado:
                observacoes.append(
                    f"{nome}: {ano} indisponivel; usado {periodo} (mais recente ate o ano pedido)."
                )
            indicadores[nome] = {
                "valor": valor,
                "unidade": config["unidade"],
                "periodo": str(periodo),
                "agregado": agregado,
                "variavel": config["variavel"],
                "url": url,
            }
        except Exception as erro:  # noqa: BLE001 - registrar e seguir
            observacoes.append(f"{nome}: falha na consulta ({erro}).")
            indicadores[nome] = {"valor": None, "erro": str(erro), "agregado": agregado}

    if ano in (2022, 2023):
        observacoes.append(
            "populacao_estimada: o agregado 6579 nao publica 2022 e 2023; "
            "para 2022 usar populacao_censo_2022 e declarar o ano do dado."
        )

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": "IBGE - API de Agregados v3",
        "uf": uf,
        "ano_solicitado": ano,
        "aviso": (
            "Componentes e contexto territorial do IBGE. "
            "IDH (PNUD) e IDHM (Atlas Brasil) nao sao publicados nesta API."
        ),
        "indicadores": indicadores,
        "observacoes": observacoes,
    }


def imprimir(resumo: dict) -> None:
    uf = resumo["uf"]
    print(f"\n{uf['nome']} ({uf['sigla']}) - ano solicitado: {resumo['ano_solicitado'] or 'mais recente'}")
    print("-" * 78)
    for nome, item in resumo["indicadores"].items():
        valor = item.get("valor")
        texto = "n/d" if valor is None else f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        print(f"{nome.replace('_', ' '):<34} {texto:>14} {item.get('unidade', ''):<8} {item.get('periodo', '')}")
    if resumo["observacoes"]:
        print("\nObservacoes:")
        for obs in resumo["observacoes"]:
            print(f"- {obs}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta indicadores de desenvolvimento humano no IBGE.")
    parser.add_argument("--uf", required=True, help="Sigla (MA) ou codigo IBGE (21) da UF.")
    parser.add_argument("--ano", type=int, default=None, help="Ano de referencia. Padrao: mais recente.")
    parser.add_argument("--saida", default="dados", help="Pasta de saida do JSON (padrao: dados).")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    uf = resolver_uf(args.uf)
    resumo = coletar(uf, args.ano)

    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"ibge_desenvolvimento_{uf['sigla']}_{args.ano or 'ultimo'}.json"
    arquivo.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    imprimir(resumo)
    print(f"\nJSON salvo em: {arquivo}")


if __name__ == "__main__":
    main()
