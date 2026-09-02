import { useEffect, useMemo, useRef, useState } from "react";
import { buildPlan, streamAgentChat } from "./services/api";
import { renderMermaid } from "./services/mermaid";

const MODES = [
  { key: "inspire", label: "Режим вдохновения" },
  { key: "standard", label: "Стандартный режим" },
  { key: "plan", label: "Режим плана" },
  { key: "code", label: "Режим кода Mermaid" },
];

const DIRECTION_OPTIONS = [
  { key: "TD", label: "Сверху вниз" },
  { key: "LR", label: "Слева направо" },
];

const MODE_PLACEHOLDER = {
  plan: "Введите шаги построчно, например:\nНачало\nОчистка данных\nОбучение модели\nКонец",
  code: "Введите код Mermaid напрямую",
  standard: "Начните ввод...",
  inspire: "Начните ввод...",
};

const CHAT_EMPTY_TEXT = {
  standard: "Опишите задачу — я помогу улучшить промпт и сгенерировать диаграмму.",
  inspire: "Расскажите идею — я помогу доработать и сгенерировать диаграмму.",
};

const ASSISTANT_PREFIX = {
  standard: "Код диаграммы по вашему запросу:",
  inspire: "Код диаграммы по вашей идее:",
};

function downloadText(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [mode, setMode] = useState("plan");
  const [direction, setDirection] = useState("TD");
  const [input, setInput] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [mermaidCode, setMermaidCode] = useState("flowchart TD\n    A[AutoFlow] --> B[Готово]");
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");
  const [statusText, setStatusText] = useState("Ожидание генерации");
  const [loading, setLoading] = useState(false);
  const [chatMap, setChatMap] = useState({ standard: [], inspire: [] });
  const [thinkingMap, setThinkingMap] = useState({ standard: false, inspire: false });
  const [zoom, setZoom] = useState(1);
  const previewRef = useRef(null);
  const dragStateRef = useRef({ dragging: false, startX: 0, startY: 0, startLeft: 0, startTop: 0 });

  const isChatMode = mode === "standard" || mode === "inspire";

  const currentChat = chatMap[mode] || [];
  const isThinking = thinkingMap[mode] || false;

  const pushChatMessage = (targetMode, message) => {
    setChatMap((prev) => ({
      ...prev,
      [targetMode]: [...(prev[targetMode] || []), message],
    }));
  };

  const canGenerate = useMemo(() => {
    if (isChatMode) return chatInput.trim().length > 0;
    if (mode === "code") return mermaidCode.trim().length > 0;
    return input.trim().length > 0;
  }, [mode, input, mermaidCode, chatInput, isChatMode]);

  const applyDirectionToCode = (code, targetDirection) => {
    const raw = (code || "").trim();
    if (!raw) return "";

    const normalized = targetDirection === "LR" ? "LR" : "TD";
    const lines = raw.split("\n");
    const firstIdx = lines.findIndex((line) => line.trim().length > 0);
    if (firstIdx === -1) return raw;

    const firstLine = lines[firstIdx];
    if (/^(flowchart|graph)\s+(TD|LR|TB|BT|RL)\b/i.test(firstLine.trim())) {
      lines[firstIdx] = firstLine.replace(/^(\s*)(flowchart|graph)\s+(TD|LR|TB|BT|RL)\b/i, `$1$2 ${normalized}`);
      return lines.join("\n");
    }

    if (/^(flowchart|graph)\b/i.test(firstLine.trim())) {
      lines[firstIdx] = firstLine.replace(/^(\s*)(flowchart|graph)\b/i, `$1$2 ${normalized}`);
      return lines.join("\n");
    }

    return `flowchart ${normalized}\n${raw}`;
  };

  const previewMermaidCode = useMemo(() => applyDirectionToCode(mermaidCode, direction), [mermaidCode, direction]);

  const zoomLabel = `${Math.round(zoom * 100)}%`;

  const clampZoom = (value) => Math.min(3, Math.max(0.3, value));

  const zoomIn = () => setZoom((prev) => clampZoom(prev + 0.1));

  const zoomOut = () => setZoom((prev) => clampZoom(prev - 0.1));

  const resetZoom = () => setZoom(1);

  const fitToView = () => {
    if (!previewRef.current || !svg) return;
    const container = previewRef.current;
    const svgEl = container.querySelector("svg");
    if (!svgEl) return;

    const vb = svgEl.viewBox?.baseVal;
    const svgWidth = vb && vb.width ? vb.width : svgEl.getBoundingClientRect().width;
    const svgHeight = vb && vb.height ? vb.height : svgEl.getBoundingClientRect().height;
    if (!svgWidth || !svgHeight) return;

    const innerPadding = 32;
    const availableWidth = Math.max(120, container.clientWidth - innerPadding);
    const availableHeight = Math.max(120, container.clientHeight - innerPadding);
    const fitted = clampZoom(Math.min(availableWidth / svgWidth, availableHeight / svgHeight));

    setZoom(fitted);
    container.scrollLeft = 0;
    container.scrollTop = 0;
  };

  const handlePreviewMouseDown = (e) => {
    if (!svg || !previewRef.current) return;
    const container = previewRef.current;
    dragStateRef.current = {
      dragging: true,
      startX: e.clientX,
      startY: e.clientY,
      startLeft: container.scrollLeft,
      startTop: container.scrollTop,
    };
  };

  const handlePreviewMouseMove = (e) => {
    if (!previewRef.current) return;
    const drag = dragStateRef.current;
    if (!drag.dragging) return;
    const dx = e.clientX - drag.startX;
    const dy = e.clientY - drag.startY;
    previewRef.current.scrollLeft = drag.startLeft - dx;
    previewRef.current.scrollTop = drag.startTop - dy;
  };

  const stopPreviewDrag = () => {
    dragStateRef.current.dragging = false;
  };

  useEffect(() => {
    async function draw() {
      const code = (previewMermaidCode || "").trim();
      if (!code) {
        setSvg("");
        setError("");
        return;
      }

      try {
        const result = await renderMermaid(code);
        setSvg(result.svg);
        setError("");
      } catch (e) {
        setError(`Ошибка рендеринга: ${e.message}`);
      }
    }
    draw();
  }, [previewMermaidCode]);

  const runPlanMode = async () => {
    const data = await buildPlan(input, "TD");
    setMermaidCode(data.mermaid_code || "");
    setZoom(1);
    setStatusText("Режим плана: диаграмма готова — смените направление в превью");
  };

  const runCodeMode = async () => {
    setStatusText("Режим кода: рендер из текущего редактора");
  };

  const runAgentMode = async () => {
    const modeKey = mode === "inspire" ? "inspire" : "standard";
    const userPrompt = chatInput.trim();

    if (!userPrompt) return;

    pushChatMessage(modeKey, { role: "user", content: userPrompt, kind: "text" });
    setThinkingMap((prev) => ({ ...prev, [modeKey]: true }));
    setChatInput("");
    let settled = false;

    try {
      await streamAgentChat(
        {
          mode: modeKey,
          prompt: userPrompt,
          direction: "TD",
        },
        ({ data }) => {
          if (data.type === "status") {
            setStatusText(`${data.phase}: ${data.message}`);
          }

          if (data.type === "result") {
            settled = true;
            setMermaidCode(data.mermaid_code || "");
            setZoom(1);
            setStatusText(`Готово: valid=${data.valid}, attempts=${data.attempts}`);
            if (modeKey === "standard" && data.optimized_text) {
              pushChatMessage(modeKey, {
                role: "assistant",
                content: data.optimized_text,
                kind: "text",
                title: "Улучшенный промпт:",
              });
            }
            pushChatMessage(modeKey, {
              role: "assistant",
              content: data.mermaid_code || "",
              kind: "code",
              title: ASSISTANT_PREFIX[modeKey],
            });
          }

          if (data.type === "error") {
            settled = true;
            setError(data.message || "Ошибка выполнения агента");
          }
        }
      );

      if (!settled) {
        throw new Error("Ответ сервера прерван — повторите");
      }
    } finally {
      setThinkingMap((prev) => ({ ...prev, [modeKey]: false }));
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setStatusText("Обработка запроса...");

    try {
      if (mode === "plan") {
        await runPlanMode();
      } else if (mode === "code") {
        await runCodeMode();
      } else {
        await runAgentMode();
      }
    } catch (e) {
      setError(e.message || "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="topbar">
        <h1>AutoFlow</h1>
        <p>От плана к диаграмме — генерация и превью в реальном времени</p>
      </header>

      <main className="workspace">
        <section className="left-panel">
          <div className="tabs">
            {MODES.map((item) => (
              <button
                key={item.key}
                className={item.key === mode ? "tab active" : "tab"}
                onClick={() => setMode(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {isChatMode ? (
            <>
              <div className="chat-box">
                {currentChat.length === 0 && !isThinking ? (
                  <div className="chat-empty-wrap">
                    <div className="chat-empty">{CHAT_EMPTY_TEXT[mode]}</div>
                    {mode === "inspire" ? <div className="chat-empty-sub">Например: «Хочу создать e-commerce платформу».</div> : null}
                  </div>
                ) : (
                  currentChat.map((msg, idx) => (
                    <div key={`${msg.role}-${idx}`} className={`chat-msg ${msg.role}`}>
                      {msg.role === "assistant" && msg.title ? <div className="chat-title">{msg.title}</div> : null}
                      {msg.kind === "code" ? (
                        <pre className="chat-code">{msg.content}</pre>
                      ) : (
                        <p>{msg.content}</p>
                      )}
                    </div>
                  ))
                )}

                {isThinking ? (
                  <div className="chat-msg assistant thinking">
                    <div className="thinking-bubble">
                      Думаю
                      <span className="dots">...</span>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="chat-input-row">
                <textarea
                  className="chat-input"
                  placeholder={MODE_PLACEHOLDER[mode]}
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && !loading) {
                      handleGenerate();
                    }
                  }}
                  rows={3}
                />
                <button className="primary" disabled={!canGenerate || loading} onClick={handleGenerate}>
                  {loading ? "Генерация" : "Отправить"}
                </button>
              </div>
            </>
          ) : (
            <>
              <textarea
                className="editor"
                placeholder={MODE_PLACEHOLDER[mode]}
                value={mode === "code" ? mermaidCode : input}
                onChange={(e) => {
                  if (mode === "code") {
                    setMermaidCode(e.target.value);
                  } else {
                    setInput(e.target.value);
                  }
                }}
              />

              <div className="actions">
                <button className="primary" disabled={!canGenerate || loading} onClick={handleGenerate}>
                  {loading ? "Генерация..." : "Сгенерировать/обновить"}
                </button>
              </div>
            </>
          )}

          <div className="log-box">
            <strong>Текущий статус</strong>
            {loading && <div className="loader" aria-label="loading" />}
            <p>{statusText}</p>
          </div>
        </section>

        <section className="right-panel">
          <div className="panel-header">
            <h2>Превью в реальном времени</h2>
            <div className="panel-tools">
              <div className="preview-controls">
                <button className="ghost" onClick={zoomOut} disabled={!svg}>
                  Уменьшить
                </button>
                <span className="zoom-label">{zoomLabel}</span>
                <button className="ghost" onClick={zoomIn} disabled={!svg}>
                  Увеличить
                </button>
                <button className="ghost" onClick={resetZoom} disabled={!svg}>
                  100%
                </button>
                <button className="ghost" onClick={fitToView} disabled={!svg}>
                  По размеру окна
                </button>
              </div>
              <div className="direction-switch">
                {DIRECTION_OPTIONS.map((item) => (
                  <button
                    key={item.key}
                    className={item.key === direction ? "dir-btn active" : "dir-btn"}
                    onClick={() => setDirection(item.key)}
                    disabled={!svg}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <div className="export-actions">
              <button className="ghost" onClick={() => downloadText("autoflow.mmd", previewMermaidCode)}>
                Экспорт .mmd
              </button>
              <button className="ghost" onClick={() => downloadText("autoflow.svg", svg)} disabled={!svg}>
                Экспорт SVG
              </button>
              </div>
            </div>
          </div>
          {error && (mermaidCode || "").trim() ? <div className="error">{error}</div> : null}
          <div
            className={svg ? "preview" : "preview is-empty"}
            ref={previewRef}
            onMouseDown={handlePreviewMouseDown}
            onMouseMove={handlePreviewMouseMove}
            onMouseUp={stopPreviewDrag}
            onMouseLeave={stopPreviewDrag}
          >
            {svg ? (
              <div className="preview-scale" style={{ transform: `scale(${zoom})` }}>
                <div className="preview-inner" dangerouslySetInnerHTML={{ __html: svg }} />
              </div>
            ) : (
              <div className="preview-empty">Диаграммы пока нет...</div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
