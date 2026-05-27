const state = {
  token: localStorage.getItem("ems_token") || "",
  email: localStorage.getItem("ems_email") || "",
  role: "",
  profileId: null,
  authView: "login",
  currentScreen: "events",
  detailView: null,
  detailEventId: null,
  detailBackTarget: null,
  taskCreatePresetEventId: null,
  resourceCreatePresetEventId: null,
  usersSearch: { id: "", q: "", speciality: "", role: "" },
  usersList: [],
  usersTotal: 0,
  usersSkip: 0,
  usersLimit: 25,
  participantsModeEventId: null,
  allocationPreset: { eventId: null, taskId: null, resourceId: null },
  events: [],
  aiDraft: null,
  taskMetrics: { total: 0, overdue: 0 },
  tasksPage: [],
  tasksTotal: 0,
  tasksSkip: 0,
  tasksLimit: 25,
  tasksFilters: { eventId: "", status: "", priority: "", q: "" },
  resources: [],
  assigneeNames: {},
  inboxTab: "incoming"
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
  usersAddEventSelect: document.getElementById("users-add-event-select"),
  usersModeHint: document.getElementById("users-mode-hint"),
  aiResult: document.getElementById("ai-result"),
  protectedContent: document.getElementById("protected-content"),
  taskEventSelect: document.getElementById("task-event-select"),
  taskCreateInviteSelect: document.getElementById("task-create-invite-select"),
  resourceEventSelect: document.getElementById("resource-event-select"),
  aiEventSelect: document.getElementById("ai-event-select"),
  allocationEventSelect: document.getElementById("allocation-event-select"),
  allocationTaskSelect: document.getElementById("allocation-task-select"),
  allocationResourceSelect: document.getElementById("allocation-resource-select")
  ,
  userDetailRoot: document.getElementById("user-detail-root")
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

function formatPublicProfileName(profile) {
  if (!profile) return "";
  const a = String(profile.first_name || "").trim();
  const b = String(profile.last_name || "").trim();
  return [a, b].filter(Boolean).join(" ").trim();
}

/** Кнопка перехода к профилю; при отсутствии ФИО в публичном профиле подпись «Профиль». */
function userProfileLinkButton(userId, profile) {
  if (userId == null || userId === "") return "—";
  const name = formatPublicProfileName(profile);
  const label = name || "Профиль";
  return `<button type="button" class="entity-link" data-entity-link="user" data-id="${userId}">${escapeHtml(label)}</button>`;
}

function userEntityLinkFromName(userId, displayName) {
  const uid = Number(userId);
  if (Number.isNaN(uid)) return "—";
  const label = (displayName || "").trim() || `Пользователь #${uid}`;
  return `<button type="button" class="entity-link" data-entity-link="user" data-id="${uid}">${escapeHtml(label)}</button>`;
}

function eventEntityLink(eventId, title) {
  const eid = Number(eventId);
  if (Number.isNaN(eid)) return "—";
  const label = (title || "").trim() || getEventTitle(eid) || `Мероприятие #${eid}`;
  return `<button type="button" class="entity-link" data-entity-link="event" data-id="${eid}">${escapeHtml(label)}</button>`;
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
  state.usersSearch = { id: "", q: "", speciality: "" };
  localStorage.removeItem("ems_token");
  localStorage.removeItem("ems_email");
  state.taskMetrics = { total: 0, overdue: 0 };
  state.tasksPage = [];
  state.tasksTotal = 0;
  state.tasksSkip = 0;
  state.tasksLimit = 25;
  state.tasksFilters = { eventId: "", status: "", priority: "", q: "" };
  state.assigneeNames = {};
  state.aiDraft = null;
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

function taskAssigneeStatusLabel(status) {
  const map = {
    pending: "ожидает ответа",
    accepted: "принято",
    declined: "отказ от задачи"
  };
  return map[String(status || "").toLowerCase()] || String(status || "");
}

function isTaskAcceptedAssignee(task) {
  if (!task || state.profileId == null) return false;
  const pid = Number(state.profileId);
  const rows = Array.isArray(task.assignees) ? task.assignees : [];
  return rows.some((a) => Number(a.user_id) === pid && String(a.status).toLowerCase() === "accepted");
}

function taskDetailMode(task) {
  if (state.role === "admin") return "full";
  if (canCreate()) return "full";
  if (
    state.role === "executor" &&
    state.profileId != null &&
    isTaskAcceptedAssignee(task)
  ) {
    return "status_only";
  }
  return "read";
}

const API_ERROR_MESSAGES_RU = {
  "User already participant": "Пользователь уже участник этого мероприятия",
  "Duplicate participant": "Участник с такими данными уже существует",
  "Participant not found": "Участник не найден",
  "Event not found": "Мероприятие не найдено",
  "Not enough permissions": "Недостаточно прав для выполнения операции",
  "Not allowed": "Операция не разрешена",
  "Cannot assign OWNER role": "Нельзя назначить роль владельца",
  "System viewer can only be added with event role viewer": "Системный наблюдатель может быть только наблюдателем мероприятия",
  "System executor cannot be assigned as event organizer": "Системный исполнитель не может быть организатором мероприятия",
  "Use decline to reject a pending invitation": "Для отклонения приглашения используйте «Отклонить»",
  "Owner cannot leave the event": "Владелец не может покинуть мероприятие",
  "No pending invitation to accept": "Нет приглашения для принятия",
  "No pending invitation to decline": "Нет приглашения для отклонения",
  "User is not a participant of this event": "Пользователь не является участником этого мероприятия",
  "Only owner allowed": "Доступно только владельцу мероприятия",
  "Pending invitation not found": "Приглашение не найдено",
  "Owner cannot remove themselves": "Владелец не может удалить себя из участников",
  "Only admin and organizer can create events": "Создавать мероприятия могут только администратор и организатор",
  "Only the event owner can delete this event": "Удалить мероприятие может только его владелец",
  "Task not found": "Задача не найдена",
  "Tasks must belong to same event": "Задачи должны относиться к одному мероприятию",
  "Task cannot depend on itself": "Задача не может зависеть от самой себя",
  "Dependency cycle detected": "Нельзя добавить зависимость: получится цикл",
  "Dependency already exists": "Такая зависимость уже существует",
  "Dependent task planned start must be on or after predecessor planned end":
    "Плановое начало зависимой задачи должно быть не раньше планового окончания предшественника",
  "Dependency not found": "Зависимость не найдена",
  "dependency_cycle": "Нельзя добавить зависимость: получится цикл",
  "self_dependency": "Задача не может зависеть от самой себя",
  "duplicate_dependency": "Такая зависимость уже существует",
  "invalid_dependency_order": "Неверный порядок зависимостей между задачами",
  "Task is blocked by unfinished dependencies": "Задача заблокирована незавершёнными зависимостями",
  "Executors can only change status": "Исполнитель может менять только статус задачи",
  "Executors can only set status to in_progress or done":
    "Исполнитель может установить только статус «В работе» или «Выполнено»",
  "Executor can only update task status": "Исполнитель может менять только статус задачи",
  "Executor can only set task status to in_progress or done":
    "Исполнитель может установить только статус «В работе» или «Выполнено»",
  "start_time must be < end_time": "Время начала должно быть раньше времени окончания",
  "end_time must be <= deadline": "Время окончания не должно быть позже дедлайна",
  "Cannot invite yourself this way": "Нельзя пригласить самого себя таким способом",
  "User already has an assignee record for this task": "Пользователь уже назначен на эту задачу",
  "You can only accept your own invitation": "Можно принять только своё приглашение",
  "You can only decline your own invitation": "Можно отклонить только своё приглашение",
  "No active assignment to withdraw from": "Нет активного назначения для отказа",
  "Assignee not found": "Исполнитель не найден",
  "History record not found": "Запись истории не найдена",
  "History does not belong to this task": "Запись истории не относится к этой задаче",
  "Resource not found": "Ресурс не найден",
  "Resource not found or access denied": "Ресурс не найден или доступ запрещён",
  "Allocation not found": "Назначение ресурса не найдено",
  "Resource allocation not found": "Назначение ресурса не найдено",
  "Resource allocation not found or access denied": "Назначение ресурса не найдено или доступ запрещён",
  "Cannot cancel completed and cancelled allocation": "Нельзя отменить завершённое или уже отменённое назначение",
  "Not enough resource available": "Недостаточно свободного ресурса на выбранный период",
  "Invalid time range": "Некорректный интервал времени",
  "Task does not belong to this event": "Задача не относится к этому мероприятию",
  "Cannot allocate to completed task": "Нельзя назначить ресурс на завершённую задачу",
  "Allocation outside task time": "Назначение выходит за рамки времени задачи",
  "Cannot update completed or cancelled allocation": "Нельзя изменить завершённое или отменённое назначение",
  "User profile already exists": "Профиль пользователя уже существует",
  "Email already in use": "Этот email уже используется",
  "Profile data violates uniqueness constraints": "Данные профиля нарушают ограничения уникальности",
  "User profile not found": "Профиль пользователя не найден",
  "Email already in use in user profiles": "Этот email уже используется в профилях",
  "User not found": "Пользователь не найден",
  "Cannot delete your own account": "Нельзя удалить свою учётную запись",
  "Failed to delete auth account": "Не удалось удалить учётную запись",
  "Notification not found": "Уведомление не найдено",
  "User profile is required. Create profile in user-service": "Требуется профиль пользователя. Создайте профиль в системе",
  "event-service unavailable": "Сервис мероприятий временно недоступен",
  "task-service unavailable": "Сервис задач временно недоступен",
  "user-service unavailable": "Сервис пользователей временно недоступен",
  "Could not validate credentials": "Не удалось проверить учётные данные",
  "Admin access required": "Требуются права администратора",
  "Service access required": "Требуется служебный доступ",
  "Invalid role": "Недопустимая роль"
};

const API_ERROR_FALLBACK_RU =
  "Не удалось выполнить операцию. Попробуйте ещё раз или обратитесь к администратору.";

function extractApiErrorDetail(body) {
  if (!body || typeof body !== "object") return "";
  const detail = body.detail ?? body.message;
  if (detail == null) return "";
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object") return item.msg || item.message || JSON.stringify(item);
        return String(item);
      })
      .filter(Boolean)
      .join("; ");
  }
  return String(detail);
}

function hasCyrillic(text) {
  return /[а-яёА-ЯЁ]/.test(text);
}

function localizeApiError(message) {
  const raw = String(message ?? "").trim();
  if (!raw) return API_ERROR_FALLBACK_RU;
  if (hasCyrillic(raw)) return raw;
  if (API_ERROR_MESSAGES_RU[raw]) return API_ERROR_MESSAGES_RU[raw];
  const lower = raw.toLowerCase();
  const matchedKey = Object.keys(API_ERROR_MESSAGES_RU).find((key) => key.toLowerCase() === lower);
  if (matchedKey) return API_ERROR_MESSAGES_RU[matchedKey];
  if (raw.startsWith("HTTP ")) return raw;
  return API_ERROR_FALLBACK_RU;
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
      const extracted = extractApiErrorDetail(body);
      if (extracted) message = extracted;
    } catch (err) {
      // ignore body parse error
    }
    const localized = localizeApiError(message);
    if (
      response.status === 401 ||
      (response.status === 403 && localized.toLowerCase().includes("учётн"))
    ) {
      clearSession();
      syncAuthUi();
      throw new Error("Сессия истекла или токен недействителен. Выполните вход снова");
    }
    throw new Error(localized);
  }
  if (response.status === 204) return null;
  return response.json();
}

