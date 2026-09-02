const state = {
  agents: [],
  lastTask: null,
  activeTaskId: null,
  mentionOptions: [],
  activeMentionIndex: 0,
};

const els = {
  agentList: document.getElementById("agentList"),
  chatForm: document.getElementById("chatForm"),
  messageInput: document.getElementById("messageInput"),
  mentionMenu: document.getElementById("mentionMenu"),
  messages: document.getElementById("messages"),
  statusText: document.getElementById("statusText"),
  refreshButton: document.getElementById("refreshButton"),
  taskView: document.getElementById("taskView"),
  eventList: document.getElementById("eventList"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

function nowText() {
  return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function linkify(text) {
  const escaped = escapeHtml(text);
  return escaped.replace(/(https?:\/\/[^\s]+|\/rss-digests\/[^\s]+)/g, (url) => {
    const href = url.startsWith("/") ? url : url;
    return `<a href="${href}" target="_blank" rel="noreferrer">${url}</a>`;
  });
}

function renderInlineMarkdown(text) {
  let html = linkify(text);
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return html;
}

function renderMarkdown(markdown) {
  const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let paragraph = [];
  let list = null;
  let code = null;

  function flushParagraph() {
    if (!paragraph.length) return;
    blocks.push(`<p>${renderInlineMarkdown(paragraph.join(" "))}</p>`);
    paragraph = [];
  }

  function flushList() {
    if (!list) return;
    const tag = list.type === "ol" ? "ol" : "ul";
    blocks.push(`<${tag}>${list.items.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join("")}</${tag}>`);
    list = null;
  }

  function flushCode() {
    if (code === null) return;
    blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
    code = null;
  }

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      if (code === null) {
        flushParagraph();
        flushList();
        code = [];
      } else {
        flushCode();
      }
      continue;
    }

    if (code !== null) {
      code.push(line);
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      blocks.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    const unordered = trimmed.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      flushParagraph();
      if (!list || list.type !== "ul") {
        flushList();
        list = { type: "ul", items: [] };
      }
      list.items.push(unordered[1]);
      continue;
    }

    const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
    if (ordered) {
      flushParagraph();
      if (!list || list.type !== "ol") {
        flushList();
        list = { type: "ol", items: [] };
      }
      list.items.push(ordered[1]);
      continue;
    }

    if (trimmed.startsWith("> ")) {
      flushParagraph();
      flushList();
      blocks.push(`<blockquote>${renderInlineMarkdown(trimmed.slice(2))}</blockquote>`);
      continue;
    }

    flushList();
    paragraph.push(trimmed);
  }

  flushCode();
  flushParagraph();
  flushList();
  return blocks.join("");
}

function appendMessage(kind, author, body) {
  const node = document.createElement("article");
  node.className = `message ${kind}`;
  node.innerHTML = `
    <div class="message-head">
      <strong>${escapeHtml(author)}</strong>
      <span>${nowText()}</span>
    </div>
    <div class="message-body">${renderMarkdown(body)}</div>
  `;
  els.messages.appendChild(node);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function insertMention(agentId) {
  const mention = `@${agentId} `;
  const current = els.messageInput.value.trimStart();
  const withoutOldMention = current.replace(/^@[a-zA-Z0-9_\-]+\s*/, "");
  els.messageInput.value = mention + withoutOldMention;
  hideMentionMenu();
  els.messageInput.focus();
}

function mentionChoices() {
  return state.agents.map((agent) => ({
    ...agent,
    mention_id: agent.agent_id,
  }));
}

function mentionQuery() {
  const value = els.messageInput.value;
  const cursor = els.messageInput.selectionStart || 0;
  const beforeCursor = value.slice(0, cursor);
  const match = beforeCursor.match(/(^|\s)@([a-zA-Z0-9_\-]*)$/);
  return match ? match[2].toLowerCase() : null;
}

function hideMentionMenu() {
  els.mentionMenu.hidden = true;
  els.mentionMenu.innerHTML = "";
  state.mentionOptions = [];
  state.activeMentionIndex = 0;
}

function chooseMention(option) {
  const value = els.messageInput.value;
  const cursor = els.messageInput.selectionStart || 0;
  const beforeCursor = value.slice(0, cursor);
  const afterCursor = value.slice(cursor);
  const replacement = `@${option.agent_id} `;
  const replacedBefore = beforeCursor.replace(/(^|\s)@[a-zA-Z0-9_\-]*$/, (prefix) => {
    const leadingSpace = prefix.startsWith(" ") ? " " : "";
    return leadingSpace + replacement;
  });
  els.messageInput.value = replacedBefore + afterCursor.trimStart();
  hideMentionMenu();
  els.messageInput.focus();
}

function renderMentionMenu() {
  const query = mentionQuery();
  if (query === null) {
    hideMentionMenu();
    return;
  }

  state.mentionOptions = mentionChoices().filter((option) => {
    const haystack = `${option.agent_id} ${option.name}`.toLowerCase();
    return haystack.includes(query);
  });
  state.activeMentionIndex = Math.min(state.activeMentionIndex, Math.max(state.mentionOptions.length - 1, 0));

  if (!state.mentionOptions.length) {
    hideMentionMenu();
    return;
  }

  els.mentionMenu.innerHTML = "";
  for (const [index, option] of state.mentionOptions.entries()) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `mention-option${index === state.activeMentionIndex ? " active" : ""}`;
    item.innerHTML = `
      <strong>@${escapeHtml(option.agent_id)} · ${escapeHtml(option.name)}</strong>
      <span>${escapeHtml(option.description || "")}</span>
    `;
    item.addEventListener("mousedown", (event) => {
      event.preventDefault();
      chooseMention(option);
    });
    els.mentionMenu.appendChild(item);
  }
  els.mentionMenu.hidden = false;
}

function renderAgents() {
  els.agentList.innerHTML = "";

  for (const agent of state.agents) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "agent-item";
    item.innerHTML = `
      <div class="agent-name">${escapeHtml(agent.name)}</div>
      <div class="agent-meta">@${escapeHtml(agent.agent_id)} | ${escapeHtml(agent.memory_policy)}</div>
      <div class="agent-meta">${escapeHtml(agent.description)}</div>
    `;
    item.addEventListener("click", () => insertMention(agent.agent_id));
    els.agentList.appendChild(item);
  }
}

