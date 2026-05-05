const state = {
  token: localStorage.getItem("ems_token") || "",
  email: localStorage.getItem("ems_email") || "",
  role: "",
  profileId: null,
  authView: "login",
  currentScreen: "dashboard",
  detailView: null,
  detailEventId: null,
  detailBackTarget: null,
  taskCreatePresetEventId: null,
  resourceCreatePresetEventId: null,
  usersSearch: { q: "", speciality: "" },
  usersList: [],
  participantsModeEventId: null,
  allocationPreset: { eventId: null, taskId: null, resourceId: null },
  events: [],
  tasks: [],
  resources: []
};

const API = {
  auth: "/api/auth",
  users: "/api/users",
  events: "/api/events/",
  tasks: "/api/tasks/",
  resources: "/api/resources/",
  ai: "/api/ai"
};

const el = {
  statusLine: document.getElementById("status-line"),
  sessionEmail: document.getElementById("session-email"),
  screenTitle: document.getElementById("screen-title"),
  topbarActions: document.getElementById("topbar-actions"),
  authBlock: document.getElementById("auth-block"),
  profileBlock: document.getElementById("profile-block"),
  eventsCount: document.getElementById("events-count"),
  tasksCount: document.getElementById("tasks-count"),
  resourcesCount: document.getElementById("resources-count"),
  overdueCount: document.getElementById("overdue-count"),
  eventsList: document.getElementById("events-list"),
  tasksList: document.getElementById("tasks-list"),
  resourcesList: document.getElementById("resources-list"),
  usersList: document.getElementById("users-list"),
  usersModeHint: document.getElementById("users-mode-hint"),
  aiResult: document.getElementById("ai-result"),
  protectedContent: document.getElementById("protected-content"),
  taskEventSelect: document.getElementById("task-event-select"),
  taskAssigneeSelect: document.getElementById("task-assignee-select"),
  resourceEventSelect: document.getElementById("resource-event-select"),
  aiEventSelect: document.getElementById("ai-event-select"),
  allocationEventSelect: document.getElementById("allocation-event-select"),
  allocationTaskSelect: document.getElementById("allocation-task-select"),
  allocationResourceSelect: document.getElementById("allocation-resource-select")
};

