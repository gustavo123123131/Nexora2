import {esc} from "../api.js";

export function settingsView(s) {
  return {
    title:"Configurações", description:"Preferências de execução e distribuição de proxies.",
    actions:"",
    html:'<section class="panel"><div class="panel-header"><h2>Limites e avisos</h2></div>' +
    '<form id="settingsForm" style="padding:24px;max-width:530px"><div class="form-grid">' +
    '<label class="full">Máximo de navegadores simultâneos' +
    '<input class="field" name="max_active" type="number" min="1" max="20" value="' +
    s.settings.max_active + '" required></label><label class="full"><input type="checkbox" name="warn_duplicate_proxy" ' +
    (s.settings.warn_duplicate_proxy ? "checked" : "") +
    '> Avisar ao reutilizar o mesmo proxy em vários perfis</label></div>' +
    '<p class="hint">O limite depende da RAM e da CPU disponíveis. Não há garantia de desempenho para dezenas de navegadores ativos.</p>' +
    '<button type="submit" class="button">Salvar configurações</button></form></section>'
  };
}

export function diagnosticsView(s) {
  return {
    title:"Diagnóstico", description:"Ambiente, navegadores instalados e requisitos.",
    actions:'<button class="button quiet" data-act="refresh-diag">↻ Executar diagnóstico</button>',
    html:'<section class="panel"><div class="panel-header"><h2>Informações técnicas</h2></div>' +
    '<pre class="diag">' + esc(s.diagnostics ? JSON.stringify(s.diagnostics,null,2) : "Carregando…") +
    '</pre></section>'
  };
}

export function logsView(s) {
  const rows = (s.logs || []).map(log => '<tr><td>' + esc(new Date(log.time).toLocaleString("pt-BR")) +
    '</td><td>' + esc(log.action) + '</td><td><small>' + esc(log.profile_id) + '</small></td></tr>').join("");
  return {
    title:"Eventos", description:"Operações recentes do gerenciador, sem senhas ou cookies.",
    actions:'<button class="button quiet" data-act="refresh-logs">↻ Atualizar eventos</button>',
    html:'<section class="panel"><div class="panel-header"><h2>Registro de operações</h2></div>' +
    (rows ? '<div class="table-wrap"><table><thead><tr><th>Data</th><th>Evento</th><th>Perfil</th></tr></thead><tbody>' +
    rows + '</tbody></table></div>' : '<div class="empty"><b>Nenhum evento registrado nesta execução</b>Inicie um perfil para gerar eventos.</div>') +
    '</section>'
  };
}