function renderTask() {
  if (!state.lastTask) {
    els.taskView.textContent = "Нет задач";
    return;
  }

  const task = state.lastTask;
  els.taskView.innerHTML = `
    <div class="task-card">
      <strong>${escapeHtml(task.title)}</strong>
      <div>Агент: ${escapeHtml(task.agent_id)}</div>
      <div>Статус：${escapeHtml(task.status)}</div>
      <div>ID задачи: ${escapeHtml(task.task_id)}</div>
    </div>
  `;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function waitForTask(taskId) {
  while (true) {
    const task = await api(`/tasks/${taskId}`);
    state.lastTask = task;
    renderTask();

    if (task.status === "completed" || task.status === "failed") {
      return task;
    }

    await refreshEvents();
    await sleep(1500);
  }
}

async function refreshEvents() {
  const data = await api("/events?limit=20");
  els.eventList.innerHTML = "";

  if (!data.events.length) {
    els.eventList.textContent = "Нет событий";
    return;
  }

  for (const event of data.events.slice().reverse()) {
    const item = document.createElement("div");
    item.className = "event-item";
    item.innerHTML = `
      <div class="event-type">${escapeHtml(event.type)}</div>
      <div>${escapeHtml(event.agent_id || "system")}</div>
      <div>${escapeHtml(event.timestamp)}</div>
    `;
    els.eventList.appendChild(item);
  }
}

async function loadAgents() {
  const data = await api("/agents");
  state.agents = data.agents;
  renderAgents();
  renderMentionMenu();
  els.statusText.textContent = `Подключено ${data.total} агентов`;
}

function parseTarget(rawText) {
  const text = rawText.trim();
  const match = text.match(/^@([a-zA-Z0-9_\-]+)\s*(.*)$/);
  if (!match) {
    return { agentId: null, message: text };
  }

  const mention = match[1];
  const message = match[2].trim();
  return { agentId: mention, message };
}

async function sendMessage(rawText) {
  const { agentId, message } = parseTarget(rawText);
  if (!message) {
    appendMessage("system", "Система", "Введите сообщение. Пример: @deep_research исследовать тему");
    return;
  }

  if (!agentId) {
    appendMessage("system", "Система", "Сначала выберите агента через @, например: @deep_research тема или @rss_digest дайджест.");
    return;
  }

  const agent = state.agents.find((item) => item.agent_id === agentId);
  if (!agent) {
    appendMessage("system", "Система", `Агент @${agentId} не найден. Нажмите на агента слева для вставки @.`);
    return;
  }

  appendMessage("user", "Вы", `@${agentId} ${message}`);
  appendMessage("system", "Система", `${agent.name} запущен в фоне — можно отправить следующее сообщение.`);

  const task = await api("/tasks", {
    method: "POST",
    body: JSON.stringify({
      title: `Диалог с ${agent.name}`,
      input: message,
      agent_id: agentId,
      metadata: { group_id: "default", mention: agentId },
    }),
  });
  state.lastTask = task;
  renderTask();

  const running = await api(`/tasks/${task.task_id}/run`, { method: "POST" });
  state.lastTask = running;
  state.activeTaskId = running.task_id;
  renderTask();

  const completed = await waitForTask(task.task_id);
  state.lastTask = completed;
  state.activeTaskId = null;
  renderTask();
  if (completed.status === "failed") {
    appendMessage("system", "Система", `${agent.name} — ошибка: ${completed.error || "неизвестная ошибка"}`);
  } else {
    appendMessage("agent", agent.name, completed.output || "(нет вывода)");
  }
  await refreshEvents();
}

els.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = els.messageInput.value.trim();
  if (!text) return;

  els.messageInput.value = "";
  try {
    await sendMessage(text);
  } catch (error) {
    appendMessage("system", "Система", `Ошибка запроса：${error.message}`);
  } finally {
    els.messageInput.focus();
  }
});

