# 🎬 Cymor Movie Hub API v2 — CLEAN EDITION
> By Legendary Smiley Cymor | Always a winner. | ZERO ADS. ZERO IFRAMES.

## How it works
- **TMDB** → all metadata, search, trending, posters, cast, trailers
- **YTS API** → movie magnet links (720p/1080p/4K) — no ads, official API
- **EZTV API** → TV episode magnet links — no ads, official API
- **Frontend** → WebTorrent.js streams magnets directly in the browser

## ⚡ Setup — ONE required step

In Render dashboard → Environment:
```
TMDB_API_KEY = your_key_here
```

## 📡 Endpoints

| Endpoint | What it returns |
|----------|----------------|
| `GET /api/trending` | Trending movies + series from TMDB |
| `GET /api/trending/movies` | Trending movies |
| `GET /api/trending/series` | Trending series |
| `GET /api/trending/popular/movies` | Popular movies |
| `GET /api/trending/popular/series` | Popular series |
| `GET /api/trending/top-rated/movies` | Top rated movies |
| `GET /api/trending/top-rated/series` | Top rated series |
| `GET /api/trending/genres/movies?genre_id=28` | Browse by genre |
| `GET /api/movies/search?q=inception` | Search movies |
| `GET /api/movies/{tmdb_id}` | Movie details + cast + trailer |
| `GET /api/movies/{tmdb_id}/sources` | YTS magnet links (all qualities) |
| `GET /api/series/search?q=breaking+bad` | Search series |
| `GET /api/series/{tmdb_id}` | Series details + season list |
| `GET /api/series/{tmdb_id}/season/{n}` | All episodes with stills |
| `GET /api/series/{tmdb_id}/sources?season=1&episode=1` | EZTV magnet links |
| `GET /api/downloads/proxy?url=...` | Proxy .torrent file download |
| `GET /api/downloads/check?url=...` | Test URL reachability |

## 🎬 Frontend Streaming (WebTorrent)
```html
<script src="https://cdn.jsdelivr.net/npm/webtorrent/webtorrent.min.js"></script>
<video id="player" controls></video>
<script>
  const client = new WebTorrent();
  // magnet comes from /api/movies/{id}/sources
  client.add(magnet, torrent => {
    const file = torrent.files.find(f => f.name.endsWith('.mp4') || f.name.endsWith('.mkv'));
    file.renderTo('#player');
  });
</script>
```

## TMDB Genre IDs
Action=28, Comedy=35, Drama=18, Horror=27, Romance=10749,
Sci-Fi=878, Thriller=53, Animation=16, Documentary=99

---
*Cymor Tech Services — Always a winner.* 🏆
