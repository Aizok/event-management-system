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
  aiResult: document.getElementById("ai-result"),
  protectedContent: document.getElementById("protected-content")
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
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
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
    ai: "AI помощник"
  };
  return map[screenId] || "Обзор";
}

function hideAllScreens() {
  document.querySelectorAll(".screen").forEach((item) => item.classList.add("hidden"));
}

function setScreen(screenId) {
  if (!state.token || el.protectedContent.classList.contains("hidden")) {
    el.screenTitle.textContent = "Авторизация";
    return;
  }
  state.currentScreen = screenId;
  state.detailView = null;
  state.detailEventId = null;
  state.detailBackTarget = null;
  hideAllScreens();
  document.getElementById(`${screenId}-screen`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.screen === screenId);
  });
  el.screenTitle.textContent = screenName(screenId);
  updateTopbarActions();
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
    if (panel) panel.classList.toggle("hidden");
  });
  container.appendChild(btn);
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

function renderEvents() {
  renderList(el.eventsList, state.events, (event) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="event" data-id="${event.id}">
        #${event.id} ${escapeHtml(event.title)}
      </button>
      <span class="badge">${event.status}</span>
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
      <span class="badge">${task.status}</span>
      <span class="badge">${task.priority}</span>
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
      <span class="badge">${resource.type}</span>
    </p>
    <p class="list-item-meta">Мероприятие: #${resource.event_id} | Кол-во: ${resource.quantity}</p>
    <p class="list-item-meta">Стоимость/час: ${resource.cost_per_hour ?? "не указано"}</p>
  `);
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
    ["event-create-panel", "task-create-panel", "resource-create-panel", "ai-create-panel"].forEach((id) => {
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
  renderDashboard();

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
    const depResults = await Promise.allSettled(
      tasks.map((t) => apiRequest(`${API.tasks}${t.id}/dependency-ids`))
    );
    const depMap = {};
    tasks.forEach((t, i) => {
      const r = depResults[i];
      depMap[t.id] = r.status === "fulfilled" && r.value?.depends_on ? r.value.depends_on : [];
    });

    el.screenTitle.textContent = event.title || `Мероприятие #${eventId}`;
    renderEventDetailCard(event, tasks, depMap);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function renderEventDetailCard(event, tasks, depMap) {
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
            <span class="badge">${t.status}</span>
            <span class="badge">${t.priority}</span>
          </p>
          <p class="list-item-meta">Дедлайн: ${new Date(t.deadline).toLocaleString()}</p>
          <div class="deps-block">Зависит от: ${depText}</div>
        </article>`;
          })
          .join("");

  const editSection = canManage
    ? `
    <div class="panel">
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
            <option value="draft" ${event.status === "draft" ? "selected" : ""}>draft</option>
            <option value="published" ${event.status === "published" ? "selected" : ""}>published</option>
            <option value="cancelled" ${event.status === "cancelled" ? "selected" : ""}>cancelled</option>
            <option value="completed" ${event.status === "completed" ? "selected" : ""}>completed</option>
          </select>
        </label>
        <button class="btn btn-primary" type="submit">Сохранить</button>
      </form>
      <div class="detail-actions" style="margin-top:12px">
        <button type="button" class="btn btn-danger" id="event-delete-btn">Удалить мероприятие</button>
      </div>
    </div>`
    : "";

  root.innerHTML = `
    <div class="panel">
      <dl class="detail-dl">
        <dt>ID</dt><dd>${event.id}</dd>
        <dt>Статус</dt><dd>${event.status}</dd>
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
      <h3>Задачи и зависимости</h3>
      ${tasksBlock}
    </div>
  `;

  if (canManage) {
    document.getElementById("event-edit-form").addEventListener("submit", (e) => onEventEditSubmit(e, event.id));
    document.getElementById("event-delete-btn").addEventListener("click", () => onEventDelete(event.id));
  }
}

async function onEventEditSubmit(event, eventId) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.budget = payload.budget ? Number(payload.budget) : 0;
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
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
    renderTaskDetailCard(task);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function renderTaskDetailCard(task) {
  const root = document.getElementById("task-detail-root");
  const mode = taskDetailMode(task);
  const canManage = canCreate();

  const statusSelect = (name, current) => `
    <select name="${name}">
      <option value="todo" ${current === "todo" ? "selected" : ""}>todo</option>
      <option value="in_progress" ${current === "in_progress" ? "selected" : ""}>in_progress</option>
      <option value="done" ${current === "done" ? "selected" : ""}>done</option>
      <option value="overdue" ${current === "overdue" ? "selected" : ""}>overdue</option>
      <option value="blocked" ${current === "blocked" ? "selected" : ""}>blocked</option>
    </select>`;

  let editSection = "";
  if (mode === "full" && canManage) {
    editSection = `
    <div class="panel">
      <h3>Редактирование</h3>
      <form id="task-edit-form" class="grid-form">
        <label>Название<input name="title" required value="${escapeHtml(task.title)}" /></label>
        <label>Описание<textarea name="description" rows="3">${escapeHtml(task.description || "")}</textarea></label>
        <label>Статус ${statusSelect("status", task.status)}</label>
        <label>Приоритет
          <select name="priority">
            <option value="low" ${task.priority === "low" ? "selected" : ""}>low</option>
            <option value="medium" ${task.priority === "medium" ? "selected" : ""}>medium</option>
            <option value="high" ${task.priority === "high" ? "selected" : ""}>high</option>
          </select>
        </label>
        <label>Исполнитель (id профиля)<input name="assignee_id" value="${task.assignee_id ?? ""}" placeholder="пусто — не назначен" /></label>
        <label>Дедлайн<input type="datetime-local" name="deadline" required value="${toDatetimeLocalValue(task.deadline)}" /></label>
        <label>Старт (план)<input type="datetime-local" name="start_time" required value="${toDatetimeLocalValue(task.start_time)}" /></label>
        <label>Окончание (план)<input type="datetime-local" name="end_time" required value="${toDatetimeLocalValue(task.end_time)}" /></label>
        <button class="btn btn-primary" type="submit">Сохранить</button>
      </form>
      <div class="detail-actions" style="margin-top:12px">
        <button type="button" class="btn btn-danger" id="task-delete-btn">Удалить задачу</button>
      </div>
    </div>`;
  } else if (mode === "status_only") {
    editSection = `
    <div class="panel">
      <h3>Смена статуса</h3>
      <p class="list-item-meta">Как исполнитель вы можете изменить только статус.</p>
      <form id="task-status-form" class="grid-form">
        <label>Статус ${statusSelect("status", task.status)}</label>
        <button class="btn btn-primary" type="submit">Сохранить статус</button>
      </form>
    </div>`;
  }

  root.innerHTML = `
    <div class="panel">
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${task.event_id}">#${task.event_id}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${task.id}</dd>
        <dt>Статус</dt><dd>${task.status}</dd>
        <dt>Приоритет</dt><dd>${task.priority}</dd>
        <dt>Исполнитель</dt><dd>${task.assignee_id ?? "—"}</dd>
        <dt>Владелец</dt><dd>${task.owner_id}</dd>
        <dt>Дедлайн</dt><dd>${new Date(task.deadline).toLocaleString()}</dd>
        <dt>План: старт — окончание</dt><dd>${new Date(task.start_time).toLocaleString()} — ${new Date(task.end_time).toLocaleString()}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(task.description || "Без описания")}</p>
    </div>
    ${editSection}
  `;

  if (mode === "full" && canManage) {
    document.getElementById("task-edit-form").addEventListener("submit", (e) => onTaskEditSubmit(e, task.id));
    document.getElementById("task-delete-btn").addEventListener("click", () => onTaskDelete(task.id));
  } else if (mode === "status_only") {
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
      <p class="list-item-title">Выделение #${a.id} <span class="badge">${a.status}</span></p>
      <p class="list-item-meta">Задача: ${a.task_id ?? "—"} | ${new Date(a.date_start).toLocaleString()} — ${new Date(a.date_end).toLocaleString()}</p>
    </article>`
          )
          .join("");

  const editSection = canManage
    ? `
    <div class="panel">
      <h3>Редактирование</h3>
      <form id="resource-edit-form" class="grid-form">
        <label>Название<input name="name" required value="${escapeHtml(resource.name)}" /></label>
        <label>Тип
          <select name="type">
            <option value="equipment" ${resource.type === "equipment" ? "selected" : ""}>equipment</option>
            <option value="venue" ${resource.type === "venue" ? "selected" : ""}>venue</option>
            <option value="personnel" ${resource.type === "personnel" ? "selected" : ""}>personnel</option>
            <option value="material" ${resource.type === "material" ? "selected" : ""}>material</option>
          </select>
        </label>
        <label>Описание<textarea name="description" rows="2">${escapeHtml(resource.description || "")}</textarea></label>
        <label>Количество<input type="number" name="quantity" required min="1" value="${resource.quantity}" /></label>
        <label>Стоимость/час<input type="number" step="0.01" name="cost_per_hour" value="${resource.cost_per_hour ?? ""}" /></label>
        <button class="btn btn-primary" type="submit">Сохранить</button>
      </form>
      <div class="detail-actions" style="margin-top:12px">
        <button type="button" class="btn btn-danger" id="resource-delete-btn">Удалить ресурс</button>
      </div>
    </div>`
    : "";

  root.innerHTML = `
    <div class="panel">
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${resource.event_id}">#${resource.event_id}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${resource.id}</dd>
        <dt>Тип</dt><dd>${resource.type}</dd>
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
    await refreshData();
  } catch (error) {
    notify(`Ошибка создания задачи: ${error.message}`, true);
  }
}

async function onResourceCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = serializeForm(form);
  payload.event_id = Number(payload.event_id);
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

function bindEvents() {
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => setScreen(btn.dataset.screen));
  });

  el.protectedContent.addEventListener("click", onProtectedClick);

  document.getElementById("login-form").addEventListener("submit", onLoginSubmit);
  document.getElementById("register-form").addEventListener("submit", onRegisterSubmit);
  document.getElementById("profile-form").addEventListener("submit", onProfileCreate);
  document.getElementById("auth-tab-login").addEventListener("click", () => setAuthView("login"));
  document.getElementById("auth-tab-register").addEventListener("click", () => setAuthView("register"));
  document.getElementById("event-form").addEventListener("submit", onEventCreate);
  document.getElementById("task-form").addEventListener("submit", onTaskCreate);
  document.getElementById("resource-form").addEventListener("submit", onResourceCreate);
  document.getElementById("ai-form").addEventListener("submit", onAiGenerate);
  document.getElementById("logout-btn").addEventListener("click", () => {
    clearSession();
    syncAuthUi();
    state.events = [];
    state.tasks = [];
    state.resources = [];
    renderEvents();
    renderTasks();
    renderResources();
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
