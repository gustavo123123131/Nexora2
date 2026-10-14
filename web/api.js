export async function api(path, method="GET", data) {
  const headers = {"x-app-token": window.NEXORA_TOKEN};
  if (data !== undefined) headers["content-type"] = "application/json";
  const response = await fetch("/api" + path, {
    method, headers, body: data === undefined ? undefined : JSON.stringify(data)
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail :
      Array.isArray(detail) ? detail.map(e => e.msg).join("; ") : "Erro de comunicação";
    throw new Error(message);
  }
  return response.json();
}

export function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}

export function showToast(message, error=false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = error ? "show error" : "show";
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.className = "", 4500);
}

export const chip = (value, mode="") =>
  '<span class="chip ' + mode + '">' + esc(value) + '</span>';
