"""Pydantic Contract (D4) — модель запроса/ответа, согласованная с интерфейсной и серверной частью."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ============ Литерал перечисления (согласован с формой внешнего интерфейса) ============

Mood = Literal["放松", "欢乐", "虐心", "烧脑", "紧张刺激", "温馨"]
PartyType = Literal["Один", "Пара", "Семья", "Друзья"]
RegionPreference = Literal["华语", "好莱坞", "日韩", "欧洲", "不限"]
YearPreference = Literal["不限", "近5年", "近10年", "经典"]


# ============ Модель запроса ============


class RecommendRequest(BaseModel):
"""Просмотр предпочтений/умных запросов рекомендаций (F1)"""

настроение: Настроение = Поле(..., описание="текущее настроение")
    party_type: PartyType = Field(..., description="观影人群")
жанры: List[str] = Field(default_factory=list,description="Тег предпочтительного типа")
    max_runtime_minutes: Optional[int] = Field(
        default=None,
описание="Максимальная продолжительность (минуты); null=без ограничений",
        examples=[120],
    )
Region_preference: RegionPreference = Поле (по умолчанию = «без ограничений», описание = «Предпочтение региона»)
Year_preference: YearPreference = Поле (по умолчанию = «Без ограничений», описание = «Предпочтение года»)
ignore_titles: List[str] = Field(default_factory=list,description="Уже посмотрел заголовок")
    spoilers_ok: bool = Field(default=False, description="是否允许剧透")
    free_text: str = Field(default="", description="额外自由文本要求")
    exclude_ids: List[int] = Field(
        default_factory=list,
описание="Идентификаторы фильмов TMDB исключаются при изменении пакетов",
    )
    taste_profile: Optional["TasteProfile"] = Field(
        default=None,
описание="Если передано, пропустите портрет Агента (повторное использование в другом пакете)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
«настроение»: «расслабиться»,
"party_type": "уникальный",
"жанры": ["Драма", "Комедия"],
                "max_runtime_minutes": 120,
"region_preference": "Без ограничений",
"year_preference": "Почти 10 лет",
                "exclude_titles": [],
                "spoilers_ok": False,
"free_text": "Не будь слишком тяжелым",
                "exclude_ids": [],
            }
        }
    }


# ============ Подмодель домена ============


class TasteProfile(BaseModel):
"""Структурированный вывод портретного агента (внутренний контракт, последующее использование агента)"""

    summary: str = Field(default="", description="口味摘要")
жанр_хинты: Список[стр] = Поле(default_factory=list,description="Тип тенденции")
Language_hints: List[str] = Field(default_factory=list,description="Язык/региональные предпочтения")
избегать: List[str] = Field(default_factory=list,description="Предметы табу/избегания")
Discover_notes: str = Field(default="",description="найдите описание удобных условий поиска")


class CandidateMovie(BaseModel):
"""Получить фильмы-кандидаты агента/MovieService"""

    id: int = Field(..., description="TMDB movie id")
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    runtime: Optional[int] = Field(default=None, description="片长（分钟）")
    rating: Optional[float] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None


class MovieDetail(CandidateMovie):
"""Информация о фильме (TMDB /movie/{id} + авторы)"""

    tagline: Optional[str] = None
    original_title: Optional[str] = None
    vote_count: Optional[int] = None
    original_language: Optional[str] = None
    countries: List[str] = Field(default_factory=list)
    directors: List[str] = Field(default_factory=list)
    cast: List[str] = Field(default_factory=list)
    tmdb_url: Optional[str] = None


class MovieCard(BaseModel):
"""Рекомендуемая карта результатов (F2 / F3)"""

    id: int = Field(..., description="TMDB movie id")
    title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    runtime: Optional[int] = None
    rating: Optional[float] = None
    poster_url: Optional[str] = None
    why: str = Field(default="", description="推荐理由")
    vibe_tags: List[str] = Field(default_factory=list)
    caution: Optional[str] = Field(default=None, description="适看提示")
overview_safe: str = Field(default="",description="Обзор безопасности (соблюдайте правила_spoilers_ok)")


class RecommendResult(BaseModel):
"""Рекомендуемый предмет результата"""

    playlist_name: str = ""
    profile_summary: str = ""
    movies: List[MovieCard] = Field(default_factory=list)
    is_fallback: bool = Field(default=False, description="是否为降级结果（D5）")
    taste_profile: Optional[TasteProfile] = Field(
        default=None,
        description="本次使用的画像；换一批时可原样回传以跳过画像 Agent",
    )

# ============ Обертка ответа ============


class RecommendResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[RecommendResult] = None


class MovieListResponse(BaseModel):
"""Ответ детерминированного списка поиска (поиск/обнаружение)"""

    success: bool
    message: str = ""
    data: List[CandidateMovie] = Field(default_factory=list)


class MovieDetailResponse(BaseModel):
"""Ответ о фильме"""

    success: bool
    message: str = ""
    data: Optional[MovieDetail] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None


RecommendRequest.model_rebuild()
RecommendResult.model_rebuild()
