"""ReAct Agent — агент с рассуждением и действием"""

import re
from typing import Optional, List, Tuple, Callable, Dict, Any
from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.config import Config
from core.message import Message
from tools.registry import ToolRegistry
from utils.cli_ui import Spinner, c, PRIMARY, ACCENT, INFO, hr, log_tool_event, clamp_text

# Шаблон промпта ReAct по умолчанию
DEFAULT_REACT_PROMPT = """Вы — ИИ-ассистент с рассуждением и действием. Анализируйте задачу, вызывайте инструменты и давайте точный ответ.

## Доступные инструменты
{tools}

## Порядок работы
Строго следуйте формату, один шаг за раз:

**Thought:** Проанализируйте задачу и определите, какая информация или действие нужны.
**Action:** Выберите действие в одном из форматов:
- `{{tool_name}}[{{tool_input}}]` — вызов инструмента
- `Finish[итоговый ответ]` — когда достаточно информации для ответа

## Важно
1. Каждый ответ должен содержать Thought и Action
2. Формат вызова: имя_инструмента[параметры]
3. Finish — только при достаточной уверенности в ответе
4. Если данных мало — другой инструмент или другие параметры

## Текущая задача
**Question:** {question}

## История выполнения
{history}

Начните рассуждение и действие:"""

