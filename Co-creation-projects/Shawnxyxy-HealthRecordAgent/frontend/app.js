const API_BASE = "http://127.0.0.1:8000";
const USER_ID_STORAGE_KEY = "healthRecordAgent_userId";
const LAST_DIET_RUN_KEY = "healthRecordAgent_lastDietRunId";
const DEV_MODE_STORAGE_KEY = "healthRecordAgent_devMode";
/** 兼容旧版「技术详情」开关 */
const LEGACY_TECH_STORAGE_KEY = "healthRecordAgent_showTech";

function isDeveloperMode() {
    const el = document.getElementById("devModeToggle");
    return !!(el && el.checked);
}

function getUserIdOrEmpty() {
    return document.getElementById("userId")?.value?.trim() || "";
}

/** 体检Анализ进度：默认对用户显示中文步骤名 */
function getHealthProgressAgents() {
    if (isDeveloperMode()) {
        return [
            { key: "PlannerAgent", label: "PlannerAgent Планирование" },
            { key: "HealthIndicatorAgent", label: "HealthIndicatorAgent Показатель" },
            { key: "RiskAssessmentAgent", label: "RiskAssessmentAgent — риски" },
            { key: "AdviceAgent", label: "AdviceAgent Рекомендации" },
            { key: "ReportAgent", label: "ReportAgent Отчёт" },
        ];
    }
    return [
        { key: "PlannerAgent", label: "Планирование" },
        { key: "HealthIndicatorAgent", label: "Интерпретация показателей" },
        { key: "RiskAssessmentAgent", label: "Оценка рисков" },
        { key: "AdviceAgent", label: "Рекомендации" },
        { key: "ReportAgent", label: "Итоговый отчёт" },
    ];
}

function getUserId() {
    const el = document.getElementById("userId");
    const raw = el ? el.value.trim() : "";
    if (!raw) {
        alert("Введите ID пользователя");
        return null;
    }
    try {
        localStorage.setItem(USER_ID_STORAGE_KEY, raw);
    } catch (_) { /* ignore */ }
    return raw;
}

