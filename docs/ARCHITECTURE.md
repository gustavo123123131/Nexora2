# Arquitetura e limitações

## Módulos

- `web/`: painel estático, sem serviços pagos nem build JavaScript.
- `backend/main.py`: API FastAPI local, política de Host/Origin e token por sessão de instalação.
- `backend/database.py`: SQLite com registros JSON; dados persistidos em `NEXORA_HOME`.
- `backend/runner.py`, `browser_launch.py`, `runner_lifecycle.py`: processos Playwright, limite de simultaneidade e desligamento.
- `backend/devices.py`: dispositivos disponíveis na versão instalada do Playwright.
- `backend/proxy_*.py`: cadastro, parser, checagem, importação e remoção de proxies.
- `backend/security.py`: token com permissões locais e cofre de senhas do sistema.
- `tests/`: testes unitários, testes HTTP e isolamento real de localStorage com Chromium headless.

## API local

Todas as rotas `/api/*` requerem cabeçalho `X-App-Token`. A página local recebe o token por HTML servido apenas a localhost. Não disponibilize a porta por túnel, reverse proxy ou encaminhamento.

| Método | Rota | Operação |
|---|---|---|
| GET, POST | `/api/profiles` | Listar / criar |
| PATCH, DELETE | `/api/profiles/{id}` | Editar / excluir |
| POST | `/api/profiles/{id}/duplicate` | Duplicar configurações |
| POST | `/api/profiles/{id}/start` e `/stop` | Abrir / fechar navegador |
| GET, POST | `/api/proxies` | Listar / criar |
| PATCH, DELETE | `/api/proxies/{id}` | Editar / remover |
| POST | `/api/proxies/import` | Importar linhas validadas |
| POST | `/api/proxies/{id}/check` | Verificar saída |
| GET | `/api/devices`, `/api/dashboard`, `/api/diagnostics`, `/api/logs` | Consultas |
| GET, PUT | `/api/settings` | Consultar / alterar preferências |

## Isolamento

Cada ID UUID armazena um perfil em `NEXORA_HOME/profiles/{id}/browser/`. Parar o navegador chama `context.close()`; excluir remove apenas esse diretório e o registro específico. Duplicar nunca copia cookies nem dados locais. O SQLite armazena configurações, mas não senhas.

## Emulação ≠ aparelho físico

Playwright aplica viewport, user-agent, toque e escalonamento dos modelos selecionados. Modelos iPhone usam WebKit, mas **não executam o Safari real de um iPhone** nem replicam hardware, modem, sensores ou OS móvel. Para testes estritos de iOS/Safari use iPhones físicos ou infraestrutura de dispositivos reais.

Suporte de proxy: HTTP(S) com autenticação quando aceita pelo motor; SOCKS5 sem autenticação para inicialização do browser. A verificação HTTPX pode ter comportamento diferente do navegador. Falhas de sites devem ser diagnosticadas sem mascarar automação ou contornar mecanismos antifraude.

## Limites conhecidos

A interface é uma aplicação web local acessada no desktop, ainda sem instalador nativo. Não houve benchmark de RAM/CPU, e `max_active` não monitora memória em tempo real. A recuperação de processos após encerramento abrupto do sistema e logs persistentes precisam de validação adicional. Perfis não simulam centenas de aparelhos físicos.
