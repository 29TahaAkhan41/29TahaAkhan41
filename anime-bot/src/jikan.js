// Jikan v4 (MyAnimeList) için küçük istemci — API anahtarı gerekmez.
const BASE = 'https://api.jikan.moe/v4';

// Jikan saniyede ~3 istek sınırı koyuyor; istekleri sıraya alıp aralıklandırıyoruz.
let queue = Promise.resolve();
const MIN_GAP_MS = 400;

async function rawGet(path, attempt = 0) {
  const res = await fetch(BASE + path);
  if (res.status === 429 && attempt < 3) {
    await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
    return rawGet(path, attempt + 1);
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Jikan hatası: ${res.status}`);
  return res.json();
}

export function get(path) {
  const job = queue.then(() => rawGet(path));
  queue = job.catch(() => {}).then(() => new Promise((r) => setTimeout(r, MIN_GAP_MS)));
  return job;
}

export const searchAnime = (q) =>
  get(`/anime?q=${encodeURIComponent(q)}&limit=10&sfw=true`).then((r) => r?.data ?? []);
export const searchManga = (q) =>
  get(`/manga?q=${encodeURIComponent(q)}&limit=10&sfw=true`).then((r) => r?.data ?? []);
export const searchCharacter = (q) =>
  get(`/characters?q=${encodeURIComponent(q)}&limit=10&order_by=favorites&sort=desc`).then((r) => r?.data ?? []);
export const randomAnime = () => get('/random/anime?sfw=true').then((r) => r?.data);
export const topAnime = (filter) =>
  get(`/top/anime?limit=10${filter ? `&filter=${filter}` : ''}`).then((r) => r?.data ?? []);
export const seasonNow = () => get('/seasons/now?limit=15&sfw=true').then((r) => r?.data ?? []);
export const schedule = (day) => get(`/schedules?filter=${day}&limit=15&sfw=true`).then((r) => r?.data ?? []);
