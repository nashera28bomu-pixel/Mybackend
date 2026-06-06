# 🎬 Cymor Movie Hub — Python Backend API

> By **Legendary Smiley Cymor** | Cymor Tech Services | *Always a winner.*

A FastAPI microservice wrapping the `moviebox-api` Python library.
Connect this backend to any frontend (React, Next.js, plain HTML, etc.) hosted on Vercel or Netlify.

---

## 📁 Project Structure

```
cymor-movie-hub-backend/
├── main.py                  # FastAPI app entry point
├── routers/
│   ├── movies.py            # /api/movies/* endpoints
│   ├── series.py            # /api/series/* endpoints
│   ├── downloads.py         # /api/downloads/* endpoints
│   └── trending.py          # /api/trending/* endpoints
├── utils/
│   ├── cache.py             # In-memory TTL cache
│   └── serializers.py       # Model → JSON converters
├── requirements.txt
├── render.yaml              # Render free tier config
├── Procfile
└── .gitignore
```

---

## 🚀 Local Setup

```bash
# 1. Clone & enter folder
cd cymor-movie-hub-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload --port 8000
```

Open: http://localhost:8000
Swagger docs: http://localhost:8000/docs

---

## 🌐 Deploy to Render (Free Tier)

1. Push this folder to a GitHub repo
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. Deploy — your API will be at `https://cymor-movie-hub-api.onrender.com`

---

## 📡 API Endpoints

### Movies

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/movies/search?q={title}` | Search movies |
| GET | `/api/movies/{page_url_encoded}` | Movie details |
| GET | `/api/movies/{page_url_encoded}/downloads` | Video + subtitle links |

### TV Series

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/series/search?q={title}` | Search TV series |
| GET | `/api/series/{page_url_encoded}` | Series details |
| GET | `/api/series/{page_url_encoded}/downloads?season=1&episode=1` | Episode download links |

### Downloads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/downloads/proxy?url={url}&filename={name}` | Stream/download a file |
| GET | `/api/downloads/redirect?url={url}` | Redirect to direct URL |

### Trending

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/trending` | Trending movies + series |
| GET | `/api/trending/movies` | Trending movies only |
| GET | `/api/trending/series` | Trending series only |

---

## 🔗 Connecting From Your Frontend (JavaScript)

```js
const API_BASE = "https://cymor-movie-hub-api.onrender.com"; // or localhost:8000

// Search movies
const searchMovies = async (query) => {
  const res = await fetch(`${API_BASE}/api/movies/search?q=${encodeURIComponent(query)}`);
  return res.json();
};

// Get movie details
const getMovieDetails = async (pageUrl) => {
  const res = await fetch(`${API_BASE}/api/movies/${encodeURIComponent(pageUrl)}`);
  return res.json();
};

// Get download links
const getMovieDownloads = async (pageUrl) => {
  const res = await fetch(`${API_BASE}/api/movies/${encodeURIComponent(pageUrl)}/downloads`);
  return res.json();
};

// Get TV series episode downloads
const getEpisodeDownloads = async (pageUrl, season, episode) => {
  const res = await fetch(
    `${API_BASE}/api/series/${encodeURIComponent(pageUrl)}/downloads?season=${season}&episode=${episode}`
  );
  return res.json();
};

// Get trending
const getTrending = async () => {
  const res = await fetch(`${API_BASE}/api/trending`);
  return res.json();
};
```

---

## ⚡ Caching Strategy

| Data Type | TTL |
|-----------|-----|
| Search results | 10 minutes |
| Movie/Series details | 30 minutes |
| Download links | 30 minutes |
| Trending | 1 hour |

Caching is in-memory (resets on Render free tier sleep). Good enough for 5–100 daily users.

---

## ⚠️ Notes

- The `moviebox-api` library scrapes MovieBox — links may occasionally break if MovieBox changes their site.
- V2 and V3 docs are still "Coming Soon" — this backend uses the stable V1 API.
- Render free tier sleeps after 15 minutes of inactivity. First request after sleep takes ~30s. Consider adding a UptimeRobot ping to keep it warm.

---

*Cymor Tech Services — Always a winner.* 🏆
