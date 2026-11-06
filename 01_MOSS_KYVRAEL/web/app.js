/* Local-only client. Token stays in memory and is not stored. */
(() => {
  "use strict";
  let token = "";
  let modelDetails = {};
  const $ = id => document.getElementById(id);
  const notify = (text, error = false) => {
    $("messages").textContent = String(text);
    $("messages").classList.toggle("error", error);
  };
  function setConnected(yes) {
    for (const button of document.querySelectorAll("button")) {
      if (button.closest("#auth-form") === null) button.disabled = !yes;
    }
  }
  async function api(path, method = "GET", body) {
    if (!token) throw Error("Introduz o token de acesso.");
    const opts = {method, headers: {Authorization: "Bearer " + token}};
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const resp = await fetch(path, opts);
    let result;
    try { result = await resp.json(); } catch { throw Error("Resposta inesperada do servidor."); }
    if (!resp.ok) throw Error(result.error || "Erro HTTP " + resp.status);
    return result;
  }
  async function task(callback) {
    try { await callback(); notify("Operação concluída."); }
    catch (err) { notify(err.message || String(err), true); }
  }
  function element(tag, value, className) {
    const node = document.createElement(tag);
    if (value !== undefined) node.textContent = String(value);
    if (className) node.className = className;
    return node;
  }
  async function loadMissions() {
    const data = await api("/api/v1/missions");
    const list = $("mission-list");
    list.replaceChildren();
    if (!data.missions.length) {
      list.append(element("p", "Ainda não existem missões.", "muted"));
      return;
    }
    for (const m of data.missions) {
      const card = element("article", undefined, "mission");
      card.append(element("strong", m.title));
      card.append(element("small", m.id));
      card.append(element("span", "Estado: " + m.state, "state"));
      if (m.details && m.details.mode === "preview" && m.state === "pending") {
        const button = element("button", "Concluir pré-visualização");
        button.type = "button";
        button.addEventListener("click", () => task(async () => {
          await api("/api/v1/missions/" + encodeURIComponent(m.id) + "/complete-preview", "POST", {});
          await loadMissions();
        }));
        card.append(button);
      }
      list.append(card);
    }
  }
  function showModelIdentity() {
    const selected = $("model").value;
    const details = modelDetails[selected];
    if (!details) {
      $("model-identity").textContent = "Origem do modelo por verificar.";
      return;
    }
    $("model-identity").textContent = "Família: " + details.family +
      " | Origem: " + details.developer + " — " + details.note;
  }
  async function loadModels() {
    const data = await api("/api/v1/models");
    modelDetails = data.model_details || {};
    const select = $("model");
    const current = select.value;
    select.replaceChildren();
    for (const name of data.models) {
      const item = element("option", name);
      item.value = name;
      select.append(item);
    }
    if (data.models.includes(current)) select.value = current;
    else if (data.models.includes("qwen2.5:1.5b")) select.value = "qwen2.5:1.5b";
    showModelIdentity();
    if (!data.models.length) throw Error("O Ollama não tem modelos disponíveis.");
  }
  async function loadChat() {
    const data = await api("/api/v1/chat");
    const list = $("chat-history");
    list.replaceChildren();
    if (!data.messages.length) {
      list.append(element("p", "O histórico está vazio.", "muted"));
    }
    for (const item of data.messages) {
      const card = element("article", undefined, "chat-entry");
      card.append(element("strong", item.role === "user" ? "Tu" : "MOSS Lab · " + item.model));
      card.append(element("p", item.content));
      list.append(card);
    }
    list.scrollTop = list.scrollHeight;
  }
  function form(id, callback) {
    $(id).addEventListener("submit", event => {
      event.preventDefault(); task(callback);
    });
  }
  form("auth-form", async () => {
    token = $("token").value.trim();
    const response = await api("/api/v1/missions");
    if (!Array.isArray(response.missions)) throw Error("Não foi possível confirmar o acesso.");
    $("token").value = "";
    setConnected(true);
    await loadMissions();
    await loadChat();
    try { await loadModels(); } catch { notify("Ligado. Não foi possível listar modelos.", true); }
  });
  $("disconnect").addEventListener("click", () => {
    token = ""; $("token").value = ""; setConnected(false);
    $("mission-list").replaceChildren();
    $("memory-list").replaceChildren();
    $("chat-history").replaceChildren();
    $("model-answer").textContent = "Sessão desligada.";
    notify("Sessão desligada.");
  });
  $("refresh").addEventListener("click", () => task(loadMissions));
  $("models-refresh").addEventListener("click", () => task(loadModels));
  $("model").addEventListener("change", showModelIdentity);
  form("mission-form", async () => {
    await api("/api/v1/missions", "POST", {title: $("mission-title").value});
    $("mission-title").value = ""; await loadMissions();
  });
  form("preview-form", async () => {
    await api("/api/v1/previews", "POST", {
      title: $("preview-title").value, actions: $("actions").value.split(",")
    });
    $("preview-title").value = ""; await loadMissions();
  });
  form("model-form", async () => {
    $("model-answer").textContent = "A gerar resposta local...";
    const data = await api("/api/v1/chat", "POST", {
      model: $("model").value, mode: $("chat-mode").value,
      prompt: $("prompt").value, max_tokens: 256
    });
    $("model-answer").textContent = data.answer;
    // Identity banner comes from server metadata, not generated answer text.
    if (data.model_identity) {
      modelDetails[data.model] = data.model_identity;
      showModelIdentity();
    }
    $("prompt").value = "";
    await loadChat();
  });
  $("chat-clear").addEventListener("click", () => {
    if (!window.confirm("Apagar permanentemente o histórico local de conversa? As missões e notas permanecem.")) return;
    task(async () => {
      await api("/api/v1/chat", "DELETE");
      $("model-answer").textContent = "Histórico apagado.";
      await loadChat();
    });
  });
  form("memory-form", async () => {
    await api("/api/v1/memory", "POST", {text: $("memory-text").value});
    $("memory-text").value = "";
  });
  form("search-form", async () => {
    const q = encodeURIComponent($("memory-query").value);
    const result = await api("/api/v1/memory?q=" + q);
    const list = $("memory-list");
    list.replaceChildren();
    if (!result.results.length) list.append(element("p", "Sem resultados.", "muted"));
    for (const record of result.results) {
      const entry = element("article");
      entry.append(element("p", record.content));
      const remove = element("button", "Apagar", "secondary");
      remove.type = "button";
      remove.addEventListener("click", () => task(async () => {
        await api("/api/v1/memory/" + record.id, "DELETE");
        entry.remove();
      }));
      entry.append(remove);
      list.append(entry);
    }
  });
  (async () => {
    try {
      const response = await fetch("/api/v1/health");
      $("server-status").textContent = response.ok ? "Servidor local ativo" : "Serviço indisponível";
    } catch { $("server-status").textContent = "Serviço indisponível"; }
    setConnected(false);
  })();
})();