els.messageInput.addEventListener("input", renderMentionMenu);
els.messageInput.addEventListener("click", renderMentionMenu);
els.messageInput.addEventListener("blur", () => {
  window.setTimeout(hideMentionMenu, 120);
});
els.messageInput.addEventListener("keydown", (event) => {
  if (els.mentionMenu.hidden) return;

  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.activeMentionIndex = (state.activeMentionIndex + 1) % state.mentionOptions.length;
    renderMentionMenu();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    state.activeMentionIndex =
      (state.activeMentionIndex - 1 + state.mentionOptions.length) % state.mentionOptions.length;
    renderMentionMenu();
  } else if (event.key === "Enter" || event.key === "Tab") {
    event.preventDefault();
    chooseMention(state.mentionOptions[state.activeMentionIndex]);
  } else if (event.key === "Escape") {
    hideMentionMenu();
  }
});

els.refreshButton.addEventListener("click", async () => {
  try {
    await loadAgents();
    await refreshEvents();
    appendMessage("system", "Система", "Агенты и журнал событий обновлены.");
  } catch (error) {
    appendMessage("system", "Система", `Ошибка обновления: ${error.message}`);
  }
});

async function boot() {
  try {
    await loadAgents();
    await refreshEvents();
    appendMessage("system", "Система", "Режим чата готов. Введите @ и выберите агента.");
  } catch (error) {
    els.statusText.textContent = "Не удалось подключиться к бэкенду";
    appendMessage("system", "Система", `Не удалось запустить：${error.message}`);
  }
}

boot();
