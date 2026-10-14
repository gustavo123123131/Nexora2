import {api,esc,showToast} from "../api.js";
import {modal,field} from "./base.js";

export function profileDialog(s, current, onSaved, preferredDevice) {
  const value = current || {};
  const devices = s.devices.map(d => '<option value="' + esc(d.name) + '" ' +
    ((value.device || preferredDevice || s.devices[0]?.name) === d.name ? "selected" : "") +
    '>' + esc(d.name) + '</option>').join("");
  const proxies = '<option value="">Sem proxy</option>' + s.proxies.map(p =>
    '<option value="' + esc(p.id) + '" ' + (value.proxy_id === p.id ? "selected" : "") +
    '>' + esc(p.name) + '</option>').join("");
  const fields = field("Nome do perfil","name",value.name || "", "text", "required maxlength=80") +
    '<label>Dispositivo<select class="field" name="device">' + devices + '</select></label>' +
    field("Grupo","group_name",value.group_name || "") +
    field("Etiquetas (separadas por vírgula)","tags",(value.tags || []).join(", ")) +
    '<label>Proxy<select class="field" name="proxy_id">' + proxies + '</select></label>' +
    field("Idioma","locale",value.locale || "pt-BR") +
    field("Fuso horário IANA","timezone",value.timezone || "America/Sao_Paulo") +
    field("Largura da viewport","viewport_width",value.viewport_width || "", "number","min=240 max=3840") +
    field("Altura da viewport","viewport_height",value.viewport_height || "", "number","min=320 max=3840");
  modal(current ? "Editar perfil" : "Novo perfil",fields,current ? "Salvar" : "Criar perfil",async data => {
    const payload = Object.fromEntries(data);
    payload.tags = payload.tags.split(",").map(x => x.trim()).filter(Boolean);
    payload.proxy_id = payload.proxy_id || null;
    for (const k of ["viewport_width","viewport_height"]) payload[k] = payload[k] ? Number(payload[k]) : null;
    const result = await api(current ? "/profiles/" + current.id : "/profiles",
      current ? "PATCH" : "POST", payload);
    showToast(result.warning || (current ? "Perfil atualizado" : "Perfil criado"));
    await onSaved();
  });
}
