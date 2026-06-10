// ─── routes/trending.js ───────────────────────────────────────────────────────
import express from 'express';
import { tmdb, normaliseSearchResult } from './tmdb.js';

const router = express.Router();

// ─── GET /api/trending — combined movies + series ─────────────────────────────
router.get('/', async (req, res) => {
  try {
    const [movies, series] = await Promise.all([
      tmdb('/trending/movie/week'),
      tmdb('/trending/tv/week'),
    ]);
    res.json({
      success: true,
      movies:  (movies.results || []).slice(0, 10).map(m => normaliseSearchResult(m, 'movie')),
      series:  (series.results || []).slice(0, 10).map(s => normaliseSearchResult(s, 'series')),
    });
  } catch (e) {
    console.error('[Trending]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/trending/movies ─────────────────────────────────────────────────
router.get('/movies', async (req, res) => {
  try {
    const data = await tmdb('/trending/movie/week');
    res.json({
      success: true,
      results: (data.results || []).map(m => normaliseSearchResult(m, 'movie')),
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/trending/series ─────────────────────────────────────────────────
router.get('/series', async (req, res) => {
  try {
    const data = await tmdb('/trending/tv/week');
    res.json({
      success: true,
      results: (data.results || []).map(s => normaliseSearchResult(s, 'series')),
    });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

export default router;
