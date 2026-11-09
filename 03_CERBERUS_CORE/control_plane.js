"use strict";
const button = document.getElementById("load");
const message = document.getElementById("message");
const services = document.getElementById("services");
const token = document.getElementById("token");
button.addEventListener("click", async () => {
  button.disabled = true;
  message.textContent = "A consultar o estado local…";
  services.replaceChildren();
  try {
    const response = await fetch("/api/v1/services", {
      headers: {"Authorization": "Bearer " + token.value.trim()},
      cache: "no-store"
    });
    if (!response.ok) throw new Error(response.status === 401 ? "Token inválido." : "Falha HTTP " + response.status);
    const data = await response.json();
    const labels = {"reachable": "Serviço acessível", "unavailable": "Não acessível", "not_integrated": "Integração pendente"};
    for (const item of data.services) {
      const card = document.createElement("article");
      card.className = "service";
      const name = document.createElement("strong");
      name.textContent = item.name;
      const line = document.createElement("div");
      const badge = document.createElement("span");
      badge.className = "status " + item.status;
      badge.textContent = labels[item.status] || "Estado desconhecido";
      line.appendChild(badge);
      card.append(name, line);
      services.appendChild(card);
    }
    message.textContent = data.services.length + " serviços no catálogo. Diagnóstico por sondas HTTP locais, sem execução de comandos.";
  } catch (error) {
    message.textContent = error.message || "Falha ao consultar.";
  } finally {
    button.disabled = false;
  }
});
