import {api,showToast} from "./api.js";
import {state,reload,loadPage} from "./state.js";
import {view} from "./views/index.js";
import {act} from "./actions.js";

function render() {
  const page = view(state.page,state);
  document.getElementById("pageTitle").textContent = page.title;
  document.getElementById("pageDescription").textContent = page.description;
  document.getElementById("breadcrumb").textContent = page.title.toUpperCase();
  document.getElementById("pageActions").innerHTML = page.actions;
  document.getElementById("content").innerHTML = page.html;
  document.querySelectorAll(".nav").forEach(node =>
    node.classList.toggle("active",node.dataset.page === state.page));
  if (state.page === "profiles") filters();
  const form = document.getElementById("settingsForm");
  if (form) form.onsubmit = async e => {
    e.preventDefault();
    try {
      await api("/settings","PUT",{
        max_active:Number(form.elements.max_active.value),
        warn_duplicate_proxy:form.elements.warn_duplicate_proxy.checked
      });
      showToast("Configurações salvas");
      await refresh();
    } catch (err) {showToast(err.message,true);}
  };
}

function filters() {
  const query = document.getElementById("searchProfiles");
  const status = document.getElementById("statusFilter");
  const sort = document.getElementById("sortProfiles");
  const tbody = document.querySelector("tbody");
  if (!tbody) return;
  const original = [...tbody.children];
  const apply = () => {
    for (const row of original) row.hidden =
      !row.dataset.search.includes(query.value.toLowerCase()) ||
      (status.value && row.dataset.status !== status.value);
  };
  query.oninput = apply;
  status.onchange = apply;
  sort.onchange = () => {
    const rows = sort.value === "name" ?
      [...original].sort((a,b) => a.dataset.search.localeCompare(b.dataset.search)) : original;
    rows.forEach(row => tbody.appendChild(row));
    apply();
  };
}

async function refresh() {
  await reload();
  if (state.page === "diagnostics" || state.page === "logs") await loadPage(state.page);
  render();
}

async function navigate(page) {
  state.page = page;
  try {await loadPage(page);render();}
  catch (err) {showToast(err.message,true);}
}

document.addEventListener("click",async e => {
  const link = e.target.closest("[data-page],[data-page-link]");
  if (link) {await navigate(link.dataset.page || link.dataset.pageLink);return;}
  const target = e.target.closest("[data-act]");
  if (target) {
    try {await act(target.dataset.act,target,refresh);}
    catch (err) {showToast(err.message,true);}
  }
});
document.getElementById("refreshBtn").onclick = () => refresh().catch(e => showToast(e.message,true));
document.addEventListener("keydown",async e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
    e.preventDefault(); await navigate("profiles");
    document.getElementById("searchProfiles")?.focus();
  }
});
refresh().catch(e => {
  document.getElementById("content").textContent = "Falha ao carregar os dados locais.";
  showToast(e.message,true);
});
