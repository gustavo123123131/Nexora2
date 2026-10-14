import {api} from "./api.js";

export const state = {
  page:"dashboard", profiles:[],proxies:[],devices:[],
  dashboard:{total:0,active:0,proxies:0,proxies_ok:0},
  settings:{max_active:3,warn_duplicate_proxy:true},
  diagnostics:null,logs:[]
};

export async function reload() {
  const results = await Promise.all([
    api("/profiles"),api("/proxies"),api("/devices"),
    api("/dashboard"),api("/settings")
  ]);
  [state.profiles,state.proxies,state.devices,state.dashboard,state.settings] = results;
}

export async function loadPage(page) {
  if (page === "diagnostics") state.diagnostics = await api("/diagnostics");
  if (page === "logs") state.logs = await api("/logs");
}
