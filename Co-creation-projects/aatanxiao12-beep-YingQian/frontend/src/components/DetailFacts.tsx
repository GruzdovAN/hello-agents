import type { MovieDetail } from '../types'

const LANG_LABEL: Record<string, string> = {
  zh: 'Китайский',
  en: 'Английский',
  ja: 'Японский',
  ko: 'Корейский',
  fr: 'Французский',
  de: 'Немецкий',
  es: 'Испанский',
  it: 'Итальянский',
  hi: 'Хинди',
  th: 'Тайский',
}

export function languageLabel(code: string | null | undefined): string | null {
  if (!code) return null
  return LANG_LABEL[code] ?? code
}

/** Блок фактов: режиссёр, актёры, страна */
export function DetailFacts({ detail }: { detail: MovieDetail }) {
  const lang = languageLabel(detail.original_language)
  const rows: { label: string; value: string }[] = []

  if (detail.directors.length) {
    rows.push({ label: 'Режиссёр', value: detail.directors.join('、') })
  }
  if (detail.cast.length) {
    rows.push({ label: 'В ролях', value: detail.cast.join('、') })
  }
  if (detail.countries.length) {
    rows.push({ label: 'Страна/регион', value: detail.countries.join('、') })
  }
  if (lang) {
    rows.push({ label: 'Язык', value: lang })
  }
  if (detail.original_title) {
    rows.push({ label: 'Оригинальное название', value: detail.original_title })
  }
  if (detail.vote_count != null && detail.vote_count > 0) {
    rows.push({ label: 'Число оценок', value: String(detail.vote_count) })
  }

  if (rows.length === 0) return null

  return (
    <dl className="detail-facts">
      {rows.map((row) => (
        <div key={row.label} className="detail-facts__row">
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  )
}
