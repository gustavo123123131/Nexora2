import {api,showToast} from "./api.js";
import {state} from "./state.js";
import {profileDialog} from "./dialogs/profile.js";
import {proxyDialog,importDialog} from "./dialogs/proxy.js";

export async function act(action, node, refresh) {
  const id = node.dataset.id;
  const profile = state.profiles.find(p => p.id === id);
  const proxy = state.proxies.find(p => p.id === id);
  if (action === "new-profile" || action === "from-device" || action === "edit") {
    if (!state.devices.length) throw new Error("Instale os navegadores Playwright");
    profileDialog(state, action === "edit" ? profile : null, refresh, node.dataset.device);
    return;
  }
  if (action === "new-proxy" || action === "edit-proxy") {
    proxyDialog(action === "edit-proxy" ? proxy : null, refresh);return;
  }
  if (action === "import-proxy") {importDialog(refresh);return;}
  if (action === "delete" && !confirm("Excluir o perfil e TODOS os dados locais dessa sessão?")) return;
  if (action === "delete-proxy" && !confirm("Excluir este proxy e desassociar os perfis?")) return;
  node.disabled = true;
  try {
    const paths = {
      start:["/profiles/"+id+"/start","POST"],
      stop:["/profiles/"+id+"/stop","POST"],
      duplicate:["/profiles/"+id+"/duplicate","POST"],
      delete:["/profiles/"+id,"DELETE"],
      "check-proxy":["/proxies/"+id+"/check","POST"],
      "delete-proxy":["/proxies/"+id,"DELETE"]
    };
    if (paths[action]) {
      const [path,method] = paths[action];
      const result = await api(path,method);
      showToast(result.warning || "Operação concluída");
    }
    if (action === "refresh-diag") state.diagnostics = await api("/diagnostics");
    if (action === "refresh-logs") state.logs = await api("/logs");
    await refresh();
  } finally {
    node.disabled = false;
  }
}
