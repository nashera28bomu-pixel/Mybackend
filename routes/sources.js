// ─── routes/sources.js ────────────────────────────────────────────────────────
// Primary: ezvidapi.com — sandbox-friendly, no ads, no redirects, free, no key
// Fallback: multiembed (SuperEmbed) — TMDB native, no sandbox issues
import express from 'express';

const router = express.Router();

// ─── Build embed URLs — TMDB ID only, no IMDB needed ─────────────────────────
function movieEmbeds(tmdbId) {
  return [
    {
      provider: 'EzVid (Auto)',
      url: `https://ezvidapi.com/embed/movie/${tmdbId}`,
      type: 'iframe',
    },
    {
      provider: 'EzVid (VidSrc)',
      url: `https://ezvidapi.com/embed/movie/${tmdbId}?provider=vidsrc`,
      type: 'iframe',
    },
    {
      provider: 'EzVid (Stremio)',
      url: `https://ezvidapi.com/embed/movie/${tmdbId}?provider=stremio`,
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
      provider: 'EzVid (Auto)',
      url: `https://ezvidapi.com/embed/tv/${tmdbId}/${season}/${episode}`,
      type: 'iframe',
    },
    {
      provider: 'EzVid (VidSrc)',
      url: `https://ezvidapi.com/embed/tv/${tmdbId}/${season}/${episode}?provider=vidsrc`,
      type: 'iframe',
    },
    {
      provider: 'EzVid (Stremio)',
      url: `https://ezvidapi.com/embed/tv/${tmdbId}/${season}/${episode}?provider=stremio`,
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
