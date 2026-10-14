import {esc,chip} from "../api.js";

export function proxiesView(s) {
  const rows = s.proxies.map(p => '<tr><td><strong>' + esc(p.name) + '</strong><small>' +
    esc(p.scheme.toUpperCase()) + ' · ' + esc(p.host) + ':' + p.port + '</small></td>' +
    '<td>' + (p.username ? esc(p.username) + ' · ' : '') + (p.has_password ? 'Cofre protegido' : 'Sem senha') + '</td>' +
    '<td>' + (p.status === "ok" ? chip("Conectado","green") : p.status === "error" ? chip("Falha","red") : chip("Não verificado")) +
    (p.exit_ip ? '<small>' + esc(p.exit_ip) + '</small>' : '') +
    (p.error ? '<small>' + esc(p.error) + '</small>' : '') + '</td>' +
    '<td><div class="actions"><button class="button small quiet" data-act="check-proxy" data-id="' + esc(p.id) + '">Testar</button>' +
    '<button class="button small quiet" data-act="edit-proxy" data-id="' + esc(p.id) + '">Editar</button>' +
    '<button class="button small danger" data-act="delete-proxy" data-id="' + esc(p.id) + '">Excluir</button></div></td></tr>').join("");
  return {
    title:"Gerenciamento de proxies",
    description:"Proxies individuais com senhas protegidas no sistema operacional.",
    actions:'<button class="button quiet" data-act="import-proxy">Importar lista</button> <button class="button" data-act="new-proxy">+ Adicionar proxy</button>',
    html:'<section class="panel"><div class="panel-header"><div><h2>Conexões cadastradas</h2>' +
      '<p>Endereço de saída confirmado somente após teste explícito.</p></div></div>' +
      (rows ? '<div class="table-wrap"><table><thead><tr><th>Proxy</th><th>Credenciais</th><th>Verificação</th><th>Ações</th></tr></thead><tbody>' +
      rows + '</tbody></table></div>' : '<div class="empty"><b>Nenhum proxy cadastrado</b>Adicione um proxy ou importe uma lista.</div>') +
      '</section><div class="hint">Formatos: host:porta, host:porta:usuário:senha ou http(s):// / socks5://. SOCKS5 com autenticação não é suportado na inicialização do navegador.</div>'
  };
}
