// ─── routes/sources.js ────────────────────────────────────────────────────────
// MovieBox API via Cloudflare Worker — direct HLS streams, zero ads, no iframe
// Worker: https://cymormoviehub.nashera28bomu.workers.dev
import express from 'express';

const MOVIEBOX = 'https://cymormoviehub.nashera28bomu.workers.dev';
const router   = express.Router();

// ─── Search MovieBox by title, return best match slug + subject_id ────────────
async function findMovieBoxMatch(title, year, type) {
  const res  = await fetch(
    `${MOVIEBOX}/search?q=${encodeURIComponent(title)}`,
    { signal: AbortSignal.timeout(10000) }
  );
  if (!res.ok) throw new Error(`MovieBox search ${res.status}`);
  const data = await res.json();

  // Results are in data.data.list or data.list depending on version
  const list = data?.data?.list || data?.list || data?.results || [];
  if (!list.length) throw new Error('No MovieBox results');

  // Find best match — prefer same year and type
  const typeKeyword = type === 'series' ? 'series' : 'movie';
  let match = list.find(item => {
    const itemYear  = String(item.year || item.release_date || '').slice(0, 4);
    const itemTitle = (item.title || item.name || '').toLowerCase();
    return itemYear === String(year) && itemTitle.includes(title.toLowerCase().slice(0, 8));
  });

  // Fallback: just take first result
  if (!match) match = list[0];

  return {
    subject_id:  String(match.id || match.subjectId || match.subject_id),
    detail_path: match.detailPath || match.detail_path || match.slug || '',
    title:       match.title || match.name || title,
  };
}

// ─── Build stream URL from subject_id + detail_path ──────────────────────────
function buildStreamUrl(subjectId, detailPath, season = 0, episode = 0, resolution = 0) {
  let url = `${MOVIEBOX}/watch/${subjectId}?detail_path=${encodeURIComponent(detailPath)}&resolution=${resolution}`;
  if (season  > 0) url += `&se=${season}`;
  if (episode > 0) url += `&ep=${episode}`;
  return url;
}

function buildApiStreamUrl(subjectId, detailPath, season = 0, episode = 0) {
  let url = `${MOVIEBOX}/api/stream/${subjectId}?detail_path=${encodeURIComponent(detailPath)}`;
  if (season  > 0) url += `&se=${season}`;
  if (episode > 0) url += `&ep=${episode}`;
  return url;
}

// ─── GET /api/sources/movie/:tmdbId ──────────────────────────────────────────
router.get('/movie/:tmdbId', async (req, res) => {
  const { tmdbId } = req.params;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    // Get movie title + year from TMDB for MovieBox search
    const { tmdb } = await import('./tmdb.js');
    const details  = await tmdb(`/movie/${tmdbId}`);
    const title    = details.title || details.original_title;
    const year     = details.release_date?.slice(0, 4) || '';

    // Find on MovieBox
    const match = await findMovieBoxMatch(title, year, 'movie');

    // Build source options (different resolutions)
    const sources = [
      {
        provider: 'MovieBox Auto',
        url:      buildStreamUrl(match.subject_id, match.detail_path, 0, 0, 0),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 1080p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, 0, 0, 1080),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 720p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, 0, 0, 720),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 480p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, 0, 0, 480),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
    ];

    res.json({
      success:    true,
      tmdb_id:    Number(tmdbId),
      type:       'movie',
      mb_title:   match.title,
      subject_id: match.subject_id,
      detail_path: match.detail_path,
      sources,
    });
  } catch (e) {
    console.error('[Sources Movie]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

// ─── GET /api/sources/episode/:tmdbId?season=1&episode=1 ─────────────────────
router.get('/episode/:tmdbId', async (req, res) => {
  const { tmdbId }              = req.params;
  const { season = '1', episode = '1' } = req.query;
  if (isNaN(tmdbId)) return res.status(400).json({ error: 'Invalid TMDB ID' });

  try {
    const { tmdb } = await import('./tmdb.js');
    const details  = await tmdb(`/tv/${tmdbId}`);
    const title    = details.name || details.original_name;
    const year     = details.first_air_date?.slice(0, 4) || '';

    const match = await findMovieBoxMatch(title, year, 'series');

    const sources = [
      {
        provider: 'MovieBox Auto',
        url:      buildStreamUrl(match.subject_id, match.detail_path, Number(season), Number(episode), 0),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 1080p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, Number(season), Number(episode), 1080),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 720p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, Number(season), Number(episode), 720),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
      {
        provider: 'MovieBox 480p',
        url:      buildStreamUrl(match.subject_id, match.detail_path, Number(season), Number(episode), 480),
        type:     'direct',
        subject_id:  match.subject_id,
        detail_path: match.detail_path,
      },
    ];

    res.json({
      success:     true,
      tmdb_id:     Number(tmdbId),
      type:        'episode',
      season:      Number(season),
      episode:     Number(episode),
      mb_title:    match.title,
      subject_id:  match.subject_id,
      detail_path: match.detail_path,
      sources,
    });
  } catch (e) {
    console.error('[Sources Episode]', e.message);
    res.status(500).json({ success: false, error: e.message });
  }
});

export default router;
