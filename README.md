# Nexora Mobile

Gerenciador **local** de perfis persistentes de navegadores móveis para testes de sites. Projeto independente, criado do zero, sem copiar código protegido do arquivo de referência.

## Instalação (Windows 10/11, macOS, Linux)

1. Instale Python 3.11+ e Git.
2. Abra o terminal na pasta do repositório e execute:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   python -m playwright install chromium webkit
   python -m nexora
   ```

3. A aplicação mostrará no terminal uma URL `http://127.0.0.1:<porta>`; porta livre escolhida automaticamente. Também abre o painel no navegador padrão. Use `python -m nexora --port 8765` para fixar porta, se disponível.

A aplicação só escuta em `127.0.0.1` e exige token de sessão para todas as rotas de gerenciamento. Não publique o painel por túnel ou proxy reverso. Os perfis usam **janelas de navegador separadas**, não celulares físicos.

### Comandos úteis

- `python -m nexora --no-open` — servidor sem abertura automática do painel.
- `python -m nexora --data-dir /minha/pasta` — diretório de dados alternativo.
- `python -m nexora --headless` — para testes automatizados; navegadores ocultos.
- `NEXORA_CHROMIUM_PATH=/usr/bin/chromium python -m nexora` — Chromium instalado no sistema (use somente se compatível com Playwright).

Os cookies/localStorage/IndexedDB de cada perfil ficam em `~/.nexora-mobile/browser-profiles/<UUID>`. Os metadados estão em `nexora.db` (SQLite WAL). A chave local `secrets.key` criptografa senhas de proxy **em repouso**, mas alguém com acesso ao usuário do sistema e à chave também pode descriptografá-las. Proteja a pasta e faça backup do banco e da chave em conjunto. Nunca suba esta pasta para GitHub.

## Funcionalidades

- Criar, editar, duplicar (sem copiar cookies), apagar, iniciar e encerrar perfis.
- Dispositivos Playwright Android/Chromium e iPhone/WebKit, viewport, locale, fuso IANA, tags, grupos.
- Proxies individuais HTTP e SOCKS5 com autenticação opcional, importação, teste manual em `https://api.ipify.org?format=json`, e aviso de compartilhamento de proxy.
- Limite de 1 a 30 perfis simultâneos; padrão 3. Limite é **quantidade**, não reserva de memória. Verifique RAM/CPU antes de aumentar.
- Dashboard, busca, filtros, ações e diagnósticos.
- Sessões persistentes por diretório; status em execução é volátil, corretamente resetado após reiniciar.

## API

Cada endpoint `/api/*` exige `X-Nexora-Token`, incluído somente na interface servida localmente; origens externas bloqueadas. Endpoints:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/dashboard` | Contadores e status |
| GET | `/api/devices` | Presets Playwright disponíveis |
| GET/POST | `/api/profiles` | Listar/criar perfil |
| PUT/DELETE | `/api/profiles/{id}` | Alterar/excluir e apagar dados do perfil |
| POST | `/api/profiles/{id}/duplicate` | Duplicar sem sessão |
| POST | `/api/profiles/{id}/start`, `/stop` | Abrir/fechar janela persistente |
| GET/POST | `/api/proxies` | Listar/criar proxy |
| PUT/DELETE | `/api/proxies/{id}` | Editar/remover proxy |
| POST | `/api/proxies/import` | Importação em lote |
| POST | `/api/proxies/{id}/test` | Verificar IP no serviço de teste |
| GET/PUT | `/api/settings` | Limite simultâneo, avisos |
| GET | `/api/logs`, `/api/diagnostics` | Diagnósticos locais |

Importação: `host:porta`, `host:porta:usuario:senha`, `socks5://usuario:senha@host:porta` e IPv6 `[2001:db8::1]:porta`. Com credenciais contendo `:` no formato simples, somente a senha pode conter `:`; para usuário/senha especiais prefira URL com percent-encoding. Entradas inválidas são reportadas por **número da linha**, nunca pelo conteúdo sensível.

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
# Para integração real de browser:
NEXORA_CHROMIUM_PATH=/usr/bin/chromium pytest -q tests/test_browser.py
```

Não há suporte a Firefox nesta versão. Instale o WebKit do Playwright para presets iPhone. WebKit no desktop é **aproximação de Safari**, não Safari em um iPhone. A biblioteca de dispositivos segue a versão do Playwright instalada; versões reais de iOS/Android não são virtualizadas. Nenhum mecanismo antidetecção/antifraude foi implementado.

## Diagnóstico e encerramento

O servidor termina contextos ativos ao receber sinal de encerramento e os demais perfis permanecem no disco. Na falha de processo/energia, o Chromium pode precisar recuperar sessões ao abrir; Chrome/Playwright têm limites próprios. `GET /api/diagnostics` relata caminhos e ambiente. Verifique WebKit não instalado, RAM disponível, credenciais do proxy e erros de inicialização.

Consulte [`docs/AUDITORIA.md`](docs/AUDITORIA.md) para a inspeção do material recebido.