function screenName(screenId) {
  const map = {
    events: "Мероприятия",
    tasks: "Задачи",
    resources: "Ресурсы",
    users: "Пользователи",
    inbox: "Приглашения",
    ai: "ИИ помощник",
    "profile-cabinet": "Профиль",
    "user-detail": "Пользователь"
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

function formatScheduleDelta(seconds) {
  if (seconds == null || Number.isNaN(Number(seconds))) return "—";
  const n = Number(seconds);
  if (n === 0) return "без отклонения";
  const sign = n > 0 ? "+" : "−";
  const abs = Math.abs(n);
  const days = Math.floor(abs / 86400);
  const hours = Math.floor((abs % 86400) / 3600);
  const mins = Math.floor((abs % 3600) / 60);
  const parts = [];
  if (days) parts.push(`${days} д`);
  if (hours) parts.push(`${hours} ч`);
  if (mins || parts.length === 0) parts.push(`${mins} мин`);
  return `${sign}${parts.join(" ")}`;
}

function buildTaskScheduleDeviationHtml(task) {
  const lateStartBadge = task.is_late_start
    ? ' <span class="badge badge-warning">Поздний старт</span>'
    : "";
  let startDeviationRow = "";
  if (task.start_delay_seconds != null) {
    startDeviationRow = `<dt>Отклонение старта</dt><dd>${formatScheduleDelta(task.start_delay_seconds)}${lateStartBadge} <span class="list-item-meta">(поздний старт — с допуском 5 мин)</span></dd>`;
  }
  let endDeviationRow = "";
  if (task.end_delay_seconds != null) {
    const endSec = Number(task.end_delay_seconds);
    const endBadge =
      endSec > 0
        ? ' <span class="badge badge-warning">Позже плана</span>'
        : endSec < 0
          ? ' <span class="badge">Раньше плана</span>'
          : "";
    endDeviationRow = `<dt>Отклонение окончания</dt><dd>${formatScheduleDelta(task.end_delay_seconds)}${endBadge}</dd>`;
  }
  return `
        <dt>План</dt><dd>${formatDateTime(task.start_time)} — ${formatDateTime(task.end_time)}</dd>
        <dt>Факт</dt><dd>${formatDateTime(task.actual_start_time)} — ${formatDateTime(task.actual_end_time)}</dd>
        ${startDeviationRow}
        ${endDeviationRow}`;
}

function renderTaskInlineBadges(task) {
  const statusBadge =
    task.status === "overdue"
      ? `<span class="badge badge-danger">${enumLabel("taskStatus", task.status)}</span>`
      : `<span class="badge">${enumLabel("taskStatus", task.status)}</span>`;
  const lateStartBadge = task.is_late_start
    ? '<span class="badge badge-warning">Поздний старт</span>'
    : "";
  return `${statusBadge}
    <span class="badge">${enumLabel("taskPriority", task.priority)}</span>
    ${lateStartBadge}`;
}

function computeTaskStatusStats(tasks) {
  const list = Array.isArray(tasks) ? tasks : [];
  const total = list.length;
  let done = 0;
  for (const t of list) {
    if (String(t.status || "").toLowerCase() === "done") done += 1;
  }
  return {
    total,
    done,
    percentDone: total ? Math.round((done / total) * 100) : 0,
  };
}

function progressStatRow(label, count, total, percent, fillClass = "") {
  const width = Math.min(100, Math.max(0, percent));
  const fillCls = fillClass ? ` progress-bar-fill ${fillClass}` : " progress-bar-fill";
  return `<div class="progress-stat-row">
    <span class="progress-stat-label">${escapeHtml(label)}</span>
    <div class="progress-bar"><div class="${fillCls.trim()}" style="width:${width}%"></div></div>
    <span class="progress-stat-value">${count} / ${total} (${percent}%)</span>
  </div>`;
}

function buildTaskProgressStatsHtml(stats) {
  if (!stats.total) {
    return '<p class="list-item-meta">Нет задач для статистики.</p>';
  }
  return progressStatRow(
    "Выполнено",
    stats.done,
    stats.total,
    stats.percentDone,
    "progress-bar-fill-done"
  );
}

function peakConcurrentQuantity(allocations) {
  const events = [];
  for (const a of allocations) {
    const qty = Number(a.quantity_used) || 0;
    if (qty <= 0) continue;
    const start = new Date(a.date_start).getTime();
    const end = new Date(a.date_end).getTime();
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) continue;
    events.push({ t: start, delta: qty });
    events.push({ t: end, delta: -qty });
  }
  if (!events.length) return 0;
  events.sort((a, b) => {
    if (a.t !== b.t) return a.t - b.t;
    return a.delta - b.delta;
  });
  let current = 0;
  let peak = 0;
  for (const e of events) {
    current += e.delta;
    if (current > peak) peak = current;
  }
  return peak;
}

function computeResourceUtilization(eventResources, _event) {
  const rows = [];
  for (const r of eventResources || []) {
    const quantity = Number(r.quantity) || 0;
    if (quantity <= 0) continue;
    const allocations = (r.allocations || []).filter(
      (a) => String(a.status || "").toLowerCase() !== "cancelled"
    );
    const peakUsed = peakConcurrentQuantity(allocations);
    const rawPercent = Math.round((peakUsed / quantity) * 100);
    const loadPercent = Math.min(100, rawPercent);
    rows.push({
      id: r.id,
      name: r.name,
      quantity,
      peakUsed,
      loadPercent,
      rawPercent,
      allocationCount: allocations.length,
    });
  }
  rows.sort((a, b) => b.rawPercent - a.rawPercent || a.name.localeCompare(b.name));
  return rows;
}

function buildResourceUtilizationHtml(rows, eventResources) {
  const resources = eventResources || [];
  if (!resources.length) {
    return '<p class="list-item-meta">Ресурсы не добавлены.</p>';
  }
  if (!rows.length) {
    return '<p class="list-item-meta">Нет ресурсов с указанной ёмкостью для расчёта загрузки.</p>';
  }
  let totalAlloc = 0;
  for (const r of resources) {
    for (const a of r.allocations || []) {
      if (String(a.status || "").toLowerCase() !== "cancelled") totalAlloc += 1;
    }
  }
  const avgLoad =
    rows.length > 0
      ? Math.round(rows.reduce((s, r) => s + r.rawPercent, 0) / rows.length)
      : 0;
  const summary = `<p class="progress-stat-summary">${resources.length} ресурсов, ${totalAlloc} назначений · средняя пиковая загрузка ${avgLoad}%</p>`;
  const bars = rows
    .map((row) => {
      const overCapacity = row.peakUsed > row.quantity;
      const fillClass = overCapacity
        ? "progress-bar-fill progress-bar-fill-warn"
        : row.loadPercent >= 80
          ? "progress-bar-fill progress-bar-fill-warn"
          : "progress-bar-fill";
      const width = Math.min(100, Math.max(0, row.loadPercent));
      const pctLabel = overCapacity ? `${row.rawPercent}%` : `${row.loadPercent}%`;
      return `<div class="progress-stat-row">
        <span class="progress-stat-label" title="${escapeHtml(row.name)}">${escapeHtml(row.name)}</span>
        <div class="progress-bar"><div class="${fillClass}" style="width:${width}%"></div></div>
        <span class="progress-stat-value">${row.peakUsed} / ${row.quantity} (${pctLabel})</span>
      </div>`;
    })
    .join("");
  return summary + bars;
}

function setFormError(form, message = "") {
  if (!form) return;
  let node = form.querySelector(".form-error");
  if (!node) {
    node = document.createElement("p");
    node.className = "form-error";
    form.appendChild(node);
  }
  node.textContent = message;
  node.classList.toggle("hidden", !message);
}

function populateUsersAddEventOptions(selectedEventId = null) {
  if (!el.usersAddEventSelect) return;
  const options = ['<option value="">Выберите мероприятие для добавления</option>'];
  state.events.forEach((event) => {
    const selected = selectedEventId != null && Number(selectedEventId) === event.id ? "selected" : "";
    options.push(`<option value="${event.id}" ${selected}>${escapeHtml(formatEventLabel(event))}</option>`);
  });
  el.usersAddEventSelect.innerHTML = options.join("");
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
    syncUsersFilterInputs();
    void loadUsersPage();
  }
  if (screenId === "profile-cabinet") {
    void loadProfileCabinet();
  }
  if (screenId === "tasks") {
    populateTasksFilterEventSelect();
    syncTasksFilterFormFromState();
    void loadTasksPage();
  }
  if (screenId === "inbox") {
    void loadInbox();
  }
  if (screenId === "ai") {
    if (state.aiDraft) renderAiDraft();
    else clearAiDraft();
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
  if (!can) {
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
        void loadTaskCreateInviteOptions(selectedId);
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
    allocBtn.textContent = "+ Создать назначение";
    allocBtn.addEventListener("click", () => {
      const panel = document.getElementById("allocation-create-panel");
      if (panel) {
        panel.classList.toggle("hidden");
        if (!panel.classList.contains("hidden")) {
          populateAllocationEventOptions(state.allocationPreset.eventId);
          void populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
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
  el.tasksCount.textContent = String(state.taskMetrics.total ?? 0);
  el.resourcesCount.textContent = String(state.resources.length);
  el.overdueCount.textContent = String(state.taskMetrics.overdue ?? 0);
}

function populateTasksFilterEventSelect() {
  const sel = document.getElementById("tasks-filter-event");
  if (!sel) return;
  const cur = state.tasksFilters.eventId || "";
  const opts = ['<option value="">Все мероприятия</option>'];
  state.events.forEach((event) => {
    const s = String(cur) === String(event.id) ? "selected" : "";
    opts.push(`<option value="${event.id}" ${s}>${escapeHtml(formatEventLabel(event))}</option>`);
  });
  sel.innerHTML = opts.join("");
}

function syncTasksFilterFormFromState() {
  const ev = document.getElementById("tasks-filter-event");
  if (ev) ev.value = state.tasksFilters.eventId || "";
  const st = document.getElementById("tasks-filter-status");
  if (st) st.value = state.tasksFilters.status || "";
  const pr = document.getElementById("tasks-filter-priority");
  if (pr) pr.value = state.tasksFilters.priority || "";
  const qn = document.getElementById("tasks-filter-q");
  if (qn) qn.value = state.tasksFilters.q || "";
  const ps = document.getElementById("tasks-page-size");
  if (ps) ps.value = String(state.tasksLimit);
}

function buildTasksListQueryString() {
  const p = new URLSearchParams();
  p.set("skip", String(state.tasksSkip));
  p.set("limit", String(state.tasksLimit));
  const f = state.tasksFilters;
  if (f.eventId) p.set("event_id", String(f.eventId));
  if (f.status) p.set("status", String(f.status));
  if (f.priority) p.set("priority", String(f.priority));
  if (f.q && String(f.q).trim()) p.set("q", String(f.q).trim());
  return p.toString();
}

function updateTasksPageControls() {
  const info = document.getElementById("tasks-page-info");
  if (info) {
    const pages = Math.max(1, Math.ceil((state.tasksTotal || 0) / (state.tasksLimit || 1)) || 1);
    const page = Math.min(pages, Math.floor(state.tasksSkip / (state.tasksLimit || 1)) + 1);
    info.textContent = `Страница ${page} из ${pages} (всего задач: ${state.tasksTotal})`;
  }
  const prev = document.getElementById("tasks-page-prev");
  const next = document.getElementById("tasks-page-next");
  if (prev) prev.disabled = state.tasksSkip <= 0;
  if (next) next.disabled = state.tasksSkip + state.tasksLimit >= state.tasksTotal;
}

async function loadTasksPage(options = {}) {
  const { resetPage = false } = options;
  if (!state.token || !state.profileId) return;
  if (resetPage) state.tasksSkip = 0;
  notify("Загрузка задач…");
  try {
    const qs = buildTasksListQueryString();
    const data = await apiRequest(`${API.tasks}?${qs}`);
    const items = Array.isArray(data?.items) ? data.items : [];
    const total = typeof data?.total === "number" ? data.total : items.length;
    state.tasksPage = items;
    state.tasksTotal = total;
    state.assigneeNames = {};
    const assigneeIds = [
      ...new Set(
        items.flatMap((t) => {
          return (t.assignees || []).map((a) => a.user_id);
        })
      )
    ].filter((id) => id != null && id !== "");
    if (assigneeIds.length) {
      const params = new URLSearchParams();
      assigneeIds.forEach((id) => params.append("ids", String(id)));
      try {
        const profiles = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
        (Array.isArray(profiles) ? profiles : []).forEach((p) => {
          const label = `${p.first_name || ""} ${p.last_name || ""}`.trim();
          if (label) state.assigneeNames[p.id] = label;
        });
      } catch {
        /* подписи исполнителей необязательны */
      }
    }
    renderTasks();
    updateTasksPageControls();
    notify("Готово");
  } catch (error) {
    state.tasksPage = [];
    state.tasksTotal = 0;
    renderTasks();
    updateTasksPageControls();
    notify(error.message, true);
  }
}

function syncInboxTabUi() {
  document.querySelectorAll(".inbox-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.inboxTab === state.inboxTab);
  });
  const hint = document.getElementById("inbox-hint");
  if (hint) {
    hint.textContent =
      state.inboxTab === "incoming"
        ? "Мероприятия и задачи, в которые вас пригласили и ожидают ответа."
        : "Приглашения, которые вы отправили и ожидают ответа.";
  }
}

async function resolveProfileNames(profileIds) {
  const ids = [...new Set(profileIds.filter((id) => id != null && id !== ""))];
  if (!ids.length) return {};
  const params = new URLSearchParams();
  ids.forEach((id) => params.append("ids", String(id)));
  try {
    const profiles = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
    return Object.fromEntries(
      (Array.isArray(profiles) ? profiles : []).map((p) => [
        Number(p.id),
        `${p.first_name || ""} ${p.last_name || ""}`.trim() || `Пользователь #${p.id}`
      ])
    );
  } catch {
    return {};
  }
}

function formatInvitationDescription(text) {
  if (!text || !String(text).trim()) return "";
  const s = String(text).trim();
  const short = s.length > 160 ? `${s.slice(0, 160)}…` : s;
  return `<p class="list-item-meta">${escapeHtml(short)}</p>`;
}

async function loadInbox() {
  const root = document.getElementById("inbox-root");
  if (!root) return;
  syncInboxTabUi();
  if (!state.token || !state.profileId) {
    root.innerHTML = '<p class="list-item-meta">Войдите в систему.</p>';
    return;
  }
  root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';
  if (state.inboxTab === "outgoing") {
    await loadInboxOutgoing(root);
  } else {
    await loadInboxIncoming(root);
  }
}

async function loadInboxIncoming(root) {
  let eventInv = [];
  let taskInv = [];
  try {
    eventInv = await apiRequest(`${API.events}invitations/me`);
  } catch {
    eventInv = [];
  }
  try {
    taskInv = await apiRequest(`${API.tasks}invitations/me`);
  } catch {
    taskInv = [];
  }
  if (!Array.isArray(eventInv)) eventInv = [];
  if (!Array.isArray(taskInv)) taskInv = [];
  if (!eventInv.length && !taskInv.length) {
    root.innerHTML = '<p class="list-item-meta">Нет ожидающих приглашений.</p>';
    return;
  }
  const taskInviterNames = await resolveProfileNames(
    taskInv.map((r) => r.invited_by).filter((id) => id != null && id !== "")
  );
  const blocks = [];
  if (eventInv.length) {
    blocks.push("<h3>Мероприятия</h3>");
    eventInv.forEach((row) => {
      const eid = Number(row.event_id);
      const when =
        row.start_time && row.end_time
          ? `${formatDateTime(row.start_time)} — ${formatDateTime(row.end_time)}`
          : "";
      const loc = row.location ? escapeHtml(row.location) : "";
      blocks.push(`
        <article class="list-item">
          <p class="list-item-title">${escapeHtml(row.title || `Мероприятие #${eid}`)}</p>
          <p class="list-item-meta">Роль: ${enumLabel("participantRole", row.role)}</p>
          ${when ? `<p class="list-item-meta">${when}</p>` : ""}
          ${loc ? `<p class="list-item-meta">Локация: ${loc}</p>` : ""}
          ${formatInvitationDescription(row.description)}
          <div class="detail-actions" style="margin-top:8px">
            <button type="button" class="btn btn-primary btn-inline" data-inbox-accept-event="${eid}">Принять</button>
            <button type="button" class="btn btn-muted btn-inline" data-inbox-decline-event="${eid}">Отклонить</button>
            <button type="button" class="btn btn-muted btn-inline" data-inbox-preview-event="${eid}">Подробнее</button>
          </div>
        </article>`);
    });
  }
  if (taskInv.length) {
    blocks.push("<h3 style=\"margin-top:16px\">Задачи</h3>");
    taskInv.forEach((row) => {
      const tid = Number(row.task_id);
      const eid = Number(row.event_id);
      const inviterId = row.invited_by != null ? Number(row.invited_by) : null;
      const inviterLine =
        inviterId != null && !Number.isNaN(inviterId)
          ? `<p class="list-item-meta">Пригласил: ${userEntityLinkFromName(inviterId, taskInviterNames[inviterId])}</p>`
          : "";
      blocks.push(`
        <article class="list-item">
          <p class="list-item-title">${escapeHtml(row.title || `Задача #${tid}`)}</p>
          <p class="list-item-meta">Мероприятие: ${eventEntityLink(eid, row.event_title)}</p>
          ${inviterLine}
          <div class="detail-actions" style="margin-top:8px">
            <button type="button" class="btn btn-primary btn-inline" data-inbox-accept-task="${tid}">Принять</button>
            <button type="button" class="btn btn-muted btn-inline" data-inbox-decline-task="${tid}">Отклонить</button>
            <button type="button" class="btn btn-muted btn-inline" data-inbox-preview-task="${tid}">Подробнее</button>
          </div>
        </article>`);
    });
  }
  root.innerHTML = blocks.join("");
}

async function loadInboxOutgoing(root) {
  let eventSent = [];
  let taskSent = [];
  try {
    eventSent = await apiRequest(`${API.events}invitations/sent/me`);
  } catch {
    eventSent = [];
  }
  try {
    taskSent = await apiRequest(`${API.tasks}invitations/sent/me`);
  } catch {
    taskSent = [];
  }
  if (!Array.isArray(eventSent)) eventSent = [];
  if (!Array.isArray(taskSent)) taskSent = [];
  const names = await resolveProfileNames([
    ...eventSent.map((r) => r.invitee_user_id),
    ...taskSent.map((r) => r.invitee_user_id)
  ]);
  if (!eventSent.length && !taskSent.length) {
    root.innerHTML = '<p class="list-item-meta">Нет отправленных приглашений в ожидании ответа.</p>';
    return;
  }
  const blocks = [];
  if (eventSent.length) {
    blocks.push("<h3>Мероприятия</h3>");
    eventSent.forEach((row) => {
      const uid = Number(row.invitee_user_id);
      const eid = Number(row.event_id);
      blocks.push(`
        <article class="list-item">
          <p class="list-item-title">${eventEntityLink(eid, row.event_title)}</p>
          <p class="list-item-meta">Кому: ${userEntityLinkFromName(uid, names[uid])} | Роль: ${enumLabel("participantRole", row.role)}</p>
          <p class="list-item-meta">Статус: ожидает ответа</p>
          <div class="detail-actions">
            <button type="button" class="btn btn-muted btn-inline" data-inbox-cancel-event-invitation="${eid}" data-inbox-cancel-event-user="${uid}">Отменить</button>
          </div>
        </article>`);
    });
  }
  if (taskSent.length) {
    blocks.push("<h3 style=\"margin-top:16px\">Задачи</h3>");
    taskSent.forEach((row) => {
      const uid = Number(row.invitee_user_id);
      const tid = Number(row.task_id);
      const eid = Number(row.event_id);
      blocks.push(`
        <article class="list-item">
          <p class="list-item-title">${escapeHtml(row.title || `Задача #${tid}`)}</p>
          <p class="list-item-meta">Кому: ${userEntityLinkFromName(uid, names[uid])} | Мероприятие: ${eventEntityLink(eid, row.event_title)}</p>
          <p class="list-item-meta">Статус: ожидает ответа</p>
          <div class="detail-actions">
            <button type="button" class="btn btn-muted btn-inline" data-inbox-cancel-task-invitation="${tid}" data-inbox-cancel-task-user="${uid}">Отменить</button>
          </div>
        </article>`);
    });
  }
  root.innerHTML = blocks.join("");
}

async function openEventInvitationPreview(eventId, opts = {}) {
  if (opts.fromInbox) {
    state.detailBackTarget = { kind: "inbox" };
  }
  state.detailView = "event-invitation";
  state.detailEventId = eventId;
  hideAllScreens();
  document.getElementById("event-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Приглашение в мероприятие";
  updateTopbarActions();

  const root = document.getElementById("event-detail-root");
  root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';

  try {
    const event = await apiRequest(`${API.events}${eventId}/invitation-preview`);
    el.screenTitle.textContent = event.title || `Мероприятие #${eventId}`;
    root.innerHTML = `
      <div class="panel">
        <p class="list-item-meta">Вы приглашены участвовать в мероприятии. Ознакомьтесь с деталями и примите решение.</p>
        <dl class="detail-dl">
          <dt>Название</dt><dd>${escapeHtml(event.title)}</dd>
          <dt>Статус</dt><dd>${enumLabel("eventStatus", event.status)}</dd>
          <dt>Начало</dt><dd>${formatDateTime(event.start_time)}</dd>
          <dt>Окончание</dt><dd>${formatDateTime(event.end_time)}</dd>
          <dt>Локация</dt><dd>${escapeHtml(event.location || "—")}</dd>
          <dt>Бюджет</dt><dd>${event.budget ?? 0}</dd>
        </dl>
        <p class="list-item-meta" style="margin-top:12px">${escapeHtml(event.description || "Без описания")}</p>
        <div class="detail-actions" style="margin-top:16px">
          <button type="button" class="btn btn-primary btn-inline" data-inbox-accept-event="${eventId}">Принять</button>
          <button type="button" class="btn btn-muted btn-inline" data-inbox-decline-event="${eventId}">Отклонить</button>
        </div>
      </div>`;
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

async function leaveEventAsParticipant(eventId) {
  if (!confirm("Покинуть это мероприятие? Вы потеряете доступ к его задачам и ресурсам.")) return;
  try {
    await apiRequest(`${API.events}${eventId}/participants/me/leave`, { method: "POST" });
    notify("Вы покинули мероприятие");
    await closeDetailView();
    await refreshData();
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

async function acceptEventInvitation(eventId) {
  await apiRequest(`${API.events}${eventId}/participants/me/accept`, { method: "POST" });
  notify("Вы приняли приглашение в мероприятие");
  if (state.detailView === "event-invitation") {
    state.detailBackTarget = null;
    state.detailView = null;
    state.detailEventId = null;
    await refreshData();
    await openEventDetail(eventId);
    return;
  }
  await refreshData();
  if (state.currentScreen === "inbox") await loadInbox();
}

async function cancelSentEventInvitation(eventId, inviteeUserId) {
  if (!confirm("Отменить отправленное приглашение в мероприятие?")) return;
  try {
    await apiRequest(`${API.events}${eventId}/invitations/${inviteeUserId}`, { method: "DELETE" });
    notify("Приглашение отменено");
    await loadInbox();
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

async function cancelSentTaskInvitation(taskId, inviteeUserId) {
  if (!confirm("Отменить отправленное приглашение на задачу?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}/assignees/${inviteeUserId}`, { method: "DELETE" });
    notify("Приглашение отменено");
    await loadInbox();
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

async function declineEventInvitation(eventId) {
  await apiRequest(`${API.events}${eventId}/participants/me/decline`, { method: "POST" });
  notify("Приглашение в мероприятие отклонено");
  if (state.detailView === "event-invitation") {
    await closeDetailView();
    return;
  }
  if (state.currentScreen === "inbox") await loadInbox();
}

function isTaskAccessDeniedError(error) {
  const msg = String(error?.message || "").toLowerCase();
  return (
    msg.includes("403") ||
    msg.includes("not enough permissions") ||
    msg.includes("недостаточно прав")
  );
}

async function openTaskInvitationPreview(taskId, opts = {}) {
  if (opts.fromInbox) {
    state.detailBackTarget = { kind: "inbox" };
  }
  state.detailView = "task-invitation";
  state.detailEventId = null;
  hideAllScreens();
  document.getElementById("task-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Приглашение на задачу";
  updateTopbarActions();

  const root = document.getElementById("task-detail-root");
  root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';

  try {
    const task = await apiRequest(`${API.tasks}${taskId}/invitation-preview`);
    el.screenTitle.textContent = task.title || `Задача #${taskId}`;
    root.innerHTML = `
      <div class="panel">
        <p class="list-item-meta">Вас пригласили исполнить задачу. Ознакомьтесь с деталями и примите решение.</p>
        <p class="list-item-meta">Мероприятие: ${eventEntityLink(task.event_id, task.event_title)}</p>
        <dl class="detail-dl">
          <dt>Название</dt><dd>${escapeHtml(task.title)}</dd>
          <dt>Статус</dt><dd>${enumLabel("taskStatus", task.status)}</dd>
          <dt>Приоритет</dt><dd>${enumLabel("taskPriority", task.priority)}</dd>
          <dt>Начало (план)</dt><dd>${formatDateTime(task.start_time)}</dd>
          <dt>Окончание (план)</dt><dd>${formatDateTime(task.end_time)}</dd>
          <dt>Дедлайн</dt><dd>${formatDateTime(task.deadline)}</dd>
        </dl>
        <p class="list-item-meta" style="margin-top:12px">${escapeHtml(task.description || "Без описания")}</p>
        <div class="detail-actions" style="margin-top:16px">
          <button type="button" class="btn btn-primary btn-inline" data-inbox-accept-task="${taskId}">Принять</button>
          <button type="button" class="btn btn-muted btn-inline" data-inbox-decline-task="${taskId}">Отклонить</button>
        </div>
      </div>`;
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

async function acceptTaskInvitation(taskId) {
  if (!state.profileId) return;
  await apiRequest(`${API.tasks}${taskId}/assignees/${state.profileId}/accept`, { method: "POST" });
  notify("Вы приняли приглашение на задачу");
  if (state.detailView === "task-invitation") {
    state.detailBackTarget = null;
    state.detailView = null;
    await refreshData();
    await openTaskDetail(taskId);
    return;
  }
  await refreshData();
  if (state.currentScreen === "inbox") await loadInbox();
}

async function declineTaskInvitation(taskId) {
  if (!state.profileId) return;
  await apiRequest(`${API.tasks}${taskId}/assignees/${state.profileId}/decline`, { method: "POST" });
  notify("Приглашение на задачу отклонено");
  if (state.detailView === "task-invitation") {
    await closeDetailView();
    return;
  }
  if (state.currentScreen === "inbox") await loadInbox();
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
        ${escapeHtml(event.title)}
      </button>
      <span class="badge">${enumLabel("eventStatus", event.status)}</span>
    </p>
    <p class="list-item-meta">Сроки: ${new Date(event.start_time).toLocaleString()} - ${new Date(event.end_time).toLocaleString()}</p>
    <p class="list-item-meta">Бюджет: ${event.budget ?? 0}</p>
  `);
}

function renderTasks() {
  renderList(el.tasksList, state.tasksPage, (task) => {
    const eventTitle = escapeHtml(getEventTitle(task.event_id));
    const rows = Array.isArray(task.assignees) ? task.assignees : [];
    let assigneeLabel;
    if (rows.length) {
      assigneeLabel = rows
        .map((a) => {
          const name = state.assigneeNames[a.user_id] || `#${a.user_id}`;
          return `${escapeHtml(name)} (${taskAssigneeStatusLabel(a.status)})`;
        })
        .join(", ");
    } else {
      assigneeLabel = "не назначен";
    }
    return `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="task" data-id="${task.id}">
        ${escapeHtml(task.title)}
      </button>
      ${renderTaskInlineBadges(task)}
    </p>
    <p class="list-item-meta">Мероприятие: ${eventTitle} | Исполнитель: ${assigneeLabel}</p>
    <p class="list-item-meta">План: ${formatDateTime(task.start_time)} — ${formatDateTime(task.end_time)}</p>
    <p class="list-item-meta">Факт: ${formatDateTime(task.actual_start_time)} — ${formatDateTime(task.actual_end_time)}</p>
    <p class="list-item-meta">Дедлайн: ${formatDateTime(task.deadline)}</p>
  `;
  });
}

function renderResources() {
  const eventBtn = (resource) => {
    const title = escapeHtml(getEventTitle(resource.event_id));
    return `<button type="button" class="entity-link" data-entity-link="event" data-id="${resource.event_id}">${title}</button>`;
  };
  renderList(el.resourcesList, state.resources, (resource) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="resource" data-id="${resource.id}">
        ${escapeHtml(resource.name)}
      </button>
      <span class="badge">${enumLabel("resourceType", resource.type)}</span>
    </p>
    <p class="list-item-meta">Мероприятие: ${eventBtn(resource)} | Кол-во: ${resource.quantity}</p>
    <p class="list-item-meta">Стоимость/час: ${resource.cost_per_hour ?? "не указано"}</p>
  `);
}

/** Роли участника мероприятия в селекте добавления: только совместимые с системной ролью пользователя (см. event-service create_participant). */
function eventParticipantRoleOptionsForSystemRole(systemRole) {
  const r = String(systemRole || "viewer").toLowerCase();
  let allowed;
  if (r === "viewer") {
    allowed = ["viewer"];
  } else if (r === "executor") {
    allowed = ["executor", "viewer"];
  } else if (r === "organizer") {
    allowed = ["organizer", "executor", "viewer"];
  } else if (r === "admin") {
    allowed = ["organizer", "executor", "viewer"];
  } else {
    allowed = ["viewer"];
  }
  return allowed
    .map(
      (role, i) =>
        `<option value="${role}"${i === 0 ? " selected" : ""}>${enumLabel("participantRole", role)}</option>`
    )
    .join("");
}

function renderUsers() {
  const inParticipantMode = state.participantsModeEventId != null;
  const canManageParticipants = canCreate();
  const controls = document.getElementById("users-add-controls");
  if (controls) controls.classList.toggle("hidden", !canManageParticipants);
  el.usersModeHint.classList.toggle("hidden", inParticipantMode);
  if (!inParticipantMode) {
    el.usersModeHint.textContent = "Список пользователей";
  }
  if (el.usersAddEventSelect) {
    el.usersAddEventSelect.disabled = false;
  }

  renderList(el.usersList, state.usersList, (user) => `
    <p class="list-item-title">
      <button type="button" class="entity-link" data-entity-link="user" data-id="${user.id}">
        ${escapeHtml(user.first_name)} ${escapeHtml(user.last_name)}
      </button>
    </p>
    <p class="list-item-meta">Роль: ${enumLabel("participantRole", user.role || "viewer")}</p>
    <p class="list-item-meta">Специализация: ${escapeHtml(user.speciality || "не указана")}</p>
    ${state.role === "admin" ? `<p class="list-item-meta">Email: ${escapeHtml(user.email || "—")} | Телефон: ${escapeHtml(user.phone || "—")}</p>` : ""}
    ${
      canManageParticipants
        ? `<div class="detail-actions">
            <select data-user-role-select="${user.id}">
              ${eventParticipantRoleOptionsForSystemRole(user.role)}
            </select>
            <button class="btn btn-inline" type="button" data-add-participant-user="${user.id}">Добавить в мероприятие</button>
          </div>`
        : ""
    }
  `);
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

async function populateAllocationTaskOptions(eventId, selectedTaskId = null) {
  if (!el.allocationTaskSelect) return;
  el.allocationTaskSelect.innerHTML = '<option value="">Без задачи</option>';
  if (!eventId) return;
  try {
    const tasks = await apiRequest(`${API.tasks}event/${eventId}`);
    (Array.isArray(tasks) ? tasks : []).forEach((task) => {
      const selected = selectedTaskId != null && Number(selectedTaskId) === task.id ? "selected" : "";
      const opt = document.createElement("option");
      opt.value = String(task.id);
      opt.textContent = task.title;
      if (selected) opt.selected = true;
      el.allocationTaskSelect.appendChild(opt);
    });
  } catch {
    /* ignore */
  }
}

function populateAllocationResourceOptions(eventId, selectedResourceId = null) {
  if (!el.allocationResourceSelect) return;
  const resources = eventId ? getResourcesByEventId(eventId) : [];
  const options = ['<option value="">Выберите ресурс</option>'];
  resources.forEach((resource) => {
    const selected = selectedResourceId != null && Number(selectedResourceId) === resource.id ? "selected" : "";
    options.push(
      `<option value="${resource.id}" ${selected}>${escapeHtml(resource.name)} (${enumLabel("resourceType", resource.type)})</option>`
    );
  });
  el.allocationResourceSelect.innerHTML = options.join("");
}

function formatEventLabel(event) {
  return `${event.title} | ${new Date(event.start_time).toLocaleString()} - ${new Date(event.end_time).toLocaleString()}`;
}

function getEventTitle(eventId) {
  if (eventId == null || eventId === "") return "Мероприятие";
  const id = Number(eventId);
  const ev = state.events.find((e) => e.id === id);
  if (ev && ev.title) return String(ev.title);
  return "Мероприятие";
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

async function loadTaskCreateInviteOptions(eventId) {
  if (!el.taskCreateInviteSelect) return;
  el.taskCreateInviteSelect.innerHTML = '<option value="">Не приглашать</option>';
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
      el.taskCreateInviteSelect.appendChild(option);
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
  await loadTaskCreateInviteOptions(eventId);
}

async function openUsersForEventParticipants(eventId) {
  state.participantsModeEventId = eventId;
  setScreen("users");
  await loadUsers();
}

async function openAllocationCreatePanel(preset = {}) {
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
  await populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
  populateAllocationResourceOptions(state.allocationPreset.eventId, state.allocationPreset.resourceId);
  const allocForm = document.getElementById("allocation-form");
  if (allocForm && state.allocationPreset.taskId) {
    try {
      const task = await apiRequest(`${API.tasks}${state.allocationPreset.taskId}`);
      if (task) {
        allocForm.elements.date_start.value = toDatetimeLocalValue(task.start_time);
        allocForm.elements.date_end.value = toDatetimeLocalValue(task.end_time);
      }
    } catch {
      /* ignore */
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
      notify("Создайте профиль для доступа к функциям", true);
      return;
    }
  }
  notify("Загрузка данных...");
  const [eventsResult, metricsResult, resourcesResult] = await Promise.allSettled([
    apiRequest(API.events),
    apiRequest(`${API.tasks}metrics`),
    apiRequest(API.resources)
  ]);

  const errors = [];

  if (eventsResult.status === "fulfilled") {
    state.events = Array.isArray(eventsResult.value) ? eventsResult.value : [];
  } else {
    state.events = [];
    errors.push(`мероприятия: ${eventsResult.reason?.message || "неизвестная ошибка"}`);
  }

  if (metricsResult.status === "fulfilled") {
    const m = metricsResult.value;
    state.taskMetrics = {
      total: typeof m?.total === "number" ? m.total : 0,
      overdue: typeof m?.overdue === "number" ? m.overdue : 0
    };
  } else {
    state.taskMetrics = { total: 0, overdue: 0 };
    errors.push(`задачи (метрики): ${metricsResult.reason?.message || "неизвестная ошибка"}`);
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
  void populateAllocationTaskOptions(state.allocationPreset.eventId, state.allocationPreset.taskId);
  populateAllocationResourceOptions(state.allocationPreset.eventId, state.allocationPreset.resourceId);
  if (state.taskCreatePresetEventId != null) {
    await loadTaskCreateInviteOptions(state.taskCreatePresetEventId);
  }

  if (state.currentScreen === "tasks") {
    populateTasksFilterEventSelect();
    syncTasksFilterFormFromState();
    await loadTasksPage();
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

function buildUsersListQueryString() {
  const p = new URLSearchParams();
  p.set("skip", String(state.usersSkip));
  p.set("limit", String(state.usersLimit));
  const s = state.usersSearch;
  if (s.id) p.set("id", String(s.id));
  if (s.q) p.set("q", String(s.q).trim());
  if (s.speciality) p.set("speciality", String(s.speciality).trim());
  if (s.role) p.set("role", String(s.role));
  return p.toString();
}

function updateUsersPageControls() {
  const info = document.getElementById("users-page-info");
  if (info) {
    const pages = Math.max(1, Math.ceil((state.usersTotal || 0) / (state.usersLimit || 1)) || 1);
    const page = Math.min(pages, Math.floor(state.usersSkip / (state.usersLimit || 1)) + 1);
    info.textContent = `Страница ${page} из ${pages} (всего: ${state.usersTotal})`;
  }
  const prev = document.getElementById("users-page-prev");
  const next = document.getElementById("users-page-next");
  if (prev) prev.disabled = state.usersSkip <= 0;
  if (next) next.disabled = state.usersSkip + state.usersLimit >= state.usersTotal;
}

function syncUsersFilterInputs() {
  const idEl = document.getElementById("users-search-id");
  if (idEl) idEl.value = state.usersSearch.id || "";
  const qEl = document.getElementById("users-search-q");
  if (qEl) qEl.value = state.usersSearch.q || "";
  const spEl = document.getElementById("users-search-speciality");
  if (spEl) spEl.value = state.usersSearch.speciality || "";
  const roleEl = document.getElementById("users-filter-role");
  if (roleEl) roleEl.value = state.usersSearch.role || "";
  const ps = document.getElementById("users-page-size");
  if (ps) ps.value = String(state.usersLimit);
}

async function loadUsersPage(options = {}) {
  const { resetPage = false } = options;
  if (!state.token) return;
  if (resetPage) state.usersSkip = 0;
  const qs = buildUsersListQueryString();
  try {
    const data =
      state.role === "admin"
        ? await apiRequest(`${API.users}/?${qs}`)
        : await apiRequest(`${API.users}/public/page?${qs}`);
    const items = Array.isArray(data?.items) ? data.items : [];
    const total = typeof data?.total === "number" ? data.total : items.length;
    state.usersList = items;
    state.usersTotal = total;
    populateUsersAddEventOptions(state.participantsModeEventId);
    if (el.usersAddEventSelect) {
      el.usersAddEventSelect.value = state.participantsModeEventId ? String(state.participantsModeEventId) : "";
    }
    updateUsersPageControls();
    renderUsers();
  } catch (error) {
    notify(`Ошибка загрузки пользователей: ${error.message}`, true);
  }
}

async function loadUsers() {
  await loadUsersPage();
}

async function closeDetailView() {
  if (state.detailBackTarget?.kind === "inbox") {
    state.detailBackTarget = null;
    state.detailView = null;
    state.detailEventId = null;
    hideAllScreens();
    document.getElementById("inbox-screen").classList.remove("hidden");
    el.screenTitle.textContent = screenName("inbox");
    updateTopbarActions();
    await loadInbox();
    return;
  }
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
    let myMembership = null;
    try {
      myMembership = await apiRequest(`${API.events}${eventId}/participants/me`);
    } catch {
      myMembership = null;
    }
    if (myMembership && String(myMembership.membership_status || "").toLowerCase() === "pending") {
      await openEventInvitationPreview(eventId);
      return;
    }

    const event = await apiRequest(`${API.events}${eventId}`);
    const tasks = await apiRequest(`${API.tasks}event/${eventId}`);
    const participants = await apiRequest(`${API.events}${eventId}/participants`);
    let participantProfiles = {};
    if (Array.isArray(participants) && participants.length) {
      const params = new URLSearchParams();
      Array.from(new Set(participants.map((p) => p.user_id))).forEach((id) => params.append("ids", String(id)));
      try {
        const profiles = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
        participantProfiles = Object.fromEntries((profiles || []).map((p) => [p.id, p]));
      } catch (err) {
        participantProfiles = {};
      }
    }
    const eventResources = state.resources.filter((resource) => resource.event_id === eventId);
    const depResults = await Promise.allSettled(
      tasks.map((t) => apiRequest(`${API.tasks}${t.id}/dependency-ids`))
    );
    const depMap = {};
    tasks.forEach((t, i) => {
      const r = depResults[i];
      depMap[t.id] = r.status === "fulfilled" && r.value?.depends_on ? r.value.depends_on : [];
    });

    let ownerProfile = event.owner_id != null ? participantProfiles[event.owner_id] ?? null : null;
    if (!ownerProfile && event.owner_id != null) {
      try {
        const owners = await apiRequest(`${API.users}/public/by-ids?ids=${event.owner_id}`);
        ownerProfile = Array.isArray(owners) && owners[0] ? owners[0] : null;
      } catch {
        ownerProfile = null;
      }
    }

    el.screenTitle.textContent = event.title || `Мероприятие #${eventId}`;
    renderEventDetailCard(
      event,
      tasks,
      depMap,
      participants,
      participantProfiles,
      eventResources,
      ownerProfile,
      myMembership
    );
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
    return `task_${task.id}["${safeTitle}"]`;
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

  const eventStart = event?.start_time ? new Date(event.start_time).getTime() : NaN;
  const eventEnd = event?.end_time ? new Date(event.end_time).getTime() : NaN;
  const tasksMinStart = Math.min(...datedTasks.map((x) => x.start));
  const tasksMaxEnd = Math.max(...datedTasks.map((x) => x.end));
  let minStart = tasksMinStart;
  let maxEnd = tasksMaxEnd;
  if (Number.isFinite(eventStart)) minStart = Math.min(minStart, eventStart);
  if (Number.isFinite(eventEnd)) maxEnd = Math.max(maxEnd, eventEnd);
  const span = Math.max(maxEnd - minStart, 1);

  const hourStep = 60 * 60 * 1000;
  const hourSlots = Math.max(1, Math.ceil(span / hourStep));
  const PIXELS_PER_HOUR = 32;
  const trackMinHeightPx = Math.max(820, hourSlots * PIXELS_PER_HOUR);
  const startHour = Math.floor(minStart / hourStep) * hourStep;
  const endHour = Math.ceil(maxEnd / hourStep) * hourStep;
  const ticks = [];
  for (let t = startHour; t <= endHour; t += hourStep) {
    const top = ((t - minStart) / span) * 100;
    ticks.push(`<div class="event-vertical-tick" style="top:${top.toFixed(2)}%"><span>${formatDateTime(new Date(t).toISOString())}</span></div>`);
  }

  const items = datedTasks
    .sort((a, b) => a.start - b.start)
    .map(({ task, start, end }) => {
      const top = ((start - minStart) / span) * 100;
      const height = Math.max(((end - start) / span) * 100, 2.5);
      return `
        <div class="event-vertical-item" style="top:${top.toFixed(2)}%;height:${height.toFixed(2)}%">
          <div class="event-vertical-bar"></div>
          <div class="event-vertical-content">
            <p class="event-vertical-title">${escapeHtml(task.title)}</p>
            <p class="event-vertical-meta">${formatDateTime(task.start_time)} — ${formatDateTime(task.end_time)}</p>
          </div>
        </div>`;
    })
    .join("");

  const trackH = trackMinHeightPx;
  return `
    <div class="event-vertical-timeline">
      <div class="event-vertical-axis" style="min-height:${trackH}px">${ticks.join("")}</div>
      <div class="event-vertical-track" style="min-height:${trackH}px">${items}</div>
    </div>
  `;
}

function buildEventDependenciesEditor(tasks, _depMap, eventId) {
  const taskOpts = tasks.map((t) => `<option value="${t.id}">${escapeHtml(t.title)}</option>`).join("");
  const succSelect = `<option value="">Выберите задачу</option>${taskOpts}`;
  const predSelect = `<option value="">Выберите предшественника</option>${taskOpts}`;

  return `
    <div class="panel event-deps-editor" data-event-id="${eventId}">
      <h3>Зависимости между задачами</h3>
      <p class="list-item-meta">Задача «наследник» не начнётся, пока не завершена «предшественник». Зависимости только между задачами этого мероприятия. Текущие связи отображаются на графе ниже; удалить зависимость можно на странице задачи.</p>
      <div class="event-deps-add-row detail-actions">
        <label class="event-deps-field"><span class="event-deps-field-label">Задача (кому нужен предшественник)</span>
          <select id="event-dep-successor-select">${succSelect}</select>
        </label>
        <label class="event-deps-field"><span class="event-deps-field-label">Зависит от (сначала выполнить)</span>
          <select id="event-dep-predecessor-select">${predSelect}</select>
        </label>
        <button type="button" class="btn btn-primary" id="event-dep-add-btn">Добавить зависимость</button>
      </div>
      <p id="event-dep-error" class="form-error hidden"></p>
    </div>`;
}

function setEventDepError(message = "") {
  const node = document.getElementById("event-dep-error");
  if (!node) return;
  node.textContent = message;
  node.classList.toggle("hidden", !message);
}

function syncEventDepPredecessorOptions(tasks, depMap) {
  const succ = document.getElementById("event-dep-successor-select");
  const pred = document.getElementById("event-dep-predecessor-select");
  if (!succ || !pred) return;
  const sid = succ.value ? Number(succ.value) : NaN;
  const currentPred = pred.value ? Number(pred.value) : null;
  const existing = Number.isFinite(sid) ? depMap[sid] || [] : [];
  let html = '<option value="">Выберите предшественника</option>';
  tasks.forEach((t) => {
    if (Number.isFinite(sid) && t.id === sid) return;
    if (Number.isFinite(sid) && existing.includes(t.id)) return;
    const sel = currentPred === t.id ? "selected" : "";
    html += `<option value="${t.id}" ${sel}>${escapeHtml(t.title)}</option>`;
  });
  pred.innerHTML = html;
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

function sortTasksByPlannedStart(tasks) {
  return [...tasks].sort((a, b) => {
    const ta = a.start_time ? new Date(a.start_time).getTime() : NaN;
    const tb = b.start_time ? new Date(b.start_time).getTime() : NaN;
    const va = Number.isFinite(ta) ? ta : Number.POSITIVE_INFINITY;
    const vb = Number.isFinite(tb) ? tb : Number.POSITIVE_INFINITY;
    if (va !== vb) return va - vb;
    return a.id - b.id;
  });
}

/** Назначения ресурсов, привязанные к задаче (из кэша state.resources). */
function collectAllocationsForTask(task) {
  const out = [];
  for (const r of state.resources || []) {
    if (Number(r.event_id) !== Number(task.event_id)) continue;
    for (const a of r.allocations || []) {
      if (a.task_id != null && a.task_id !== "" && Number(a.task_id) === Number(task.id)) {
        out.push({ alloc: a, resource: r });
      }
    }
  }
  out.sort((x, y) => {
    const ta = new Date(x.alloc.date_start).getTime();
    const tb = new Date(y.alloc.date_start).getTime();
    return (Number.isFinite(ta) ? ta : 0) - (Number.isFinite(tb) ? tb : 0);
  });
  return out;
}

/** Назначения без привязки к задаче (уровень мероприятия). */
function collectEventLevelAllocations(eventResources) {
  const out = [];
  for (const r of eventResources || []) {
    for (const a of r.allocations || []) {
      if (a.task_id == null || a.task_id === "") {
        out.push({ alloc: a, resource: r });
      }
    }
  }
  out.sort((x, y) => {
    const ta = new Date(x.alloc.date_start).getTime();
    const tb = new Date(y.alloc.date_start).getTime();
    return (Number.isFinite(ta) ? ta : 0) - (Number.isFinite(tb) ? tb : 0);
  });
  return out;
}

function canEditAllocation(alloc) {
  const status = String(alloc?.status || "").toLowerCase();
  return status !== "completed" && status !== "cancelled";
}

function buildAllocationTaskSelectOptions(tasks, selectedTaskId) {
  const opts = ['<option value="">Без задачи</option>'];
  for (const t of tasks || []) {
    const selected = selectedTaskId != null && Number(selectedTaskId) === Number(t.id) ? "selected" : "";
    const label = (t.title && String(t.title).trim()) || `Задача #${t.id}`;
    opts.push(`<option value="${t.id}" ${selected}>${escapeHtml(label)}</option>`);
  }
  return opts.join("");
}

function buildAllocationItemHtml(alloc, options = {}) {
  const {
    canManage = false,
    eventId = null,
    tasks = [],
    taskById = {},
    resource = null,
    returnEventId = null
  } = options;
  const editable = canManage && canEditAllocation(alloc);
  const deletable = canManage;
  const statusBadge = `<span class="badge">${enumLabel("allocationStatus", alloc.status)}</span>`;

  let titleHtml = `<p class="list-item-title">${statusBadge}</p>`;
  if (resource) {
    titleHtml = `
      <p class="list-item-title">
        <button type="button" class="entity-link" data-entity-link="resource" data-id="${resource.id}">
          ${escapeHtml(resource.name)}
        </button>
        <span class="badge">${enumLabel("resourceType", resource.type)}</span>
        ${statusBadge}
      </p>`;
  }

  let metaHtml;
  if (resource) {
    metaHtml = `<p class="list-item-meta">Количество: ${alloc.quantity_used} | ${formatDateTime(alloc.date_start)} — ${formatDateTime(alloc.date_end)}</p>`;
  } else {
    const tid = alloc.task_id;
    let taskHtml = "—";
    if (tid != null && tid !== "") {
      const titleFromMap = taskById[tid] || "";
      const retAttr =
        returnEventId != null
          ? ` data-return-event="${returnEventId}"`
          : eventId != null
            ? ` data-return-event="${eventId}"`
            : "";
      taskHtml = `<button type="button" class="entity-link" data-entity-link="task" data-id="${tid}"${retAttr}>${escapeHtml(titleFromMap || "Без названия")}</button>`;
    }
    metaHtml = `<p class="list-item-meta">Задача: ${taskHtml} | Количество: ${alloc.quantity_used} | ${formatDateTime(alloc.date_start)} — ${formatDateTime(alloc.date_end)}</p>`;
  }

  const actions = deletable
    ? `
    <div class="detail-actions" style="margin-top:8px">
      ${editable ? `<button type="button" class="btn btn-muted btn-inline" data-allocation-edit-toggle="${alloc.id}">Редактировать</button>` : ""}
      <button type="button" class="btn btn-danger btn-inline" data-allocation-delete="${alloc.id}">Удалить</button>
    </div>
    ${
      !editable && canManage
        ? '<p class="list-item-meta">Изменить параметры можно только для запланированных и активных назначений.</p>'
        : ""
    }`
    : "";

  const editForm = editable
    ? `
    <div id="allocation-edit-${alloc.id}" class="hidden" style="margin-top:10px">
      <form class="grid-form allocation-edit-form" data-allocation-id="${alloc.id}">
        <label>Задача
          <select name="task_id">${buildAllocationTaskSelectOptions(tasks, alloc.task_id)}</select>
        </label>
        <label>Количество<input name="quantity_used" type="number" min="1" value="${alloc.quantity_used}" required></label>
        <label>Начало<input name="date_start" type="datetime-local" required value="${toDatetimeLocalValue(alloc.date_start)}"></label>
        <label>Окончание<input name="date_end" type="datetime-local" required value="${toDatetimeLocalValue(alloc.date_end)}"></label>
        <div class="detail-actions">
          <button class="btn btn-primary btn-inline" type="submit">Сохранить</button>
          <button type="button" class="btn btn-muted btn-inline" data-allocation-edit-cancel="${alloc.id}">Отмена</button>
        </div>
      </form>
    </div>`
    : "";

  return `
    <article class="list-item" data-allocation-item="${alloc.id}">
      ${titleHtml}
      ${metaHtml}
      ${actions}
      ${editForm}
    </article>`;
}

function wireAllocationListActions(container, context) {
  if (!container || !context?.canManage) return;

  container.querySelectorAll("[data-allocation-edit-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.allocationEditToggle;
      container.querySelectorAll('[id^="allocation-edit-"]').forEach((el) => el.classList.add("hidden"));
      document.getElementById(`allocation-edit-${id}`)?.classList.remove("hidden");
    });
  });

  container.querySelectorAll("[data-allocation-delete]").forEach((btn) => {
    btn.addEventListener("click", () => {
      void onAllocationDelete(Number(btn.dataset.allocationDelete), context.onRefresh);
    });
  });

  container.querySelectorAll(".allocation-edit-form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      void onAllocationEditSubmit(e, Number(form.dataset.allocationId), context.onRefresh);
    });
  });

  container.querySelectorAll("[data-allocation-edit-cancel]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById(`allocation-edit-${btn.dataset.allocationEditCancel}`)?.classList.add("hidden");
    });
  });
}

async function onAllocationDelete(allocationId, onRefresh) {
  if (!confirm("Удалить назначение ресурса?")) return;
  try {
    await apiRequest(`${API.resources}allocations/${allocationId}`, { method: "DELETE" });
    notify("Назначение удалено");
    if (typeof onRefresh === "function") {
      await onRefresh();
    } else {
      await refreshData();
    }
  } catch (error) {
    notify(`Ошибка удаления: ${error.message}`, true);
  }
}

async function onAllocationEditSubmit(event, allocationId, onRefresh) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.task_id = payload.task_id ? Number(payload.task_id) : null;
  payload.quantity_used = Number(payload.quantity_used);
  payload.date_start = toIsoOrNull(payload.date_start);
  payload.date_end = toIsoOrNull(payload.date_end);

  if (!payload.quantity_used || !payload.date_start || !payload.date_end) {
    setFormError(form, "Заполните все поля назначения");
    return;
  }

  try {
    await apiRequest(`${API.resources}allocations/${allocationId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    notify("Назначение обновлено");
    if (typeof onRefresh === "function") {
      await onRefresh();
    } else {
      await refreshData();
    }
  } catch (error) {
    setFormError(form, `Ошибка сохранения: ${error.message}`);
    notify(`Ошибка сохранения: ${error.message}`, true);
  }
}

function renderEventDetailCard(
  event,
  tasks,
  depMap,
  participants,
  participantProfiles,
  eventResources,
  ownerProfile,
  myMembership = null
) {
  const root = document.getElementById("event-detail-root");
  const canManage = canCreate();
  const canLeaveEvent =
    myMembership &&
    String(myMembership.membership_status || "").toLowerCase() === "active" &&
    state.profileId != null &&
    Number(state.profileId) !== Number(event.owner_id);
  const canRemoveEventParticipants =
    state.profileId != null && Number(state.profileId) === Number(event.owner_id);
  const canViewParticipantAssignedTasks =
    state.role === "admin" ||
    (myMembership &&
      String(myMembership.membership_status || "").toLowerCase() === "active" &&
      ["owner", "organizer"].includes(String(myMembership.role || "").toLowerCase()));
  const taskById = Object.fromEntries(tasks.map((t) => [t.id, t]));
  const tasksForList = sortTasksByPlannedStart(tasks);

  const tasksBlock =
    tasks.length === 0
      ? '<p class="list-item-meta">Задач по этому мероприятию нет.</p>'
      : tasksForList
          .map((t) => {
            const deps = depMap[t.id] || [];
            const depText =
              deps.length === 0
                ? "нет зависимостей"
                : deps
                    .map((did) => {
                      const dt = taskById[did];
                      return dt ? `«${escapeHtml(dt.title)}»` : "другая задача";
                    })
                    .join("; ");
            const deleteBtn = canManage
              ? `<button type="button" class="btn btn-danger btn-inline" data-event-task-delete="${t.id}">Удалить</button>`
              : "";
            return `
        <article class="list-item">
          <p class="list-item-title event-detail-task-row">
            <span class="event-detail-task-row-titleblock">
            <button type="button" class="entity-link" data-entity-link="task" data-id="${t.id}" data-return-event="${event.id}">
              ${escapeHtml(t.title)}
            </button>
            ${renderTaskInlineBadges(t)}
            </span>
            ${deleteBtn}
          </p>
          <p class="list-item-meta">План: ${formatDateTime(t.start_time)} — ${formatDateTime(t.end_time)}</p>
          <p class="list-item-meta">Дедлайн: ${formatDateTime(t.deadline)}</p>
          <div class="deps-block">Зависит от: ${depText}</div>
        </article>`;
          })
          .join("");
  const timelineBlock = buildEventTimeline(tasks, event);
  const eventLevelAllocRows = collectEventLevelAllocations(eventResources);
  const eventAllocContext = {
    canManage,
    eventId: event.id,
    tasks,
    taskById: Object.fromEntries(tasks.map((t) => [t.id, (t.title && String(t.title).trim()) || ""])),
    returnEventId: event.id,
    onRefresh: async () => {
      await refreshData();
      await openEventDetail(event.id);
    }
  };
  const eventLevelAllocationsBlock =
    eventLevelAllocRows.length === 0
      ? '<p class="list-item-meta">Нет назначений уровня мероприятия (без привязки к задаче).</p>'
      : eventLevelAllocRows
          .map(({ alloc: a, resource: r }) =>
            buildAllocationItemHtml(a, { ...eventAllocContext, resource: r })
          )
          .join("");
  const participantsBlock =
    !participants || participants.length === 0
      ? '<p class="list-item-meta">Участников пока нет.</p>'
      : participants
          .map(
            (participant) => {
              const showRemove =
                canRemoveEventParticipants && Number(participant.user_id) !== Number(event.owner_id);
              const removeBtn = showRemove
                ? `<button type="button" class="btn btn-danger btn-inline" data-event-remove-participant="${participant.user_id}">Удалить</button>`
                : "";
              const assignedTasksBtn = canViewParticipantAssignedTasks
                ? `<button type="button" class="btn btn-muted btn-inline" data-event-participant-tasks="${participant.user_id}">Назначенные задачи</button>`
                : "";
              return `
        <article class="list-item" data-participant-id="${participant.user_id}">
          <p class="list-item-title event-detail-task-row">
            <span class="event-detail-task-row-titleblock">
            <button type="button" class="entity-link" data-entity-link="user" data-id="${participant.user_id}">
              ${escapeHtml(
                participantProfiles?.[participant.user_id]
                  ? `${participantProfiles[participant.user_id].first_name} ${participantProfiles[participant.user_id].last_name}`
                  : `Пользователь #${participant.user_id}`
              )}
            </button>
            </span>
            ${assignedTasksBtn}${removeBtn}
          </p>
          <p class="list-item-meta">Роль в мероприятии: ${enumLabel("participantRole", participant.role)}</p>
          <div id="participant-tasks-${participant.user_id}" class="hidden" style="margin-top:8px"></div>
        </article>`;
            }
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
              ${escapeHtml(resource.name)}
            </button>
            <span class="badge">${enumLabel("resourceType", resource.type)}</span>
          </p>
          <p class="list-item-meta">Количество: ${resource.quantity} | Стоимость/час: ${resource.cost_per_hour ?? "—"}</p>
        </article>`
          )
          .join("");

  const canDeleteEvent =
    state.role === "admin" ||
    (state.profileId != null && Number(state.profileId) === Number(event.owner_id));

  const manageButtonsHtml = canManage
    ? `
        <button type="button" class="btn btn-muted btn-inline" id="event-toggle-edit-btn">Редактировать</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-users-btn">+ Добавить участника</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-task-create-btn">+ Создать задачу</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-resource-create-btn">+ Создать ресурс</button>
        <button type="button" class="btn btn-muted btn-inline" id="event-open-allocation-btn">+ Создать назначение ресурса</button>`
    : "";

  const deleteButtonHtml = canDeleteEvent
    ? `<button type="button" class="btn btn-danger btn-inline" id="event-delete-btn">Удалить мероприятие</button>`
    : "";

  const leaveButtonHtml = canLeaveEvent
    ? `<button type="button" class="btn btn-danger btn-inline" data-event-leave-participant="${event.id}">Покинуть мероприятие</button>`
    : "";

  const editFormHtml = canManage
    ? `
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
          <button type="button" class="btn btn-muted btn-inline" id="event-cancel-edit-btn">Отмена</button>
        </div>
      </div>`
    : "";

  const actionsSection =
    canManage || canLeaveEvent || canDeleteEvent
      ? `
    <div class="panel">
      <div class="detail-actions">
        ${manageButtonsHtml}
        ${deleteButtonHtml}
        ${leaveButtonHtml}
      </div>
      ${editFormHtml}
    </div>`
      : "";

  const eventDepsEditorBlock =
    canManage && tasks.length > 0 ? buildEventDependenciesEditor(tasks, depMap, event.id) : "";

  const taskStatsHtml = buildTaskProgressStatsHtml(computeTaskStatusStats(tasks));
  const resourceUtilHtml = buildResourceUtilizationHtml(
    computeResourceUtilization(eventResources, event),
    eventResources
  );

  root.innerHTML = `
    <div class="panel">
      <dl class="detail-dl">
        <dt>ID</dt><dd>${event.id}</dd>
        <dt>Статус</dt><dd>${enumLabel("eventStatus", event.status)}</dd>
        <dt>Владелец</dt><dd>${userProfileLinkButton(event.owner_id, ownerProfile)}</dd>
        <dt>Начало</dt><dd>${new Date(event.start_time).toLocaleString()}</dd>
        <dt>Окончание</dt><dd>${new Date(event.end_time).toLocaleString()}</dd>
        <dt>Локация</dt><dd>${escapeHtml(event.location || "—")}</dd>
        <dt>Бюджет</dt><dd>${event.budget ?? 0}</dd>
        <dt>Создано</dt><dd>${event.created_at ? new Date(event.created_at).toLocaleString() : "—"}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(event.description || "Без описания")}</p>
    </div>
    ${actionsSection}
    <div class="panel">
      <h3>Участники мероприятия</h3>
      ${participantsBlock}
    </div>
    <div class="panel">
      <h3>Задачи и зависимости</h3>
      ${tasksBlock}
    </div>
    ${eventDepsEditorBlock}
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
    <div class="panel">
      <h3>Используемые ресурсы</h3>
      ${resourcesBlock}
    </div>
    <div class="panel" id="event-allocations-panel">
      <h3>Назначения ресурсов на мероприятие</h3>
      <p class="list-item-meta">Назначения без привязки к задаче (уровень мероприятия).</p>
      ${eventLevelAllocationsBlock}
    </div>
    <div class="panel">
      <h3>Статистика выполнения задач</h3>
      ${taskStatsHtml}
    </div>
    <div class="panel">
      <h3>Загрузка ресурсов</h3>
      ${resourceUtilHtml}
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
      void openAllocationCreatePanel({ eventId: event.id });
    });
    document.getElementById("event-toggle-edit-btn").addEventListener("click", () => {
      document.getElementById("event-edit-section").classList.remove("hidden");
    });
    document.getElementById("event-cancel-edit-btn").addEventListener("click", () => {
      document.getElementById("event-edit-section").classList.add("hidden");
    });
    document.getElementById("event-edit-form").addEventListener("submit", (e) => onEventEditSubmit(e, event.id));

    root.querySelectorAll("[data-event-task-delete]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        void onTaskDelete(Number(btn.dataset.eventTaskDelete), { reopenEventId: event.id });
      });
    });

    const depEditor = root.querySelector(".event-deps-editor");
    if (depEditor) {
      const succSel = document.getElementById("event-dep-successor-select");
      succSel?.addEventListener("change", () => syncEventDepPredecessorOptions(tasks, depMap));
      syncEventDepPredecessorOptions(tasks, depMap);
      setEventDepError("");
      document.getElementById("event-dep-add-btn")?.addEventListener("click", () => void onEventDepAdd(event.id));
    }
    wireAllocationListActions(document.getElementById("event-allocations-panel"), eventAllocContext);
  }
  if (canDeleteEvent) {
    document.getElementById("event-delete-btn").addEventListener("click", () => onEventDelete(event.id));
  }
  if (canRemoveEventParticipants) {
    root.querySelectorAll("[data-event-remove-participant]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        void onRemoveEventParticipant(event.id, Number(btn.dataset.eventRemoveParticipant));
      });
    });
  }
  if (canViewParticipantAssignedTasks) {
    root.querySelectorAll("[data-event-participant-tasks]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        void onEventParticipantTasksToggle(event.id, Number(btn.dataset.eventParticipantTasks));
      });
    });
  }
  void renderEventDependencyMermaid(tasks, depMap);
}

function renderParticipantAssignedTasksHtml(tasks, participantUserId, eventId) {
  if (!tasks.length) {
    return '<p class="list-item-meta">Нет назначенных задач</p>';
  }
  return `<ul class="list">${tasks
    .map((t) => {
      const assignee = (Array.isArray(t.assignees) ? t.assignees : []).find(
        (a) => Number(a.user_id) === Number(participantUserId)
      );
      const assignLabel = assignee ? taskAssigneeStatusLabel(assignee.status) : "—";
      return `<li class="list-item">
          <p class="list-item-title">
            <button type="button" class="entity-link" data-entity-link="task" data-id="${t.id}" data-return-event="${eventId}">
              ${escapeHtml(t.title)}
            </button>
            <span class="badge">${enumLabel("taskStatus", t.status)}</span>
          </p>
          <p class="list-item-meta">План: ${formatDateTime(t.start_time)} — ${formatDateTime(t.end_time)}</p>
          <p class="list-item-meta">Назначение: ${escapeHtml(assignLabel)}</p>
        </li>`;
    })
    .join("")}</ul>`;
}

async function onEventParticipantTasksToggle(eventId, userId) {
  const panel = document.getElementById(`participant-tasks-${userId}`);
  if (!panel) return;
  if (!panel.classList.contains("hidden")) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  if (panel.dataset.loaded === "1") return;
  panel.innerHTML = '<p class="list-item-meta">Загрузка…</p>';
  try {
    const tasks = await apiRequest(
      `${API.tasks}event/${eventId}/participant/${userId}/assigned`
    );
    panel.innerHTML = renderParticipantAssignedTasksHtml(tasks, userId, eventId);
    panel.dataset.loaded = "1";
  } catch (error) {
    panel.innerHTML = `<p class="list-item-meta" style="color:var(--danger)">${escapeHtml(error.message)}</p>`;
  }
}

async function onEventEditSubmit(event, eventId) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.budget = payload.budget ? Number(payload.budget) : 0;
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
  if (payload.start_time && payload.end_time && new Date(payload.end_time) < new Date(payload.start_time)) {
    setFormError(form, "Дата окончания мероприятия не может быть раньше даты начала");
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
    setFormError(form, `Ошибка сохранения: ${error.message}`);
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

async function onRemoveEventParticipant(eventId, participantUserId) {
  if (!participantUserId) return;
  if (!confirm("Удалить участника из мероприятия?")) return;
  try {
    await apiRequest(`${API.events}${eventId}/participants/${participantUserId}`, { method: "DELETE" });
    notify("Участник удалён");
    await openEventDetail(eventId);
    await refreshData();
  } catch (error) {
    notify(`Ошибка удаления участника: ${error.message}`, true);
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
    let task;
    try {
      task = await apiRequest(`${API.tasks}${taskId}`);
    } catch (error) {
      if (isTaskAccessDeniedError(error)) {
        await openTaskInvitationPreview(taskId);
        return;
      }
      throw error;
    }
    el.screenTitle.textContent = task.title || `Задача #${taskId}`;
    let eventRecord = null;
    try {
      eventRecord = await apiRequest(`${API.events}${task.event_id}`);
    } catch {
      eventRecord = null;
    }
    const eventTitle =
      eventRecord?.title?.trim() ? eventRecord.title : getEventTitle(task.event_id) || "Мероприятие";
    const mode = taskDetailMode(task);
    let eventParticipants = [];
    if (canCreate() && mode === "full") {
      try {
        eventParticipants = await apiRequest(`${API.events}${task.event_id}/participants`);
        if (!Array.isArray(eventParticipants)) eventParticipants = [];
      } catch {
        eventParticipants = [];
      }
    }
    const assigneeUserIds = (Array.isArray(task.assignees) ? task.assignees : []).map((a) => a.user_id);
    const participantUserIds = eventParticipants.map((p) => p.user_id);
    const profileIds = [...new Set([task.owner_id, ...assigneeUserIds, ...participantUserIds])].filter(
      (id) => id != null && id !== ""
    );
    let profilesById = {};
    if (profileIds.length) {
      const params = new URLSearchParams();
      [...new Set(profileIds.map(Number))].forEach((id) => params.append("ids", String(id)));
      try {
        const plist = await apiRequest(`${API.users}/public/by-ids?${params.toString()}`);
        profilesById = Object.fromEntries((plist || []).map((p) => [Number(p.id), p]));
      } catch {
        profilesById = {};
      }
    }
    const taskDetailMeta = {
      eventTitle,
      ownerProfile: profilesById[Number(task.owner_id)],
      taskAllocations: collectAllocationsForTask(task),
      assigneeProfilesById: profilesById,
      eventParticipants
    };
    let dependsOn = [];
    let eventTasksForDeps = [];
    try {
      eventTasksForDeps = await apiRequest(`${API.tasks}event/${task.event_id}`);
      if (!Array.isArray(eventTasksForDeps)) eventTasksForDeps = [];
    } catch {
      eventTasksForDeps = [];
    }
    if (mode === "full" && canCreate()) {
      try {
        const depPayload = await apiRequest(`${API.tasks}${taskId}/dependency-ids`);
        dependsOn = Array.isArray(depPayload?.depends_on) ? depPayload.depends_on : [];
      } catch (depErr) {
        notify(`Не удалось загрузить зависимости: ${depErr.message}`, true);
      }
    }
    renderTaskDetailCard(task, dependsOn, eventTasksForDeps, taskDetailMeta);
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function buildTaskDependenciesPanel(task, dependsOnIds, eventTasksList = []) {
  const inEvent = Array.isArray(eventTasksList) ? eventTasksList : [];
  const taskById = Object.fromEntries(inEvent.map((t) => [t.id, t]));
  const listBlock =
    dependsOnIds.length === 0
      ? '<p class="list-item-meta">Нет зависимостей.</p>'
      : `<ul class="list">${dependsOnIds
          .map((did) => {
            const t = taskById[did];
            const label = t ? escapeHtml(t.title) : "Задача недоступна в списке мероприятия";
            return `<li class="list-item" style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><span>${label}</span><button type="button" class="btn btn-muted btn-inline task-dep-remove-btn" data-depends-on="${did}">Удалить</button></li>`;
          })
          .join("")}</ul>`;

  const candidates = inEvent.filter(
    (t) => t.id !== task.id && !dependsOnIds.includes(t.id)
  );
  const selectOpts =
    '<option value="">Выберите задачу-предшественник</option>' +
    candidates
      .map((t) => `<option value="${t.id}">${escapeHtml(t.title)}</option>`)
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

function renderTaskDetailCard(task, dependsOnIds = [], eventTasksForDeps = [], meta = {}) {
  const root = document.getElementById("task-detail-root");
  const mode = taskDetailMode(task);
  const canManage = canCreate();
  const depsSection = mode === "full" && canManage ? buildTaskDependenciesPanel(task, dependsOnIds, eventTasksForDeps) : "";
  const eventTitle = meta.eventTitle?.trim() ? meta.eventTitle : "Мероприятие";
  const profilesMap = meta.assigneeProfilesById || {};
  const assignRows = Array.isArray(task.assignees) ? task.assignees : [];
  const assigneesSummary =
    assignRows.length === 0
      ? "—"
      : assignRows
          .map((a) => {
            const uid = Number(a.user_id);
            const prof = profilesMap[uid];
            return `${userProfileLinkButton(uid, prof)} (${taskAssigneeStatusLabel(a.status)})`;
          })
          .join(", ");
  const ownerDd = userProfileLinkButton(task.owner_id, meta.ownerProfile);

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
        <button type="button" class="btn btn-muted btn-inline" id="task-toggle-edit-btn">Редактировать</button>
        <button type="button" class="btn btn-muted btn-inline" id="task-open-allocation-btn">+ Создать назначение ресурса</button>
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

  const canWithdrawFromTask = isTaskAcceptedAssignee(task);
  const withdrawSection = canWithdrawFromTask
    ? `<div class="panel" style="margin-top:12px">
      <div class="detail-actions">
        <button type="button" class="btn btn-danger btn-inline" id="task-withdraw-btn">Отказаться от задачи</button>
      </div>
    </div>`
    : "";

  const assigneesListHtml =
    assignRows.length === 0
      ? '<p class="list-item-meta">Нет приглашённых исполнителей.</p>'
      : `<ul class="list">${assignRows
          .map((a) => {
            const uid = Number(a.user_id);
            const prof = profilesMap[uid];
            const st = taskAssigneeStatusLabel(a.status);
            const revoke =
              mode === "full" && canManage
                ? `<button type="button" class="btn btn-muted btn-inline task-assignee-revoke-btn" data-user-id="${uid}">Отозвать</button>`
                : "";
            return `<li class="list-item" style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap"><span>${userProfileLinkButton(uid, prof)} <span class="list-item-meta">(${st})</span></span>${revoke}</li>`;
          })
          .join("")}</ul>`;

  const busyAssigneeIds = new Set(
    assignRows
      .filter((a) => {
        const s = String(a.status || "").toLowerCase();
        return s === "pending" || s === "accepted";
      })
      .map((a) => Number(a.user_id))
  );
  const eventParts = Array.isArray(meta.eventParticipants) ? meta.eventParticipants : [];
  const inviteOptions = eventParts
    .filter((p) => !busyAssigneeIds.has(Number(p.user_id)) && Number(p.user_id) !== Number(task.owner_id))
    .map((p) => {
      const uid = Number(p.user_id);
      const prof = profilesMap[uid];
      const nameLabel = formatPublicProfileName(prof) || `Пользователь #${uid}`;
      return `<option value="${uid}">${escapeHtml(`${nameLabel} — ${enumLabel("participantRole", p.role)}`)}</option>`;
    })
    .join("");

  const inviteBlock =
    mode === "full" && canManage
      ? `<div style="margin-top:12px" id="task-assignees-invite-panel">
          <h4>Пригласить исполнителя</h4>
          <p class="list-item-meta">Из активных участников мероприятия.</p>
          <div class="detail-actions" style="margin-top:8px;flex-wrap:wrap;gap:8px">
            <select id="task-assignee-invite-select" style="min-width:220px">
              <option value="">Выберите пользователя</option>
              ${inviteOptions}
            </select>
            <button type="button" class="btn btn-primary" id="task-assignee-invite-btn">Пригласить</button>
          </div>
        </div>`
      : "";

  const assigneesPanel = `
    <div class="panel" style="margin-top:12px" id="task-assignees-panel">
      <h3>Исполнители и приглашения</h3>
      ${assigneesListHtml}
      ${inviteBlock}
    </div>`;

  const taskAllocRows = Array.isArray(meta.taskAllocations) ? meta.taskAllocations : [];
  const taskAllocContext = {
    canManage: mode === "full" && canManage,
    eventId: task.event_id,
    tasks: eventTasksForDeps,
    taskById: Object.fromEntries(
      (eventTasksForDeps || []).map((t) => [t.id, (t.title && String(t.title).trim()) || ""])
    ),
    returnEventId: task.event_id,
    onRefresh: async () => {
      await refreshData();
      await openTaskDetail(task.id);
    }
  };
  const taskResourceAllocSection = `
    <div class="panel" id="task-allocations-panel">
      <h3>Назначения ресурсов на задачу</h3>
      ${
        taskAllocRows.length === 0
          ? '<p class="list-item-meta">Нет назначений ресурсов, привязанных к этой задаче.</p>'
          : taskAllocRows
              .map(({ alloc: a, resource: r }) =>
                buildAllocationItemHtml(a, { ...taskAllocContext, resource: r })
              )
              .join("")
      }
    </div>`;

  root.innerHTML = `
    <div class="panel">
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${task.event_id}">${escapeHtml(eventTitle)}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${task.id}</dd>
        <dt>Статус</dt><dd>${enumLabel("taskStatus", task.status)}${task.is_late_start ? ' <span class="badge badge-warning">Поздний старт</span>' : ""}</dd>
        <dt>Приоритет</dt><dd>${enumLabel("taskPriority", task.priority)}</dd>
        <dt>Исполнители</dt><dd>${assigneesSummary}</dd>
        <dt>Владелец</dt><dd>${ownerDd}</dd>
        <dt>Дедлайн</dt><dd>${formatDateTime(task.deadline)}</dd>
        ${buildTaskScheduleDeviationHtml(task)}
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(task.description || "Без описания")}</p>
    </div>
    ${assigneesPanel}
    ${taskResourceAllocSection}
    ${depsSection}
    ${editSection}
    ${withdrawSection}
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
    document.getElementById("task-open-allocation-btn").addEventListener("click", () => {
      void openAllocationCreatePanel({ eventId: task.event_id, taskId: task.id });
    });
    document.getElementById("task-toggle-edit-btn").addEventListener("click", () => {
      document.getElementById("task-edit-section").classList.remove("hidden");
    });
    document.getElementById("task-cancel-edit-btn").addEventListener("click", () => {
      document.getElementById("task-edit-section").classList.add("hidden");
    });
    document.getElementById("task-edit-form").addEventListener("submit", (e) => onTaskEditSubmit(e, task.id));
    document.getElementById("task-delete-btn").addEventListener("click", () => onTaskDelete(task.id));
    document.querySelectorAll(".task-assignee-revoke-btn").forEach((btn) => {
      btn.addEventListener("click", () => void onTaskAssigneeRevoke(task.id, Number(btn.dataset.userId)));
    });
    const invBtn = document.getElementById("task-assignee-invite-btn");
    if (invBtn) {
      invBtn.addEventListener("click", () => void onTaskAssigneeInvite(task.id));
    }
    wireAllocationListActions(document.getElementById("task-allocations-panel"), taskAllocContext);
  } else if (mode === "status_only") {
    document.getElementById("task-toggle-status-btn").addEventListener("click", () => {
      document.getElementById("task-status-section").classList.remove("hidden");
    });
    document.getElementById("task-status-form").addEventListener("submit", (e) => onTaskStatusSubmit(e, task.id));
  }
  const withdrawBtn = document.getElementById("task-withdraw-btn");
  if (withdrawBtn) {
    withdrawBtn.addEventListener("click", () => void onTaskAssigneeWithdraw(task.id));
  }
}

async function onTaskAssigneeWithdraw(taskId) {
  if (!confirm("Отказаться от выполнения этой задачи?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}/assignees/me/withdraw`, { method: "POST" });
    notify("Вы отказались от задачи");
    await refreshData();
    await openTaskDetail(taskId, taskDetailReopenOpts());
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

async function onTaskAssigneeInvite(taskId) {
  const sel = document.getElementById("task-assignee-invite-select");
  if (!sel || !sel.value) {
    notify("Выберите пользователя для приглашения", true);
    return;
  }
  const userId = Number(sel.value);
  try {
    await apiRequest(`${API.tasks}${taskId}/assignees`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId })
    });
    notify("Приглашение отправлено");
    await openTaskDetail(taskId, taskDetailReopenOpts());
    await refreshData();
  } catch (error) {
    notify(`Ошибка приглашения: ${error.message}`, true);
  }
}

async function onTaskAssigneeRevoke(taskId, userId) {
  if (!userId) return;
  if (!confirm("Отозвать приглашение или убрать исполнителя из задачи?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}/assignees/${userId}`, { method: "DELETE" });
    notify("Запись исполнителя удалена");
    await openTaskDetail(taskId, taskDetailReopenOpts());
    await refreshData();
  } catch (error) {
    notify(`Ошибка: ${error.message}`, true);
  }
}

async function onTaskEditSubmit(event, taskId) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);
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
    setFormError(form, `Ошибка сохранения: ${error.message}`);
    notify(`Ошибка сохранения: ${error.message}`, true);
  }
}

