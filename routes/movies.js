// ─── routes/movies.js ─────────────────────────────────────────────────────────
import express from 'express';
import { tmdb, normaliseMovie, normaliseSearchResult } from './tmdb.js';

const router = express.Router();

// ─── GET /api/movies/search?q=avengers&page=1 ─────────────────────────────────
router.get('/search', async (req, res) => {
  const { q, page = 1 } = req.query;
  if (!q?.trim()) return res.status(400).json({ error: 'q param required' });
  try {
    const data = await tmdb('/search/movie', { query: q.trim(), page });
    res.json({
      success: true,
      page: data.page,
      total_pages: data.total_pages,
      total_results: data.total_results,
      results: (data.results || []).map(m => normaliseSearchResult(m, 'movie')),
    });
  } catch (e) {
    console.error('[Movies Search]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/movies/trending ─────────────────────────────────────────────────
router.get('/trending', async (req, res) => {
  try {
    const data = await tmdb('/trending/movie/week');
    res.json({
      success: true,
      results: (data.results || []).map(m => normaliseSearchResult(m, 'movie')),
    });
  } catch (e) {
    console.error('[Movies Trending]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/movies/:id ──────────────────────────────────────────────────────
router.get('/:id', async (req, res) => {
  const { id } = req.params;
  if (isNaN(id)) return res.status(400).json({ error: 'Invalid TMDB ID' });
  try {
    const [details, extIds] = await Promise.all([
      tmdb(`/movie/${id}`, { append_to_response: 'credits,videos' }),
      tmdb(`/movie/${id}/external_ids`),
    ]);
    const movie = normaliseMovie({ ...details, imdb_id: extIds.imdb_id });

    // Add cast and trailer
    movie.cast = (details.credits?.cast || []).slice(0, 10).map(c => ({
      name: c.name,
      character: c.character,
      photo: c.profile_path ? `https://image.tmdb.org/t/p/w185${c.profile_path}` : null,
    }));
    movie.trailer = (details.videos?.results || []).find(
      v => v.type === 'Trailer' && v.site === 'YouTube'
    )?.key || null;

    res.json({ success: true, movie });
  } catch (e) {
    console.error('[Movie Details]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/movies/:id/recommendations ──────────────────────────────────────
router.get('/:id/recommendations', async (req, res) => {
  const { id } = req.params;
  try {
    const data = await tmdb(`/movie/${id}/recommendations`);
    res.json({
      success: true,
      results: (data.results || []).slice(0, 12).map(m => normaliseSearchResult(m, 'movie')),
    });
  } catch (e) {
    res.json({ success: true, results: [] }); // silent fail
  }
});

export default router;
