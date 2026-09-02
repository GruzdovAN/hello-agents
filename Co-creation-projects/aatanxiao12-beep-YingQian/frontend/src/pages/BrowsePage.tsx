import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { discoverMovies, searchMovies } from '../api/movies'
import { CatalogDetail } from '../components/CatalogDetail'
import { CatalogTile } from '../components/CatalogTile'
import { SiteFooter } from '../components/SiteFooter'
import { SiteNav } from '../components/SiteNav'
import { loadSeen, type SeenEntry } from '../lib/seen'
import type { CandidateMovie } from '../types'
import { GENRE_OPTIONS } from '../types'

type Mode = 'search' | 'discover'

const SORT_OPTIONS = [
  { value: 'popularity.desc', label: 'Популярность' },
  { value: 'vote_average.desc', label: 'Рейтинг' },
  { value: 'primary_release_date.desc', label: 'Сначала новинки' },
] as const

const LANG_OPTIONS = [
  { value: '', label: 'Любой язык' },
  { value: 'zh', label: 'Китайский' },
  { value: 'en', label: 'Английский' },
  { value: 'ja', label: 'Японский' },
  { value: 'ko', label: 'Корейский' },
] as const

export function BrowsePage() {
  const [mode, setMode] = useState<Mode>('search')
  const [query, setQuery] = useState('')
  const [year, setYear] = useState('')
  const [genres, setGenres] = useState<string[]>([])
  const [lang, setLang] = useState('')
  const [sortBy, setSortBy] = useState<string>('popularity.desc')
  const [yearGte, setYearGte] = useState('')
  const [maxRuntime, setMaxRuntime] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<CandidateMovie[] | null>(null)
  const [selected, setSelected] = useState<CandidateMovie | null>(null)
  const [seenList, setSeenList] = useState<SeenEntry[]>(() => loadSeen())

  const runDiscover = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await discoverMovies({
        with_genres: genres.length ? genres.join(',') : undefined,
        year_gte: yearGte ? Number(yearGte) : undefined,
        max_runtime: maxRuntime ? Number(maxRuntime) : undefined,
        with_original_language: lang || undefined,
        sort_by: sortBy,
        page: 1,
      })
      setResults(res.data)
      setSelected(null)
    } catch (err) {
      setResults(null)
      setError(err instanceof Error ? err.message : 'Ошибка поиска')
    } finally {
      setLoading(false)
    }
  }, [genres, yearGte, maxRuntime, lang, sortBy])

  useEffect(() => {
    if (mode !== 'discover') return
    void runDiscover()
  }, [mode, runDiscover])

  async function onSearchSubmit(e: FormEvent) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return

    setLoading(true)
    setError(null)
    try {
      const res = await searchMovies(q, year ? Number(year) : undefined)
      setResults(res.data)
      setSelected(null)
    } catch (err) {
      setResults(null)
      setError(err instanceof Error ? err.message : 'Ошибка поиска')
    } finally {
      setLoading(false)
    }
  }

  function toggleGenre(g: string) {
    setGenres((prev) =>
      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g].slice(0, 3),
    )
  }

  const seenIds = new Set(seenList.map((e) => e.id))

  return (
    <div className="page page--browse">
      <SiteNav active="browse" />

      <header className="browse-hero">
        <p className="section-kicker">Каталог</p>
        <h1 className="browse-title">Найдите фильм на вечер</h1>
        <p className="browse-lead">
          Поиск по названию или фильтры. Нажмите постер для деталей, отметьте просмотренные.
        </p>
      </header>

      <div className="mode-tabs" role="tablist" aria-label="Способ поиска">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'search'}
          className={mode === 'search' ? 'mode-tab is-active' : 'mode-tab'}
          onClick={() => {
            setMode('search')
            setResults(null)
            setSelected(null)
            setError(null)
          }}
        >
          Поиск по ключевым словам
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'discover'}
          className={mode === 'discover' ? 'mode-tab is-active' : 'mode-tab'}
          onClick={() => setMode('discover')}
        >
          Поиск по фильтрам
        </button>
      </div>

      {mode === 'search' ? (
        <form className="browse-toolbar" onSubmit={(e) => void onSearchSubmit(e)}>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Название или ключевые слова, например: Inception"
            autoComplete="off"
            aria-label="Ключевые слова"
          />
          <input
            type="number"
            className="browse-year"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            placeholder="Год"
            min={1900}
            max={2100}
            aria-label="Год выхода"
          />
          <button
            type="submit"
            className="btn btn--primary"
            disabled={loading || !query.trim()}
          >
            {loading ? 'Поиск…' : 'Поиск'}
          </button>
        </form>
      ) : (
        <div className="browse-filters">
          <div className="chip-row" aria-label="Жанры, до трёх">
            {GENRE_OPTIONS.map((g) => (
              <button
                key={g}
                type="button"
                className={genres.includes(g) ? 'chip is-on' : 'chip'}
                onClick={() => toggleGenre(g)}
              >
                {g}
              </button>
            ))}
          </div>
          <div className="browse-filters__row">
            <label>
              <span className="sr-only">Год от</span>
              <input
                type="number"
                value={yearGte}
                onChange={(e) => setYearGte(e.target.value)}
                placeholder="С"
                min={1900}
                max={2100}
              />
            </label>
            <label>
              <span className="sr-only">Макс. длительность</span>
              <select
                value={maxRuntime}
                onChange={(e) => setMaxRuntime(e.target.value)}
              >
                <option value="">Любая длительность</option>
                <option value="90">≤ 90 мин</option>
                <option value="120">≤ 120 мин</option>
                <option value="150">≤ 150 мин</option>
              </select>
            </label>
            <label>
              <span className="sr-only">Язык</span>
              <select value={lang} onChange={(e) => setLang(e.target.value)}>
                {LANG_OPTIONS.map((o) => (
                  <option key={o.value || 'any'} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="sr-only">Сортировка</span>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn btn--primary"
              onClick={() => void runDiscover()}
              disabled={loading}
            >
              {loading ? 'Обновление…' : 'Обновить'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <p className="error-banner" role="alert">
          {error}
        </p>
      )}

      <div className={selected ? 'browse-split has-detail' : 'browse-split'}>
        <section className="catalog-grid" aria-label="Список фильмов">
          {loading && !results && <p className="muted">Подключение к каталогу…</p>}
          {results && results.length === 0 && (
            <p className="muted">Нет подходящих фильмов — измените запрос или фильтры.</p>
          )}
          {results &&
            results.map((m, i) => (
              <CatalogTile
                key={m.id}
                movie={m}
                index={i}
                selected={selected?.id === m.id}
                seen={seenIds.has(m.id)}
                onSelect={setSelected}
              />
            ))}
          {!loading && results == null && mode === 'search' && (
            <p className="browse-empty muted">
              Введите название или переключитесь на «Поиск по фильтрам».
            </p>
          )}
        </section>

        {selected && (
          <CatalogDetail
            movie={selected}
            onClose={() => setSelected(null)}
            onSeenChange={setSeenList}
          />
        )}
      </div>

      {seenList.length > 0 && (
        <p className="browse-seen-hint muted">
          Отмечено {seenList.length} просмотренных; они исключаются из рекомендаций.
        </p>
      )}

      <SiteFooter />
    </div>
  )
}