async function onTaskStatusSubmit(event, taskId) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
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
    setFormError(form, `Ошибка: ${error.message}`);
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
  } catch (error) {
    notify(`Не удалось удалить зависимость: ${error.message}`, true);
  }
}

async function onEventDepAdd(eventId) {
  const succ = document.getElementById("event-dep-successor-select");
  const pred = document.getElementById("event-dep-predecessor-select");
  setEventDepError("");
  if (!succ?.value || !pred?.value) {
    setEventDepError("Выберите задачу и предшественника");
    return;
  }
  const taskId = Number(succ.value);
  const dependsOn = Number(pred.value);
  if (taskId === dependsOn) {
    setEventDepError("Задача не может зависеть от самой себя");
    return;
  }
  try {
    await apiRequest(`${API.tasks}${taskId}/dependencies/${dependsOn}`, { method: "POST" });
    notify("Зависимость добавлена");
    await openEventDetail(eventId);
  } catch (error) {
    setEventDepError(error.message);
  }
}

async function onTaskDelete(taskId, opts = {}) {
  if (!confirm("Удалить задачу?")) return;
  try {
    await apiRequest(`${API.tasks}${taskId}`, { method: "DELETE" });
    notify("Задача удалена");
    if (opts.reopenEventId != null) {
      await openEventDetail(opts.reopenEventId);
      await refreshData();
      return;
    }
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

    const [event, ownerRaw, eventTasks] = await Promise.all([
      apiRequest(`${API.events}${resource.event_id}`).catch(() => null),
      state.role === "admin"
        ? apiRequest(`${API.users}/${resource.owner_id}`).catch(() => null)
        : apiRequest(`${API.users}/public/by-ids?ids=${resource.owner_id}`).catch(() => null),
      apiRequest(`${API.tasks}event/${resource.event_id}`).catch(() => [])
    ]);

    const eventTitle = event?.title?.trim() ? event.title : "Мероприятие";
    const owner = Array.isArray(ownerRaw) ? ownerRaw[0] : ownerRaw;
    const ownerName = owner
      ? `${owner.first_name || ""} ${owner.last_name || ""}`.trim() || "Пользователь"
      : "Не удалось загрузить";

    const taskById = {};
    for (const t of Array.isArray(eventTasks) ? eventTasks : []) {
      taskById[t.id] = (t.title && String(t.title).trim()) || "";
    }

    renderResourceDetailCard(resource, {
      eventTitle,
      ownerName,
      taskById,
      eventTasks: Array.isArray(eventTasks) ? eventTasks : []
    });
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function buildSystemRoleOptions(currentRole) {
  const roles = ["admin", "organizer", "executor", "viewer"];
  return roles
    .map(
      (role) =>
        `<option value="${role}" ${String(currentRole || "").toLowerCase() === role ? "selected" : ""}>${enumLabel("participantRole", role)}</option>`
    )
    .join("");
}

async function onUserProfileDelete(profileId) {
  if (
    !confirm(
      "Удалить пользователя безвозвратно? Будут удалены профиль и учётная запись (вход по email станет невозможен)."
    )
  ) {
    return;
  }
  try {
    await apiRequest(`${API.users}/${profileId}`, { method: "DELETE" });
    notify("Пользователь удалён");
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

async function onUserRoleChange(authUserId, profileId) {
  const roleSelect = document.getElementById("user-role-edit-select");
  if (!roleSelect?.value) {
    notify("Выберите роль", true);
    return;
  }
  const authId = Number(authUserId);
  if (!Number.isFinite(authId) || authId <= 0) {
    notify("Не удалось определить учётную запись пользователя", true);
    return;
  }
  const nextRole = roleSelect.value;
  try {
    await apiRequest(`${API.auth}/users/${authId}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role: nextRole })
    });
    notify("Роль обновлена");
    await refreshData();
    await openUserDetail(profileId);
  } catch (error) {
    notify(`Ошибка смены роли: ${error.message}`, true);
  }
}

async function openUserDetail(userId) {
  state.detailBackTarget = null;
  state.detailView = "user";
  hideAllScreens();
  document.getElementById("user-detail-screen").classList.remove("hidden");
  el.screenTitle.textContent = "Пользователь";
  updateTopbarActions();
  notify("Загрузка…");
  const root = el.userDetailRoot;
  if (root) root.innerHTML = '<p class="list-item-meta">Загрузка…</p>';
  try {
    let user;
    if (state.role === "admin") {
      user = await apiRequest(`${API.users}/${userId}`);
    } else if (state.profileId != null && Number(userId) === Number(state.profileId)) {
      user = await apiRequest(`${API.users}/${userId}`);
    } else {
      const list = await apiRequest(`${API.users}/public/by-ids?ids=${userId}`);
      user = Array.isArray(list) ? list[0] : null;
    }
    if (!user) throw new Error("Пользователь не найден");
    el.screenTitle.textContent = `${user.first_name || ""} ${user.last_name || ""}`.trim() || `Пользователь #${userId}`;
    const showContacts =
      state.role === "admin" || (state.profileId != null && Number(userId) === Number(state.profileId));
    const canChangeSystemRole =
      state.role === "admin" &&
      state.profileId != null &&
      Number(userId) !== Number(state.profileId) &&
      user.auth_user_id != null;
    const canDeleteUser =
      state.role === "admin" &&
      state.profileId != null &&
      Number(userId) !== Number(state.profileId);
    const roleManagePanel = canChangeSystemRole
      ? `
      <div class="panel">
        <h3>Системная роль</h3>
        <p class="list-item-meta">Изменение системной роли пользователя</p>
        <div class="detail-actions">
          <select id="user-role-edit-select">
            ${buildSystemRoleOptions(user.role)}
          </select>
          <button type="button" class="btn btn-primary btn-inline" id="user-role-save-btn">Сохранить роль</button>
        </div>
      </div>`
      : "";
    const deleteUserPanel = canDeleteUser
      ? `
      <div class="panel">
        <h3>Опасная зона</h3>
        <p class="list-item-meta">Удаляются профиль и учётная запись. Действие необратимо.</p>
        <button type="button" class="btn btn-danger" id="user-profile-delete-btn">Удалить пользователя</button>
      </div>`
      : "";
    root.innerHTML = `
      <div class="panel">
        <dl class="detail-dl">
          <dt>ID профиля</dt><dd>${user.id}</dd>
          ${showContacts && user.auth_user_id != null ? `<dt>ID учётной записи</dt><dd>${user.auth_user_id}</dd>` : ""}
          <dt>Имя</dt><dd>${escapeHtml(user.first_name || "—")}</dd>
          <dt>Фамилия</dt><dd>${escapeHtml(user.last_name || "—")}</dd>
          <dt>Специализация</dt><dd>${escapeHtml(user.speciality || "—")}</dd>
          <dt>Роль</dt><dd>${enumLabel("participantRole", user.role || "viewer")}</dd>
          ${
            showContacts
              ? `<dt>Email</dt><dd>${escapeHtml(user.email || "—")}</dd><dt>Телефон</dt><dd>${escapeHtml(user.phone || "—")}</dd>`
              : ""
          }
        </dl>
      </div>
      ${roleManagePanel}
      ${deleteUserPanel}
    `;
    if (canChangeSystemRole) {
      document.getElementById("user-role-save-btn")?.addEventListener("click", () =>
        void onUserRoleChange(user.auth_user_id, user.id)
      );
    }
    if (canDeleteUser) {
      document.getElementById("user-profile-delete-btn")?.addEventListener("click", () =>
        void onUserProfileDelete(user.id)
      );
    }
    notify("Готово");
  } catch (error) {
    notify(error.message, true);
    await closeDetailView();
  }
}

function renderResourceDetailCard(resource, meta = {}) {
  const root = document.getElementById("resource-detail-root");
  const canManage = canCreate();
  const allocs = Array.isArray(resource.allocations) ? resource.allocations : [];
  const { eventTitle = "Мероприятие", ownerName = "—", taskById = {}, eventTasks = [] } = meta;
  const allocContext = {
    canManage,
    eventId: resource.event_id,
    tasks: eventTasks,
    taskById,
    returnEventId: resource.event_id,
    onRefresh: async () => {
      await refreshData();
      await openResourceDetail(resource.id);
    }
  };

  const allocBlock =
    allocs.length === 0
      ? '<p class="list-item-meta">Нет назначений.</p>'
      : allocs.map((a) => buildAllocationItemHtml(a, allocContext)).join("");

  const editSection = canManage
    ? `
    <div class="panel">
      <div class="detail-actions">
        <button type="button" class="btn btn-muted btn-inline" id="resource-open-allocation-btn">+ Создать назначение ресурса</button>
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
      <p class="list-item-meta">Мероприятие: <button type="button" class="entity-link" data-entity-link="event" data-id="${resource.event_id}">${escapeHtml(eventTitle)}</button></p>
      <dl class="detail-dl">
        <dt>ID</dt><dd>${resource.id}</dd>
        <dt>Тип</dt><dd>${enumLabel("resourceType", resource.type)}</dd>
        <dt>Владелец</dt><dd><button type="button" class="entity-link" data-entity-link="user" data-id="${resource.owner_id}">${escapeHtml(ownerName)}</button></dd>
        <dt>Количество</dt><dd>${resource.quantity}</dd>
        <dt>Стоимость/час</dt><dd>${resource.cost_per_hour ?? "—"}</dd>
      </dl>
      <p class="list-item-meta" style="margin-top:12px">${escapeHtml(resource.description || "")}</p>
    </div>
    ${editSection}
    <div class="panel" id="resource-allocations-panel">
      <h3>Назначения</h3>
      ${allocBlock}
    </div>
  `;

  if (canManage) {
    wireAllocationListActions(document.getElementById("resource-allocations-panel"), allocContext);
    document.getElementById("resource-open-allocation-btn").addEventListener("click", () => {
      void openAllocationCreatePanel({ eventId: resource.event_id, resourceId: resource.id });
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
  setFormError(form, "");
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
    setFormError(form, `Ошибка сохранения: ${error.message}`);
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
  const inboxTab = e.target.closest("[data-inbox-tab]");
  if (inboxTab) {
    e.preventDefault();
    const tab = inboxTab.dataset.inboxTab;
    if (tab === "incoming" || tab === "outgoing") {
      state.inboxTab = tab;
      void loadInbox();
    }
    return;
  }
  const previewEv = e.target.closest("[data-inbox-preview-event]");
  if (previewEv) {
    e.preventDefault();
    const id = Number(previewEv.dataset.inboxPreviewEvent);
    if (!Number.isNaN(id)) void openEventInvitationPreview(id, { fromInbox: true });
    return;
  }
  const previewTk = e.target.closest("[data-inbox-preview-task]");
  if (previewTk) {
    e.preventDefault();
    const id = Number(previewTk.dataset.inboxPreviewTask);
    if (!Number.isNaN(id)) void openTaskInvitationPreview(id, { fromInbox: true });
    return;
  }
  const leaveEv = e.target.closest("[data-event-leave-participant]");
  if (leaveEv) {
    e.preventDefault();
    const id = Number(leaveEv.dataset.eventLeaveParticipant);
    if (!Number.isNaN(id)) void leaveEventAsParticipant(id);
    return;
  }
  const acceptEv = e.target.closest("[data-inbox-accept-event]");
  if (acceptEv) {
    e.preventDefault();
    const id = Number(acceptEv.dataset.inboxAcceptEvent);
    if (!Number.isNaN(id)) void acceptEventInvitation(id);
    return;
  }
  const declineEv = e.target.closest("[data-inbox-decline-event]");
  if (declineEv) {
    e.preventDefault();
    const id = Number(declineEv.dataset.inboxDeclineEvent);
    if (!Number.isNaN(id)) void declineEventInvitation(id);
    return;
  }
  const acceptTk = e.target.closest("[data-inbox-accept-task]");
  if (acceptTk) {
    e.preventDefault();
    const id = Number(acceptTk.dataset.inboxAcceptTask);
    if (!Number.isNaN(id)) void acceptTaskInvitation(id);
    return;
  }
  const declineTk = e.target.closest("[data-inbox-decline-task]");
  if (declineTk) {
    e.preventDefault();
    const id = Number(declineTk.dataset.inboxDeclineTask);
    if (!Number.isNaN(id)) void declineTaskInvitation(id);
    return;
  }
  const cancelEv = e.target.closest("[data-inbox-cancel-event-invitation]");
  if (cancelEv) {
    e.preventDefault();
    const eventId = Number(cancelEv.dataset.inboxCancelEventInvitation);
    const userId = Number(cancelEv.dataset.inboxCancelEventUser);
    if (!Number.isNaN(eventId) && !Number.isNaN(userId)) {
      void cancelSentEventInvitation(eventId, userId);
    }
    return;
  }
  const cancelTk = e.target.closest("[data-inbox-cancel-task-invitation]");
  if (cancelTk) {
    e.preventDefault();
    const taskId = Number(cancelTk.dataset.inboxCancelTaskInvitation);
    const userId = Number(cancelTk.dataset.inboxCancelTaskUser);
    if (!Number.isNaN(taskId) && !Number.isNaN(userId)) {
      void cancelSentTaskInvitation(taskId, userId);
    }
    return;
  }
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
    return;
  }
  if (kind === "user") {
    void openUserDetail(id);
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
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.budget = payload.budget ? Number(payload.budget) : 0;
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);
  if (payload.start_time && payload.end_time && new Date(payload.end_time) < new Date(payload.start_time)) {
    setFormError(form, "Дата окончания мероприятия не может быть раньше даты начала");
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
    setFormError(form, `Ошибка создания мероприятия: ${error.message}`);
    notify(`Ошибка создания мероприятия: ${error.message}`, true);
  }
}

async function onTaskCreate(event) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);

  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    setFormError(form, "Выберите мероприятие");
    return;
  }
  const inviteUserId = el.taskCreateInviteSelect?.value ? Number(el.taskCreateInviteSelect.value) : null;
  payload.deadline = toIsoOrNull(payload.deadline);
  payload.start_time = toIsoOrNull(payload.start_time);
  payload.end_time = toIsoOrNull(payload.end_time);

  try {
    const created = await apiRequest(API.tasks, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    if (inviteUserId && created?.id) {
      await apiRequest(`${API.tasks}${created.id}/assignees`, {
        method: "POST",
        body: JSON.stringify({ user_id: inviteUserId })
      });
      notify("Задача создана, приглашение исполнителю отправлено");
    } else {
      notify("Задача создана");
    }
    form.reset();
    state.taskCreatePresetEventId = null;
    populateTaskEventOptions();
    await loadTaskCreateInviteOptions(null);
    await refreshData();
  } catch (error) {
    setFormError(form, `Ошибка создания задачи: ${error.message}`);
    notify(`Ошибка создания задачи: ${error.message}`, true);
  }
}

async function onTaskEventChange(event) {
  const eventId = Number(event.target.value);
  state.taskCreatePresetEventId = Number.isNaN(eventId) || !eventId ? null : eventId;
  await loadTaskCreateInviteOptions(state.taskCreatePresetEventId);
}

async function onUsersSearchSubmit(event) {
  event.preventDefault();
  const payload = serializeForm(event.target);
  state.usersSearch.id = (payload.id || "").trim();
  state.usersSearch.q = (payload.q || "").trim();
  state.usersSearch.speciality = (payload.speciality || "").trim();
  state.usersSearch.role = (payload.role || "").trim();
  await loadUsersPage({ resetPage: true });
}

async function onUsersListClick(event) {
  const addBtn = event.target.closest("[data-add-participant-user]");
  if (!addBtn) return;

  const userId = Number(addBtn.dataset.addParticipantUser);
  if (!userId) return;
  const fromSelect = Number(el.usersAddEventSelect?.value || 0);
  const targetEventId = (fromSelect > 0 ? fromSelect : state.participantsModeEventId) || 0;
  if (!targetEventId) {
    notify("Выберите мероприятие для добавления участника", true);
    return;
  }
  const roleSelect = document.querySelector(`[data-user-role-select="${userId}"]`);
  const role = roleSelect ? roleSelect.value : "viewer";

  try {
    const created = await apiRequest(`${API.events}${targetEventId}/participants`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role })
    });
    const msg =
      created && String(created.membership_status || "").toLowerCase() === "pending"
        ? "Приглашение в мероприятие отправлено"
        : "Участник добавлен";
    notify(msg);
  } catch (error) {
    notify(`Ошибка добавления участника: ${error.message}`, true);
  }
}

async function onAllocationEventChange(event) {
  const eventId = Number(event.target.value) || null;
  state.allocationPreset.eventId = eventId;
  state.allocationPreset.taskId = null;
  state.allocationPreset.resourceId = null;
  await populateAllocationTaskOptions(eventId, null);
  populateAllocationResourceOptions(eventId, null);
}

async function onAllocationTaskChange(event) {
  const taskId = Number(event.target.value) || null;
  state.allocationPreset.taskId = taskId;
  if (!taskId) return;
  let task;
  try {
    task = await apiRequest(`${API.tasks}${taskId}`);
  } catch {
    return;
  }
  if (!task) return;
  state.allocationPreset.eventId = task.event_id;
  if (el.allocationEventSelect) {
    el.allocationEventSelect.value = String(task.event_id);
  }
  await populateAllocationTaskOptions(task.event_id, taskId);
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
  setFormError(form, "");
  const payload = serializeForm(form);
  const eventId = Number(payload.event_id);
  payload.task_id = payload.task_id ? Number(payload.task_id) : null;
  payload.resource_id = Number(payload.resource_id);
  payload.quantity_used = payload.quantity_used ? Number(payload.quantity_used) : 1;
  payload.date_start = toIsoOrNull(payload.date_start);
  payload.date_end = toIsoOrNull(payload.date_end);

  if (!eventId || !payload.resource_id || !payload.date_start || !payload.date_end) {
    setFormError(form, "Заполните обязательные поля назначения");
    return;
  }

  try {
    await apiRequest(`${API.resources}allocations/`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
    notify("Назначение создано");
    form.reset();
    state.allocationPreset = { eventId: null, taskId: null, resourceId: null };
    populateAllocationEventOptions();
    void populateAllocationTaskOptions(null);
    populateAllocationResourceOptions(null);
  } catch (error) {
    setFormError(form, `Ошибка создания назначения: ${error.message}`);
    notify(`Ошибка создания назначения: ${error.message}`, true);
  }
}

async function onResourceCreate(event) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    setFormError(form, "Выберите мероприятие для ресурса");
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
    setFormError(form, `Ошибка создания ресурса: ${error.message}`);
    notify(`Ошибка создания ресурса: ${error.message}`, true);
  }
}

function clearAiDraft() {
  state.aiDraft = null;
  if (el.aiResult) {
    el.aiResult.innerHTML =
      '<p class="list-item-meta">Сгенерируйте план по форме выше. Черновик задач появится здесь до сохранения в базу.</p>';
  }
}

function renderAiDraft() {
  if (!el.aiResult || !state.aiDraft) return;
  const { event_id: eventId, event_title: eventTitle, event_name: eventName, tasks } = state.aiDraft;
  const rows = tasks
    .map((t, i) => {
      const st = toDatetimeLocalValue(t.start_time);
      const en = toDatetimeLocalValue(t.end_time);
      const dl = toDatetimeLocalValue(t.deadline);
      const pr = t.priority || "medium";
      return `
    <article class="list-item ai-draft-task" data-index="${i}">
      <label class="ai-draft-include-label"><input type="checkbox" class="ai-draft-include" checked /> Включить при сохранении</label>
      <label>Название<input type="text" class="ai-draft-title" value="${escapeHtml(t.title)}" maxlength="255" /></label>
      <label>Описание<textarea class="ai-draft-desc" rows="2">${escapeHtml(t.description || "")}</textarea></label>
      <label>Старт (план)<input type="datetime-local" class="ai-draft-start" value="${st}" /></label>
      <label>Окончание (план)<input type="datetime-local" class="ai-draft-end" value="${en}" /></label>
      <label>Дедлайн<input type="datetime-local" class="ai-draft-deadline" value="${dl}" /></label>
      <label>Приоритет
        <select class="ai-draft-priority">
          <option value="low" ${pr === "low" ? "selected" : ""}>${enumLabel("taskPriority", "low")}</option>
          <option value="medium" ${pr === "medium" ? "selected" : ""}>${enumLabel("taskPriority", "medium")}</option>
          <option value="high" ${pr === "high" ? "selected" : ""}>${enumLabel("taskPriority", "high")}</option>
        </select>
      </label>
    </article>`;
    })
    .join("");

  el.aiResult.innerHTML = `
    <div class="panel ai-draft-panel">
      <h3>Черновик: ${escapeHtml(eventName)}</h3>
      <p class="list-item-meta">Мероприятие: ${escapeHtml(eventTitle)}</p>
      <div class="detail-actions" style="margin:12px 0;flex-wrap:wrap;gap:8px">
        <button type="button" class="btn btn-primary" id="ai-draft-commit-btn">Добавить выбранные в БД</button>
        <button type="button" class="btn btn-muted" id="ai-draft-cancel-btn">Отменить черновик</button>
      </div>
      <div class="ai-draft-tasks">${rows}</div>
    </div>
  `;

  document.getElementById("ai-draft-commit-btn")?.addEventListener("click", () => void onAiDraftCommit());
  document.getElementById("ai-draft-cancel-btn")?.addEventListener("click", () => clearAiDraft());
}

function gatherAiDraftTasksPayload() {
  if (!state.aiDraft) return [];
  const eventId = state.aiDraft.event_id;
  const out = [];
  document.querySelectorAll(".ai-draft-task").forEach((article) => {
    const inc = article.querySelector(".ai-draft-include");
    if (!inc?.checked) return;
    const title = article.querySelector(".ai-draft-title")?.value?.trim() || "";
    if (!title) return;
    const desc = article.querySelector(".ai-draft-desc")?.value?.trim() || "";
    const start = toIsoOrNull(article.querySelector(".ai-draft-start")?.value);
    const end = toIsoOrNull(article.querySelector(".ai-draft-end")?.value);
    const deadline = toIsoOrNull(article.querySelector(".ai-draft-deadline")?.value);
    const priority = article.querySelector(".ai-draft-priority")?.value || "medium";
    if (!start || !end || !deadline) return;
    out.push({
      title,
      description: desc || null,
      event_id: eventId,
      start_time: start,
      end_time: end,
      deadline,
      priority
    });
  });
  return out;
}

function renderAiCommitResult(res) {
  if (!el.aiResult) return;
  const created = res.tasks || [];
  const errors = res.errors || [];
  const links = created
    .map(
      (t) =>
        `<p class="list-item-meta"><button type="button" class="entity-link" data-entity-link="task" data-id="${t.id}">${escapeHtml(t.title)}</button></p>`
    )
    .join("");
  const errHtml =
    errors.length > 0
      ? `<p class="list-item-meta" style="color:var(--danger)">Ошибки: ${escapeHtml(errors.join("; "))}</p>`
      : "";
  el.aiResult.innerHTML = `
    <div class="panel">
      <h3>Создано задач: ${created.length}</h3>
      ${links || '<p class="list-item-meta">Ни одна задача не была создана.</p>'}
      ${errHtml}
      <p class="list-item-meta" style="margin-top:12px"><button type="button" class="btn btn-muted" id="ai-draft-dismiss-result">Очистить результат</button></p>
    </div>
  `;
  document.getElementById("ai-draft-dismiss-result")?.addEventListener("click", () => clearAiDraft());
}

async function onAiDraftCommit() {
  if (!state.aiDraft) return;
  const tasks = gatherAiDraftTasksPayload();
  if (!tasks.length) {
    notify("Отметьте и заполните хотя бы одну задачу (название и все даты обязательны).", true);
    return;
  }
  const btn = document.getElementById("ai-draft-commit-btn");
  const prev = btn?.textContent;
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Сохранение…";
  }
  try {
    const res = await apiRequest(`${API.ai}/commit`, {
      method: "POST",
      body: JSON.stringify({ event_id: state.aiDraft.event_id, tasks })
    });
    state.aiDraft = null;
    notify(`Создано задач: ${(res.tasks || []).length}${(res.errors || []).length ? " (есть ошибки)" : ""}`);
    renderAiCommitResult(res);
    await refreshData();
  } catch (error) {
    notify(`Ошибка сохранения: ${error.message}`, true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = prev || "Добавить выбранные в БД";
    }
  }
}

