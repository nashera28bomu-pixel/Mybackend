// ─── utils/tmdb.js ────────────────────────────────────────────────────────────
const TMDB_KEY  = process.env.TMDB_API_KEY || '';
const TMDB_BASE = 'https://api.themoviedb.org/3';
const IMG_BASE  = 'https://image.tmdb.org/t/p';

if (!TMDB_KEY) console.warn('[TMDB] ⚠️  TMDB_API_KEY env var not set!');

export async function tmdb(path, params = {}) {
  const url = new URL(TMDB_BASE + path);
  url.searchParams.set('api_key', TMDB_KEY);
  url.searchParams.set('language', 'en-US');
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);

  const res = await fetch(url.toString(), { signal: AbortSignal.timeout(10000) });
  if (!res.ok) throw new Error(`TMDB ${res.status}: ${path}`);
  return res.json();
}

// ─── Normalise a TMDB movie object → clean frontend shape ────────────────────
export function normaliseMovie(m) {
  return {
    id:       m.id,
    tmdb_id:  m.id,
    imdb_id:  m.imdb_id || null,
    title:    m.title || m.original_title || 'Unknown',
    overview: m.overview || '',
    poster:   m.poster_path   ? `${IMG_BASE}/w500${m.poster_path}`   : null,
    backdrop: m.backdrop_path ? `${IMG_BASE}/w1280${m.backdrop_path}` : null,
    year:     m.release_date  ? m.release_date.slice(0, 4) : null,
    rating:   m.vote_average  ? Number(m.vote_average).toFixed(1) : null,
    votes:    m.vote_count    || 0,
    genres:   (m.genres || []).map(g => g.name),
    runtime:  m.runtime       || null,
    type:     'movie',
  };
}

// ─── Normalise a TMDB series object → clean frontend shape ───────────────────
export function normaliseSeries(s) {
  return {
    id:            s.id,
    tmdb_id:       s.id,
    imdb_id:       s.external_ids?.imdb_id || null,
    title:         s.name || s.original_name || 'Unknown',
    overview:      s.overview || '',
    poster:        s.poster_path   ? `${IMG_BASE}/w500${s.poster_path}`   : null,
    backdrop:      s.backdrop_path ? `${IMG_BASE}/w1280${s.backdrop_path}` : null,
    year:          s.first_air_date ? s.first_air_date.slice(0, 4) : null,
    rating:        s.vote_average  ? Number(s.vote_average).toFixed(1) : null,
    votes:         s.vote_count    || 0,
    genres:        (s.genres || []).map(g => g.name),
    seasons:       s.number_of_seasons  || null,
    episodes:      s.number_of_episodes || null,
    status:        s.status || null,
    type:          'series',
  };
}

// ─── Normalise search result (no full details) ────────────────────────────────
export function normaliseSearchResult(item, type = 'movie') {
  const IMG = 'https://image.tmdb.org/t/p';
  if (type === 'movie') {
    return {
      id:      item.id,
      tmdb_id: item.id,
      title:   item.title || item.original_title || 'Unknown',
      poster:  item.poster_path ? `${IMG}/w342${item.poster_path}` : null,
      year:    item.release_date ? item.release_date.slice(0, 4) : null,
      rating:  item.vote_average ? Number(item.vote_average).toFixed(1) : null,
      type:    'movie',
    };
  }
  return {
    id:      item.id,
    tmdb_id: item.id,
    title:   item.name || item.original_name || 'Unknown',
    poster:  item.poster_path ? `${IMG}/w342${item.poster_path}` : null,
    year:    item.first_air_date ? item.first_air_date.slice(0, 4) : null,
    rating:  item.vote_average ? Number(item.vote_average).toFixed(1) : null,
    type:    'series',
  };
}
