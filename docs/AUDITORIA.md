# Auditoria do material de referência (14/10/2026)

Fonte: `_proxybet_research(9).zip` recebido exclusivamente para inspeção local. **Não incluso no repositório.**

- 8.647 entradas ZIP, ~1,39 GB descompactados; inclui node_modules, memória integral, traces e material de engenharia reversa.
- App observado: ProxyBet 2.5.10; shell Electron + Node; launcher em bytecode `.jsc`/bytenode; núcleo protegido em `content.asar.enc`.
- `dist/app/preload.js` expõe IPC `proxies:list`, `proxies:save`, `proxy:test`, `session:start`, `session:stop`, `tags:list`, `tags:save`, `instances:list` e `open-browser`. Contratos existentes não comprovam implementação completa auditável.
- Dependências do pacote: `bytenode`, `electron-updater`, `node-window-manager`, `@msgpack/msgpack`, `ws`, `lz4-napi`, `unidecode`, `qrcode`, `@faker-js/faker`.
- `package.json` declara `license: MIT`, mas não acompanha arquivo de licença para o código protegido; o arquivo compactado contém também código de ferramentas de terceiros com licenças próprias. **Não foi assumida autorização para reutilizar o núcleo, artefatos criptografados, capturas ou memory dumps.**
- Dados sensíveis podem existir nos dumps. Não abrir em ambientes remotos nem publicar.

## Estratégia nova

Implementação independente FastAPI + Playwright + SQLite, com armazenamento de dados de navegador em diretórios separados e interface estática entregue pelo backend local. Licença MIT aplica-se somente ao novo código autoral deste repositório.

## Limites

Emulação Playwright usa viewport, propriedades móveis, toque, UA de presets documentados e motores Chromium/WebKit; **não** emula firmware, sensores, telephony, hardware, Safari iOS real ou o fingerprint de dispositivos físicos. Proxy SOCKS5 e HTTP configuráveis; sites HTTPS usam túnel CONNECT ao usar proxy HTTP. HTTPS como transporte até o próprio proxy (TLS proxy) não foi validado/suportado nesta versão. Não há ocultação de automação nem bypass de antifraude.