class ReActAgent(Agent):
    """
    ReAct (Reasoning and Acting) Agent
    
    Агент с рассуждением и действием:
    1. Анализирует задачу и планирует действия
    2. Вызывает внешние инструменты
    3. Рассуждает на основе наблюдений
    4. Итерирует до итогового ответа
    
    Классический паттерн агента (Agent), подходит для задач с внешними данными.
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None,
        observation_summarizer: Optional[Callable[[str, str, str], str]] = None,
        summarize_threshold_chars: int = 2000,
        finalize_on_max_steps: bool = True,
        early_stop_on_repeat: bool = True,
        repeat_action_threshold: int = 2,
    ):
        """
        Инициализирует ReActAgent

        Args:
            name: Имя агента
            llm: Экземпляр LLM
            tool_registry: Реестр инструментов (опционально; иначе создаётся пустой)
            system_prompt: Системный промпт
            config: Объект конфигурации
            max_steps: Максимум шагов
            custom_prompt: Пользовательский шаблон промпта
        """
        super().__init__(name, llm, system_prompt, config)

        # Пустой реестр, если не передан
        if tool_registry is None:
            self.tool_registry = ToolRegistry()
        else:
            self.tool_registry = tool_registry

        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.last_trace: List[Dict[str, Any]] = []
        self.observation_summarizer = observation_summarizer
        self.summarize_threshold_chars = summarize_threshold_chars
        self.finalize_on_max_steps = finalize_on_max_steps
        self.early_stop_on_repeat = early_stop_on_repeat
        self.repeat_action_threshold = repeat_action_threshold

        # Промпт: пользовательский или по умолчанию
        self.prompt_template = custom_prompt if custom_prompt else DEFAULT_REACT_PROMPT

    def add_tool(self, tool):
        """
        Добавляет инструмент в реестр
        Поддерживает авторазвёртывание MCP

        Args:
            tool: Экземпляр Tool или MCPTool
        """
        # Проверка MCP-инструмента
        if hasattr(tool, 'auto_expand') and tool.auto_expand:
            # MCP разворачивается в несколько инструментов
            if hasattr(tool, '_available_tools') and tool._available_tools:
                for mcp_tool in tool._available_tools:
                    # Обёртка инструмента
                    from tools.base import Tool
                    wrapped_tool = Tool(
                        name=f"{tool.name}_{mcp_tool['name']}",
                        description=mcp_tool.get('description', ''),
                        func=lambda input_text, t=tool, tn=mcp_tool['name']: t.run({
                            "action": "call_tool",
                            "tool_name": tn,
                            "arguments": {"input": input_text}
                        })
                    )
                    self.tool_registry.register_tool(wrapped_tool)
                print(f"✅ MCP-инструмент '{tool.name}' развёрнут в {len(tool._available_tools)} отдельных инструментов")
            else:
                self.tool_registry.register_tool(tool)
        else:
            self.tool_registry.register_tool(tool)

    def run(self, input_text: str, **kwargs) -> str:
        """
        Запускает ReAct Agent
        
        Args:
            input_text: Вопрос пользователя
            **kwargs: Прочие параметры
            
        Returns:
            Итоговый ответ
        """
        self.current_history = []
        self.last_trace = []
        current_step = 0
        
        # Avoid dumping huge stitched prompts to console (CLI UX)
        preview = input_text.replace("\n", " ")
        if len(preview) > 160:
            preview = preview[:160] + "..."
        print("\n" + hr("=", 80))
        print(c(f"🤖 {self.name}", PRIMARY) + " " + c(f"{preview}", INFO))
        print(hr("=", 80))
        
        repeat_count = 0
        last_action_sig: Optional[str] = None

        while current_step < self.max_steps:
            current_step += 1
            print(c(f"\n--- Step {current_step}/{self.max_steps} ---", ACCENT))
            
            # Сборка промпта
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )
            
            # Вызов LLM
            messages = [{"role": "user", "content": prompt}]
            spinner = Spinner("Thinking…")
            spinner.start()
            response_text = self.llm.invoke(messages, **kwargs)
            spinner.stop()
            
            if not response_text:
                print("❌ Ошибка: LLM не вернул корректный ответ.")
                break
            
            # Разбор вывода
            thought, action = self._parse_output(response_text)
            
            if thought:
                print(c("Thought:", INFO), thought)
            
            if not action:
                # One forced retry: ask model to rewrite in strict format (helps for greetings / bilingual models)
                try:
                    repair_sys = (
                        "You MUST output exactly two lines:\n"
                        "Thought: ...\n"
                        "Action: tool_name[tool_input] OR Finish[final answer]\n"
                        "No extra text. No markdown headers."
                    )
                    repair_user = f"Rewrite the following into the required two-line format:\n\n{response_text}"
                    spinner = Spinner("Repairing format…")
                    spinner.start()
                    repaired = self.llm.invoke(
                        [{"role": "system", "content": repair_sys}, {"role": "user", "content": repair_user}],
                        max_tokens=200,
                    )
                    spinner.stop()
                    thought, action = self._parse_output(repaired or "")
                except Exception:
                    pass

                if not action:
                    print("⚠️ Предупреждение: не удалось разобрать Action, выполнение прервано.")
                    break
            
            # Проверка завершения
            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(c("Finish:", PRIMARY))
                print(final_answer)
                
                # Сохранение в историю
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                
                return final_answer
            
            # Вызов инструмента
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or tool_input is None:
                self.current_history.append("Observation: неверный формат Action, проверьте.")
                continue
            
            log_tool_event(tool_name, tool_input)
            
            # Вызов инструмента
            observation = self.tool_registry.execute_tool(tool_name, tool_input)
            observation_full = observation
            observation_summary = None
            if (
                self.observation_summarizer is not None
                and isinstance(observation, str)
                and len(observation) > self.summarize_threshold_chars
            ):
                try:
                    observation_summary = self.observation_summarizer(tool_name, tool_input, observation)
                    if observation_summary and isinstance(observation_summary, str):
                        observation = observation_summary.strip() + "\n...truncated...\n"
                except Exception:
                    # fall back to raw observation
                    pass

            log_tool_event(f"{tool_name} result", clamp_text(str(observation), limit=6000))

            # Досрочная остановка при повторе action без прогресса
            action_sig = f"{tool_name}|{tool_input}".strip()
            if self.early_stop_on_repeat:
                if last_action_sig == action_sig:
                    repeat_count += 1
                else:
                    repeat_count = 0
                last_action_sig = action_sig

                if repeat_count >= self.repeat_action_threshold:
                    self.current_history.append("Observation: обнаружен повтор действия; остановите вызовы инструментов и дайте текущий вывод/следующие шаги.")
                    break
            
            # Обновление истории
            self.current_history.append(f"Action: {action}")
            self.current_history.append(f"Observation: {observation}")
            self.last_trace.append(
                {
                    "action": action,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "observation_full_len": len(observation_full) if isinstance(observation_full, str) else None,
                    "observation_summary": observation_summary,
                }
            )
        
        # Finish не достигнут — финальная конвергенция
        if self.finalize_on_max_steps:
            try:
                tools_desc = self.tool_registry.get_tools_description()
                history_str = "\n".join(self.current_history[-24:])
                finalize_prompt = (
                    "Вы — финальный конвергер ReAct-агента. Этап вызова инструментов завершён."
                    "На основе истории Thought/Action/Observation дайте максимально полезный итоговый ответ."
                    "Требования:\n"
                    "1) Больше не вызывать инструменты\n"
                    "2) Явно перечислить собранные факты\n"
                    "3) При нехватке данных — что не хватает и 1–3 минимальных следующих шага\n"
                )
                messages = [
                    {"role": "system", "content": finalize_prompt},
                    {"role": "user", "content": f"Question:\n{input_text}\n\nTools:\n{tools_desc}\n\nTrace:\n{history_str}"},
                ]
                final_answer = self.llm.invoke(messages, max_tokens=600)
                if final_answer:
                    self.add_message(Message(input_text, "user"))
                    self.add_message(Message(final_answer, "assistant"))
                    return final_answer
            except Exception:
                pass

        print("⏰ Достигнут лимит шагов, выполнение прервано.")
        final_answer = "Извините, не удалось завершить задачу за отведённые шаги. Сузьте запрос или укажите целевой файл/модуль."
        
        # Сохранение в историю
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        
        return final_answer
    
    def _parse_output(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Разбирает вывод LLM: мысль и действие.

        Совместимость с вариантами:
        - полноширинное двоеточие (：) в Thought/Action
        - китайские метки: 思考/行动
        - Markdown: **Thought:** / **Action:**
        """
        # Normalize to make regex easier
        t = (text or "").strip()

        # Primary: strict 2-line format, allow markdown markers and fullwidth colon
        m = re.search(
            r"(?:\*\*)?(Thought|思考)(?:\*\*)?\s*[:：]\s*(.*?)\n(?:\*\*)?(Action|行动)(?:\*\*)?\s*[:：]\s*(.*)\s*$",
            t,
            flags=re.DOTALL,
        )
        if m:
            thought = m.group(2).strip()
            action = m.group(4).strip()
            return thought or None, action or None

        # Fallback: find first Thought-like line and first Action-like line anywhere
        thought_match = re.search(r"(?:\*\*)?(Thought|思考)(?:\*\*)?\s*[:：]\s*(.*)", t)
        action_match = re.search(r"(?:\*\*)?(Action|行动)(?:\*\*)?\s*[:：]\s*(.*)", t)
        thought = thought_match.group(2).strip() if thought_match else None
        action_raw = action_match.group(2).strip() if action_match else None
        
        # Обрезка action при вложенных Thought/Action/Observation
        # Защита от захвата лишнего текста в первый Action
        if action_raw:
            stop_patterns = [
                r"\nThought:", r"\n思考:", r"\nAction:", r"\n行动:",
                r"\nObservation:", r"\n观察:", r"\n\*\*Thought", r"\n\*\*Action",
            ]
            earliest_stop = len(action_raw)
            for pat in stop_patterns:
                m = re.search(pat, action_raw, re.IGNORECASE)
                if m and m.start() < earliest_stop:
                    earliest_stop = m.start()
            action_raw = action_raw[:earliest_stop].strip()
        
        return thought, action_raw
    
    def _parse_action(self, action_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Разбирает действие: имя инструмента и ввод
        
        Сопоставление скобок для вложенного JSON.
        """
        # Имя инструмента
        name_match = re.match(r"(\w+)\[", action_text)
        if not name_match:
            return None, None
        
        tool_name = name_match.group(1)
        start = name_match.end() - 1  # позиция '['
        
        # Поиск закрывающей ']'
        depth = 0
        in_string = False
        escape = False
        end_pos = None
        
        for i, c in enumerate(action_text[start:], start):
            if escape:
                escape = False
                continue
            if c == '\\' and in_string:
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    end_pos = i
                    break
        
        if end_pos is not None:
            tool_input = action_text[start + 1:end_pos]
            return tool_name, tool_input
        
        # fallback: простой regex без многострочности
        # Без re.DOTALL — точка не матчит перевод строки
        match = re.match(r"(\w+)\[([^\n]*)\]", action_text)
        if match:
            return match.group(1), match.group(2)
        
        return None, None
    
    def _parse_action_input(self, action_text: str) -> str:
        """Разбирает ввод действия

        Варианты записи Finish:
        - Finish[...]
        - Finish：... / Finish: ... (без скобок)
        - Finish\n<content> (контент/патч с новой строки)
        """
        # Канонический формат Finish[...]
        match = re.match(r"\w+\[(.*)\]\s*$", action_text, flags=re.DOTALL)
        if match:
            return match.group(1)

        # Свободный формат Finish: / Finish：
        m2 = re.match(r"finish\s*[:：]\s*(.*)", action_text, flags=re.IGNORECASE | re.DOTALL)
        if m2:
            return m2.group(1)

        # Удаление префикса Finish
        if action_text.lower().startswith("finish"):
            return action_text[len("finish"):].strip()

        return ""
