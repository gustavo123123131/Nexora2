# Nexora2 — Multi-Login Mobile

Gerenciador local de perfis móveis para **testes legítimos de compatibilidade**. Novo projeto independente, com interface escura, API FastAPI, dados em SQLite e navegadores Playwright com pastas de perfil separadas.

> **Estado:** implementação inicial em uma branch de desenvolvimento. Os resultados dos testes automatizados devem ser conferidos no GitHub Actions. Não é um navegador antidetect, um simulador de aparelho físico ou um executável Windows já empacotado.

## Instalação (Windows / PowerShell)

Instale Python 3.11+ e execute na pasta clonada:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium webkit
python -m backend
```

Abra **http://127.0.0.1:8765** no navegador desktop. Se essa porta estiver ocupada, defina `$env:NEXORA_PORT="8766"` **antes** de iniciar o aplicativo. O serviço se vincula apenas a `127.0.0.1`, nunca a `0.0.0.0`.

Linux/macOS: use `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`, `python -m playwright install chromium webkit`, `python -m backend`.

## Recursos implementados no código

- Criar, editar, agrupar, etiquetar, duplicar e excluir perfis.
- Sessões Chromium/WebKit isoladas com armazenamento persistente por UUID, preservadas ao parar e reiniciar.
- Biblioteca de modelos móveis reais do Playwright; idioma, fuso e viewport configuráveis.
- Proxies HTTP, HTTPS e SOCKS5 por perfil, importação, testes de saída e desassociação.
- Credenciais guardadas no cofre do sistema operacional com `keyring`; nunca no SQLite.
- Limite de navegadores simultâneos, estados, painel local, configurações e diagnóstico.
- Ações de interface ligadas à API, autenticação por token local e proteção de origem.

## Configuração

| Variável | Padrão | Objetivo |
|---|---|---|
| `NEXORA_PORT` | `8765` | Porta local (alterar se indisponível) |
| `NEXORA_HOME` | `~/.nexora2` | Banco, token e pastas persistentes |
| `NEXORA_HEADLESS` | `false` | `true` para execução em CI |
| `NEXORA_IP_CHECK_URL` | `https://api.ipify.org?format=json` | Endpoint autorizado para teste de IP |

O cofre de credenciais usa a implementação de `keyring` disponível no sistema. Em Linux headless é necessário configurar um backend seguro; sem isso, a gravação de senhas de proxy retorna erro, em vez de salvá-las em texto puro.

## Testes

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
NEXORA_HEADLESS=true python -m pytest -q
```

No PowerShell: `$env:NEXORA_HEADLESS="true"; python -m pytest -q`.

Veja [arquitetura e limitações](docs/ARCHITECTURE.md) e [situação da revisão do ZIP](docs/OPEN_SOURCE_AUDIT.md). Não reutilize componentes de terceiros antes de verificar e respeitar a licença.
