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
    message.textContent = data.services.length + " serviços no catálogo. Estado local e testes Docker supervisionados.";
    await loadMissionCatalog();
  } catch (error) {
    message.textContent = error.message || "Falha ao consultar.";
  } finally {
    button.disabled = false;
  }
});

const taskSelect = document.getElementById("taskSelect");
const prepareButton = document.getElementById("prepare");
const approveButton = document.getElementById("approve");
const refreshButton = document.getElementById("refresh");
const cancelButton = document.getElementById("cancel");
const missionPreview = document.getElementById("missionPreview");
const missionOutput = document.getElementById("missionOutput");
let preparedTicket = null;
let activeMissionId = null;

async function missionAPI(path, body = null) {
  const headers = {"Authorization": "Bearer " + token.value.trim()};
  if (body !== null) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {
    method: body === null ? "GET" : "POST",
    headers,
    body: body === null ? undefined : JSON.stringify(body),
    cache: "no-store"
  });
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Falha HTTP " + response.status);
  return data;
}
async function loadMissionCatalog() {
  const data = await missionAPI("/api/v1/missions/catalog");
  taskSelect.replaceChildren();
  for (const task of data.tasks) {
    const opt = document.createElement("option");
    opt.value = task.id;
    opt.textContent = task.title + " — " + task.timeout_seconds + "s máx.";
    taskSelect.append(opt);
  }
  taskSelect.disabled = data.tasks.length === 0;
  prepareButton.disabled = data.tasks.length === 0;
  refreshButton.disabled = false;
  preparedTicket = null;
  approveButton.disabled = true;
}
taskSelect.addEventListener("change", () => {
  preparedTicket = null;
  approveButton.disabled = true;
  missionPreview.textContent = "Missão alterada. Prepara e aprova novamente.";
});
prepareButton.addEventListener("click", async () => {
  prepareButton.disabled = true;
  approveButton.disabled = true;
  preparedTicket = null;
  try {
    const data = await missionAPI("/api/v1/missions/prepare", {task_id: taskSelect.value});
    preparedTicket = data.ticket;
    missionPreview.textContent = "Preparado: " + data.task.title + ". " + data.task.description +
      ". Isolamento: " + data.task.isolation + ". Prazo da aprovação: " + data.expires_in_seconds +
      "s. A execução ainda NÃO começou.";
    approveButton.disabled = false;
  } catch (error) {
    missionPreview.textContent = error.message;
  } finally {
    prepareButton.disabled = false;
  }
});
approveButton.addEventListener("click", async () => {
  if (!preparedTicket) return;
  const ticket = preparedTicket;
  preparedTicket = null;
  approveButton.disabled = true;
  try {
    const data = await missionAPI("/api/v1/missions/start", {ticket, approve: true});
    activeMissionId = data.id;
    cancelButton.disabled = false;
    missionPreview.textContent = "Missão iniciada: " + data.task_id + ". Usa 'Consultar resultado'.";
    missionOutput.textContent = "A executar sob limites Docker…";
  } catch (error) {
    missionPreview.textContent = error.message;
  }
});
async function showMission() {
  try {
    const result = activeMissionId
      ? await missionAPI("/api/v1/missions/" + encodeURIComponent(activeMissionId))
      : (await missionAPI("/api/v1/missions")).missions[0];
    if (!result) {
      missionOutput.textContent = "Sem missões registadas.";
      return;
    }
    activeMissionId = result.id;
    missionOutput.textContent = "Missão: " + result.task_id + "\nEstado: " + result.state +
      "\nIniciada: " + result.created + "\nConcluída: " + (result.finished || "—") +
      "\nCódigo de saída: " + (result.exit_code === null ? "—" : result.exit_code) +
      "\n\n" + (result.output || "Sem saída registada.");
    cancelButton.disabled = result.state !== "RUNNING";
  } catch (error) {
    missionOutput.textContent = error.message;
  }
}
refreshButton.addEventListener("click", showMission);
cancelButton.addEventListener("click", async () => {
  if (!activeMissionId) return;
  cancelButton.disabled = true;
  try {
    const data = await missionAPI("/api/v1/missions/cancel", {id: activeMissionId});
    missionPreview.textContent = "Cancelamento solicitado: " + data.state + ". Consulta o resultado.";
  } catch (error) {
    missionPreview.textContent = error.message;
  }
});
