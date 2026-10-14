import {showToast} from "../api.js";

export function modal(title, fields, submitLabel, onSubmit) {
  const dialog = document.getElementById("dialog");
  document.getElementById("dialogContent").innerHTML =
    '<h2>' + title + '</h2><form id="modalForm"><div class="form-grid">' + fields +
    '</div><div class="modal-actions"><button type="button" class="button quiet" id="cancelModal">Cancelar</button>' +
    '<button class="button" type="submit">' + submitLabel + '</button></div></form>';
  document.getElementById("cancelModal").onclick = () => dialog.close();
  document.getElementById("modalForm").onsubmit = async ev => {
    ev.preventDefault();
    const button = ev.currentTarget.querySelector('[type="submit"]');
    button.disabled = true;
    try {
      await onSubmit(new FormData(ev.currentTarget));
      dialog.close();
    } catch (e) {
      showToast(e.message, true);
    } finally {
      button.disabled = false;
    }
  };
  dialog.showModal();
}

export const field = (label, name, value="", type="text", extra="") =>
  '<label>' + label + '<input class="field" name="' + name + '" type="' + type +
  '" value="' + String(value ?? "").replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;") +
  '" ' + extra + '></label>';
