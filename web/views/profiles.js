import {esc, chip} from "../api.js";

export function profileTable(profiles, proxies, compact=false) {
  if (!profiles.length) return '<div class="empty"><b>Nenhum perfil criado</b>Crie um ambiente móvel para começar.</div>';
  const rows = profiles.map(p => {
    const proxy = proxies.find(x => x.id === p.proxy_id);
    const running = p.status === "running";
    const status = p.status === "starting" ? chip("Iniciando", "yellow") :
      running ? chip("Em execução", "green") : chip("Parado");
    const actions = compact ? "" : '<td><div class="actions">' +
      '<button class="button small ' + (running ? "danger" : "") + '" data-act="' + (running ? "stop" : "start") + '" data-id="' + esc(p.id) + '">' + (running ? "Parar" : "Iniciar") + '</button>' +
      '<button class="button small quiet" data-act="edit" data-id="' + esc(p.id) + '">Editar</button>' +
      '<button class="button small quiet" data-act="duplicate" data-id="' + esc(p.id) + '">Duplicar</button>' +
      '<button class="button small danger" data-act="delete" data-id="' + esc(p.id) + '">Excluir</button></div></td>';
    return '<tr data-search="' + esc([p.name,p.device,p.group_name,...p.tags].join(" ").toLowerCase()) + '" data-status="' + esc(p.status) + '">' +
      '<td><strong>' + esc(p.name) + '</strong><small>' + esc(p.group_name || "Sem grupo") + '</small></td>' +
      '<td>' + esc(p.device) + '</td><td>' + esc(proxy?.name || "Direto") + '</td><td>' + status + '</td>' + actions + '</tr>';
  }).join("");
  return '<div class="table-wrap"><table><thead><tr><th>Perfil</th><th>Dispositivo</th><th>Conexão</th><th>Status</th>' +
    (compact ? '' : '<th>Ações</th>') + '</tr></thead><tbody>' + rows + '</tbody></table></div>';
}

export function profilesView(s) {
  return {
    title: "Perfis de navegador", description: "Sessões móveis com cookies e dados independentes.",
    actions: '<button class="button" data-act="new-profile">+ Novo perfil</button>',
    html: '<section class="panel"><div class="filters"><input id="searchProfiles" placeholder="Buscar por nome, grupo ou dispositivo…">' +
      '<select id="statusFilter"><option value="">Todos os status</option><option value="running">Em execução</option><option value="stopped">Parados</option></select>' +
      '<select id="sortProfiles"><option value="recent">Mais recentes</option><option value="name">Nome A–Z</option></select></div>' +
      profileTable(s.profiles, s.proxies) + '</section>'
  };
}
