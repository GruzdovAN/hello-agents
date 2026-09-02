import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { postRecommend } from '../api/recommend'
import { FallbackAlert } from '../components/FallbackAlert'
import { MovieCardView } from '../components/MovieCard'
import { ProgressOverlay } from '../components/ProgressOverlay'
import { SiteFooter } from '../components/SiteFooter'
import { SiteNav } from '../components/SiteNav'
import { formatPlaylistText } from '../lib/format'
import { loadSession, saveSession } from '../lib/session'
import type { SessionPayload } from '../types'
import { PROGRESS_STAGES } from '../types'

export function ResultPage() {
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionPayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [stageIndex, setStageIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const data = loadSession()
    if (!data) {
      navigate('/', { replace: true })
      return
    }
    setSession(data)
  }, [navigate])

  useEffect(() => {
    if (!copied) return
    const id = window.setTimeout(() => setCopied(false), 2000)
    return () => window.clearTimeout(id)
  }, [copied])

  async function handleRefresh() {
    if (!session) return
    setError(null)
    setLoading(true)

    const exclude_ids = session.result.movies.map((m) => m.id)
    const taste_profile =
      session.result.taste_profile ??
      ({
        summary:
          session.result.profile_summary ||
          `${session.request.mood}/${session.request.party_type} — просмотр`,
        genre_hints: [...session.request.genres],
        language_hints: [] as string[],
        avoid: [] as string[],
        discover_notes: session.request.free_text || '',
      })

    // Другие варианты已跳过画像：假进度从「Поиск в каталоге」起
    setStageIndex(1)
    const timers: number[] = []
    PROGRESS_STAGES.forEach((_, i) => {
      if (i <= 1) return
      timers.push(window.setTimeout(() => setStageIndex(i), 4_500 * (i - 1)))
    })

    const request = {
      ...session.request,
      exclude_ids: [
        ...new Set([...session.request.exclude_ids, ...exclude_ids]),
      ],
      taste_profile,
    }

    try {
      const res = await postRecommend(request)
      if (!res.success || !res.data) {
        throw new ApiError(res.message || 'Не удалось обновить подборку')
      }
      const next: SessionPayload = {
        request: {
          ...request,
          taste_profile: undefined,
        },
        result: {
          ...res.data,
          taste_profile: res.data.taste_profile ?? taste_profile,
        },
        message: res.message,
      }
      saveSession(next)
      setSession(next)
      setStageIndex(PROGRESS_STAGES.length - 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обновить подборку')
    } finally {
      timers.forEach((id) => window.clearTimeout(id))
      setLoading(false)
    }
  }

  async function handleCopy() {
    if (!session) return
    const text = formatPlaylistText(session.result.movies)
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch {
      setError('Не удалось скопировать — выделите текст вручную')
    }
  }

  if (!session) {
    return (
      <div className="page page--result">
        <p className="muted">Загрузка результатов…</p>
      </div>
    )
  }

  const { result, message } = session

  return (
    <div className="page page--result">
      <SiteNav active="result" />

      <header className="result-header">
        <p className="result-kicker">Список на вечер</p>
        <h1 className="result-title">{result.playlist_name || 'Рекомендации'}</h1>
        {result.profile_summary && (
          <p className="result-summary">{result.profile_summary}</p>
        )}
      </header>

      <div className="result-actions">
        <Link to="/" className="btn btn--ghost">
          Изменить предпочтения
        </Link>
        <Link to="/browse" className="btn btn--ghost">
          Каталог
        </Link>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => void handleRefresh()}
          disabled={loading}
        >
          Другие варианты
        </button>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => void handleCopy()}
          disabled={loading || result.movies.length === 0}
        >
          {copied ? 'Скопировано' : 'Копировать список'}
        </button>
      </div>

      <FallbackAlert message={message} isFallback={result.is_fallback} />
      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}

      <section className="movie-grid" aria-label="Рекомендованные фильмы">
        {result.movies.length === 0 ? (
          <p className="muted">Нет рекомендаций — вернитесь и измените предпочтения.</p>
        ) : (
          result.movies.map((movie, i) => (
            <MovieCardView key={movie.id} movie={movie} index={i} />
          ))
        )}
      </section>

      <SiteFooter />
      <ProgressOverlay active={loading} stageIndex={stageIndex} />
    </div>
  )
}
