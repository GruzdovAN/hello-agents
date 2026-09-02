import logging
import random
import re
import time
from typing import Dict, List
from hello_agents import SimpleAgent, HelloAgentsLLM, Message

from config import get_config
from game_logic import GameSession

logger = logging.getLogger("game.agent")

# Пул категорий персонажей для случайной подстановки в system prompt
_FIGURE_DOMAINS = [
    "Древнекитайские императоры (например, У-ди, Тай-цзун, У Цзэтянь, Канси и др.)",
    "Древнекитайские поэты и учёные (например, Ли Бо, Ду Фу, Су Ши, Ван Сичжи и др.)",
    "Древнекитайские полководцы (например, Юэ Фэй, Хуо Цюйбин, Ци Цзиguang, Хань Синь и др.)",
    "Персонажи китайской мифологии (например, Нюйва, Чанъэ, Нэчжа, Эрлан-шэнь и др.)",
    "Персонажи «Путешествия на Запад» (например, Сунь Укун, Чжу Бэцze, Тан Саньцzang, Ша Уцzin и др.)",
    "Персонажи эпохи Трёх царств (например, Чжугэ Лян, Цao Цao, Лiu Бэй, Гуань Юй, Чжоу Юй и др.)",
    "Западные исторические личности (например, Наполеон, Цезарь, Александр Македонский, Ньютон и др.)",
    "Персонажи западной мифологии (например, Зевс, Афина, Геракл, Ахиллес и др.)",
    "Мировые учёные (например, Эйнштейн, Мария Склодовская-Кюри, Леонардо да Vinci, Галилей и др.)",
    "Известные вымышленные персонажи (например, Гарри Поттер, Шерлок Холмс, Дораэмон, Белоснежка и др.)",
    "Современные спортивные звёзды (например, Яо Мин, Ли На, Майкл Джordan, Пелé и др.)",
    "Китайские личности нового времени (например, Лu Синь, Лян Цichao, Чжэн Chenggong, Линь Zexu и др.)",
    "Интернет-знаменитости и блогеры (например, Li Ziqi, papi, известные онлайн-личности и др.)",
]

_NAME_PREFIXES = ("Название:", "Название：", "Имя:", "Имя：")
_BIO_PREFIXES = ("Краткое описание:", "Краткое описание：", "Описание:", "Описание：", "Биография:", "Биография：")


def _build_random_figure_prompt() -> str:
    """Dynamically build a system prompt with a random domain and seed to avoid LLM caching."""
    domain = random.choice(_FIGURE_DOMAINS)
    seed = random.randint(10000, 99999)
    return f"""Вы — генератор случайных известных личностей. Случайное зерно: {seed}
На этот раз выберите одну личность из категории «{domain}».
Требования:
1. Это должна быть широко известная личность, о которой достаточно информации для угадывания
2. Только личность (реальная или вымышленная), не здания, растения, животные, природные объекты и т.п.
3. Строго такой формат вывода (две строки, без лишнего текста):
Название: <имя личности>
Краткое описание: <одно предложение о характере и главных достижениях, до 50 слов>
4. Каждый раз выбирайте случайно, не повторяйте одного и того же"""

_HINT_SYSTEM_PROMPT = """Вы — эрудированный помощник.
На основе предоставленных материалов поиска сгенерируйте 3 подсказки для игры «угадай, кто я».
Требования:
1. Каждая подсказка на отдельной строке, формат: Подсказка N: <текст>
2. Подсказки от общих к конкретным: 1-я самая расплывчатая, 3-я самая конкретная
3. Нельзя называть ответ напрямую
4. Только 3 строки подсказок, без другого текста"""

_SEMANTIC_MATCH_PROMPT = """Вы — эрудированный помощник. Определите, указывают ли следующие два названия на одну и ту же личность или предмет.
Ответьте только «да» или «нет», без каких-либо других слов.
Название A: {guess}
Название B: {actual}"""

_ROLEPLAY_SYSTEM_PROMPT = """Вы участвуете в игре «угадай, кто я», изображая таинственную личность (кодовое имя: 【загадка】).

## Предыстория персонажа (только для вашей справки, нельзя раскрывать напрямую):
{bio}

## Правила диалога:
1. Отвечайте от первого лица этой личности, тон и стиль должны соответствовать её характеру и эпохе
2. Пользователь будет задавать вопросы, чтобы угадать вашу личность; **обязательно давайте прямой ответ на вопрос** (например, «да» / «нет» / «именно так» и т.п.), не уходите от темы
3. После прямого ответа можно добавить одну фразу в духе персонажа, чтобы сделать игру интереснее
4. Каждый ответ должен быть коротким (1–2 предложения), без длинных монологов
5. Опирайтесь на реальную биографию, характер и достижения персонажа, ничего не выдумывайте
6. **Категорически запрещено называть имя персонажа** (включая имя, прозвище, титул, прозвища и любые другие обозначения)
7. Если вопрос совсем не связан с персонажем, вежливо объясните это в его манере"""


