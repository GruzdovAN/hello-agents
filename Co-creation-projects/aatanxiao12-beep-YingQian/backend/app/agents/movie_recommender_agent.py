"""多智能体电影推荐编排（串行流水线）。

Парадигма: конвейер + использование инструментов
① Portrait Agent (без инструмента) → TasteProfile
② Поисковый агент (повесить MovieTool) → Реальные кандидаты в фильмы
③ Рекомендовать агента (без инструмента) → генерировать RecommendResult только в пределах идентификатора кандидата.

Этот модуль предоставляет только оркестратор; HTTP-маршрутизация будет подключена позже.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, List, Optional, Tuple

from hello_agents import Config, SimpleAgent

from ..config import get_settings
from ..models.schemas import (
    CandidateMovie,
    MovieCard,
    RecommendRequest,
    RecommendResult,
    TasteProfile,
)
from ..services.llm_service import get_llm
from ..services.movie_service import get_movie_service, normalize_tmdb_language
from ..tools.movie_tool import get_movie_tool
from ..utils.logger import get_logger

logger = get_logger("app.agents")

# ============ Prompts ============

PROFILE_AGENT_PROMPT = """你是观影口味画像专家。根据用户偏好输出结构化 JSON，不要推荐具体片名。

Возвращайте только следующий JSON (без пояснений за пределами блока кода Markdown):
{
"summary": "Одно предложение о вкусе",
"genre_hints": ["type1", "type2"],
  "language_hints": ["仅填 ISO 码：zh / en / ja / ko，可空；禁止写好莱坞、英语等中文"],
"avoid": ["Содержимое, которого следует избегать"],
"discover_notes": "Краткие заметки по поиску для обнаружения TMDB"
}
"""

SEARCH_AGENT_PROMPT = """你是电影检索专家。必须调用工具从 TMDB 取真实影片，禁止编造片名。

Доступные инструменты:
- Movies_discover: основной путь, обнаруженный по типу/году/длительности/языку (разрешено вызывать только один раз в этом раунде)
- Movies_search: используйте только тогда, когда вам нужно проанализировать «просмотренные названия фильмов» (необязательно, до 1–2 раз)

Жесткие правила:
1. movies_discover 只调用一次：用建议参数一次取够候选，禁止换参反复 discover
2. with_original_language 只能是 zh/en/ja/ko；不要传「好莱坞」「英语」等中文
3. Немедленно выведите окончательный JSON после получения результатов инструмента и больше не настраивайте «уточнение» инструмента.
4. В окончательных фильмах ключевые поля (включая poster_url) должны быть скопированы из результатов инструмента в том виде, в котором они есть.

После получения номера окончательный ответ должен быть в формате JSON (без лишних объяснений):
{
  "movies": [
    {
      "id": 123,
      "title": "...",
      "year": 2020,
      "genres": [],
      "rating": 7.5,
      "poster_url": "https://...",
      "overview": "..."
    }
  ]
}

Требовать:
1. Попробуйте вернуть 15–25 деталей.
2. id / title / poster_url 等必须来自工具结果，禁止省略 poster_url
3. Исключите ignore_ids, указанные пользователем.
"""

RECOMMEND_AGENT_PROMPT = """你是电影推荐专家。你没有外部工具，只能从「候选列表」中挑选 3~5 部。

Жесткие ограничения:
1. Идентификатор каждого фильма должен присутствовать в списке кандидатов.
2. Запрещается придумывать названия и идентификаторы фильмов, не являющихся кандидатами.
3. Соблюдать спойлеры_ок: если false, то обзор_безопасно не писать конечные спойлеры
4. почему оно должно соответствовать настроению пользователя и толпе
5. title / year / genres / rating / poster_url 尽量原样沿用候选列表（勿改写为空）

