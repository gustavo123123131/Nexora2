import {api,esc,showToast} from "../api.js";
import {modal,field} from "./base.js";

export function proxyDialog(current, onSaved) {
  const p = current || {};
  const schemes = ["http","https","socks5"].map(x => '<option value="' + x +
    '" ' + ((p.scheme || "http") === x ? "selected" : "") + '>' + x.toUpperCase() +
    '</option>').join("");
  const fields = field("Nome","name",p.name || "Proxy") +
    '<label>Protocolo<select class="field" name="scheme">' + schemes + '</select></label>' +
    field("Host","host",p.host || "", "text", "required") +
    field("Porta","port",p.port || "", "number", "min=1 max=65535 required") +
    field("Usuário","username",p.username || "") +
    field(current ? "Nova senha (opcional)" : "Senha","password","","password") +
    (current ? '<label class="full"><input type="checkbox" name="clear_password"> Remover senha armazenada</label>' : "");
  modal(current ? "Editar proxy" : "Adicionar proxy",fields,current ? "Salvar" : "Adicionar",async data => {
    const payload = Object.fromEntries(data);
    payload.port = Number(payload.port);
    if (current && !payload.password) delete payload.password;
    if (data.has("clear_password")) payload.password = "";
    delete payload.clear_password;
    await api(current ? "/proxies/" + current.id : "/proxies",current ? "PATCH" : "POST",payload);
    showToast("Proxy salvo com sucesso");
    await onSaved();
  });
}

export function importDialog(onSaved) {
  const fields = '<label class="full">Lista de proxies<textarea class="field" name="lines" required ' +
    'placeholder="host:porta:usuário:senha&#10;http://user:pass@host:porta"></textarea></label>';
  modal("Importar proxies",fields,"Importar",async data => {
    const result = await api("/proxies/import","POST",{lines:data.get("lines")});
    showToast(result.imported.length + " proxies importados");
    await onSaved();
  });
}