async function onAiGenerate(event) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.event_id = Number(payload.event_id);
  if (!payload.event_id) {
    setFormError(form, "Выберите мероприятие для AI генерации");
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
    const tasks = result.tasks || [];
    state.aiDraft = {
      event_id: payload.event_id,
      event_title: getEventTitle(payload.event_id),
      event_name: result.event_name || "План",
      tasks
    };
    renderAiDraft();
    notify(`Сгенерировано задач в черновике: ${tasks.length}. Проверьте и сохраните в базу.`);
  } catch (error) {
    setFormError(form, `Ошибка AI генерации: ${error.message}`);
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
  setFormError(form, "");
  const payload = serializeForm(form);
  payload.phone = payload.phone?.trim() || null;
  payload.speciality = payload.speciality?.trim() || null;
  payload.bio = payload.bio?.trim() || null;
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
    setFormError(form, `Ошибка создания профиля: ${error.message}`);
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
    setText("cabinet-view-system-role", state.role ? enumLabel("participantRole", state.role) : "—");
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
    const roleNode = document.getElementById("cabinet-view-system-role");
    if (roleNode) roleNode.textContent = state.role ? enumLabel("participantRole", state.role) : "—";
    notify(`Не удалось загрузить профиль: ${error.message}`, true);
  }
}

