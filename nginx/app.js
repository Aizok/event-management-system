const state = {
  token: localStorage.getItem("ems_token") || "",
  email: localStorage.getItem("ems_email") || "",
  role: "",
  authView: "login",
  currentScreen: "dashboard",
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

function toIsoOrNull(value) {
  if (!value) return null;
  return new Date(value).toISOString();
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

function setScreen(screenId) {
  if (!state.token || el.protectedContent.classList.contains("hidden")) {
    el.screenTitle.textContent = "Авторизация";
    return;
  }
  state.currentScreen = screenId;
  document.querySelectorAll(".screen").forEach((item) => item.classList.add("hidden"));
  document.getElementById(`${screenId}-screen`).classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.screen === screenId);
  });
  el.screenTitle.textContent = screenName(screenId);
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
      #${event.id} ${event.title}
      <span class="badge">${event.status}</span>
    </p>
    <p class="list-item-meta">Сроки: ${new Date(event.start_time).toLocaleString()} - ${new Date(event.end_time).toLocaleString()}</p>
    <p class="list-item-meta">Бюджет: ${event.budget ?? 0}</p>
  `);
}

function renderTasks() {
  renderList(el.tasksList, state.tasks, (task) => `
    <p class="list-item-title">
      #${task.id} ${task.title}
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
      #${resource.id} ${resource.name}
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
  } else {
    el.screenTitle.textContent = screenName(state.currentScreen);
  }
  syncCreateControls();
}

function setProfileRequired(isRequired) {
  if (!state.token) return;
  el.profileBlock.classList.toggle("hidden", !isRequired);
  el.protectedContent.classList.toggle("hidden", isRequired);
  el.screenTitle.textContent = isRequired ? "Создание профиля" : screenName(state.currentScreen);
}

function syncCreateControls() {
  const canCreate = state.role === "admin" || state.role === "organizer";
  document.querySelectorAll(".create-toggle-btn").forEach((btn) => {
    btn.classList.toggle("hidden", !canCreate);
  });
  if (!canCreate) {
    ["event-create-panel", "task-create-panel", "resource-create-panel", "ai-create-panel"].forEach((id) => {
      const panel = document.getElementById(id);
      if (panel) {
        panel.classList.add("hidden");
      }
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
    await apiRequest(`${API.users}/me`);
    setProfileRequired(false);
  } catch (error) {
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
      <p class="list-item-title">#${task.id} ${task.title}</p>
      <p class="list-item-meta">${task.description || "Описание не указано"}</p>
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

  document.getElementById("login-form").addEventListener("submit", onLoginSubmit);
  document.getElementById("register-form").addEventListener("submit", onRegisterSubmit);
  document.getElementById("profile-form").addEventListener("submit", onProfileCreate);
  document.getElementById("auth-tab-login").addEventListener("click", () => setAuthView("login"));
  document.getElementById("auth-tab-register").addEventListener("click", () => setAuthView("register"));
  document.getElementById("event-form").addEventListener("submit", onEventCreate);
  document.getElementById("task-form").addEventListener("submit", onTaskCreate);
  document.getElementById("resource-form").addEventListener("submit", onResourceCreate);
  document.getElementById("ai-form").addEventListener("submit", onAiGenerate);
  document.querySelectorAll(".create-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const panel = document.getElementById(targetId);
      panel.classList.toggle("hidden");
    });
  });
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
