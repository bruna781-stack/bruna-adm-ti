#!/usr/bin/env python3
"""Coleta as séries oficiais de IDH/IDHM na API do IpeaData (OData v4).

Fonte: http://www.ipeadata.gov.br/api/odata4/

Séries usadas
-------------
IDHM    IDHM - Índice de Desenvolvimento Humano Municipal (Atlas DH)
IDHMED  IDHM - Dimensão Educação
IDHMLO  IDHM - Dimensão Longevidade
IDHMRE  IDHM - Dimensão Renda
PNUD_IDH  IDH global (PNUD), Brasil, série 1990-2023

As séries IDHM* têm nível territorial "Estados" (27 UFs), "Regiões" (5) e
"Brasil" (TERCODIGO = 0). O ano mais recente publicado é 2024.

Saídas
------
dados/idhm_oficial_2024_uf.json
dados/idhm_oficial_2024_uf.csv
dados/idh_oficial_pnud_brasil.csv
dados/ipea/<SERCODIGO>.json  (cache bruto)

Uso
---
python .opencode/skills/analise-idh-ibge/coleta_ipea.py [--refresh]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ufs import UF_NOMES

ROOT = Path(__file__).resolve().parents[3]
DADOS = ROOT / "dados"
CACHE = DADOS / "ipea"

BASE = "http://www.ipeadata.gov.br/api/odata4"
USER_AGENT = "analise-idh-ibge/1.0 (IDH/IPEA)"
ANO_OFICIAL = 2024

# chave usada no JSON -> código da série no IpeaData
DIMENSOES = {
    "idh": "IDHM",
    "educacao": "IDHMED",
    "longevidade": "IDHMLO",
    "renda": "IDHMRE",
}


def get_json(url: str, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        bruto = resp.read()
        if resp.headers.get("Content-Encoding", "").lower() == "gzip":
            bruto = gzip.decompress(bruto)
    return json.loads(bruto.decode("utf-8"))


def valores(codigo: str, refresh: bool = False) -> list[dict]:
    """Valores de uma série, com cache local em dados/ipea/."""
    destino = CACHE / f"{codigo}.json"
    if destino.exists() and not refresh:
        return json.loads(destino.read_text(encoding="utf-8"))
    payload = get_json(f"{BASE}/ValoresSerie(SERCODIGO='{codigo}')")
    lista = payload.get("value", [])
    if not lista:
        raise RuntimeError(f"série {codigo} vazia na API do IpeaData")
    CACHE.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(lista, ensure_ascii=False), encoding="utf-8")
    return lista


def coletar(ano: int = ANO_OFICIAL, refresh: bool = False) -> dict:
    """Monta o IDHM oficial do ano pedido por UF, mais a série do IDH (PNUD)."""
    ufs: dict[str, dict] = {}
    for chave, codigo in DIMENSOES.items():
        for registro in valores(codigo, refresh):
            if not registro["VALDATA"].startswith(str(ano)):
                continue
            if registro["NIVNOME"] not in ("Estados", "Brasil"):
                continue
            cod = str(registro["TERCODIGO"])
            ufs.setdefault(cod, {"codigo": cod})[chave] = round(
                float(registro["VALVALOR"]), 4
            )

    faltando = [cod for cod in UF_NOMES if cod not in ufs]
    if faltando:
        raise RuntimeError(f"IDHM {ano} incompleto; faltam as UFs {faltando}")

    for cod, dados in ufs.items():
        if cod == "0":
            dados.update(sigla="BR", nome="Brasil")
        else:
            sigla, nome = UF_NOMES[cod]
            dados.update(sigla=sigla, nome=nome)
        for chave in DIMENSOES:
            if chave not in dados:
                raise RuntimeError(f"série sem a dimensão {chave} para {cod} em {ano}")

    ranking = sorted(
        (d for c, d in ufs.items() if c != "0"),
        key=lambda d: d["idh"],
        reverse=True,
    )
    for posicao, dados in enumerate(ranking, start=1):
        dados["posicao"] = posicao

    serie_pnud = {}
    for registro in valores("PNUD_IDH", refresh):
        if registro["NIVNOME"] != "Brasil":
            continue
        serie_pnud[int(registro["VALDATA"][:4])] = round(
            float(registro["VALVALOR"]), 4
        )

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ano": ano,
        "fonte": {
            "api": BASE,
            "series": DIMENSOES,
            "serie_idh_global": "PNUD_IDH",
            "observacao": (
                "IDHM do Atlas do Desenvolvimento Humano (PNUD/Ipea/FJP), "
                "reproduzido pela API do IpeaData. Não é o IDH global do PNUD."
            ),
        },
        "brasil": ufs["0"],
        "ufs": {c: d for c, d in ufs.items() if c != "0"},
        "serie_idh_pnud_brasil": dict(sorted(serie_pnud.items())),
    }


def escrever(saida: dict) -> None:
    DADOS.mkdir(parents=True, exist_ok=True)
    (DADOS / "idhm_oficial_2024_uf.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    campos = ["posicao", "codigo", "sigla", "nome", "idh", "renda", "educacao", "longevidade"]
    with (DADOS / "idhm_oficial_2024_uf.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as fh:
        escritor = csv.DictWriter(fh, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        for item in sorted(saida["ufs"].values(), key=lambda x: x["posicao"]):
            escritor.writerow({k: item[k] for k in campos})

    with (DADOS / "idh_oficial_pnud_brasil.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as fh:
        escritor = csv.writer(fh, delimiter=";")
        escritor.writerow(["ano", "idh_pnud_brasil"])
        for ano, valor in saida["serie_idh_pnud_brasil"].items():
            escritor.writerow([ano, valor])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Coleta IDH/IDHM no IpeaData")
    parser.add_argument("--refresh", action="store_true", help="ignora o cache local")
    args = parser.parse_args()

    saida = coletar(refresh=args.refresh)
    escrever(saida)

    br = saida["brasil"]
    ufs = saida["ufs"]
    topo = max(ufs.values(), key=lambda d: d["idh"])
    base = min(ufs.values(), key=lambda d: d["idh"])
    print(f"IDHM oficial {saida['ano']} — Brasil {br['idh']:.3f}")
    print(f"Maior: {topo['sigla']} {topo['idh']:.3f} | Menor: {base['sigla']} {base['idh']:.3f}")
    print(f"Série IDH (PNUD, Brasil): {len(saida['serie_idh_pnud_brasil'])} anos")
    print(f"OK: {DADOS / 'idhm_oficial_2024_uf.json'}")
    print(f"OK: {DADOS / 'idhm_oficial_2024_uf.csv'}")
    print(f"OK: {DADOS / 'idh_oficial_pnud_brasil.csv'}")


if __name__ == "__main__":
    main()
