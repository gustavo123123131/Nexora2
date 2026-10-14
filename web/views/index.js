import {dashboardView,devicesView} from "./dashboard.js";
import {profilesView} from "./profiles.js";
import {proxiesView} from "./proxies.js";
import {settingsView,diagnosticsView,logsView} from "./system.js";

const views = {
  dashboard:dashboardView,
  profiles:profilesView,
  proxies:proxiesView,
  devices:devicesView,
  settings:settingsView,
  diagnostics:diagnosticsView,
  logs:logsView
};

export function view(page, state) {
  return (views[page] || dashboardView)(state);
}
