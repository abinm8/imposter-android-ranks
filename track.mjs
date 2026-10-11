// Daily Google Play rank check for "Imposter Game: Malayalam Party".
// Reads the Top Free "Word" games chart in each country and appends today's
// rank to android_ranks.json (rank is null when the app isn't in the top 200).
import gplay from 'google-play-scraper';
import fs from 'node:fs';

const APP_ID = 'com.malayalam.impostergame';
const OUT = 'android_ranks.json';
const COUNTRIES = [
  ['India', 'in', 'Home'],
  ['UAE', 'ae', 'Gulf'], ['Saudi Arabia', 'sa', 'Gulf'], ['Qatar', 'qa', 'Gulf'],
  ['Kuwait', 'kw', 'Gulf'], ['Oman', 'om', 'Gulf'], ['Bahrain', 'bh', 'Gulf'],
  ['United States', 'us', 'Diaspora'], ['United Kingdom', 'gb', 'Diaspora'],
  ['Canada', 'ca', 'Diaspora'], ['Australia', 'au', 'Diaspora'],
  ['New Zealand', 'nz', 'Diaspora'], ['Ireland', 'ie', 'Diaspora'],
  ['Singapore', 'sg', 'Diaspora'], ['Malaysia', 'my', 'Diaspora'], ['Germany', 'de', 'Diaspora'],
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const today = new Date().toISOString().slice(0, 10);
const history = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : [];
const kept = history.filter((r) => r.date !== today); // re-running a day replaces it

let failures = 0;
for (const [country, code, region] of COUNTRIES) {
  let rank = null, error;
  try {
    const list = await gplay.list({
      collection: gplay.collection.TOP_FREE,
      category: gplay.category.GAME_WORD,
      country: code,
      lang: 'en',
      num: 200,
    });
    const i = list.findIndex((a) => a.appId === APP_ID);
    rank = i === -1 ? null : i + 1;
  } catch (e) {
    error = String(e.message || e);
    failures++;
  }
  kept.push({ date: today, store: 'Google Play', country, code, region, rank, ...(error ? { error } : {}) });
  console.log(`${code}  ${rank ?? '—'}${error ? '  (error: ' + error + ')' : ''}`);
  await sleep(1500); // stay gentle with Google Play
}

fs.writeFileSync(OUT, JSON.stringify(kept, null, 1));
if (failures === COUNTRIES.length) {
  console.error('Every country failed — Google Play may have changed its pages. Try `npm update google-play-scraper`.');
  process.exit(1);
}
