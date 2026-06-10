// ─── routes/sources.js ────────────────────────────────────────────────────────
// 5-provider chain — most reliable first
// No sandbox needed, no heavy redirects, TMDB IDs work on all
import express from 'express';

const router = express.Router();

function movieEmbeds(tmdbId) {
  return [
    {
      provider: 'VidBinge',
      url: `https://vidbinge.to/movie/${tmdbId}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc ICU',
      url: `https://vidsrc.icu/embed/movie/${tmdbId}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc Pro',
      url: `https://vidsrc.pro/embed/movie/${tmdbId}`,
      type: 'iframe',
    },
    {
      provider: 'AutoEmbed',
      url: `https://autoembed.co/movie/tmdb/${tmdbId}`,
      type: 'iframe',
    },
    {
      provider: 'SuperEmbed',
      url: `https://multiembed.mov/?video_id=${tmdbId}&tmdb=1`,
      type: 'iframe',
    },
  ];
}

function episodeEmbeds(tmdbId, season, episode) {
  return [
    {
      provider: 'VidBinge',
      url: `https://vidbinge.to/tv/${tmdbId}/${season}/${episode}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc ICU',
      url: `https://vidsrc.icu/embed/tv/${tmdbId}/${season}/${episode}`,
      type: 'iframe',
    },
    {
      provider: 'VidSrc Pro',
      url: `https://vidsrc.pro/embed/tv/${tmdbId}/${season}/${episode}`,
      type: 'iframe',
    },
    {
      provider: 'AutoEmbed',
      url: `https://autoembed.co/tv/tmdb/${tmdbId}-${season}-${episode}`,
      type: 'iframe',
    },
    {
      provider: 'SuperEmbed',
      url: `https://multiembed.mov/?video_id=${tmdbId}&tmdb=1&s=${season}&e=${episode}`,
      type: 'iframe',
    },
  ];
}

// ─── GET /api/sources/movie/:tmdbId ──────────────────────────────────────────
router.get('/movie/:tmdbId', (req, res) => {
  const { tmdbId } = req.params;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });
  res.json({
    success: true,
    tmdb_id: Number(tmdbId),
    type: 'movie',
    sources: movieEmbeds(tmdbId),
  });
});

// ─── GET /api/sources/episode/:tmdbId?season=1&episode=1 ─────────────────────
router.get('/episode/:tmdbId', (req, res) => {
  const { tmdbId } = req.params;
  const { season = '1', episode = '1' } = req.query;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });
  res.json({
    success: true,
    tmdb_id: Number(tmdbId),
    type: 'episode',
    season: Number(season),
    episode: Number(episode),
    sources: episodeEmbeds(tmdbId, season, episode),
  });
});

export default router;
