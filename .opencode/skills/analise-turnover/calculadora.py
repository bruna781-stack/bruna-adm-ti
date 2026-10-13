"""Calculadora de turnover - skill analise-turnover.
Uso: python calculadora.py --admissoes 6 --desligamentos 8 --quadro 60 --voluntarios 5 --periodo "S1 2026"
"""
import argparse


def calcular(admissoes: int, desligamentos: int, quadro: int, voluntarios: int = 0):
    if quadro <= 0:
        raise ValueError("quadro deve ser > 0")
    geral = ((admissoes + desligamentos) / 2) / quadro * 100
    taxa_deslig = desligamentos / quadro * 100
    volunt = voluntarios / quadro * 100 if voluntarios else 0.0
    return round(geral, 2), round(taxa_deslig, 2), round(volunt, 2)


def classificar(taxa_anual_estimada: float) -> str:
    if taxa_anual_estimada < 10:
        return "ok / saudavel"
    if taxa_anual_estimada <= 15:
        return "atencao"
    return "critico"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--admissoes", type=int, required=True)
    ap.add_argument("--desligamentos", type=int, required=True)
    ap.add_argument("--quadro", type=int, required=True)
    ap.add_argument("--voluntarios", type=int, default=0)
    ap.add_argument("--periodo", type=str, default="periodo informado")
    args = ap.parse_args()

    geral, deslig, vol = calcular(args.admissoes, args.desligamentos, args.quadro, args.voluntarios)
    print(f"## Resultado Turnover - {args.periodo}")
    print(f"- Admissoes: {args.admissoes} | Desligamentos: {args.desligamentos} | Quadro: {args.quadro}")
    print(f"- Turnover geral: {geral}%  [(Adm+Des)/2]/Quadro*100")
    print(f"- Taxa desligamentos: {deslig}%")
    if args.voluntarios:
        print(f"- Turnover voluntario: {vol}%")
    print(f"- Faixa (ref. anual): {classificar(geral)}")
    print("- Fonte: calculo proprio + Ticket 2026. Sem benchmark setorial = dado a confirmar.")
