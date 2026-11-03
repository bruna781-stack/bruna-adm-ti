#!/usr/bin/env python3
"""Serve o site gerado em site/ por HTTP local.

Uso:
  python .opencode/skills/site-idh-ibge/servir.py
  python .opencode/skills/site-idh-ibge/servir.py --port 8080 --no-browser

O servidor escuta apenas em 127.0.0.1 (nao expoe o site na rede) e abre o
navegador padrao. Encerre com Ctrl+C.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socket
import sys
import threading
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SITE = RAIZ / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".csv": "text/csv; charset=utf-8",
        ".html": "text/html; charset=utf-8",
    }

    def log_message(self, formato: str, *args) -> None:  # noqa: A003
        sys.stderr.write("[site] %s\n" % (formato % args))


def porta_livre(inicial: int, tentativas: int = 20) -> int:
    for porta in range(inicial, inicial + tentativas):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", porta))
            except OSError:
                continue
            return porta
    raise SystemExit(f"nenhuma porta livre entre {inicial} e {inicial + tentativas - 1}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Servidor local do site de IDH")
    parser.add_argument("--port", type=int, default=8000, help="porta inicial (padrão: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="não abrir o navegador")
    args = parser.parse_args()

    if not (SITE / "index.html").exists():
        raise SystemExit(
            "site/index.html não encontrado. Rode primeiro:\n"
            "  python .opencode/skills/site-idh-ibge/gera_site.py"
        )

    porta = porta_livre(args.port)
    handler = functools.partial(Handler, directory=str(SITE))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    url = f"http://127.0.0.1:{porta}/"

    print(f"Site disponível em {url}")
    print("Encerre com Ctrl+C.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
