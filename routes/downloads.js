// ─── routes/downloads.js ──────────────────────────────────────────────────────
import express from 'express';
import { tmdb } from './tmdb.js';

const router = express.Router();

// ─── GET /api/downloads/movie/:tmdbId ────────────────────────────────────────
router.get('/movie/:tmdbId', async (req, res) => {
  const { tmdbId } = req.params;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    // Get IMDB ID first
    const extIds = await tmdb(`/movie/${tmdbId}/external_ids`);
    const imdbId = extIds.imdb_id;
    if (!imdbId) return res.status(404).json({ error: 'No IMDB ID found' });

    // Query YTS
    const ytsRes = await fetch(
      `https://yts.mx/api/v2/movie_details.json?imdb_id=${imdbId}&with_images=false&with_cast=false`,
      { signal: AbortSignal.timeout(10000) }
    );
    const ytsData = await ytsRes.json();
    const movie   = ytsData?.data?.movie;

    if (!movie || !movie.torrents?.length) {
      return res.json({ success: true, downloads: [], message: 'No downloads available for this title' });
    }

    const downloads = movie.torrents.map(t => ({
      quality:   t.quality,
      type:      t.type,         // bluray / web
      size:      t.size,
      seeds:     t.seeds,
      peers:     t.peers,
      magnet:    `magnet:?xt=urn:btih:${t.hash}&dn=${encodeURIComponent(movie.title_long)}&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://glotorrents.pw:6969/announce&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://torrent.gresille.org:80/announce`,
      torrent_url: t.url,
    }));

    res.json({
      success:   true,
      title:     movie.title_long,
      imdb_id:   imdbId,
      cover:     movie.medium_cover_image,
      downloads,
    });
  } catch (e) {
    console.error('[Downloads Movie]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/downloads/series/:tmdbId?season=1&episode=1 ────────────────────
router.get('/series/:tmdbId', async (req, res) => {
  const { tmdbId } = req.params;
  const { season = '1', episode = '1' } = req.query;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    // Get IMDB ID + series name
    const [extIds, details] = await Promise.all([
      tmdb(`/tv/${tmdbId}/external_ids`),
      tmdb(`/tv/${tmdbId}`),
    ]);
    const imdbId = extIds.imdb_id;
    const title  = details.name || details.original_name || '';

    if (!imdbId) return res.status(404).json({ error: 'No IMDB ID found' });

    // Query EZTV
    const ezRes  = await fetch(
      `https://eztv.re/api/get-torrents?imdb_id=${imdbId.replace('tt', '')}&limit=20`,
      { signal: AbortSignal.timeout(10000) }
    );
    const ezData = await ezRes.json();
    const all    = ezData?.torrents || [];

    // Filter to requested season/episode
    const s = String(season).padStart(2, '0');
    const e = String(episode).padStart(2, '0');
    const pattern = new RegExp(`[Ss]${s}[Ee]${e}|${Number(season)}x${Number(episode).toString().padStart(2,'0')}`, 'i');

    const matched = all.filter(t => pattern.test(t.title));
    const source  = matched.length ? matched : all.slice(0, 5); // fallback to latest if no match

    const downloads = source.map(t => ({
      title:       t.title,
      quality:     t.title.match(/1080p|720p|480p|2160p|4K/i)?.[0] || 'Unknown',
      size:        t.size_bytes ? formatBytes(t.size_bytes) : 'Unknown',
      seeds:       t.seeds || 0,
      magnet:      t.magnet_url,
      torrent_url: t.torrent_url,
    }));

    res.json({
      success: true,
      title,
      imdb_id: imdbId,
      season:  Number(season),
      episode: Number(episode),
      downloads,
    });
  } catch (e) {
    console.error('[Downloads Series]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── Helper ───────────────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (!bytes) return 'Unknown';
  const gb = bytes / 1e9;
  const mb = bytes / 1e6;
  return gb >= 1 ? `${gb.toFixed(2)} GB` : `${mb.toFixed(0)} MB`;
}

export default router;
