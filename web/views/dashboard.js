import {esc} from "../api.js";
import {profileTable} from "./profiles.js";

export function dashboardView(s) {
  const d = s.dashboard;
  const metric = (label, number, note) => '<div class="metric"><div class="label">' + label +
    '</div><strong>' + number + '</strong><div class="foot">' + note + '</div></div>';
  return {
    title: "Visão geral",
    description: "Controle seus perfis e acompanhe o estado dos navegadores.",
    actions: '<button class="button" data-act="new-profile">+ Criar perfil</button>',
    html: '<div class="metrics">' +
      metric("Total de perfis", d.total, "Ambientes registrados") +
      metric("Navegadores ativos", d.active, "Limite: " + s.settings.max_active) +
      metric("Proxies cadastrados", d.proxies, "Configuração individual") +
      metric("Proxies verificados", d.proxies_ok, "Última checagem bem-sucedida") +
      '</div><section class="panel"><div class="panel-header"><div><h2>Seus ambientes</h2><p>Últimos perfis cadastrados</p></div>' +
      '<button class="button quiet small" data-page-link="profiles">Ver todos →</button></div>' +
      profileTable(s.profiles.slice(0,6), s.proxies, true) + '</section>' +
      '<section class="panel"><div class="panel-header"><div><h2>Ambiente local e independente</h2><p>Um diretório de sessão para cada perfil</p></div></div>' +
      '<div class="hint" style="padding:20px 23px">O Playwright emula viewport, toque e User-Agent do dispositivo selecionado. Não cria um celular físico nem oferece Safari nativo do iOS.</div></section>'
  };
}

export function devicesView(s) {
  return {
    title: "Biblioteca de dispositivos",
    description: "Modelos realmente disponibilizados pela versão instalada do Playwright.",
    actions: "",
    html: '<div class="grid">' + s.devices.map(d =>
      '<div class="device-card"><div class="device-icon">' + (d.name.startsWith("iPhone") ? "▯" : "▤") +
      '</div><h2>' + esc(d.name) + '</h2><p>' + esc(d.browser) + ' · ' + d.viewport.width + ' × ' +
      d.viewport.height + ' CSS pixels</p><button class="button small quiet" data-act="from-device" data-device="' +
      esc(d.name) + '">Criar perfil</button></div>').join("") + '</div>'
  };
}