function setTab(name) {
    const tabs = ["analysis", "diet", "history"];
    const n = tabs.includes(name) ? name : "analysis";
    tabs.forEach((t) => {
        const panel = document.getElementById(`tab-${t}`);
        if (panel) panel.classList.toggle("hidden", t !== n);
    });
    document.querySelectorAll(".tab-segment [role='tab']").forEach((btn) => {
        const on = btn.dataset.tab === n;
        btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    if (`#${n}` !== location.hash) {
        history.replaceState(null, "", `#${n}`);
    }
    if (n === "diet") {
        refreshReflectRunOptions();
    }
}

function tabFromHash() {
    const h = (location.hash || "").replace(/^#/, "").toLowerCase();
    if (h === "diet" || h === "history" || h === "analysis") return h;
    return "analysis";
}

document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("userId");
    if (el) {
        try {
            const saved = localStorage.getItem(USER_ID_STORAGE_KEY);
            if (saved) el.value = saved;
        } catch (_) { /* ignore */ }
    }

    setTab(tabFromHash());
    window.addEventListener("hashchange", () => setTab(tabFromHash()));

    document.querySelectorAll(".tab-segment [data-tab]").forEach((btn) => {
        btn.addEventListener("click", () => setTab(btn.dataset.tab || "analysis"));
    });

    const devCb = document.getElementById("devModeToggle");
    if (devCb) {
        try {
            const dm = localStorage.getItem(DEV_MODE_STORAGE_KEY);
            const legacy = localStorage.getItem(LEGACY_TECH_STORAGE_KEY);
            if (dm === "1" || legacy === "1") devCb.checked = true;
        } catch (_) { /* ignore */ }
        devCb.addEventListener("change", () => {
            try {
                localStorage.setItem(DEV_MODE_STORAGE_KEY, devCb.checked ? "1" : "0");
            } catch (_) { /* ignore */ }
            refreshReflectRunOptions();
        });
    }

    const dlg = document.getElementById("reflectPromptDialog");
    const go = document.getElementById("reflectDialogGo");
    const later = document.getElementById("reflectDialogLater");
    if (go) {
        go.addEventListener("click", () => {
            if (dlg && typeof dlg.close === "function") dlg.close();
            focusFeedbackSection();
        });
    }
    if (later) {
        later.addEventListener("click", () => {
            if (dlg && typeof dlg.close === "function") dlg.close();
        });
    }

    document.querySelectorAll('input[name="reflectFollowedChoice"]').forEach((el) => {
        el.addEventListener("change", syncReflectReasonVisibility);
    });
    syncReflectReasonVisibility();
});

/** 选「否」时展示未执行原因；选「是」时隐藏并Очистить原因（后端会将 reason 置为 executed_ok）。 */
function syncReflectReasonVisibility() {
    const yes = document.getElementById("reflectFollowedYes");
    const no = document.getElementById("reflectFollowedNo");
    const block = document.getElementById("reflectReasonBlock");
    const sel = document.getElementById("reflectReasonCode");
    const detail = document.getElementById("reflectDetail");
    if (!block || !sel) return;
    if (no?.checked) {
        block.classList.remove("hidden");
    } else {
        block.classList.add("hidden");
        sel.value = "";
        if (detail) detail.value = "";
    }
}

/** 拉取近期Рекомендации по питанию，填充「反馈」下拉的选项；preferredRunId 优先选中（如刚生成的一条）。 */
async function refreshReflectRunOptions(preferredRunId) {
    const sel = document.getElementById("reflectRunSelect");
    if (!sel) return;

    const userId = getUserIdOrEmpty();
    sel.innerHTML = "";

    const addPlaceholder = (text, disabled = true) => {
        const o = document.createElement("option");
        o.value = "";
        o.textContent = text;
        if (disabled) o.disabled = true;
        o.selected = true;
        sel.appendChild(o);
    };

    if (!userId) {
        addPlaceholder("Сначала введите ID пользователя");
        return;
    }

    try {
        const res = await fetch(
            `${API_BASE}/api/diet/users/${encodeURIComponent(userId)}/runs?limit=20`
        );
        const data = await res.json().catch(() => ({}));
        const items = data.items || [];
        if (!items.length) {
            addPlaceholder("Нет рекомендаций — сгенерируйте первую");
            return;
        }

        const dev = isDeveloperMode();
        items.forEach((row) => {
            const o = document.createElement("option");
            o.value = row.run_id;
            let label = "";
            try {
                const t = row.created_at
                    ? new Date(row.created_at).toLocaleString("zh-CN", {
                          month: "2-digit",
                          day: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                      })
                    : "";
                const tp =
                    row.total_protein != null
                        ? `~${row.total_protein} г белка`
                        : "Рекомендации по питанию";
                label = t ? `${t} · ${tp}` : tp;
                if (dev) label += ` · ${row.run_id}`;
            } catch (_) {
                label = row.run_id;
            }
            o.textContent = label;
            sel.appendChild(o);
        });

        const pick =
            preferredRunId ||
            (() => {
                try {
                    return localStorage.getItem(LAST_DIET_RUN_KEY);
                } catch (_) {
                    return null;
                }
            })();
        if (pick && Array.from(sel.options).some((opt) => opt.value === pick)) {
            sel.value = pick;
        }
    } catch (e) {
        console.error(e);
        addPlaceholder("Не удалось загрузить список — повторите");
    }
}

function openReflectPromptDialog() {
    const dlg = document.getElementById("reflectPromptDialog");
    if (dlg && typeof dlg.showModal === "function") {
        dlg.showModal();
    } else {
        focusFeedbackSection();
    }
}

function focusFeedbackSection() {
    const h = document.getElementById("feedbackSectionTitle");
    h?.scrollIntoView({ behavior: "smooth", block: "start" });
    const first = document.getElementById("reflectRunSelect");
    if (first) {
        setTimeout(() => first.focus(), 400);
    }
}

function renderMealPlan(mp) {
    if (!mp) return "<p>(нет meal_plan)</p>";
    const tips = Array.isArray(mp.tips) ? mp.tips.filter(Boolean).join("；") : "";
    let h = `<p><strong>Оценка общего белка</strong>：${mp.total_est_protein_g ?? "—"} g</p><ul class="meal-plan-list">`;
    (mp.items || []).forEach((it) => {
        h += `<li><strong>${escapeHtml(it.name || "")}</strong> — ${escapeHtml(it.portion || "")}`;
        if (it.est_protein_g != null) h += ` (~<strong>${it.est_protein_g}</strong> г белка)`;
        if (it.why) h += `<br><span class="muted-why">${escapeHtml(it.why)}</span>`;
        h += "</li>";
    });
    h += "</ul>";
    if (tips) h += `<p class="meal-tips"><strong>Подсказка</strong>：${escapeHtml(tips)}</p>`;
    return h;
}

function escapeHtml(s) {
    if (!s) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
}

async function recommendDiet() {
    const userId = getUserId();
    if (!userId) return;

    const statusEl = document.getElementById("dietStatus");
    const outEl = document.getElementById("dietResult");
    if (!statusEl || !outEl) return;

    statusEl.textContent = isDeveloperMode()
        ? "⏳ Planning + ReAct (может занять время)…"
        : "⏳ Генерация рекомендаций…";
    outEl.classList.add("hidden");
    outEl.innerHTML = "";

    const foodLog = document.getElementById("dietFoodLog")?.value?.trim() || "";
    if (!foodLog) {
        statusEl.textContent = "⚠️ Сначала укажите, что съели сегодня";
        return;
    }

    const body = {
        user_id: userId,
        context: {
            today_food_log_text: foodLog,
            goal: document.getElementById("dietGoal")?.value || "muscle_gain",
            channels: ["convenience_store", "delivery"],
            activity_context: document.getElementById("dietActivityContext")?.value?.trim() || "",
            free_notes: document.getElementById("dietNotes")?.value?.trim() || "",
        },
    };

    try {
        const res = await fetch(`${API_BASE}/api/diet/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.detail ? JSON.stringify(data.detail) : `HTTP ${res.status}`);
        }

        const runId = data.run_id;
        try {
            localStorage.setItem(LAST_DIET_RUN_KEY, runId);
        } catch (_) { /* ignore */ }
        const planning = data.planning || {};
        const ver = data.schema_version || "1";
        const mode = data.pipeline_mode || "legacy";
        const tech = isDeveloperMode();

        let html = "";
        if (tech) {
            html += `<p><strong>run_id</strong>：<code>${escapeHtml(runId)}</code> &nbsp; <small>schema=${escapeHtml(String(ver))} / ${escapeHtml(String(mode))}</small></p>`;
        }
        if (data.degraded) {
            html += tech
                ? `<p class="banner banner-warning"><strong>Пониженный режим</strong>：Часть этапов — по шаблону, см. <code>errors</code>。</p>`
                : `<p class="banner banner-warning"><strong>Примечание</strong>：Часть контента дополнена правилами — ориентируйтесь на список действий.</p>`;
        }
        if (planning.reasoning) {
            html += tech
                ? `<p><strong>Planning (Nutritionist)</strong>: ${escapeHtml(planning.reasoning)}</p>`
                : `<p><strong>Сводка по питанию</strong>：${escapeHtml(planning.reasoning)}</p>`;
        }
        const ns = data.nutrition_summary || {};
        if (!tech) {
            html += `<p><strong>Оценка питания за сегодня</strong>：белки ${escapeHtml(String(ns.protein_g ?? 0))} г, углеводы ${escapeHtml(String(ns.carb_g ?? 0))} г, жиры ${escapeHtml(String(ns.fat_g ?? 0))} г, калории ${escapeHtml(String(ns.calories_kcal ?? 0))} kcal</p>`;
        } else {
            html += `<details class="diet-trace"><summary>Разбор продуктов и оценка питания</summary><pre style="white-space:pre-wrap;max-height:220px;overflow:auto;">${escapeHtml(JSON.stringify({ food_parse: data.food_parse, nutrition_summary: data.nutrition_summary }, null, 2))}</pre></details>`;
        }
        const hx = data.habit_extras;
        if (hx && hx.reflect_alignment) {
            html += tech
                ? `<p><strong>Habit · Reflect</strong>: ${escapeHtml(hx.reflect_alignment)}</p>`
                : `<p><strong>Учёт прошлой обратной связи</strong>：${escapeHtml(hx.reflect_alignment)}</p>`;
            if (hx.execution_hints && hx.execution_hints.length) {
                html += `<p><strong>Подсказки по выполнению</strong>：${escapeHtml(hx.execution_hints.join("；"))}</p>`;
            }
        }
        html += `<h4>Рекомендуемый план</h4>${renderMealPlan(data.meal_plan)}`;

        if (tech) {
            if (data.errors && data.errors.length) {
                html += `<details class="diet-trace"><summary>错误记录（${data.errors.length}）</summary><pre style="white-space:pre-wrap;max-height:200px;overflow:auto;">${escapeHtml(JSON.stringify(data.errors, null, 2))}</pre></details>`;
            }
            if (data.reflect_memory_used) {
                html += `<details class="diet-trace"><summary>已注入的 Reflect Память摘要</summary><pre style="white-space:pre-wrap;">${escapeHtml(String(data.reflect_memory_used))}</pre></details>`;
            }
            if (data.react_trace && data.react_trace.length) {
                html += `<details class="diet-trace"><summary>流水线轨迹（${data.react_trace.length} сегм.）</summary><pre style="white-space:pre-wrap;max-height:280px;overflow:auto;">${escapeHtml(JSON.stringify(data.react_trace, null, 2))}</pre></details>`;
            }
        }

        outEl.innerHTML = html;
        outEl.classList.remove("hidden");
        statusEl.textContent = data.degraded
            ? tech
                ? "⚠️ Рекомендация готова (с понижением, записано)"
                : "⚠️ Рекомендация сохранена (частично автоматически)"
            : tech
              ? "✅ Рекомендация готова (записано)"
              : "✅ Рекомендация сохранена";

        await refreshReflectRunOptions(runId);
        openReflectPromptDialog();
    } catch (e) {
        console.error(e);
        statusEl.textContent = "❌ Ошибка запроса";
        outEl.innerHTML = `<p class="banner-error">${escapeHtml(e.message || String(e))}</p>`;
        outEl.classList.remove("hidden");
    }
}

async function submitDietReflect() {
    const userId = getUserId();
    if (!userId) return;

    const runId = document.getElementById("reflectRunSelect")?.value?.trim();
    if (!runId) {
        alert("Выберите рекомендацию в списке или сгенерируйте новую");
        return;
    }

    const yes = document.getElementById("reflectFollowedYes")?.checked;
    const no = document.getElementById("reflectFollowedNo")?.checked;
    if (!yes && !no) {
        alert("Выберите, выполнили ли рекомендацию");
        return;
    }
    const followed = !!yes;
    let reasonCode = null;
    let detail = null;
    if (followed) {
        reasonCode = null;
        detail = null;
    } else {
        reasonCode = document.getElementById("reflectReasonCode")?.value?.trim() || null;
        if (!reasonCode) {
            alert("Укажите причину невыполнения");
            return;
        }
        detail = document.getElementById("reflectDetail")?.value?.trim() || null;
    }

    const statusEl = document.getElementById("dietStatus");
    if (statusEl) statusEl.textContent = "⏳ Сохранение отзыва…";

    try {
        const res = await fetch(`${API_BASE}/api/diet/reflect`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                diet_run_id: runId,
                followed,
                reason_code: reasonCode,
                reason_detail: detail,
            }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.detail ? JSON.stringify(data.detail) : `HTTP ${res.status}`);
        }
        if (statusEl) {
            statusEl.textContent = isDeveloperMode()
                ? `✅ Reflect 已Сохранить（id=${data.reflect_id}），下次推荐会读取`
                : "✅ Отзыв сохранён — учтётся в следующий раз";
        }
        await loadDietHistory();
    } catch (e) {
        console.error(e);
        if (statusEl) statusEl.textContent = "❌ Не удалось сохранить：" + (e.message || e);
    }
}

async function loadDietHistory() {
    const userId = getUserId();
    if (!userId) return;

    const pre = document.getElementById("dietHistoryPre");
    const hint = document.getElementById("historyEmptyHint");
    const summaryEl = document.getElementById("historySummary");
    const rawDetails = document.getElementById("historyRawDetails");
    if (!pre) return;

    if (hint) hint.classList.add("hidden");
    if (summaryEl) {
        summaryEl.classList.remove("hidden");
        summaryEl.textContent = "Загрузка…";
    }
    if (rawDetails) {
        rawDetails.classList.add("hidden");
        rawDetails.open = false;
    }
    pre.textContent = "";

    try {
        const [r1, r2] = await Promise.all([
            fetch(`${API_BASE}/api/diet/users/${encodeURIComponent(userId)}/runs?limit=15`).then((r) => r.json()),
            fetch(`${API_BASE}/api/diet/users/${encodeURIComponent(userId)}/reflect_history?limit=15`).then((r) => r.json()),
        ]);
        const n1 = (r1.items || []).length;
        const n2 = (r2.items || []).length;
        if (summaryEl) {
            summaryEl.textContent = `已加载 ${n1} 条Рекомендации по питанию记录、${n2} 条反馈记录。`;
        }
        pre.textContent = JSON.stringify({ diet_runs: r1, reflect: r2 }, null, 2);
        if (rawDetails) {
            if (isDeveloperMode()) {
                rawDetails.classList.remove("hidden");
            } else {
                rawDetails.classList.add("hidden");
            }
        }
    } catch (e) {
        if (summaryEl) {
            summaryEl.textContent = "Ошибка загрузки: " + (e.message || e);
        }
        pre.textContent = "";
    }
}
/**
 * 显示 / 更新多 Agent 进度。仅在 agents Кол-во变化时重建 DOM，轮询时只更新Статус文案，避免整表闪烁。
 */
function showAgentProgress(agentContainer, agents, statusFunc) {
    const getStatus =
        typeof statusFunc === "function" ? statusFunc : () => statusFunc;
    const needRebuild =
        agentContainer.children.length !== agents.length ||
        agents.some((a, i) => agentContainer.children[i]?.dataset?.agentKey !== a.key);

    if (needRebuild) {
        agentContainer.innerHTML = "";
        agents.forEach((agent) => {
            const li = document.createElement("li");
            li.dataset.agentKey = agent.key;
            const labelSpan = document.createElement("span");
            labelSpan.className = "agent-progress-label";
            labelSpan.textContent = agent.label;
            const statusSpan = document.createElement("span");
            statusSpan.className = "agent-progress-status";
            statusSpan.textContent = getStatus(agent.key);
            li.appendChild(labelSpan);
            li.appendChild(document.createTextNode("："));
            li.appendChild(statusSpan);
            agentContainer.appendChild(li);
        });
        return;
    }

    agents.forEach((agent, i) => {
        const li = agentContainer.children[i];
        const statusSpan = li?.querySelector?.(".agent-progress-status");
        if (statusSpan) statusSpan.textContent = getStatus(agent.key);
    });
}

// 公共函数：Отправить任务并轮询Статус
async function submitAndPollTask(url, body, agents, resultCard, reportDiv, analysisDiv, progressList, loadingText, doneText, errorText) {
    reportDiv.innerHTML = "";
    analysisDiv.innerText = loadingText;
    progressList.classList.remove("hidden");
    showAgentProgress(progressList, agents, () => "⏳ Выполняется...");
    resultCard.classList.add("hidden");

    try {
        const response = await fetch(url, body);
        if (!response.ok) throw new Error(`服务器返回错误Статус：${response.status}`);

        const data = await response.json();
        const taskId = data.task_id;

        let taskStatus = await fetch(`${API_BASE}/api/health/task_status/${taskId}`).then(r => r.json());
        while (taskStatus.state !== "completed") {
            showAgentProgress(progressList, agents, agentKey => taskStatus.agents?.[agentKey] ?? "⏳ Выполняется...");
            await new Promise(res => setTimeout(res, 1000));
            taskStatus = await fetch(`${API_BASE}/api/health/task_status/${taskId}`).then(r => r.json());
        }
        // 任务Готово后Обновить一次 agent Статус，保证 ReportAgent 也显示 completed
        showAgentProgress(progressList, agents, agentKey => taskStatus.agents?.[agentKey] ?? "⏳ Выполняется...");
        // 显示最终Отчёт
        const summary = taskStatus.report?.report?.summary || "<p>❌ Отчёт не получен</p>";
        reportDiv.innerHTML = typeof summary === "string" ? summary : JSON.stringify(summary, null, 2);
        analysisDiv.innerText = doneText;
        resultCard.classList.remove("hidden");

    } catch (error) {
        const errorMessage = error?.message || JSON.stringify(error);
        console.error("任务Отправить或轮询出错:", errorMessage);
        reportDiv.innerHTML = `<p>❌ ${errorText}: ${errorMessage}</p>`;
        analysisDiv.innerText = `❌ ${errorText}`;
        progressList.innerHTML = "";
    }
}

// ТекстОтчётАнализ
async function analyze() {
    const userId = getUserId();
    if (!userId) return;

    const reportText = document.getElementById("reportText").value;
    if (!reportText) {
        alert("Введите содержимое медосмотра");
        return;
    }

    const resultCard = document.getElementById("resultCard");
    const reportDiv = document.getElementById("report");
    const analysisDiv = document.getElementById("analysis");
    const progressList = document.getElementById("progressList");

    const agents = getHealthProgressAgents();

    await submitAndPollTask(
        `${API_BASE}/api/health/analysis`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ report_text: reportText, user_id: userId })
        },
        agents,
        resultCard,
        reportDiv,
        analysisDiv,
        progressList,
        isDeveloperMode() ? "⏳ Анализ текста…" : "⏳ Анализ…",
        "✅ Анализ завершён",
        "Не удалось сгенерировать отчёт"
    );
}

// PDFОтчётАнализ
async function uploadPDF() {
    const userId = getUserId();
    if (!userId) return;

    const fileInput = document.getElementById("pdfFile");
    const file = fileInput.files[0];
    if (!file) {
        alert("Выберите PDF-файл");
        return;
    }

    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("file", file);

    const resultCard = document.getElementById("resultCard");
    const reportDiv = document.getElementById("report");
    const analysisDiv = document.getElementById("analysis");
    const progressList = document.getElementById("progressList");

    const agents = getHealthProgressAgents();

    await submitAndPollTask(
        `${API_BASE}/api/health/analysis/pdf`,
        { method: "POST", body: formData },
        agents,
        resultCard,
        reportDiv,
        analysisDiv,
        progressList,
        isDeveloperMode() ? "⏳ Анализ PDF…" : "⏳ Анализ PDF…",
        "✅ Анализ завершён",
        "Ошибка загрузки"
    );
}
