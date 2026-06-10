// ─── server.js ────────────────────────────────────────────────────────────────
import express from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';

import moviesRouter    from './routes/movies.js';
import seriesRouter    from './routes/series.js';
import trendingRouter  from './routes/trending.js';
import sourcesRouter   from './routes/sources.js';
import downloadsRouter from './routes/downloads.js';

const app  = express();
const PORT = process.env.PORT || 3000;

// ─── Trust Render proxy ───────────────────────────────────────────────────────
app.set('trust proxy', 1);

// ─── CORS ─────────────────────────────────────────────────────────────────────
app.use(cors({
  origin: [
    'https://cymor-movie-hub-api-3n1z.onrender.com',
    'https://cymormoviehub.onrender.com',
    /\.onrender\.com$/,
    /\.netlify\.app$/,
    /\.vercel\.app$/,
    'http://localhost:3000',
    'http://localhost:5500',
    'http://127.0.0.1:5500',
  ],
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json());

// ─── Rate limiter (generous — protects Render free tier) ─────────────────────
app.use('/api/', rateLimit({
  windowMs: 60 * 1000,   // 1 minute
  max: 120,
  standardHeaders: true,
  legacyHeaders: false,
  message: { success: false, error: 'Too many requests, slow down a bit.' },
}));

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use('/api/movies',    moviesRouter);
app.use('/api/series',    seriesRouter);
app.use('/api/trending',  trendingRouter);
app.use('/api/sources',   sourcesRouter);
app.use('/api/downloads', downloadsRouter);

// ─── Health check ─────────────────────────────────────────────────────────────
app.get('/', (_, res) => res.json({
  name: 'Cymor Movie Hub API',
  version: '3.1.0',
  status: 'online',
  endpoints: [
    'GET  /api/movies/search?q=&page=',
    'GET  /api/movies/trending',
    'GET  /api/movies/:tmdbId',
    'GET  /api/movies/:tmdbId/recommendations',
    'GET  /api/series/search?q=&page=',
    'GET  /api/series/trending',
    'GET  /api/series/:tmdbId',
    'GET  /api/series/:tmdbId/seasons',
    'GET  /api/trending',
    'GET  /api/sources/movie/:tmdbId',
    'GET  /api/sources/episode/:tmdbId?season=&episode=',
    'GET  /api/downloads/movie/:imdbId',
    'GET  /api/downloads/series/:imdbId?season=&episode=',
  ],
}));

app.listen(PORT, () => console.log(`🎬 Cymor Movie Hub API running on port ${PORT}`));
