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

## Verificação adicional do ZIP desta conversa: (10)

Também foi examinado diretamente `_proxybet_research(10).zip` em 14/10/2026, sem extrair seus dumps sensíveis: 514,81 MB compactados, **8.647 entradas** e aproximadamente **1,39 GB** de conteúdo descompactado. O inventário corresponde à estrutura já descrita acima.

- `asar_extracted_20260824/package.json`: aplicação `proxybet`, versão `2.5.10`, campo `license: MIT`, dependências Electron/bytenode/lz4-napi e outras.
- `dist/main.js` inicia o launcher ou o processo de instância; `dist/app/main.js` depende de `content.asar.enc`, executa código bytecode via `bytenode` e inclui validação de licença. O conteúdo protegido **não está disponível como fonte aberta auditável** neste arquivo.
- `dist/app/preload.js` confirma nomes de contratos IPC de sessões, proxies e tags, mas não a implementação interna dos serviços.
- Não foi identificada licença principal separada para o núcleo proprietário no inventário. O atributo MIT do `package.json` isoladamente **não autoriza concluir que os blobs protegidos e dumps podem ser redistribuídos**.

**Decisão:** nenhum código, recurso protegido, bytecode, dump ou sessão do ZIP (10) foi incorporado ao Nexora Mobile. Os módulos novos continuam sendo implementação independente. Os contratos IPC observáveis servem apenas como informação arquitetural, não como garantia de funcionamento nem autorização para cópia.
