/** TypeScript 契约，对齐 backend/app/models/schemas.py（D4） */

export type Mood = 'Расслабиться' | 'Веселье' | 'Драматичное' | 'Сложное' | 'Напряжённое' | 'Тёплое'
export type PartyType = 'Один' | 'Пара' | 'Семья' | 'Друзья'
export type RegionPreference = 'Китайский' | 'Голливуд' | 'Япония/Корея' | 'Европа' | 'Любой'
export type YearPreference = 'Любой' | 'За 5 лет' | 'За 10 лет' | 'Классика'

export interface RecommendRequest {
  mood: Mood
  party_type: PartyType
  genres: string[]
  max_runtime_minutes: number | null
  region_preference: RegionPreference
  year_preference: YearPreference
  exclude_titles: string[]
  spoilers_ok: boolean
  free_text: string
  exclude_ids: number[]
  /** Другие варианты时回传，后端跳过画像 Agent */
  taste_profile?: TasteProfile | null
}

export interface TasteProfile {
  summary: string
  genre_hints: string[]
  language_hints: string[]
  avoid: string[]
  discover_notes: string
}

export interface CandidateMovie {
  id: number
  title: string
  year: number | null
  genres: string[]
  runtime: number | null
  rating: number | null
  poster_url: string | null
  overview: string | null
}

export interface MovieDetail extends CandidateMovie {
  tagline: string | null
  original_title: string | null
  vote_count: number | null
  original_language: string | null
  countries: string[]
  directors: string[]
  cast: string[]
  tmdb_url: string | null
}

export interface MovieCard {
  id: number
  title: string
  year: number | null
  genres: string[]
  runtime: number | null
  rating: number | null
  poster_url: string | null
  why: string
  vibe_tags: string[]
  caution: string | null
  overview_safe: string
}

export interface RecommendResult {
  playlist_name: string
  profile_summary: string
  movies: MovieCard[]
  is_fallback: boolean
  taste_profile?: TasteProfile | null
}

export interface RecommendResponse {
  success: boolean
  message: string
  data: RecommendResult | null
}

export interface MovieListResponse {
  success: boolean
  message: string
  data: CandidateMovie[]
}

export interface MovieDetailResponse {
  success: boolean
  message: string
  data: MovieDetail | null
}

export const MOODS: Mood[] = ['Расслабиться', 'Веселье', 'Драматичное', 'Сложное', 'Напряжённое', 'Тёплое']
export const PARTY_TYPES: PartyType[] = ['Один', 'Пара', 'Семья', 'Друзья']
export const REGIONS: RegionPreference[] = ['Любой', 'Китайский', 'Голливуд', 'Япония/Корея', 'Европа']
export const YEARS: YearPreference[] = ['Любой', 'За 5 лет', 'За 10 лет', 'Классика']
export const GENRE_OPTIONS = [
  'Драма',
  'Комедия',
  'Мелодрама',
  'Фантастика',
  'Анимация',
  'Детектив',
  'Документальный',
  'Боевик',
  'Приключения',
  'Ужасы',
  'Триллер',
  'Фэнтези',
] as const
export const RUNTIME_OPTIONS: { label: string; value: number | null }[] = [
  { label: 'Любой', value: null },
  { label: '90 мин', value: 90 },
  { label: '120 мин', value: 120 },
  { label: '150 мин', value: 150 },
]

export const DEMO_REQUEST: RecommendRequest = {
  mood: 'Расслабиться',
  party_type: 'Один',
  genres: ['Драма', 'Комедия'],
  max_runtime_minutes: 120,
  region_preference: 'Любой',
  year_preference: 'За 10 лет',
  exclude_titles: [],
  spoilers_ok: false,
  free_text: 'Не слишком тяжёлое',
  exclude_ids: [],
}

export const PROGRESS_STAGES = [
  'Анализ вкусов',
  'Поиск в каталоге',
  'Генерация рекомендаций',
  'Проверка',
] as const

export type ProgressStage = (typeof PROGRESS_STAGES)[number]

export interface SessionPayload {
  request: RecommendRequest
  result: RecommendResult
  message: string
}