async function onProfileCabinetSave(event) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  if (!state.profileId) {
    setFormError(form, "Сначала создайте профиль");
    return;
  }
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
    setFormError(form, `Ошибка сохранения профиля: ${error.message}`);
    notify(`Ошибка сохранения профиля: ${error.message}`, true);
  }
}

async function onAccountCabinetSave(event) {
  event.preventDefault();
  const form = event.target;
  setFormError(form, "");
  const raw = serializeForm(form);
  const emailTrim = raw.email?.trim() || "";
  const newPassword = raw.new_password?.trim() || "";
  const currentPassword = raw.current_password?.trim() || "";

  if (!emailTrim && !newPassword) {
    setFormError(form, "Укажите новый email и/или новый пароль");
    return;
  }
  if (!currentPassword) {
    setFormError(form, "Введите текущий пароль");
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
    setFormError(form, `Ошибка учётной записи: ${error.message}`);
    notify(`Ошибка учётной записи: ${error.message}`, true);
  }
}

async function onTasksFilterSubmit(event) {
  event.preventDefault();
  state.tasksFilters.eventId = document.getElementById("tasks-filter-event")?.value || "";
  state.tasksFilters.status = document.getElementById("tasks-filter-status")?.value || "";
  state.tasksFilters.priority = document.getElementById("tasks-filter-priority")?.value || "";
  state.tasksFilters.q = document.getElementById("tasks-filter-q")?.value || "";
  const ps = document.getElementById("tasks-page-size");
  if (ps) state.tasksLimit = Math.min(100, Math.max(1, Number(ps.value) || 25));
  await loadTasksPage({ resetPage: true });
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
  const tasksFilterForm = document.getElementById("tasks-filter-form");
  if (tasksFilterForm) {
    tasksFilterForm.addEventListener("submit", (e) => {
      void onTasksFilterSubmit(e);
    });
  }
  const tasksPrev = document.getElementById("tasks-page-prev");
  if (tasksPrev) {
    tasksPrev.addEventListener("click", () => {
      state.tasksSkip = Math.max(0, state.tasksSkip - state.tasksLimit);
      void loadTasksPage();
    });
  }
  const tasksNext = document.getElementById("tasks-page-next");
  if (tasksNext) {
    tasksNext.addEventListener("click", () => {
      if (state.tasksSkip + state.tasksLimit < state.tasksTotal) {
        state.tasksSkip += state.tasksLimit;
        void loadTasksPage();
      }
    });
  }
  const tasksPageSize = document.getElementById("tasks-page-size");
  if (tasksPageSize) {
    tasksPageSize.addEventListener("change", (e) => {
      state.tasksLimit = Math.min(100, Math.max(1, Number(e.target.value) || 25));
      state.tasksSkip = 0;
      void loadTasksPage();
    });
  }
  document.getElementById("task-event-select").addEventListener("change", (e) => {
    void onTaskEventChange(e);
  });
  document.getElementById("users-search-form").addEventListener("submit", (e) => {
    void onUsersSearchSubmit(e);
  });
  const usersPrev = document.getElementById("users-page-prev");
  if (usersPrev) {
    usersPrev.addEventListener("click", () => {
      state.usersSkip = Math.max(0, state.usersSkip - state.usersLimit);
      void loadUsersPage();
    });
  }
  const usersNext = document.getElementById("users-page-next");
  if (usersNext) {
    usersNext.addEventListener("click", () => {
      if (state.usersSkip + state.usersLimit < state.usersTotal) {
        state.usersSkip += state.usersLimit;
        void loadUsersPage();
      }
    });
  }
  const usersPageSize = document.getElementById("users-page-size");
  if (usersPageSize) {
    usersPageSize.addEventListener("change", (e) => {
      state.usersLimit = Math.min(100, Math.max(1, Number(e.target.value) || 25));
      state.usersSkip = 0;
      void loadUsersPage();
    });
  }
  document.getElementById("allocation-form").addEventListener("submit", (e) => {
    void onAllocationCreate(e);
  });
  document.getElementById("allocation-event-select").addEventListener("change", (e) => {
    void onAllocationEventChange(e);
  });
  document.getElementById("allocation-task-select").addEventListener("change", (e) => {
    void onAllocationTaskChange(e);
  });
  document.getElementById("resource-form").addEventListener("submit", onResourceCreate);
  document.getElementById("ai-form").addEventListener("submit", onAiGenerate);
  document.getElementById("logout-btn").addEventListener("click", () => {
    clearSession();
    syncAuthUi();
    state.events = [];
    state.tasksPage = [];
    state.tasksTotal = 0;
    state.taskMetrics = { total: 0, overdue: 0 };
    state.resources = [];
    state.usersList = [];
    state.usersTotal = 0;
    state.usersSkip = 0;
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
    renderEvents();
    renderTasks();
    renderResources();
    await refreshData();
  } else {
    notify("Войдите, чтобы загрузить данные");
  }
}

bootstrap();