class HistoricalFigureAgent:
    """GuessWhoAmI game Agent wrapper"""

    def __init__(self, game_session: GameSession):
        """
        Initialize Agent: use LLM to randomly generate a subject (person/object/landmark etc.)
        with brief intro, then use TavilySearchTool to pre-generate 3 hints, finally create
        role-play Agent.

        Args:
            game_session: game session object to store current subject info
        """
        self.game_session = game_session
        config = get_config()

        logger.info(f"[AGENT] Initializing LLM: model={config.LLM_MODEL_ID} base_url={config.LLM_BASE_URL}")

        self._llm = HelloAgentsLLM(
            model=config.LLM_MODEL_ID,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            timeout=config.LLM_TIMEOUT,
            provider="modelscope"
        )
        self._config = config

        # Register search tool
        self._search_tool = None
        if config.TAVILY_API_KEY:
            from tools.tavily_search_tool import TavilySearchTool
            self._search_tool = TavilySearchTool(api_key=config.TAVILY_API_KEY)
            logger.info("[AGENT] TavilySearchTool registered")
        else:
            logger.warning("[AGENT] TAVILY_API_KEY not set, search tool disabled")

        # Register Wikipedia image tool (no API key required)
        from tools.search_image_tool import SearchImageTool
        self._image_tool = SearchImageTool()
        logger.info("[AGENT] SearchImageTool (Wikipedia) registered")

        # Step 1: LLM generates subject name + brief intro
        figure = self._generate_figure()
        self.game_session.current_figure = figure
        logger.info(f"[AGENT] Subject loaded: {figure}")

        # Step 2: pre-generate 3 hints via tavily search
        hints = self._generate_hints(figure["name"])
        self.game_session.hints = hints
        logger.info(f"[AGENT] Hints pre-generated: {hints}")

        # Step 3: create role-play Agent
        self.agent = self._create_roleplay_agent()

    # ── Subject generation ────────────────────────────────────────────────────

    def _generate_figure(self) -> Dict[str, str]:
        """Use LLM to randomly generate a subject (person/object/landmark) with brief intro."""
        try:
            system_prompt = _build_random_figure_prompt()
            ts = int(time.time() * 1000)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Дайте мне случайную личность (метка времени: {ts}, случайное число: {random.randint(1, 9999)})"},
            ]
            raw = self._llm.invoke(messages).strip()
            logger.info(f"[AGENT] LLM generated subject raw: {raw!r}")
            return self._parse_figure(raw)
        except Exception as e:
            logger.error(f"[AGENT] Failed to generate subject via LLM: {e}", exc_info=True)
            return self._fallback_figure()

    def _parse_figure(self, raw: str) -> Dict[str, str]:
        """Parse LLM output into {name, bio} dict."""
        name = ""
        bio = ""
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith(_NAME_PREFIXES):
                name = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif line.startswith(_BIO_PREFIXES):
                bio = line.split("：", 1)[-1].split(":", 1)[-1].strip()
        if not name:
            logger.warning("[AGENT] Failed to parse subject name, using fallback")
            return self._fallback_figure()
        return {"name": name, "bio": bio}

    def _fallback_figure(self) -> Dict[str, str]:
        """Return a minimal fallback person when LLM fails."""
        persons = [
            ("Конфуций", "Мыслитель и педагог эпохи Чуньцю, основатель конфуцианства, мягкий и твёрдый характер, всю жизнь посвятил ритуалам и человечности"),
            ("Сунь Укун", "Мифический герой «Путешествия на Запад», озорной и воинственный, 72 превращения, смутил Небесную обитель"),
            ("У Цзэтянь", "Единственная женщина-императрица в истории Китая, жёстко правила, проницательная, основала династию Чжоу"),
            ("Чжугэ Лян", "Канцлер державы Шу эпохи Трёх царств, мудрый и преданный, известен планом из Лунчжун и приёмом с пустым городом"),
            ("Гарри Поттер", "Главный герой серии «Гарри Поттер», смелый и добрый, в итоге победил Волан-де-Морта"),
        ]
        name, bio = random.choice(persons)
        return {"name": name, "bio": bio}

    # ── Hint generation ───────────────────────────────────────────────────────

    def _generate_hints(self, name: str) -> List[str]:
        """Use TavilySearchTool to search subject info, then LLM generates 3 hints."""
        if not self._search_tool:
            return self._fallback_hints(name)

        try:
            search_results = self._search_tool.run(
                {"query": f"{name} биография особенности описание"}
            )
            logger.info(f"[AGENT] Search results for hints, length: {len(search_results)} chars")

            messages = [
                {"role": "system", "content": _HINT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Ответ: {name}\n\nМатериалы поиска:\n{search_results}\n\nСгенерируйте 3 подсказки:"},
            ]
            raw = self._llm.invoke(messages).strip()
            logger.info(f"[AGENT] LLM hint raw output: {raw!r}")
            return self._parse_hints(raw, name)

        except Exception as e:
            logger.error(f"[AGENT] Hint generation failed: {e}", exc_info=True)
            return self._fallback_hints(name)

    def _parse_hints(self, raw: str, name: str) -> List[str]:
        """Parse LLM hint output into a list of 3 hint strings."""
        hints = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Remove prefix like "Подсказка1:" / "Подсказка 1:" / "1." etc.
            cleaned = re.sub(r'^(Подсказка\s*\d[：:]\s*|\d+[\.、]\s*)', '', line, flags=re.IGNORECASE).strip()
            if cleaned:
                hints.append(cleaned)
        # Ensure exactly 3 hints
        if len(hints) >= 3:
            return hints[:3]
        # Pad with fallback if not enough
        fallback = self._fallback_hints(name)
        hints.extend(fallback[len(hints):])
        return hints[:3]

    def _fallback_hints(self, name: str) -> List[str]:
        """Return fallback hints when search/LLM fails."""
        return [
            "Это широко известная личность",
            "Она занимает важное место в своей области или эпохе",
            "Её имя хорошо знакомо во многих странах",
        ]

    # ── Role-play Agent ───────────────────────────────────────────────────────

    def _create_roleplay_agent(self) -> SimpleAgent:
        """Create the role-play SimpleAgent (no tools, conversation only)"""
        system_prompt = self._create_system_prompt()
        agent = SimpleAgent(
            name="guess_who_agent",
            llm=self._llm,
            system_prompt=system_prompt,
            enable_tool_calling=False,
        )
        subject_name = self.game_session.current_figure.get("name", "Неизвестно")
        logger.info(f"[AGENT] Role-play agent created | subject={subject_name}")
        return agent

    def _create_system_prompt(self) -> str:
        """Create dynamic system prompt based on current subject"""
        figure = self.game_session.current_figure
        return _ROLEPLAY_SYSTEM_PROMPT.format(
            bio=figure["bio"],
        )

    # ── Guess ─────────────────────────────────────────────────────────────────

    def make_guess(self, guess_name: str) -> Dict:
        """Process a guess: semantic match via self._llm, then delegate to game_session.
        If correct, fetch figure portrait via SearchImageTool (Wikipedia).
        """
        result = self.game_session.make_guess(
            guess_name,
            semantic_match_fn=self._semantic_match
        )

        # If guessed correctly, fetch portrait images via Wikipedia
        if result.get("correct") and self._image_tool:
            figure_name = self.game_session.current_figure.get("name", guess_name)
            logger.info(f"[AGENT] Fetching portrait images for {figure_name!r}")
            photos = self._image_tool.search_photos(figure_name, per_page=3)
            result["portrait_images"] = photos
            logger.info(f"[AGENT] Portrait images fetched: {len(photos)} results")

        return result

    def _semantic_match(self, guess: str, actual: str) -> bool:
        """Use LLM to semantically judge whether guess and actual refer to the same subject."""
        try:
            prompt = _SEMANTIC_MATCH_PROMPT.format(guess=guess.strip(), actual=actual)
            result = self._llm.invoke([{"role": "user", "content": prompt}]).strip()
            logger.info(f"[AGENT] Semantic match | guess={guess!r} actual={actual!r} llm_answer={result!r}")
            return result.lower().startswith("да")
        except Exception as e:
            logger.error(f"[AGENT] Semantic match failed: {e}", exc_info=True)
            return False

    # ── Chat ──────────────────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        """
        Process user message and return Agent reply

        Args:
            user_message: user input message

        Returns:
            Agent reply content
        """
        try:
            logger.info(f"[AGENT] Calling LLM | user={user_message!r}")
            response = self.agent.run(user_message)
            logger.info(f"[AGENT] LLM response received | response={response!r}")

            # Update game state (increment question count)
            self.game_session.ask_question()

            return response
        except Exception as e:
            logger.error(f"[AGENT] LLM call failed: {e}", exc_info=True)
            return "Извините, я немного растерялся — повторите вопрос, пожалуйста."

    def get_conversation_history(self) -> List[Message]:
        """Get full conversation history"""
        return self.agent.get_history()

    def reset_conversation(self):
        """Reset conversation history and reload subject"""
        self.agent.clear_history()
        # Reload a new subject
        figure = self._generate_figure()
        self.game_session.current_figure = figure
        # Re-generate hints
        hints = self._generate_hints(figure["name"])
        self.game_session.hints = hints
        # Rebuild system prompt
        system_prompt = self._create_system_prompt()
        self.agent.system_prompt = system_prompt
        logger.info("[AGENT] Conversation reset and new subject loaded")


# ── Utility functions ─────────────────────────────────────────────────────────

def check_guess(guess: str, actual_name: str) -> bool:
    """
    Check if user guess is correct

    Args:
        guess: user guessed name
        actual_name: actual subject name

    Returns:
        bool: whether guess is correct
    """
    return guess.strip().lower() == actual_name.lower()


def provide_hint(figure: Dict, hints: List[str], hint_index: int = 0) -> str:
    """
    Provide hint about the subject

    Args:
        figure: subject info dict
        hints: pre-generated hint list
        hint_index: which hint to return (0-based)

    Returns:
        str: hint message
    """
    if hints and hint_index < len(hints):
        return hints[hint_index]
    return "Это широко известная личность"
