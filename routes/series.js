// ─── routes/series.js ─────────────────────────────────────────────────────────
import express from 'express';
import { tmdb, normaliseSeries, normaliseSearchResult } from './tmdb.js';

const router = express.Router();

// ─── GET /api/series/search?q=breaking+bad&page=1 ─────────────────────────────
router.get('/search', async (req, res) => {
  const { q, page = 1 } = req.query;
  if (!q?.trim()) return res.status(400).json({ error: 'q param required' });
  try {
    const data = await tmdb('/search/tv', { query: q.trim(), page });
    res.json({
      success: true,
      page: data.page,
      total_pages: data.total_pages,
      total_results: data.total_results,
      results: (data.results || []).map(s => normaliseSearchResult(s, 'series')),
    });
  } catch (e) {
    console.error('[Series Search]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/series/trending ─────────────────────────────────────────────────
router.get('/trending', async (req, res) => {
  try {
    const data = await tmdb('/trending/tv/week');
    res.json({
      success: true,
      results: (data.results || []).map(s => normaliseSearchResult(s, 'series')),
    });
  } catch (e) {
    console.error('[Series Trending]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/series/:id ──────────────────────────────────────────────────────
router.get('/:id', async (req, res) => {
  const { id } = req.params;
  if (isNaN(id)) return res.status(400).json({ error: 'Invalid TMDB ID' });
  try {
    const [details, extIds] = await Promise.all([
      tmdb(`/tv/${id}`, { append_to_response: 'credits,videos,external_ids' }),
      tmdb(`/tv/${id}/external_ids`),
    ]);
    const series = normaliseSeries({ ...details, external_ids: extIds });

    // Add cast and trailer
    series.cast = (details.credits?.cast || []).slice(0, 10).map(c => ({
      name: c.name,
      character: c.character,
      photo: c.profile_path ? `https://image.tmdb.org/t/p/w185${c.profile_path}` : null,
    }));
    series.trailer = (details.videos?.results || []).find(
      v => v.type === 'Trailer' && v.site === 'YouTube'
    )?.key || null;

    // Season list
    series.season_list = (details.seasons || [])
      .filter(s => s.season_number > 0)
      .map(s => ({
        season_number: s.season_number,
        name: s.name,
        episode_count: s.episode_count,
        poster: s.poster_path ? `https://image.tmdb.org/t/p/w342${s.poster_path}` : null,
        air_date: s.air_date,
      }));

    res.json({ success: true, series });
  } catch (e) {
    console.error('[Series Details]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/series/:id/seasons ──────────────────────────────────────────────
// Returns episode list for a given season
router.get('/:id/seasons', async (req, res) => {
  const { id } = req.params;
  const { season = 1 } = req.query;
  try {
    const data = await tmdb(`/tv/${id}/season/${season}`);
    res.json({
      success: true,
      season_number: data.season_number,
      episodes: (data.episodes || []).map(ep => ({
        episode_number: ep.episode_number,
        name: ep.name,
        overview: ep.overview,
        still: ep.still_path ? `https://image.tmdb.org/t/p/w300${ep.still_path}` : null,
        air_date: ep.air_date,
        runtime: ep.runtime,
      })),
    });
  } catch (e) {
    console.error('[Series Seasons]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/series/:id/recommendations ─────────────────────────────────────
router.get('/:id/recommendations', async (req, res) => {
  const { id } = req.params;
  try {
    const data = await tmdb(`/tv/${id}/recommendations`);
    res.json({
      success: true,
      results: (data.results || []).slice(0, 12).map(s => normaliseSearchResult(s, 'series')),
    });
  } catch (e) {
    res.json({ success: true, results: [] });
  }
});

export default router;