Возвращать только JSON:
{
"playlist_name": "Название темы плейлиста",
"profile_summary": "Сводка вкусов пользователей в одно предложение",
  "movies": [
    {
      "id": 123,
      "title": "...",
      "year": 2020,
      "genres": ["..."],
      "runtime": null,
      "rating": 7.5,
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
"Why": "Причина рекомендации",
"vibe_tags": ["теги"],
      "caution": null,
"overview_safe": "Обзор безопасности"
    }
  ],
  "is_fallback": false
}
"""


REGION_LANGUAGE = {
"华语": "чж",
"Голливуд": "ru",
    "日韩": "ja",  # 简化：先按日语；韩语可由画像 language_hints 覆盖
"Европа": "",
"Без ограничений": "",
}


class MultiAgentMovieRecommender:
    """串行三 Agent 推荐编排器（画像 → 检索 → 推荐 + 白名单校验）。"""

    def __init__(self) -> None:
        """初始化共享 LLM / MovieTool，并创建三个 SimpleAgent。"""
        self.llm = get_llm()
        self.movie_tool = get_movie_tool()
        settings = get_settings()
# Трассировка переключателей из .env: TRACE_ENABLED/TRACE_DIR
        agent_config = Config(
            trace_enabled=settings.trace_enabled,
            trace_dir=settings.trace_dir,
        )

# Портрет: структурируйте только предпочтения, запрещайте подвешивание инструментов (избегайте этого шага и просто ищите фильмы/редактируйте названия)
        self.profile_agent = SimpleAgent(
name="Изображение дома",
            llm=self.llm,
            system_prompt=PROFILE_AGENT_PROMPT,
            config=agent_config,
            enable_tool_calling=False,
        )
        # 检索：唯一允许碰 TMDB 的 Agent；工具展开为 discover / search
        # max_tool_iterations=2：1 轮工具 + 1 轮收尾文本；再高容易反复换参 discover
        self.search_agent = SimpleAgent(
name="Эксперт поиска",
            llm=self.llm,
            system_prompt=SEARCH_AGENT_PROMPT,
            config=agent_config,
            max_tool_iterations=2,
        )
        self.search_agent.add_tool(self.movie_tool)

# Рекомендация: нет инструментов, можно выбирать и рассуждать только среди вышестоящих кандидатов (ядро против галлюцинаций)
        self.recommend_agent = SimpleAgent(
name="Рекомендуемый эксперт",
            llm=self.llm,
            system_prompt=RECOMMEND_AGENT_PROMPT,
            config=agent_config,
            enable_tool_calling=False,
        )
        logger.info(
            "MultiAgentMovieRecommender 就绪: tools=%s trace=%s",
            self.search_agent.list_tools(),
            settings.trace_enabled,
        )

    def recommend(self, request: RecommendRequest) -> Tuple[RecommendResult, str]:
"""Запустите полный конвейер рекомендаций.

        Returns:
            (RecommendResult, message)：业务结果 + 给人看的状态说明（含降级提示）。
        """
        pipeline_t0 = time.perf_counter()
        try:
logger.info("Рекомендуемое начало настроения=%s party=%s", request.mood, request.party_type)

            # ① 偏好 → TasteProfile；换一批可携带 taste_profile 跳过画像 LLM
            t0 = time.perf_counter()
            profile, profile_reused = self._resolve_profile(request)
            logger.info(
"Этап завершен этап=профиль истек=%.2fs повторно использован=%s сводка=%s",
                time.perf_counter() - t0,
                profile_reused,
                profile.summary,
            )

# ② Кандидаты в реальные фильмы; в случае неудачи их рейтинг будет понижен, чтобы избежать слепых рекомендаций по пустому списку.
            t0 = time.perf_counter()
            candidates = self._run_search(request, profile)
            logger.info(
                "阶段完成 stage=search elapsed=%.2fs candidates=%d",
                time.perf_counter() - t0,
                len(candidates),
            )
            if not candidates:
result = self._fallback_result(request, Profile, [], «Фильм-кандидат не получен»)
результат возврата: «Результаты не найдены, возвращен пониженный список фильмов»

# ③ Рекомендация среди кандидатов + белый список идентификаторов уровня кода (бессознательное недоверие к модели)
            t0 = time.perf_counter()
            result = self._run_recommend(request, profile, candidates)
            logger.info(
                "阶段完成 stage=recommend_llm elapsed=%.2fs",
                time.perf_counter() - t0,
            )
            t0 = time.perf_counter()
            result = self._enforce_candidate_ids(result, candidates, profile)
            result = self._attach_taste_profile(result, profile)
            logger.info(
"этап завершен этап=принудительное завершение=%.2fs фильмы=%d запасной вариант=%s всего=%.2fs",
                time.perf_counter() - t0,
                len(result.movies),
                result.is_fallback,
                time.perf_counter() - pipeline_t0,
            )
            msg = "推荐生成成功" if not result.is_fallback else "推荐已做 id 校正/降级"
            if profile_reused:
msg = f"{msg}(изображение пропущено)"
            return result, msg

        except Exception as e:
# Неперехваченные исключения также возвращают полную структуру, и во внешнем интерфейсе нет белого экрана
logger.Exception("Рекомендуемое исключение конвейера")
            result = self._fallback_result(request, None, [], str(e))
возвращаемый результат, f «Рекомендуемое исключение, пониженная версия: {e}»

    # ----- stages -----

    def _resolve_profile(self, request: RecommendRequest) -> Tuple[TasteProfile, bool]:
        """解析画像：请求携带可用 taste_profile 则复用，否则跑画像 Agent。"""
        reused = request.taste_profile
        if reused is not None and (
            (reused.summary or "").strip()
            or reused.genre_hints
            or (reused.discover_notes or "").strip()
        ):
            logger.info("跳过画像 Agent，复用请求中的 taste_profile")
            return self._sanitize_profile(reused, request), True
        return self._sanitize_profile(self._run_profile(request), request), False

    def _sanitize_profile(
        self,
        profile: TasteProfile,
        request: RecommendRequest,
    ) -> TasteProfile:
"""Нормализация языковых_хинтов в соответствии с кодом ISO; недопустимые записи отбрасываются."""
        cleaned: List[str] = []
        for hint in profile.language_hints or []:
            code = normalize_tmdb_language(hint)
            if code and code not in cleaned:
                cleaned.append(code)
        if not cleaned:
            fallback = normalize_tmdb_language(
                REGION_LANGUAGE.get(request.region_preference, "")
            )
            if fallback:
                cleaned = [fallback]
        if cleaned != list(profile.language_hints or []):
            logger.info(
                "画像 language_hints 已归一化: %s -> %s",
                profile.language_hints,
                cleaned,
            )
        profile.language_hints = cleaned
        return profile

    def _resolve_language(
        self,
        request: RecommendRequest,
        profile: TasteProfile,
    ) -> Optional[str]:
"""Проанализируйте код языка, который в конечном итоге использовался для обнаружения."""
        if profile.language_hints:
            code = normalize_tmdb_language(profile.language_hints[0])
            if code:
                return code
        return normalize_tmdb_language(
            REGION_LANGUAGE.get(request.region_preference, "")
        )

    def _attach_taste_profile(
        self,
        result: RecommendResult,
        profile: TasteProfile,
    ) -> RecommendResult:
"""Прикрепите этот портрет к результату для новой партии возвратов."""
        result.taste_profile = profile
        if not result.profile_summary:
            result.profile_summary = profile.summary
        return result

    def _run_profile(self, request: RecommendRequest) -> TasteProfile:
        """阶段①：调用画像 Agent，解析为 TasteProfile；失败则用表单字段兜底。"""
        self.profile_agent.clear_history()
        raw = self.profile_agent.run(self._build_profile_query(request))
        data = self._extract_json(raw) or {}
        try:
            return TasteProfile(**data)
        except Exception:
            # 画像 JSON 坏了：用表单字段拼可用 profile，保证后续检索能继续
            return TasteProfile(
                summary=f"{request.mood}/{request.party_type} 观影",
                genre_hints=list(request.genres),
                language_hints=[REGION_LANGUAGE.get(request.region_preference, "")],
                avoid=[],
                discover_notes=request.free_text or "",
            )

    def _run_search(
        self,
        request: RecommendRequest,
        profile: TasteProfile,
    ) -> List[CandidateMovie]:
        """阶段②：检索 Agent 调工具取真片；解析失败则 MovieService 规则 discover 兜底。"""
        self.search_agent.clear_history()
        self.movie_tool.begin_search_run(discover_limit=1)
        t0 = time.perf_counter()
        try:
            raw = self.search_agent.run(self._build_search_query(request, profile))
        finally:
            self.movie_tool.end_search_run()
        logger.info(
            "检索 Agent run 结束 elapsed=%.2fs raw_len=%d",
            time.perf_counter() - t0,
            len(raw or ""),
        )
        movies = self._parse_candidates(raw, request.exclude_ids)
        if movies:
            missing_poster = sum(1 for m in movies if not m.poster_url)
            logger.info(
                "检索 Agent 解析成功 count=%d missing_poster=%d",
                len(movies),
                missing_poster,
            )
            return movies

        # Agent 未给出可用 JSON 时，用 profile 规则直连 MovieService（仍是真数据）
        logger.warning("检索 Agent 未解析出候选，改用 MovieService 规则兜底")
        t0 = time.perf_counter()
        fallback = self._discover_by_profile(request, profile)
        logger.info(
"Этап завершен stage=search_fallback_discover elapsed=%.2fs count=%d",
            time.perf_counter() - t0,
            len(fallback),
        )
        return fallback

    def _run_recommend(
        self,
        request: RecommendRequest,
        profile: TasteProfile,
        candidates: List[CandidateMovie],
    ) -> RecommendResult:
        """阶段③：推荐 Agent 仅在候选内产出 RecommendResult；JSON 坏则降级。"""
        self.recommend_agent.clear_history()
        raw = self.recommend_agent.run(
            self._build_recommend_query(request, profile, candidates)
        )
        data = self._extract_json(raw)
        if not data:
return self._fallback_result(запрос, профиль, кандидаты, «Не удалось выполнить рекомендуемый анализ JSON»)
        try:
            data.setdefault("is_fallback", False)
# Портрет монтируется оркестратором, а поле вкуса_профиля, поставляемое с моделью, не используется.
            data.pop("taste_profile", None)
            return RecommendResult(**data)
        except Exception:
return self._fallback_result(запрос, профиль, кандидаты, «Проверка рекомендуемой структуры не удалась»)

    # ----- queries -----

    def _build_profile_query(self, request: RecommendRequest) -> str:
        """把 RecommendRequest 拼成画像 Agent 的用户输入文本。"""
        return (
f"Чувство: {request.mood}\n"
f"Толпа: {request.party_type}\n"
            f"类型偏好: {', '.join(request.genres) or '无'}\n"
            f"时长上限(分钟): {request.max_runtime_minutes}\n"
f"Регион: {request.region_preference}\n"
f"Год: {request.year_preference}\n"
            f"已看过: {', '.join(request.exclude_titles) or '无'}\n"
f"Разрешены спойлеры: {request.spoilers_ok}\n"
f"Дополнительные требования: {request.free_text или 'None'}\n"
«Пожалуйста, выведите TasteProfile JSON».
        )

    def _build_search_query(self, request: RecommendRequest, profile: TasteProfile) -> str:
        """把画像 + 表单约束拼成检索 Agent 输入（含建议的 discover 参数）。"""
# Предварительный расчет подсказок параметров обнаружения, чтобы уменьшить вероятность случайного заполнения моделью параметров инструмента.
        year_gte, year_lte = self._year_bounds(request.year_preference)
        lang = self._resolve_language(request, profile) or ""

        genres = ",".join(profile.genre_hints or request.genres)
        parts = [
«Пожалуйста, вызывайте Movies_discover только один раз (используя следующие рекомендуемые параметры) и выводите JSON сразу после получения результата; не изменяйте параметры Discover повторно.»,
f"Описание изображения: {profile.summary}",
f"Рекомендовать with_genres: {жанры или «без ограничений»}»,
f"建议year_gte: {year_gte или 0},year_lte: {year_lte или 0}",
            f"建议 max_runtime: {request.max_runtime_minutes or 0}",
f"Рекомендовать with_original_language: {lang или 'no limit'} (только zh/en/ja/ko)",
            f"discover_notes: {profile.discover_notes}",
            f"exclude_ids: {request.exclude_ids}",
f"Названия фильмов, которые были просмотрены (используйте Movies_search только для исключения при необходимости): {request.exclude_titles}",
            "最终只输出含 movies 数组的 JSON，且每部必须带工具返回的 poster_url。",
        ]
        return "\n".join(parts)

    def _build_recommend_query(
        self,
        request: RecommendRequest,
        profile: TasteProfile,
        candidates: List[CandidateMovie],
    ) -> str:
"""Предпочтения пользователя + сокращенный список кандидатов объединяются в рекомендуемые данные агента."""
# Добавляйте в приглашение только упрощенные поля; названия фильмов/постеры и т. д. в конечном итоге подлежат метаданным кандидата.
        slim = [
            {
                "id": c.id,
                "title": c.title,
                "year": c.year,
                "genres": c.genres,
                "rating": c.rating,
                "poster_url": c.poster_url,
                "overview": (c.overview or "")[:180],
            }
            for c in candidates
        ]
        return (
            f"用户心情: {request.mood}; 人群: {request.party_type}; "
f"Разрешены спойлеры: {request.spoilers_ok}\n"
f"Изображение: {profile.summary}\n"
f"Дополнительные требования: {request.free_text или 'None'}\n"
            f"候选列表(只能从中选):\n{json.dumps(slim, ensure_ascii=False)}\n"
«Пожалуйста, выведите RecommendResult JSON (3–5 частей)».
        )

    # ----- helpers -----

    @staticmethod
    def _year_bounds(year_preference: str) -> Tuple[Optional[int], Optional[int]]:
        """表单年代偏好 → TMDB discover 的 (year_gte, year_lte)。"""
        year = datetime.now().year
ifyear_preference == "последние 5 лет":
            return year - 5, None
ifyear_preference == "около 10 лет":
            return year - 10, None
если год_преференция == "классический":
            return None, 2000
        return None, None

    def _discover_by_profile(
        self,
        request: RecommendRequest,
        profile: TasteProfile,
    ) -> List[CandidateMovie]:
"""Без LLM осуществляйте детерминированные открытия в соответствии с полем портрета; пустые результаты автоматически смягчают условия."""
        year_gte, year_lte = self._year_bounds(request.year_preference)
        lang = self._resolve_language(request, profile)
        genres = ",".join(profile.genre_hints or request.genres) or None
        return get_movie_service().discover_with_relax(
            with_genres=genres,
            year_gte=year_gte,
            year_lte=year_lte,
            max_runtime=request.max_runtime_minutes,
            with_original_language=lang,
            page=1,
            exclude_ids=request.exclude_ids,
        )

    def _parse_candidates(self, raw: str, exclude_ids: List[int]) -> List[CandidateMovie]:
        """从检索 Agent 文本抽出 movies，过滤 exclude_ids 与空标题。"""
        data = self._extract_json(raw)
        if not data:
            return []
        items = data.get("movies") if isinstance(data, dict) else None
        if not isinstance(items, list):
            return []
        exclude = set(exclude_ids)
        out: List[CandidateMovie] = []
        for item in items:
            if not isinstance(item, dict) or "id" not in item:
                continue
            try:
                movie = CandidateMovie(
                    id=int(item["id"]),
                    title=str(item.get("title") or ""),
                    year=item.get("year"),
                    genres=item.get("genres") or [],
                    runtime=item.get("runtime"),
                    rating=item.get("rating"),
                    poster_url=item.get("poster_url"),
                    overview=item.get("overview") or "",
                )
            except Exception:
                continue
            if movie.id in exclude or not movie.title:
                continue
            out.append(movie)
        return out

    def _card_from_candidate(
        self,
        src: CandidateMovie,
        *,
        why: str = "",
        vibe_tags: Optional[List[str]] = None,
        caution: Optional[str] = None,
        overview_safe: str = "",
        runtime: Optional[int] = None,
        poster_url: Optional[str] = None,
    ) -> MovieCard:
        """候选 → MovieCard；缺海报时按 id 拉 detail 回填（仅最终 3~5 部）。"""
        poster = src.poster_url or poster_url
        title = src.title
        year = src.year
        genres = list(src.genres or [])
        rating = src.rating
        overview = overview_safe or (src.overview or "")[:200]
        rt = runtime if runtime is not None else src.runtime

        if not poster:
            try:
                detail = get_movie_service().get_detail(src.id)
                poster = detail.poster_url
                title = title or detail.title
                year = year if year is not None else detail.year
                genres = genres or list(detail.genres or [])
                rating = rating if rating is not None else detail.rating
                if not overview_safe and detail.overview:
                    overview = detail.overview[:200]
                if rt is None:
                    rt = detail.runtime
            except Exception:
                logger.warning("MovieCard 海报回填失败 id=%s", src.id)

        return MovieCard(
            id=src.id,
            title=title,
            year=year,
            genres=genres,
            runtime=rt,
            rating=rating,
            poster_url=poster,
            why=why,
            vibe_tags=vibe_tags or [],
            caution=caution,
            overview_safe=overview,
        )

    def _enforce_candidate_ids(
        self,
        result: RecommendResult,
        candidates: List[CandidateMovie],
        profile: TasteProfile,
    ) -> RecommendResult:
        """白名单闸：丢弃候选外 id；元数据以 TMDB 候选为准；不足 3 部则补齐并降级。"""
        allowed = {c.id: c for c in candidates}
        kept: List[MovieCard] = []
        for card in result.movies:
            if card.id not in allowed:
                continue
            src = allowed[card.id]
            kept.append(
                self._card_from_candidate(
                    src,
                    why=card.why,
                    vibe_tags=card.vibe_tags,
                    caution=card.caution,
                    overview_safe=card.overview_safe or (src.overview or "")[:200],
                    runtime=card.runtime if card.runtime is not None else src.runtime,
                    poster_url=card.poster_url,
                )
            )
        if 3 <= len(kept) <= 5:
            result.movies = kept
            return result

# Легальных фильмов меньше 3-х: заполните кандидатов по рейтингу и отметьте их для понижения.
        result.is_fallback = True
        have = {m.id for m in kept}
        ranked = sorted(
            candidates,
            key=lambda m: (m.rating is not None, m.rating or 0),
            reverse=True,
        )
        for c in ranked:
            if c.id in have:
                continue
            kept.append(
                self._card_from_candidate(
                    c,
Why="Система дополняет список на основании популярности кандидата",
                    overview_safe=(c.overview or "")[:200],
                )
            )
            if len(kept) >= 3:
                break
        result.movies = kept[:5]
        if not result.profile_summary and profile:
            result.profile_summary = profile.summary
        if not result.playlist_name:
result.playlist_name = "Быстрый выбор сегодняшнего кандидата"
        return result

    def _fallback_result(
        self,
        request: RecommendRequest,
        profile: Optional[TasteProfile],
        candidates: List[CandidateMovie],
        reason: str,
    ) -> RecommendResult:
        """诚实降级：尽量用真片凑片单，强制 is_fallback=True。"""
        if not candidates:
            try:
                candidates = self._discover_by_profile(
                    request,
                    profile
                    or TasteProfile(
                        summary=reason,
                        genre_hints=list(request.genres),
                    ),
                )
            except Exception:
                candidates = []

        movies: List[MovieCard] = []
        for c in candidates[:5]:
            movies.append(
                self._card_from_candidate(
                    c,
Why=f"Рекомендация по понижению версии ({reason})",
                    overview_safe=(c.overview or "")[:200],
                )
            )
        return RecommendResult(
playlist_name="Понизить плейлист",
            profile_summary=(profile.summary if profile else reason),
            movies=movies,
            is_fallback=True,
            taste_profile=profile,
        )

    @staticmethod
    def _extract_json(text: str) -> Optional[dict]:
        """从模型文本提取 JSON 对象（纯 JSON / 代码块 / 夹杂说明均可）。"""
        if not text:
            return None
        text = text.strip()
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence:
            try:
                data = json.loads(fence.group(1))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                pass
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
        return None

    def health_snapshot(self) -> dict[str, Any]:
        """返回各 Agent 名称与工具数量（供 /api/recommend/health）。"""
        return {
            "agents": [
                {"name": self.profile_agent.name, "tools_count": 0},
                {
                    "name": self.search_agent.name,
                    "tools_count": len(self.search_agent.list_tools()),
                },
                {"name": self.recommend_agent.name, "tools_count": 0},
            ]
        }


_recommender: Optional[MultiAgentMovieRecommender] = None


def get_movie_recommender() -> MultiAgentMovieRecommender:
"""Получить синглтон внутрипроцессного оркестратора (ленивая загрузка, чтобы избежать повторной инициализации LLM/агента)."""
    global _recommender
    if _recommender is None:
        _recommender = MultiAgentMovieRecommender()
    return _recommender