function notify(text, isError = false) {
  el.statusLine.textContent = text;
  el.statusLine.style.color = isError ? "#b33a3a" : "#6d6962";
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const enumLabels = {
  eventStatus: {
    draft: "Черновик",
    published: "Опубликовано",
    cancelled: "Отменено",
    completed: "Завершено"
  },
  taskStatus: {
    todo: "К выполнению",
    in_progress: "В работе",
    done: "Завершено",
    overdue: "Просрочено",
    blocked: "Заблокировано"
  },
  taskPriority: {
    low: "Низкий",
    medium: "Средний",
    high: "Высокий"
  },
  resourceType: {
    equipment: "Оборудование",
    venue: "Площадка",
    personnel: "Персонал",
    material: "Материал"
  },
  participantRole: {
    owner: "Владелец",
    organizer: "Организатор",
    executor: "Исполнитель",
    viewer: "Наблюдатель",
    admin: "Администратор"
  },
  allocationStatus: {
    planned: "Запланировано",
    active: "Активно",
    completed: "Завершено",
    cancelled: "Отменено"
  }
};

function enumLabel(group, value) {
  const normalized = value == null ? "" : String(value);
  return enumLabels[group]?.[normalized] || normalized;
}

function toIsoOrNull(value) {
  if (!value) return null;
  return new Date(value).toISOString();
}

function toDatetimeLocalValue(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function serializeForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function saveSession(token, email) {
  state.token = token;
  state.email = email;
  state.role = getRoleFromToken(token);
  localStorage.setItem("ems_token", token);
  localStorage.setItem("ems_email", email);
}

function clearSession() {
  state.token = "";
  state.email = "";
  state.role = "";
  state.profileId = null;
  state.detailView = null;
  state.detailEventId = null;
  state.detailBackTarget = null;
  state.taskCreatePresetEventId = null;
  state.resourceCreatePresetEventId = null;
  state.participantsModeEventId = null;
  state.allocationPreset = { eventId: null, taskId: null, resourceId: null };
  state.usersList = [];
  state.usersSearch = { q: "", speciality: "" };
  localStorage.removeItem("ems_token");
  localStorage.removeItem("ems_email");
}

function getRoleFromToken(token) {
  if (!token) return "";
  try {
    const payloadPart = token.split(".")[1];
    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(normalized));
    return decoded.role || "";
  } catch (error) {
    return "";
  }
}

function canCreate() {
  return state.role === "admin" || state.role === "organizer";
}

function taskDetailMode(task) {
  if (state.role === "admin") return "full";
  if (canCreate()) return "full";
  if (state.role === "executor" && state.profileId != null && task.assignee_id === state.profileId) {
    return "status_only";
  }
  return "read";
}

async function apiRequest(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const hasBody = options.body !== undefined && options.body !== null;
  if (hasBody && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (error) {
    throw new Error("Сетевое соединение недоступно или API gateway не отвечает");
  }
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch (err) {
      // ignore body parse error
    }
    if (
      response.status === 401 ||
      (response.status === 403 && typeof message === "string" && message.toLowerCase().includes("credentials"))
    ) {
      clearSession();
      syncAuthUi();
      throw new Error("Сессия истекла или токен недействителен. Выполните вход снова");
    }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function screenName(screenId) {
  const map = {
    dashboard: "Обзор",
    events: "Мероприятия",
    tasks: "Задачи",
    resources: "Ресурсы",
    users: "Пользователи",
    ai: "AI помощник",
    "profile-cabinet": "Профиль"
  };
  return map[screenId] || "Обзор";
}

function hideAllScreens() {
  document.querySelectorAll(".screen").forEach((item) => item.classList.add("hidden"));
}

function closeCreatePanels() {
  ["event-create-panel", "task-create-panel", "resource-create-panel", "allocation-create-panel", "ai-create-panel"].forEach((id) => {
    const panel = document.getElementById(id);
    if (panel) panel.classList.add("hidden");
  });
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
}

function setScreen(screenId) {
  if (!state.token || el.protectedContent.classList.contains("hidden")) {
    el.screenTitle.textContent = "Авторизация";
    return;
  }
  state.currentScreen = screenId;
  if (screenId !== "users") {
    state.participantsModeEventId = null;
  }
  state.detailView = null;
  state.detailEventId = null;
  state.detailBackTarget = null;
  closeCreatePanels();
  hideAllScreens();
  document.getElementById(`${screenId}-screen`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.screen === screenId);
  });
  el.screenTitle.textContent = screenName(screenId);
  updateTopbarActions();
  if (screenId === "users") {
    void loadUsers();
  }
  if (screenId === "profile-cabinet") {
    void loadProfileCabinet();
  }
}

function updateTopbarActions() {
  const container = el.topbarActions;
  container.innerHTML = "";
  if (!state.token || el.protectedContent.classList.contains("hidden")) {
    container.classList.add("hidden");
    return;
  }
  if (el.profileBlock && !el.profileBlock.classList.contains("hidden")) {
    container.classList.add("hidden");
    return;
  }

  if (state.detailView) {
    const back = document.createElement("button");
    back.type = "button";
    back.className = "btn btn-muted btn-inline";
    back.textContent = "← Назад";
    back.addEventListener("click", () => closeDetailView());
    container.appendChild(back);
    container.classList.remove("hidden");
    return;
  }

  const can = canCreate();
  if (!can || state.currentScreen === "dashboard") {
    container.classList.add("hidden");
    return;
  }

  const map = {
    events: { panel: "event-create-panel", label: "+ Создать мероприятие" },
    tasks: { panel: "task-create-panel", label: "+ Создать задачу" },
    resources: { panel: "resource-create-panel", label: "+ Создать ресурс" },
    ai: { panel: "ai-create-panel", label: "+ Сгенерировать план" }
  };
  const cfg = map[state.currentScreen];
  if (!cfg) {
    container.classList.add("hidden");
    return;
  }

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn-muted btn-inline";
  btn.textContent = cfg.label;
  btn.addEventListener("click", () => {
    const panel = document.getElementById(cfg.panel);
    if (panel) {
      panel.classList.toggle("hidden");
      if (cfg.panel === "task-create-panel" && !panel.classList.contains("hidden")) {
        const selectedId = state.taskCreatePresetEventId;
        populateTaskEventOptions(selectedId);
        void loadAssigneeOptions(selectedId);
      }
      if (cfg.panel === "resource-create-panel" && !panel.classList.contains("hidden")) {
        populateResourceEventOptions();
      }
      if (cfg.panel === "ai-create-panel" && !panel.classList.contains("hidden")) {
        populateAiEventOptions();
      }
    }
  });
  container.appendChild(btn);
  if (state.currentScreen === "resources") {
    const allocBtn = document.createElement("button");
    allocBtn.type = "button";
    allocBtn.className = "btn btn-muted btn-inline";
    allocBtn.textContent = "+ Создать выделение";
    allocBtn.addEventListener("click", () => {
      const panel = document.getElementById("allocation-create-panel");
      if (panel) {
        panel.classList.toggle("hidden");
        if (!panel.classList.contains("hidden")) {
          populateAllocationEventOptions(state.allocationPreset.eventId);
          populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
          populateAllocationResourceOptions(state.allocationPreset.eventId, state.allocationPreset.resourceId);
        }
      }
    });
    container.appendChild(allocBtn);
  }
  container.classList.remove("hidden");
}

function renderList(listNode, items, formatter) {
  listNode.innerHTML = "";
  if (!items.length) {
    listNode.innerHTML = '<div class="list-item"><p class="list-item-meta">Пока данных нет</p></div>';
    return;
  }
  items.forEach((item) => {
    const wrapper = document.createElement("article");
    wrapper.className = "list-item";
    wrapper.innerHTML = formatter(item);
    listNode.appendChild(wrapper);
  });
}

function renderDashboard() {
  el.eventsCount.textContent = String(state.events.length);
  el.tasksCount.textContent = String(state.tasks.length);
  el.resourcesCount.textContent = String(state.resources.length);
  const overdue = state.tasks.filter((task) => task.status === "overdue").length;
  el.overdueCount.textContent = String(overdue);
}

function populateResourceEventOptions(selectedEventId = null) {
  if (!el.resourceEventSelect) return;
  const effectiveSelected = selectedEventId ?? state.resourceCreatePresetEventId;
  const options = ['<option value="">Выберите мероприятие</option>'];
  state.events.forEach((event) => {
    const isSelected = effectiveSelected != null && Number(effectiveSelected) === event.id;
    options.push(`<option value="${event.id}" ${isSelected ? "selected" : ""}>${escapeHtml(formatEventLabel(event))}</option>`);
  });
  el.resourceEventSelect.innerHTML = options.join("");
}

function openResourceCreateForEvent(eventId) {
  state.resourceCreatePresetEventId = eventId;
  setScreen("resources");
  const panel = document.getElementById("resource-create-panel");
  if (panel) {
    panel.classList.remove("hidden");
  }
  populateResourceEventOptions(eventId);
}

function populateAiEventOptions(selectedEventId = null) {
  if (!el.aiEventSelect) return;
  const options = ['<option value="">Выберите мероприятие</option>'];
  state.events.forEach((event) => {
    const isSelected = selectedEventId != null && Number(selectedEventId) === event.id;
    options.push(`<option value="${event.id}" ${isSelected ? "selected" : ""}>${escapeHtml(formatEventLabel(event))}</option>`);
  });
  el.aiEventSelect.innerHTML = options.join("");
}

function renderEvents() {
  renderList(el.eventsList, state.events, (event) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="event" data-id="${event.id}">
        #${event.id} ${escapeHtml(event.title)}
      </button>
      <span class="badge">${enumLabel("eventStatus", event.status)}</span>
    </p>
    <p class="list-item-meta">Сроки: ${new Date(event.start_time).toLocaleString()} - ${new Date(event.end_time).toLocaleString()}</p>
    <p class="list-item-meta">Бюджет: ${event.budget ?? 0}</p>
  `);
}

function renderTasks() {
  renderList(el.tasksList, state.tasks, (task) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="task" data-id="${task.id}">
        #${task.id} ${escapeHtml(task.title)}
      </button>
      <span class="badge">${enumLabel("taskStatus", task.status)}</span>
      <span class="badge">${enumLabel("taskPriority", task.priority)}</span>
      ${task.status === "overdue" ? '<span class="badge badge-danger">Просрочено</span>' : ""}
    </p>
    <p class="list-item-meta">Мероприятие: #${task.event_id} | Исполнитель: ${task.assignee_id ?? "не назначен"}</p>
    <p class="list-item-meta">Дедлайн: ${new Date(task.deadline).toLocaleString()}</p>
  `);
}

function renderResources() {
  renderList(el.resourcesList, state.resources, (resource) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="resource" data-id="${resource.id}">
        #${resource.id} ${escapeHtml(resource.name)}
      </button>
      <span class="badge">${enumLabel("resourceType", resource.type)}</span>
    </p>
    <p class="list-item-meta">Мероприятие: #${resource.event_id} | Кол-во: ${resource.quantity}</p>
    <p class="list-item-meta">Стоимость/час: ${resource.cost_per_hour ?? "не указано"}</p>
  `);
}

function renderUsers() {
  const inParticipantMode = state.participantsModeEventId != null;
  el.usersModeHint.classList.toggle("hidden", !inParticipantMode);
  el.usersModeHint.textContent = inParticipantMode
    ? `Режим добавления участников для мероприятия #${state.participantsModeEventId}`
    : "Список пользователей";

  renderList(el.usersList, state.usersList, (user) => `
    <p class="list-item-title">#${user.id} ${escapeHtml(user.first_name)} ${escapeHtml(user.last_name)}</p>
    <p class="list-item-meta">Роль: ${enumLabel("participantRole", user.role || "viewer")}</p>
    <p class="list-item-meta">Специализация: ${escapeHtml(user.speciality || "не указана")}</p>
    ${state.role === "admin" ? `<p class="list-item-meta">Email: ${escapeHtml(user.email || "—")} | Телефон: ${escapeHtml(user.phone || "—")}</p>` : ""}
    ${
      inParticipantMode
        ? `<div class="detail-actions">
            <select data-user-role-select="${user.id}">
              <option value="organizer">${enumLabel("participantRole", "organizer")}</option>
              <option value="executor">${enumLabel("participantRole", "executor")}</option>
              <option value="viewer">${enumLabel("participantRole", "viewer")}</option>
            </select>
            <button class="btn btn-inline" type="button" data-add-participant-user="${user.id}">Добавить в мероприятие</button>
          </div>`
        : ""
    }
  `);
}

function getTasksByEventId(eventId) {
  return state.tasks.filter((task) => task.event_id === Number(eventId));
}

function getResourcesByEventId(eventId) {
  return state.resources.filter((resource) => resource.event_id === Number(eventId));
}

function populateAllocationEventOptions(selectedEventId = null) {
  if (!el.allocationEventSelect) return;
  const options = ['<option value="">Выберите мероприятие</option>'];
  state.events.forEach((event) => {
    const selected = selectedEventId != null && Number(selectedEventId) === event.id ? "selected" : "";
    options.push(`<option value="${event.id}" ${selected}>${escapeHtml(formatEventLabel(event))}</option>`);
  });
  el.allocationEventSelect.innerHTML = options.join("");
}

function populateAllocationTaskOptions(eventId, selectedTaskId = null) {
  if (!el.allocationTaskSelect) return;
  const tasks = eventId ? getTasksByEventId(eventId) : [];
  const options = ['<option value="">Без задачи</option>'];
  tasks.forEach((task) => {
    const selected = selectedTaskId != null && Number(selectedTaskId) === task.id ? "selected" : "";
    options.push(`<option value="${task.id}" ${selected}>#${task.id} ${escapeHtml(task.title)}</option>`);
  });
  el.allocationTaskSelect.innerHTML = options.join("");
}

function populateAllocationResourceOptions(eventId, selectedResourceId = null) {
  if (!el.allocationResourceSelect) return;
  const resources = eventId ? getResourcesByEventId(eventId) : [];
  const options = ['<option value="">Выберите ресурс</option>'];
  resources.forEach((resource) => {
    const selected = selectedResourceId != null && Number(selectedResourceId) === resource.id ? "selected" : "";
    options.push(`<option value="${resource.id}" ${selected}>#${resource.id} ${escapeHtml(resource.name)}</option>`);
  });
  el.allocationResourceSelect.innerHTML = options.join("");
}

function formatEventLabel(event) {
  return `${event.title} | ${new Date(event.start_time).toLocaleString()} - ${new Date(event.end_time).toLocaleString()}`;
}

function populateTaskEventOptions(selectedEventId = null) {
  if (!el.taskEventSelect) return;
  const options = ['<option value="">Выберите мероприятие</option>'];
  state.events.forEach((event) => {
    const isSelected = selectedEventId != null && Number(selectedEventId) === event.id;
    options.push(
      `<option value="${event.id}" ${isSelected ? "selected" : ""}>${escapeHtml(formatEventLabel(event))}</option>`
    );
  });
  el.taskEventSelect.innerHTML = options.join("");
}

async function loadAssigneeOptions(eventId, selectedAssigneeId = null) {
  if (!el.taskAssigneeSelect) return;
  el.taskAssigneeSelect.innerHTML = '<option value="">Без исполнителя</option>';
  if (!eventId) return;
  try {
    const participants = await apiRequest(`${API.events}${eventId}/participants`);
    const candidateIds = Array.from(
      new Set(
        (participants || [])
          .filter((item) => ["owner", "organizer", "executor"].includes(item.role))
          .map((item) => item.user_id)
      )
    );
    if (!candidateIds.length) return;
    const params = new URLSearchParams();
    candidateIds.forEach((id) => params.append("ids", String(id)));
    const profiles = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
    profiles.forEach((profile) => {
      if (!["organizer", "executor"].includes(profile.role)) {
        return;
      }
      const option = document.createElement("option");
      option.value = String(profile.id);
      option.textContent = `${profile.first_name} ${profile.last_name} (${enumLabel("participantRole", profile.role)})`;
      if (selectedAssigneeId != null && Number(selectedAssigneeId) === profile.id) {
        option.selected = true;
      }
      el.taskAssigneeSelect.appendChild(option);
    });
  } catch (error) {
    notify(`Не удалось загрузить исполнителей: ${error.message}`, true);
  }
}

async function loadTaskEditAssigneeOptions(eventId, selectedAssigneeId = null) {
  const select = document.getElementById("task-edit-assignee-select");
  if (!select) return;
  select.innerHTML = '<option value="">Без исполнителя</option>';
  if (!eventId) return;
  try {
    const participants = await apiRequest(`${API.events}${eventId}/participants`);
    const candidateIds = Array.from(
      new Set(
        (participants || [])
          .filter((item) => ["owner", "organizer", "executor"].includes(item.role))
          .map((item) => item.user_id)
      )
    );
    if (!candidateIds.length) return;
    const params = new URLSearchParams();
    candidateIds.forEach((id) => params.append("ids", String(id)));
    const profiles = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
    profiles.forEach((profile) => {
      if (!["organizer", "executor"].includes(profile.role)) return;
      const option = document.createElement("option");
      option.value = String(profile.id);
      option.textContent = `${profile.first_name} ${profile.last_name} (${enumLabel("participantRole", profile.role)})`;
      if (selectedAssigneeId != null && Number(selectedAssigneeId) === profile.id) {
        option.selected = true;
      }
      select.appendChild(option);
    });
  } catch (error) {
    notify(`Не удалось загрузить исполнителей: ${error.message}`, true);
  }
}

async function presetTaskCreateForEvent(eventId) {
  setScreen("tasks");
  if (!canCreate()) return;
  const panel = document.getElementById("task-create-panel");
  if (panel) {
    panel.classList.remove("hidden");
  }
  populateTaskEventOptions(eventId);
  await loadAssigneeOptions(eventId);
}

async function openUsersForEventParticipants(eventId) {
  state.participantsModeEventId = eventId;
  setScreen("users");
  await loadUsers();
}

function openAllocationCreatePanel(preset = {}) {
  state.allocationPreset = {
    eventId: preset.eventId ?? null,
    taskId: preset.taskId ?? null,
    resourceId: preset.resourceId ?? null
  };
  setScreen("resources");
  if (!canCreate()) return;
  const panel = document.getElementById("allocation-create-panel");
  if (panel) {
    panel.classList.remove("hidden");
  }
  populateAllocationEventOptions(state.allocationPreset.eventId);
  populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
  populateAllocationResourceOptions(state.allocationPreset.eventId, state.allocationPreset.resourceId);
  const allocForm = document.getElementById("allocation-form");
  if (allocForm && state.allocationPreset.taskId) {
    const task = state.tasks.find((item) => item.id === Number(state.allocationPreset.taskId));
    if (task) {
      allocForm.elements.date_start.value = toDatetimeLocalValue(task.start_time);
      allocForm.elements.date_end.value = toDatetimeLocalValue(task.end_time);
    }
  }
}

function syncAuthUi() {
  const isAuth = Boolean(state.token);
  el.authBlock.classList.toggle("hidden", isAuth);
  el.sessionEmail.textContent = isAuth ? state.email : "Не авторизован";
  document.getElementById("logout-btn").classList.toggle("hidden", !isAuth);
  if (!isAuth) {
    el.screenTitle.textContent = "Авторизация";
    el.profileBlock.classList.add("hidden");
    el.protectedContent.classList.add("hidden");
  } else if (!el.profileBlock.classList.contains("hidden")) {
    el.screenTitle.textContent = "Создание профиля";
  } else if (state.detailView) {
    /* title set by detail view */
  } else {
    el.screenTitle.textContent = screenName(state.currentScreen);
  }
  syncCreateControls();
  updateTopbarActions();
}

function setProfileRequired(isRequired) {
  if (!state.token) return;
  el.profileBlock.classList.toggle("hidden", !isRequired);
  el.protectedContent.classList.toggle("hidden", isRequired);
  el.screenTitle.textContent = isRequired ? "Создание профиля" : screenName(state.currentScreen);
  if (!isRequired) {
    hideAllScreens();
    document.getElementById(`${state.currentScreen}-screen`).classList.remove("hidden");
  }
  updateTopbarActions();
}

function syncCreateControls() {
  const can = canCreate();
  if (!can) {
    ["event-create-panel", "task-create-panel", "resource-create-panel", "allocation-create-panel", "ai-create-panel"].forEach((id) => {
      const panel = document.getElementById(id);
      if (panel) panel.classList.add("hidden");
    });
  }
}

function setAuthView(view) {
  state.authView = view;
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const loginTab = document.getElementById("auth-tab-login");
  const registerTab = document.getElementById("auth-tab-register");

  loginForm.classList.toggle("hidden", view !== "login");
  registerForm.classList.toggle("hidden", view !== "register");
  loginTab.classList.toggle("active", view === "login");
  registerTab.classList.toggle("active", view === "register");
}

async function refreshData() {
  if (!state.token) return;
  try {
    const me = await apiRequest(`${API.users}/me`);
    state.profileId = me.id;
    setProfileRequired(false);
  } catch (error) {
    state.profileId = null;
    if (String(error.message).includes("User profile not found")) {
      setProfileRequired(true);
      notify("Создайте профиль в user-service для доступа к функциям", true);
      return;
    }
  }
  notify("Загрузка данных...");
  const [eventsResult, tasksResult, resourcesResult] = await Promise.allSettled([
    apiRequest(API.events),
    apiRequest(API.tasks),
    apiRequest(API.resources)
  ]);

  const errors = [];

  if (eventsResult.status === "fulfilled") {
    state.events = Array.isArray(eventsResult.value) ? eventsResult.value : [];
  } else {
    state.events = [];
    errors.push(`мероприятия: ${eventsResult.reason?.message || "неизвестная ошибка"}`);
  }

  if (tasksResult.status === "fulfilled") {
    state.tasks = Array.isArray(tasksResult.value) ? tasksResult.value : [];
  } else {
    state.tasks = [];
    errors.push(`задачи: ${tasksResult.reason?.message || "неизвестная ошибка"}`);
  }

  if (resourcesResult.status === "fulfilled") {
    state.resources = Array.isArray(resourcesResult.value) ? resourcesResult.value : [];
  } else {
    state.resources = [];
    errors.push(`ресурсы: ${resourcesResult.reason?.message || "неизвестная ошибка"}`);
  }

  renderEvents();
  renderTasks();
  renderResources();
  renderUsers();
  renderDashboard();
  populateTaskEventOptions(state.taskCreatePresetEventId);
  populateResourceEventOptions();
  populateAiEventOptions();
  populateAllocationEventOptions(state.allocationPreset.eventId);
  populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
  populateAllocationResourceOptions(state.allocationPreset.eventId, state.allocationPreset.resourceId);
  if (state.taskCreatePresetEventId != null) {
    await loadAssigneeOptions(state.taskCreatePresetEventId);
  }

  if (errors.length) {
    if (errors.every((entry) => entry.includes("Сессия истекла или токен недействителен"))) {
      notify("Сессия истекла. Пожалуйста, войдите снова", true);
      return;
    }
    notify(`Частичная загрузка. Ошибки: ${errors.join(" | ")}`, true);
    return;
  }
  notify("Данные обновлены");
}

async function loadUsers() {
  if (!state.token) return;
  const params = new URLSearchParams();
  if (state.usersSearch.q) params.set("q", state.usersSearch.q);
  if (state.usersSearch.speciality) params.set("speciality", state.usersSearch.speciality);
  try {
    const list =
      state.role === "admin"
        ? await apiRequest(`${API.users}/?${params.toString()}`)
        : await apiRequest(`${API.users}/public?${params.toString()}`);
    state.usersList = Array.isArray(list) ? list : [];
    if (state.role !== "admin") {
      state.usersList = state.usersList.filter((item) => item.role !== "admin");
    }
    renderUsers();
  } catch (error) {
    notify(`Ошибка загрузки пользователей: ${error.message}`, true);
  }
}

async function closeDetailView() {
  if (state.detailBackTarget?.kind === "event") {
    const id = state.detailBackTarget.id;
    state.detailBackTarget = null;
    await openEventDetail(id);
    return;
  }
  state.detailBackTarget = null;
  state.detailView = null;
  state.detailEventId = null;
  hideAllScreens();
  document.getElementById(`${state.currentScreen}-screen`).classList.remove("hidden");
  el.screenTitle.textContent = screenName(state.currentScreen);
  updateTopbarActions();
  await refreshData();
}

async function openEventDetail(eventId) {
  state.detailBackTarget = null;
  state.detailView = "event";
  state.detailEventId = eventId;
  hideAllScreens();
  document.getElementById("event-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Мероприятие";
  updateTopbarActions();
  notify("Загрузка…");

  const root = document.getElementById("event-detail-root");
  root.innerHTML = '<p class="list-item-meta">Загрузка карточки…</p>';

  try {
    const event = await apiRequest(`${API.events}${eventId}`);
    const tasks = await apiRequest(`${API.tasks}event/${eventId}`);
    const participants = await apiRequest(`${API.events}${eventId}/participants`);
    const eventResources = state.resources.filter((resource) => resource.event_id === eventId);
    const depResults = await Promise.allSettled(
      tasks.map((t) => apiRequest(`${API.tasks}${t.id}/dependency-ids`))
    );
    const depMap = {};
    tasks.forEach((t, i) => {
      const r = depResults[i];
      depMap[t.id] = r.status === "fulfilled" && r.value?.depends_on ? r.value.depends_on : [];
    });

    el.screenTitle.textContent = event.title || `Мероприятие #${eventId}`;
    renderEventDetailCard(event, tasks, depMap, participants, eventResources);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function buildMermaidDependencyGraph(tasks, depMap) {
  const taskIds = new Set(tasks.map((task) => task.id));
  const nodes = tasks.map((task) => {
    const safeTitle = String(task.title || "").replace(/"/g, '\\"').slice(0, 60);
    return `task_${task.id}["#${task.id}: ${safeTitle}"]`;
  });
  const edges = [];
  tasks.forEach((task) => {
    (depMap[task.id] || []).forEach((dependsOnId) => {
      if (taskIds.has(dependsOnId)) {
        edges.push(`task_${dependsOnId} --> task_${task.id}`);
      }
    });
  });
  if (!edges.length) return "";
  return ["graph LR", ...nodes, ...edges].join("\n");
}

function buildEventTimeline(tasks, event) {
  const datedTasks = (tasks || [])
    .filter((task) => task.start_time && task.end_time)
    .map((task) => ({ task, start: new Date(task.start_time).getTime(), end: new Date(task.end_time).getTime() }))
    .filter((entry) => Number.isFinite(entry.start) && Number.isFinite(entry.end) && entry.end > entry.start);

  if (!datedTasks.length) {
    return '<p class="list-item-meta">Нет задач с валидными плановыми датами для построения таймлайна.</p>';
  }

  const eventStart = event?.start_time ? new Date(event.start_time).getTime() : null;
  const eventEnd = event?.end_time ? new Date(event.end_time).getTime() : null;
  const minStart = Number.isFinite(eventStart) ? eventStart : Math.min(...datedTasks.map((x) => x.start));
  const maxEnd = Number.isFinite(eventEnd) ? eventEnd : Math.max(...datedTasks.map((x) => x.end));
  const span = Math.max(maxEnd - minStart, 1);

  const rows = datedTasks
    .sort((a, b) => a.start - b.start)
    .map(({ task, start, end }) => {
      const left = ((start - minStart) / span) * 100;
      const width = Math.max(((end - start) / span) * 100, 1.5);
      return `
      <div class="timeline-row">
        <div class="timeline-task-title">#${task.id} ${escapeHtml(task.title)}</div>
        <div class="timeline-track">
          <div class="timeline-bar" style="left:${left.toFixed(2)}%;width:${width.toFixed(2)}%"></div>
        </div>
        <div class="timeline-task-meta">${formatDateTime(task.start_time)} — ${formatDateTime(task.end_time)}</div>
      </div>`;
    })
    .join("");

  return `
    <div class="timeline-head">
      <span>${formatDateTime(new Date(minStart).toISOString())}</span>
      <span>${formatDateTime(new Date(maxEnd).toISOString())}</span>
    </div>
    <div class="timeline-grid">${rows}</div>
  `;
}

async function renderEventDependencyMermaid(tasks, depMap) {
  const root = document.getElementById("event-dependency-graph-root");
  if (!root) return;
  const graphDef = buildMermaidDependencyGraph(tasks, depMap);
  if (!graphDef) {
    root.innerHTML = '<p class="list-item-meta">Зависимостей между задачами нет.</p>';
    return;
  }
  if (!window.mermaid) {
    root.innerHTML = '<p class="list-item-meta">Граф недоступен: Mermaid не загружен.</p>';
    return;
  }
  try {
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
    const renderId = `event_dep_graph_${Date.now()}`;
    const result = await window.mermaid.render(renderId, graphDef);
    root.innerHTML = result.svg;
  } catch (error) {
    root.innerHTML = '<p class="list-item-meta">Не удалось отрисовать граф зависимостей.</p>';
  }
}

function renderEventDetailCard(event, tasks, depMap, participants, eventResources) {
  const root = document.getElementById("event-detail-root");
  const canManage = canCreate();
  const taskById = Object.fromEntries(tasks.map((t) => [t.id, t]));

  const tasksBlock =
    tasks.length === 0
      ? '<p class="list-item-meta">Задач по этому мероприятию нет.</p>'
      : tasks
          .map((t) => {
            const deps = depMap[t.id] || [];
            const depText =
              deps.length === 0
                ? "нет зависимостей"
                : deps
                    .map((did) => {
                      const dt = taskById[did];
                      return dt ? `#${did} «${escapeHtml(dt.title)}»` : `#${did}`;
                    })
                    .join("; ");
            return `
        <article class="list-item">
          <p class="list-item-title">
            <button type="button" class="entity-link" data-entity-link="task" data-id="${t.id}" data-return-event="${event.id}">
              #${t.id} ${escapeHtml(t.title)}
            </button>
            <span class="badge">${enumLabel("taskStatus", t.status)}</span>
            <span class="badge">${enumLabel("taskPriority", t.priority)}</span>
          </p>
          <p class="list-item-meta">План: ${formatDateTime(t.start_time)} — ${formatDateTime(t.end_time)}</p>
          <p class="list-item-meta">Дедлайн: ${formatDateTime(t.deadline)}</p>
          <div class="deps-block">Зависит от: ${depText}</div>
        </article>`;
          })
          .join("");
  const timelineBlock = buildEventTimeline(tasks, event);
  const participantsBlock =
    !participants || participants.length === 0
      ? '<p class="list-item-meta">Участников пока нет.</p>'
      : participants
          .map(
            (participant) => `
        <article class="list-item">
          <p class="list-item-title">Пользователь #${participant.user_id}</p>
          <p class="list-item-meta">Роль в мероприятии: ${enumLabel("participantRole", participant.role)}</p>
        </article>`
          )
          .join("");
  const resourcesBlock =
    !eventResources || eventResources.length === 0
      ? '<p class="list-item-meta">Ресурсов пока нет.</p>'
      : eventResources
          .map(
            (resource) => `
        <article class="list-item">
          <p class="list-item-title">
            <button type="button" class="entity-link" data-entity-link="resource" data-id="${resource.id}">
              #${resource.id} ${escapeHtml(resource.name)}
            </button>
            <span class="badge">${enumLabel("resourceType", resource.type)}</span>
          </p>
          <p class="list-item-meta">Количество: ${resource.quantity} | Стоимость/час: ${resource.cost_per_hour ?? "—"}</p>
        </article>`
          )
          .join("");

  const editSection = canManage
    ? `
    <div class="panel">
      <div class="detail-actions">
        <button type="button" class="btn btn-muted btn-inline" id="event-open-task-create-btn">+ Создать задачу</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-resource-create-btn">+ Создать ресурс</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-users-btn">+ Добавить участника</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-allocation-btn">+ Создать выделение ресурса</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-toggle-edit-btn">Редактировать</button>
      </div>
      <div id="event-edit-section" class="hidden" style="margin-top:12px">
        <h3>Редактирование</h3>
        <form id="event-edit-form" class="grid-form">
          <label>Название<input name="title" required value="${escapeHtml(event.title)}" /></label>
          <label>Описание<textarea name="description" rows="3">${escapeHtml(event.description || "")}</textarea></label>
          <label>Начало<input type="datetime-local" name="start_time" required value="${toDatetimeLocalValue(event.start_time)}" /></label>
          <label>Окончание<input type="datetime-local" name="end_time" required value="${toDatetimeLocalValue(event.end_time)}" /></label>
          <label>Локация<input name="location" value="${escapeHtml(event.location || "")}" /></label>
          <label>Бюджет<input type="number" step="0.01" name="budget" value="${event.budget ?? 0}" /></label>
          <label>Статус
            <select name="status">
              <option value="draft" ${event.status === "draft" ? "selected" : ""}>${enumLabel("eventStatus", "draft")}</option>
              <option value="published" ${event.status === "published" ? "selected" : ""}>${enumLabel("eventStatus", "published")}</option>
              <option value="cancelled" ${event.status === "cancelled" ? "selected" : ""}>${enumLabel("eventStatus", "cancelled")}</option>
              <option value="completed" ${event.status === "completed" ? "selected" : ""}>${enumLabel("eventStatus", "completed")}</option>
            </select>
          </label>
          <button class="btn btn-primary" type="submit">Сохранить</button>
        </form>
        <div class="detail-actions" style="margin-top:12px">
          <button type="button" class="btn btn-danger" id="event-delete-btn">Удалить мероприятие</button>
          <button type="button" class="btn btn-muted btn-inline" id="event-cancel-edit-btn">Отмена</button>
        </div>
      </div>
    </div>`
    : "";

  root.innerHTML = `
    <div class="panel">
      <dl class="detail-dl">
        <dt>ID</dt><dd>${event.id}</dd>
        <dt>Статус</dt><dd>${enumLabel("eventStatus", event.status)}</dd>
        <dt>Владелец</dt><dd>${event.owner_id}</dd>
        <dt>Начало</dt><dd>${new Date(event.start_time).toLocaleString()}</dd>
        <dt>Окончание</dt><dd>${new Date(event.end_time).toLocaleString()}</dd>
        <dt>Локация</dt><dd>${escapeHtml(event.location || "—")}</dd>
        <dt>Бюджет</dt><dd>${event.budget ?? 0}</dd>
        <dt>Создано</dt><dd>${event.created_at ? new Date(event.created_at).toLocaleString() : "—"}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(event.description || "Без описания")}</p>
    </div>
    ${editSection}
    <div class="panel">
      <h3>Участники мероприятия</h3>
      ${participantsBlock}
    </div>
    <div class="panel">
      <h3>Используемые ресурсы</h3>
      ${resourcesBlock}
    </div>
    <div class="panel">
      <h3>Задачи и зависимости</h3>
      ${tasksBlock}
    </div>
    <div class="panel">
      <h3>Граф зависимостей задач</h3>
      <div id="event-dependency-graph-root">
        <p class="list-item-meta">Построение графа…</p>
      </div>
    </div>
    <div class="panel">
      <h3>План задач (таймлайн)</h3>
      ${timelineBlock}
    </div>
  `;

  if (canManage) {
    document.getElementById("event-open-task-create-btn").addEventListener("click", () => {
      state.taskCreatePresetEventId = event.id;
      void presetTaskCreateForEvent(event.id);
    });
    document.getElementById("event-open-resource-create-btn").addEventListener("click", () => {
      openResourceCreateForEvent(event.id);
    });
    document.getElementById("event-open-users-btn").addEventListener("click", () => {
      void openUsersForEventParticipants(event.id);
    });
    document.getElementById("event-open-allocation-btn").addEventListener("click", () => {
      openAllocationCreatePanel({ eventId: event.id });
    });
    document.getElementById("event-toggle-edit-btn").addEventListener("click", () => {
      document.getElementById("event-edit-section").classList.remove("hidden");
    });
    document.getElementById("event-cancel-edit-btn").addEventListener("click", () => {
      document.getElementById("event-edit-section").classList.add("hidden");
    });
    document.getElementById("event-edit-form").addEventListener("submit", (e) => onEventEditSubmit(e, event.id));
    document.getElementById("event-delete-btn").addEventListener("click", () => onEventDelete(event.id));
  }
  void renderEventDependencyMermaid(tasks, depMap);
}

async function onEventEditSubmit(event, eventId) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.budget = payload.budget ? Number(payload.budget) : 0;
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
  if (payload.start_time && payload.end_time && new Date(payload.end_time) < new Date(payload.start_time)) {
    notify("Дата окончания мероприятия не может быть раньше даты начала", true);
    return;
  }
  if (!payload.description) payload.description = null;
  if (!payload.location) payload.location = null;

  try {
    await apiRequest(`${API.events}${eventId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Мероприятие обновлено");
    await openEventDetail(eventId);
    await refreshData();
  } catch (error) {
    notify(`Ошибка сохранения: ${error.message}`, true);
  }
}

async function onEventDelete(eventId) {
  if (!confirm("Удалить мероприятие? Это действие необратимо.")) return;
  try {
    await apiRequest(`${API.events}${eventId}`, { method: "DELETE" });
    notify("Мероприятие удалено");
    state.detailView = null;
    state.detailEventId = null;
    hideAllScreens();
    document.getElementById(`${state.currentScreen}-screen`).classList.remove("hidden");
    el.screenTitle.textContent = screenName(state.currentScreen);
    updateTopbarActions();
    await refreshData();
  } catch (error) {
    notify(`Ошибка удаления: ${error.message}`, true);
  }
}

async function openTaskDetail(taskId, opts = {}) {
  if (opts.returnToEventId != null) {
    state.detailBackTarget = { kind: "event", id: opts.returnToEventId };
  } else {
    state.detailBackTarget = null;
  }
  state.detailView = "task";
  state.detailEventId = null;
  hideAllScreens();
  document.getElementById("task-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Задача";
  updateTopbarActions();
  notify("Загрузка…");

  const root = document.getElementById("task-detail-root");
  root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';

  try {
    const task = await apiRequest(`${API.tasks}${taskId}`);
    el.screenTitle.textContent = task.title || `Задача #${taskId}`;
    let dependsOn = [];
    const mode = taskDetailMode(task);
    if (mode === "full" && canCreate()) {
      try {
        const depPayload = await apiRequest(`${API.tasks}${taskId}/dependency-ids`);
        dependsOn = Array.isArray(depPayload?.depends_on) ? depPayload.depends_on : [];
      } catch (depErr) {
        notify(`Не удалось загрузить зависимости: ${depErr.message}`, true);
      }
    }
    renderTaskDetailCard(task, dependsOn);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function buildTaskDependenciesPanel(task, dependsOnIds) {
  const inEvent = state.tasks.filter((t) => t.event_id === task.event_id);
  const taskById = Object.fromEntries(inEvent.map((t) => [t.id, t]));
  const listBlock =
    dependsOnIds.length === 0
      ? '<p class="list-item-meta">Нет зависимостей.</p>'
      : `<ul class="list">${dependsOnIds
          .map((did) => {
            const t = taskById[did];
            const label = t ? `#${did} — ${escapeHtml(t.title)}` : `#${did}`;
            return `<li class="list-item" style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><span>${label}</span><button type="button" class="btn btn-muted btn-inline task-dep-remove-btn" data-depends-on="${did}">Удалить</button></li>`;
          })
          .join("")}</ul>`;

  const candidates = inEvent.filter(
    (t) => t.id !== task.id && !dependsOnIds.includes(t.id)
  );
  const selectOpts =
    '<option value="">Выберите задачу-предшественник</option>' +
    candidates
      .map((t) => `<option value="${t.id}">#${t.id} — ${escapeHtml(t.title)}</option>`)
      .join("");

  return `
    <div class="panel" style="margin-top:12px" id="task-deps-panel">
      <h3>Зависимости</h3>
      <p class="list-item-meta">Текущая задача зависит от выбранных задач того же мероприятия (их нужно завершить раньше).</p>
      ${listBlock}
      <div class="detail-actions" style="margin-top:12px;flex-wrap:wrap;gap:8px">
        <select id="task-dep-add-select" style="min-width:220px">${selectOpts}</select>
        <button type="button" class="btn btn-primary" id="task-dep-add-btn">Добавить зависимость</button>
      </div>
    </div>`;
}

function renderTaskDetailCard(task, dependsOnIds = []) {
  const root = document.getElementById("task-detail-root");
  const mode = taskDetailMode(task);
  const canManage = canCreate();
  const depsSection = mode === "full" && canManage ? buildTaskDependenciesPanel(task, dependsOnIds) : "";

  const statusSelect = (name, current, options = ["todo", "in_progress", "done", "overdue", "blocked"]) => `
    <select name="${name}">
      ${options
        .map((option) => `<option value="${option}" ${current === option ? "selected" : ""}>${enumLabel("taskStatus", option)}</option>`)
        .join("")}
    </select>`;

  let editSection = "";
  if (mode === "full" && canManage) {
    editSection = `
    <div class="panel">
      <div class="detail-actions">
        <button type="button" class="btn btn-muted btn-inline" id="task-open-allocation-btn">+ Создать выделение ресурса</button>
        <button type="button" class="btn btn-muted btn-inline" id="task-toggle-edit-btn">Редактировать</button>
      </div>
      <div id="task-edit-section" class="hidden" style="margin-top:12px">
        <h3>Редактирование</h3>
        <form id="task-edit-form" class="grid-form">
          <label>Название<input name="title" required value="${escapeHtml(task.title)}" /></label>
          <label>Описание<textarea name="description" rows="3">${escapeHtml(task.description || "")}</textarea></label>
          <label>Статус ${statusSelect("status", task.status)}</label>
          <label>Приоритет
            <select name="priority">
              <option value="low" ${task.priority === "low" ? "selected" : ""}>${enumLabel("taskPriority", "low")}</option>
              <option value="medium" ${task.priority === "medium" ? "selected" : ""}>${enumLabel("taskPriority", "medium")}</option>
              <option value="high" ${task.priority === "high" ? "selected" : ""}>${enumLabel("taskPriority", "high")}</option>
            </select>
          </label>
          <label>Исполнитель
            <select name="assignee_id" id="task-edit-assignee-select">
              <option value="">Без исполнителя</option>
            </select>
          </label>
          <label>Старт (план)<input type="datetime-local" name="start_time" required value="${toDatetimeLocalValue(task.start_time)}" /></label>
          <label>Окончание (план)<input type="datetime-local" name="end_time" required value="${toDatetimeLocalValue(task.end_time)}" /></label>
          <label>Дедлайн<input type="datetime-local" name="deadline" required value="${toDatetimeLocalValue(task.deadline)}" /></label>
          <button class="btn btn-primary" type="submit">Сохранить</button>
        </form>
        <div class="detail-actions" style="margin-top:12px">
          <button type="button" class="btn btn-danger" id="task-delete-btn">Удалить задачу</button>
          <button type="button" class="btn btn-muted btn-inline" id="task-cancel-edit-btn">Отмена</button>
        </div>
      </div>
    </div>`;
  } else if (mode === "status_only") {
    editSection = `
    <div class="panel">
      <div class="detail-actions">
        <button type="button" class="btn btn-muted btn-inline" id="task-toggle-status-btn">Изменить статус</button>
      </div>
      <div id="task-status-section" class="hidden" style="margin-top:12px">
        <h3>Смена статуса</h3>
        <p class="list-item-meta">Как исполнитель вы можете изменить только статус.</p>
        <form id="task-status-form" class="grid-form">
          <label>Статус ${statusSelect("status", task.status, ["in_progress", "done"])}</label>
          <button class="btn btn-primary" type="submit">Сохранить статус</button>
        </form>
      </div>
    </div>`;
  }

  root.innerHTML = `
    <div class="panel">
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${task.event_id}">#${task.event_id}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${task.id}</dd>
        <dt>Статус</dt><dd>${enumLabel("taskStatus", task.status)}</dd>
        <dt>Приоритет</dt><dd>${enumLabel("taskPriority", task.priority)}</dd>
        <dt>Исполнитель</dt><dd>${task.assignee_id ?? "—"}</dd>
        <dt>Владелец</dt><dd>${task.owner_id}</dd>
        <dt>Дедлайн</dt><dd>${new Date(task.deadline).toLocaleString()}</dd>
        <dt>План: старт — окончание</dt><dd>${new Date(task.start_time).toLocaleString()} — ${new Date(task.end_time).toLocaleString()}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(task.description || "Без описания")}</p>
    </div>
    ${depsSection}
    ${editSection}
  `;

  if (mode === "full" && canManage) {
    const depPanel = document.getElementById("task-deps-panel");
    if (depPanel) {
      depPanel.querySelectorAll(".task-dep-remove-btn").forEach((btn) => {
        btn.addEventListener("click", () => onTaskDependencyRemove(task.id, Number(btn.dataset.dependsOn)));
      });
      const addBtn = document.getElementById("task-dep-add-btn");
      if (addBtn) {
        addBtn.addEventListener("click", () => onTaskDependencyAdd(task.id));
      }
    }
    void loadTaskEditAssigneeOptions(task.event_id, task.assignee_id);
    document.getElementById("task-open-allocation-btn").addEventListener("click", () => {
      openAllocationCreatePanel({ eventId: task.event_id, taskId: task.id });
    });
    document.getElementById("task-toggle-edit-btn").addEventListener("click", () => {
      document.getElementById("task-edit-section").classList.remove("hidden");
    });
    document.getElementById("task-cancel-edit-btn").addEventListener("click", () => {
      document.getElementById("task-edit-section").classList.add("hidden");
    });
    document.getElementById("task-edit-form").addEventListener("submit", (e) => onTaskEditSubmit(e, task.id));
    document.getElementById("task-delete-btn").addEventListener("click", () => onTaskDelete(task.id));
  } else if (mode === "status_only") {
    document.getElementById("task-toggle-status-btn").addEventListener("click", () => {
      document.getElementById("task-status-section").classList.remove("hidden");
    });
    document.getElementById("task-status-form").addEventListener("submit", (e) => onTaskStatusSubmit(e, task.id));
  }
}

async function onTaskEditSubmit(event, taskId) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.assignee_id = payload.assignee_id ? Number(payload.assignee_id) : null;
  payload.deadline = toIsoOrNull(payload.deadline);
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
  if (!payload.description) payload.description = null;

  try {
    await apiRequest(`${API.tasks}${taskId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Задача обновлена");
    await openTaskDetail(taskId, {
      returnToEventId: state.detailBackTarget?.kind === "event" ? state.detailBackTarget.id : undefined
    });
    await refreshData();
  } catch (error) {
    notify(`Ошибка сохранения: ${error.message}`, true);
  }
}

async function onTaskStatusSubmit(event, taskId) {
  event.preventDefault();
  const form = event.target;
  const payload = { status: serializeForm(form).status };
  try {
    await apiRequest(`${API.tasks}${taskId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Статус обновлён");
    await openTaskDetail(taskId, {
      returnToEventId: state.detailBackTarget?.kind === "event" ? state.detailBackTarget.id : undefined
    });
    await refreshData();
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

function taskDetailReopenOpts() {
  return {
    returnToEventId: state.detailBackTarget?.kind === "event" ? state.detailBackTarget.id : undefined
  };
}

async function onTaskDependencyAdd(taskId) {
  const sel = document.getElementById("task-dep-add-select");
  if (!sel || !sel.value) {
    notify("Выберите задачу-предшественник", true);
    return;
  }
  const dependsOn = Number(sel.value);
  try {
    await apiRequest(`${API.tasks}${taskId}/dependencies/${dependsOn}`, { method: "POST" });
    notify("Зависимость добавлена");
    await openTaskDetail(taskId, taskDetailReopenOpts());
    if (state.detailBackTarget?.kind === "event") {
      const eventTasks = await apiRequest(`${API.tasks}event/${state.detailBackTarget.id}`);
      if (Array.isArray(eventTasks)) state.tasks = eventTasks;
    }
  } catch (error) {
    notify(`Не удалось добавить зависимость: ${error.message}`, true);
  }
}

async function onTaskDependencyRemove(taskId, dependsOnTaskId) {
  if (!confirm("Удалить эту зависимость?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}/dependencies/${dependsOnTaskId}`, { method: "DELETE" });
    notify("Зависимость удалена");
    await openTaskDetail(taskId, taskDetailReopenOpts());
    if (state.detailBackTarget?.kind === "event") {
      const eventTasks = await apiRequest(`${API.tasks}event/${state.detailBackTarget.id}`);
      if (Array.isArray(eventTasks)) state.tasks = eventTasks;
    }
  } catch (error) {
    notify(`Не удалось удалить зависимость: ${error.message}`, true);
  }
}

async function onTaskDelete(taskId) {
  if (!confirm("Удалить задачу?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}`, { method: "DELETE" });
    notify("Задача удалена");
    state.detailBackTarget = null;
    state.detailView = null;
    hideAllScreens();
    document.getElementById(`${state.currentScreen}-screen`).classList.remove("hidden");
    el.screenTitle.textContent = screenName(state.currentScreen);
    updateTopbarActions();
    await refreshData();
  } catch (error) {
    notify(`Ошибка удаления: ${error.message}`, true);
  }
}

async function openResourceDetail(resourceId) {
  state.detailBackTarget = null;
  state.detailView = "resource";
  hideAllScreens();
  document.getElementById("resource-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Ресурс";
  updateTopbarActions();
  notify("Загрузка…");

  const root = document.getElementById("resource-detail-root");
  root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';

  try {
    const resource = await apiRequest(`${API.resources}${resourceId}`);
    el.screenTitle.textContent = resource.name || `Ресурс #${resourceId}`;
    renderResourceDetailCard(resource);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function renderResourceDetailCard(resource) {
  const root = document.getElementById("resource-detail-root");
  const canManage = canCreate();
  const allocs = Array.isArray(resource.allocations) ? resource.allocations : [];

  const allocBlock =
    allocs.length === 0
      ? '<p class="list-item-meta">Нет выделений.</p>'
      : allocs
          .map(
            (a) => `
    <article class="list-item">
      <p class="list-item-title">Выделение #${a.id} <span class="badge">${enumLabel("allocationStatus", a.status)}</span></p>
      <p class="list-item-meta">Задача: ${a.task_id ?? "—"} | ${new Date(a.date_start).toLocaleString()} — ${new Date(a.date_end).toLocaleString()}</p>
    </article>`
          )
          .join("");

  const editSection = canManage
    ? `
    <div class="panel">
      <div class="detail-actions">
        <button type="button" class="btn btn-muted btn-inline" id="resource-open-allocation-btn">+ Создать выделение ресурса</button>
        <button type="button" class="btn btn-muted btn-inline" id="resource-toggle-edit-btn">Редактировать</button>
      </div>
      <div id="resource-edit-section" class="hidden" style="margin-top:12px">
        <h3>Редактирование</h3>
        <form id="resource-edit-form" class="grid-form">
          <label>Название<input name="name" required value="${escapeHtml(resource.name)}" /></label>
          <label>Тип
            <select name="type">
              <option value="equipment" ${resource.type === "equipment" ? "selected" : ""}>${enumLabel("resourceType", "equipment")}</option>
              <option value="venue" ${resource.type === "venue" ? "selected" : ""}>${enumLabel("resourceType", "venue")}</option>
              <option value="personnel" ${resource.type === "personnel" ? "selected" : ""}>${enumLabel("resourceType", "personnel")}</option>
              <option value="material" ${resource.type === "material" ? "selected" : ""}>${enumLabel("resourceType", "material")}</option>
            </select>
          </label>
          <label>Описание<textarea name="description" rows="2">${escapeHtml(resource.description || "")}</textarea></label>
          <label>Количество<input type="number" name="quantity" required min="1" value="${resource.quantity}" /></label>
          <label>Стоимость/час<input type="number" step="0.01" name="cost_per_hour" value="${resource.cost_per_hour ?? ""}" /></label>
          <button class="btn btn-primary" type="submit">Сохранить</button>
        </form>
        <div class="detail-actions" style="margin-top:12px">
          <button type="button" class="btn btn-danger" id="resource-delete-btn">Удалить ресурс</button>
          <button type="button" class="btn btn-muted btn-inline" id="resource-cancel-edit-btn">Отмена</button>
        </div>
      </div>
    </div>`
    : "";

  root.innerHTML = `
    <div class="panel">
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${resource.event_id}">#${resource.event_id}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${resource.id}</dd>
        <dt>Тип</dt><dd>${enumLabel("resourceType", resource.type)}</dd>
        <dt>Владелец</dt><dd>${resource.owner_id}</dd>
        <dt>Количество</dt><dd>${resource.quantity}</dd>
        <dt>Стоимость/час</dt><dd>${resource.cost_per_hour ?? "—"}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(resource.description || "")}</p>
    </div>
    ${editSection}
    <div class="panel">
      <h3>Выделения</h3>
      ${allocBlock}
    </div>
  `;

  if (canManage) {
    document.getElementById("resource-open-allocation-btn").addEventListener("click", () => {
      openAllocationCreatePanel({ eventId: resource.event_id, resourceId: resource.id });
    });
    document.getElementById("resource-toggle-edit-btn").addEventListener("click", () => {
      document.getElementById("resource-edit-section").classList.remove("hidden");
    });
    document.getElementById("resource-cancel-edit-btn").addEventListener("click", () => {
      document.getElementById("resource-edit-section").classList.add("hidden");
    });
    document.getElementById("resource-edit-form").addEventListener("submit", (e) => onResourceEditSubmit(e, resource.id));
    document.getElementById("resource-delete-btn").addEventListener("click", () => onResourceDelete(resource.id));
  }
}

async function onResourceEditSubmit(event, resourceId) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.quantity = Number(payload.quantity);
  payload.cost_per_hour = payload.cost_per_hour ? Number(payload.cost_per_hour) : null;
  if (!payload.description) payload.description = null;

  try {
    await apiRequest(`${API.resources}${resourceId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Ресурс обновлён");
    await openResourceDetail(resourceId);
    await refreshData();
  } catch (error) {
    notify(`Ошибка сохранения: ${error.message}`, true);
  }
}

async function onResourceDelete(resourceId) {
  if (!confirm("Удалить ресурс?")) return;
  try {
    await apiRequest(`${API.resources}${resourceId}`, { method: "DELETE" });
    notify("Ресурс удалён");
    state.detailView = null;
    hideAllScreens();
    document.getElementById(`${state.currentScreen}-screen`).classList.remove("hidden");
    el.screenTitle.textContent = screenName(state.currentScreen);
    updateTopbarActions();
    await refreshData();
  } catch (error) {
    notify(`Ошибка удаления: ${error.message}`, true);
  }
}

function onProtectedClick(e) {
  const t = e.target.closest("[data-entity-link]");
  if (!t) return;
  const kind = t.dataset.entityLink;
  const id = Number(t.dataset.id);
  if (!kind || Number.isNaN(id)) return;
  e.preventDefault();

  if (kind === "event") {
    void openEventDetail(id);
    return;
  }
  if (kind === "task") {
    const ret = t.dataset.returnEvent;
    void openTaskDetail(id, ret ? { returnToEventId: Number(ret) } : {});
    return;
  }
  if (kind === "resource") {
    void openResourceDetail(id);
  }
}

async function onLoginSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  try {
    const result = await apiRequest(`${API.auth}/login`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    saveSession(result.access_token, payload.email);
    form.reset();
    syncAuthUi();
    notify("Успешный вход");
    await refreshData();
  } catch (error) {
    notify(`Ошибка входа: ${error.message}`, true);
  }
}

async function onRegisterSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  try {
    await apiRequest(`${API.auth}/register`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Пользователь создан. Теперь можно войти");
    form.reset();
    setAuthView("login");
  } catch (error) {
    notify(`Ошибка регистрации: ${error.message}`, true);
  }
}

async function onEventCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.budget = payload.budget ? Number(payload.budget) : 0;
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
  if (payload.start_time && payload.end_time && new Date(payload.end_time) < new Date(payload.start_time)) {
    notify("Дата окончания мероприятия не может быть раньше даты начала", true);
    return;
  }

  try {
    await apiRequest(API.events, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Мероприятие создано");
    form.reset();
    await refreshData();
  } catch (error) {
    notify(`Ошибка создания мероприятия: ${error.message}`, true);
  }
}

async function onTaskCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);

  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    notify("Выберите мероприятие", true);
    return;
  }
  payload.assignee_id = payload.assignee_id ? Number(payload.assignee_id) : null;
  payload.deadline = toIsoOrNull(payload.deadline);
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);

  try {
    await apiRequest(API.tasks, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Задача создана");
    form.reset();
    state.taskCreatePresetEventId = null;
    populateTaskEventOptions();
    await loadAssigneeOptions(null);
    await refreshData();
  } catch (error) {
    notify(`Ошибка создания задачи: ${error.message}`, true);
  }
}

async function onTaskEventChange(event) {
  const eventId = Number(event.target.value);
  state.taskCreatePresetEventId = Number.isNaN(eventId) || !eventId ? null : eventId;
  await loadAssigneeOptions(state.taskCreatePresetEventId);
}

async function onUsersSearchSubmit(event) {
  event.preventDefault();
  const payload = serializeForm(event.target);
  state.usersSearch.q = (payload.q || "").trim();
  state.usersSearch.speciality = (payload.speciality || "").trim();
  await loadUsers();
}

async function onUsersListClick(event) {
  const addBtn = event.target.closest("[data-add-participant-user]");
  if (!addBtn) return;
  if (!state.participantsModeEventId) return;

  const userId = Number(addBtn.dataset.addParticipantUser);
  if (!userId) return;
  const roleSelect = document.querySelector(`[data-user-role-select="${userId}"]`);
  const role = roleSelect ? roleSelect.value : "viewer";

  try {
    await apiRequest(`${API.events}${state.participantsModeEventId}/participants`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role })
    });
    notify("Участник добавлен");
  } catch (error) {
    notify(`Ошибка добавления участника: ${error.message}`, true);
  }
}

function onAllocationEventChange(event) {
  const eventId = Number(event.target.value) || null;
  state.allocationPreset.eventId = eventId;
  state.allocationPreset.taskId = null;
  state.allocationPreset.resourceId = null;
  populateAllocationTaskOptions(eventId, null);
  populateAllocationResourceOptions(eventId, null);
}

function onAllocationTaskChange(event) {
  const taskId = Number(event.target.value) || null;
  state.allocationPreset.taskId = taskId;
  if (!taskId) return;
  const task = state.tasks.find((item) => item.id === taskId);
  if (!task) return;
  state.allocationPreset.eventId = task.event_id;
  if (el.allocationEventSelect) {
    el.allocationEventSelect.value = String(task.event_id);
  }
  populateAllocationTaskOptions(task.event_id, taskId);
  populateAllocationResourceOptions(task.event_id, state.allocationPreset.resourceId);
  const form = document.getElementById("allocation-form");
  if (form) {
    form.elements.date_start.value = toDatetimeLocalValue(task.start_time);
    form.elements.date_end.value = toDatetimeLocalValue(task.end_time);
  }
}

async function onAllocationCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  const eventId = Number(payload.event_id);
  payload.task_id = payload.task_id ? Number(payload.task_id) : null;
  payload.resource_id = Number(payload.resource_id);
  payload.quantity_used = payload.quantity_used ? Number(payload.quantity_used) : 1;
  payload.date_start = toIsoOrNull(payload.date_start);
  payload.date_end = toIsoOrNull(payload.date_end);

  if (!eventId || !payload.resource_id || !payload.date_start || !payload.date_end) {
    notify("Заполните обязательные поля выделения", true);
    return;
  }

  try {
    await apiRequest(`${API.resources}allocations/`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Выделение создано");
    form.reset();
    state.allocationPreset = { eventId: null, taskId: null, resourceId: null };
    populateAllocationEventOptions();
    populateAllocationTaskOptions(null);
    populateAllocationResourceOptions(null);
  } catch (error) {
    notify(`Ошибка создания выделения: ${error.message}`, true);
  }
}

async function onResourceCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    notify("Выберите мероприятие для ресурса", true);
    return;
  }
  payload.quantity = Number(payload.quantity);
  payload.cost_per_hour = payload.cost_per_hour ? Number(payload.cost_per_hour) : null;

  try {
    await apiRequest(API.resources, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Ресурс создан");
    form.reset();
    await refreshData();
  } catch (error) {
    notify(`Ошибка создания ресурса: ${error.message}`, true);
  }
}

async function onAiGenerate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    notify("Выберите мероприятие для AI генерации", true);
    return;
  }
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn ? submitBtn.textContent : "";
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Генерация...";
  }

  try {
    const result = await apiRequest(`${API.ai}/generate`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    renderList(el.aiResult, result.tasks || [], (task) => `
      <p class="list-item-title">
        <button type="button" class="entity-link" data-entity-link="task" data-id="${task.id}">
          #${task.id} ${escapeHtml(task.title)}
        </button>
      </p>
      <p class="list-item-meta">${escapeHtml(task.description || "Описание не указано")}</p>
      <p class="list-item-meta">Мероприятие: #${task.event_id}</p>
    `);
    notify(`AI сгенерировал задач: ${(result.tasks || []).length}`);
    await refreshData();
  } catch (error) {
    notify(`Ошибка AI генерации: ${error.message}`, true);
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText || "Сгенерировать";
    }
  }
}

async function onProfileCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  try {
    await apiRequest(`${API.users}/`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Профиль создан");
    form.reset();
    setProfileRequired(false);
    await refreshData();
  } catch (error) {
    notify(`Ошибка создания профиля: ${error.message}`, true);
  }
}

function setCabinetEditMode(mode) {
  const profileForm = document.getElementById("profile-cabinet-form");
  const accountForm = document.getElementById("account-cabinet-form");
  const openProfileBtn = document.getElementById("cabinet-open-profile-edit-btn");
  const openAccountBtn = document.getElementById("cabinet-open-account-edit-btn");
  if (!profileForm || !accountForm || !openProfileBtn || !openAccountBtn) return;
  profileForm.classList.toggle("hidden", mode !== "profile");
  accountForm.classList.toggle("hidden", mode !== "account");
  openProfileBtn.classList.toggle("hidden", mode === "profile");
  openAccountBtn.classList.toggle("hidden", mode === "account");
}

async function loadProfileCabinet() {
  if (!state.token) return;
  setCabinetEditMode(null);
  const emailEl = document.getElementById("cabinet-auth-email-display");
  try {
    const me = await apiRequest(`${API.users}/me`);
    state.profileId = me.id;
    const setText = (id, value) => {
      const node = document.getElementById(id);
      if (node) node.textContent = value || "—";
    };
    setText("cabinet-view-first-name", me.first_name);
    setText("cabinet-view-last-name", me.last_name);
    setText("cabinet-view-phone", me.phone);
    setText("cabinet-view-speciality", me.speciality);
    setText("cabinet-view-bio", me.bio);
    if (emailEl) {
      emailEl.textContent = me.email || state.email || "—";
    }

    const profileForm = document.getElementById("profile-cabinet-form");
    if (profileForm) {
      profileForm.first_name.value = me.first_name || "";
      profileForm.last_name.value = me.last_name || "";
      profileForm.phone.value = me.phone || "";
      profileForm.speciality.value = me.speciality || "";
      profileForm.bio.value = me.bio || "";
    }
  } catch (error) {
    if (emailEl) emailEl.textContent = state.email || "—";
    notify(`Не удалось загрузить профиль: ${error.message}`, true);
  }
}

async function onProfileCabinetSave(event) {
  event.preventDefault();
  if (!state.profileId) {
    notify("Сначала создайте профиль", true);
    return;
  }
  const form = event.target;
  const payload = serializeForm(form);
  payload.phone = payload.phone?.trim() || null;
  payload.speciality = payload.speciality?.trim() || null;
  payload.bio = payload.bio?.trim() || null;
  try {
    await apiRequest(`${API.users}/${state.profileId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Профиль сохранён");
    setCabinetEditMode(null);
    await loadProfileCabinet();
    await refreshData();
  } catch (error) {
    notify(`Ошибка сохранения профиля: ${error.message}`, true);
  }
}

async function onAccountCabinetSave(event) {
  event.preventDefault();
  const form = event.target;
  const raw = serializeForm(form);
  const emailTrim = raw.email?.trim() || "";
  const newPassword = raw.new_password?.trim() || "";
  const currentPassword = raw.current_password?.trim() || "";

  if (!emailTrim && !newPassword) {
    notify("Укажите новый email и/или новый пароль", true);
    return;
  }
  if (!currentPassword) {
    notify("Введите текущий пароль", true);
    return;
  }

  const payload = { current_password: currentPassword };
  if (emailTrim) payload.email = emailTrim;
  if (newPassword) payload.new_password = newPassword;

  try {
    const result = await apiRequest(`${API.auth}/me`, {
      method: "PATCH",
      body: JSON.stringify(payload)
    });
    notify(result.message || "Учётная запись обновлена");
    form.reset();
    if (result.access_token) {
      const nextEmail = emailTrim || state.email;
      saveSession(result.access_token, nextEmail);
      syncAuthUi();
    }
    setCabinetEditMode(null);
    await loadProfileCabinet();
    await refreshData();
  } catch (error) {
    notify(`Ошибка учётной записи: ${error.message}`, true);
  }
}

function bindEvents() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => setScreen(btn.dataset.screen));
  });
  document.querySelectorAll(".metric-card[data-screen-target]").forEach((card) => {
    card.style.cursor = "pointer";
    card.addEventListener("click", () => {
      setScreen(card.dataset.screenTarget);
    });
  });

  el.protectedContent.addEventListener("click", onProtectedClick);
  if (el.usersList) {
    el.usersList.addEventListener("click", (e) => {
      void onUsersListClick(e);
    });
  }

  document.getElementById("login-form").addEventListener("submit", onLoginSubmit);
  document.getElementById("register-form").addEventListener("submit", onRegisterSubmit);
  document.getElementById("profile-form").addEventListener("submit", onProfileCreate);
  document.getElementById("profile-cabinet-form").addEventListener("submit", (e) => {
    void onProfileCabinetSave(e);
  });
  document.getElementById("account-cabinet-form").addEventListener("submit", (e) => {
    void onAccountCabinetSave(e);
  });
  document.getElementById("session-profile-btn").addEventListener("click", () => {
    setScreen("profile-cabinet");
  });
  document.getElementById("cabinet-open-profile-edit-btn").addEventListener("click", () => {
    setCabinetEditMode("profile");
  });
  document.getElementById("cabinet-cancel-profile-edit-btn").addEventListener("click", () => {
    setCabinetEditMode(null);
  });
  document.getElementById("cabinet-open-account-edit-btn").addEventListener("click", () => {
    setCabinetEditMode("account");
  });
  document.getElementById("cabinet-cancel-account-edit-btn").addEventListener("click", () => {
    setCabinetEditMode(null);
  });
  document.getElementById("auth-tab-login").addEventListener("click", () => setAuthView("login"));
  document.getElementById("auth-tab-register").addEventListener("click", () => setAuthView("register"));
  document.getElementById("event-form").addEventListener("submit", onEventCreate);
  document.getElementById("task-form").addEventListener("submit", onTaskCreate);
  document.getElementById("task-event-select").addEventListener("change", (e) => {
    void onTaskEventChange(e);
  });
  document.getElementById("users-search-form").addEventListener("submit", (e) => {
    void onUsersSearchSubmit(e);
  });
  document.getElementById("allocation-form").addEventListener("submit", (e) => {
    void onAllocationCreate(e);
  });
  document.getElementById("allocation-event-select").addEventListener("change", onAllocationEventChange);
  document.getElementById("allocation-task-select").addEventListener("change", onAllocationTaskChange);
  document.getElementById("resource-form").addEventListener("submit", onResourceCreate);
  document.getElementById("ai-form").addEventListener("submit", onAiGenerate);
  document.getElementById("logout-btn").addEventListener("click", () => {
    clearSession();
    syncAuthUi();
    state.events = [];
    state.tasks = [];
    state.resources = [];
    state.usersList = [];
    renderEvents();
    renderTasks();
    renderResources();
    renderUsers();
    renderDashboard();
    setProfileRequired(false);
    notify("Сессия очищена");
  });
}

async function bootstrap() {
  state.role = getRoleFromToken(state.token);
  bindEvents();
  setAuthView("login");
  syncAuthUi();
  if (state.token) {
    renderDashboard();
    renderEvents();
    renderTasks();
    renderResources();
    await refreshData();
  } else {
    notify("Войдите, чтобы загрузить данные");
  }
}

bootstrap();
