import { BRAND_NAME, BRAND_TAGLINE } from '../brand'

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <p className="site-footer__brand">{BRAND_NAME}</p>
      <p className="site-footer__tagline">{BRAND_TAGLINE}</p>
      <p>
        Используется{' '}
        <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
          TMDB
        </a>{' '}
         API; не является продуктом, одобренным TMDB. Данные фильмов — The Movie Database.
      </p>
    </footer>
  )
}
