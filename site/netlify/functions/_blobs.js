// Minimal Netlify Blobs client (site-wide store "ngqa") without dependencies.
// On Netlify, Lambda-style functions get the Blobs endpoint and token in event.blobs (base64 JSON {url, token})
// and the site id in the x-nf-site-id header; newer functions get NETLIFY_BLOBS_CONTEXT. Same protocol as @netlify/blobs.
// Local tests: set BLOBS_DIR to a folder and the data is kept in JSON files there.
const fs = require('fs'), path = require('path');
const STORE = 'site:ngqa';
const dec = s => JSON.parse(Buffer.from(s, 'base64').toString('utf8'));
function ctx(event) {
  if (process.env.BLOBS_DIR) return { dir: process.env.BLOBS_DIR };
  if (event && event.blobs) { const d = dec(event.blobs); const h = event.headers || {}; return { url: d.url, token: d.token, site: h['x-nf-site-id'] || h['X-Nf-Site-Id'] }; }
  if (process.env.NETLIFY_BLOBS_CONTEXT) { const d = dec(process.env.NETLIFY_BLOBS_CONTEXT); return { url: d.edgeURL, token: d.token, site: d.siteID }; }
  return null;
}
const okKey = k => /^[a-z0-9][a-z0-9._-]{0,80}$/.test(k);
async function call(c, method, key, body) {
  const u = `${c.url.replace(/\/$/, '')}/${c.site}/${STORE}/${key}`;
  for (let i = 0; i < 4; i++) {
    const r = await fetch(u, { method, headers: { authorization: 'Bearer ' + c.token }, body });
    if (r.status === 429 || r.status >= 500) { await new Promise(s => setTimeout(s, 200 * 2 ** i)); continue; }
    return r;
  }
  throw new Error('האחסון לא זמין כרגע, נסו שוב');
}
module.exports = function blobs(event) {
  const c = ctx(event);
  if (!c) throw new Error('אחסון הנתונים (Netlify Blobs) לא זמין');
  return {
    async get(key) {
      if (!okKey(key)) throw new Error('bad key');
      if (c.dir) { try { return JSON.parse(fs.readFileSync(path.join(c.dir, key + '.json'), 'utf8')); } catch (e) { return null; } }
      const r = await call(c, 'GET', key);
      if (r.status === 404) return null;
      if (!r.ok) throw new Error('קריאה מהאחסון נכשלה (' + r.status + ')');
      const t = await r.text(); try { return t ? JSON.parse(t) : null; } catch (e) { return null; }
    },
    async set(key, value) {
      if (!okKey(key)) throw new Error('bad key');
      const s = JSON.stringify(value);
      if (c.dir) { fs.mkdirSync(c.dir, { recursive: true }); fs.writeFileSync(path.join(c.dir, key + '.json'), s); return; }
      const r = await call(c, 'PUT', key, s);
      if (!r.ok) throw new Error('שמירה באחסון נכשלה (' + r.status + ')');
    }
  };
};
