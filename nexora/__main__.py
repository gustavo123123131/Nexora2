"""CLI: loopback HTTP server on a free OS-assigned port by default."""
import argparse
import os
import socket
import webbrowser
import uvicorn
from .api import create_app


def main():
    parser = argparse.ArgumentParser(description='Nexora Mobile: multi-perfis locais')
    parser.add_argument('--port', type=int, default=0, help='Porta local; 0 = porta livre automática')
    parser.add_argument('--data-dir', default=None, help='Diretório persistente de dados')
    parser.add_argument('--headless', action='store_true', help='Navegadores sem janela (somente testes)')
    parser.add_argument('--no-open', action='store_true', help='Não abrir painel automaticamente')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('porta fora do intervalo')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('127.0.0.1', args.port))
    except OSError as exc:
        parser.error(f'porta indisponível: {exc}')
    sock.listen(128)
    port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    print(f'\nNEXORA MOBILE | {url}\nDados persistentes: {args.data_dir or "~/.nexora-mobile"}\n', flush=True)
    if not args.no_open:
        import threading
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app = create_app(args.data_dir, args.headless)
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False))
    try:
        server.run(sockets=[sock])
    finally:
        sock.close()


if __name__ == '__main__':
    main()
