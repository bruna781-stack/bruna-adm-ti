#!/usr/bin/env python3
"""Tabela de Unidades da Federação usada pelos scripts do skill.

Códigos IBGE de 2 dígitos, sigla e nome. Compartilhado entre
``coleta_ipea.py`` e ``gera_mapa_idh.py`` para evitar duplicação.
"""

from __future__ import annotations

UF_NOMES: dict[str, tuple[str, str]] = {
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

SIGLAS: dict[str, str] = {cod: sigla for cod, (sigla, _) in UF_NOMES.items()}
CODIGOS: dict[str, str] = {sigla: cod for cod, (sigla, _) in UF_NOMES.items()}
