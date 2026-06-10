// ─── routes/sources.js ────────────────────────────────────────────────────────
// Returns array of embed URLs — frontend tries each in order
// All providers are free, no ads on the embed player itself
import express from 'express';
import { tmdb } from './tmdb.js';

const router = express.Router();

// ─── Build embed URLs from IMDB/TMDB ID ──────────────────────────────────────
function movieEmbeds(imdbId, tmdbId) {
  return [
    {
      provider: 'VidSrc Pro',
      url: `https://vidsrc.pro/embed/movie/${imdbId}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc',
      url: `https://vidsrc.me/embed/movie?imdb=${imdbId}`,
      type: 'iframe',
    },
    {
      provider: '2Embed',
      url: `https://www.2embed.cc/embed/${imdbId}`,
      type: 'iframe',
    },
    {
      provider: 'EmbedSu',
      url: `https://embed.su/embed/movie/${tmdbId}`,
      type: 'iframe',
    },
  ];
}

function episodeEmbeds(imdbId, tmdbId, season, episode) {
  return [
    {
      provider: 'VidSrc Pro',
      url: `https://vidsrc.pro/embed/tv/${imdbId}/${season}/${episode}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc',
      url: `https://vidsrc.me/embed/tv?imdb=${imdbId}&season=${season}&episode=${episode}`,
      type: 'iframe',
    },
    {
      provider: '2Embed',
      url: `https://www.2embed.cc/embedtv/${imdbId}&s=${season}&e=${episode}`,
      type: 'iframe',
    },
    {
      provider: 'EmbedSu',
      url: `https://embed.su/embed/tv/${tmdbId}/${season}/${episode}`,
      type: 'iframe',
    },
  ];
}

// ─── GET /api/sources/movie/:tmdbId ──────────────────────────────────────────
router.get('/movie/:tmdbId', async (req, res) => {
  const { tmdbId } = req.params;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    // Get IMDB ID from TMDB
    const extIds = await tmdb(`/movie/${tmdbId}/external_ids`);
    const imdbId = extIds.imdb_id;

    if (!imdbId) {
      return res.status(404).json({ success: false, error: 'No IMDB ID found for this movie' });
    }

    res.json({
      success: true,
      tmdb_id: Number(tmdbId),
      imdb_id: imdbId,
      type: 'movie',
      sources: movieEmbeds(imdbId, tmdbId),
    });
  } catch (e) {
    console.error('[Movie Sources]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/sources/episode/:tmdbId?season=1&episode=1 ─────────────────────
router.get('/episode/:tmdbId', async (req, res) => {
  const { tmdbId } = req.params;
  const { season = '1', episode = '1' } = req.query;

  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    const extIds = await tmdb(`/tv/${tmdbId}/external_ids`);
    const imdbId = extIds.imdb_id;

    if (!imdbId) {
      return res.status(404).json({ success: false, error: 'No IMDB ID found for this series' });
    }

    res.json({
      success: true,
      tmdb_id: Number(tmdbId),
      imdb_id: imdbId,
      type: 'episode',
      season: Number(season),
      episode: Number(episode),
      sources: episodeEmbeds(imdbId, tmdbId, season, episode),
    });
  } catch (e) {
    console.error('[Episode Sources]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

export default router;
