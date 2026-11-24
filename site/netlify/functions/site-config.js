// Public site settings for the pages (v3.13): which courses have recorded lessons, whether PDF downloads are shown,
// and the edited "מידע על הקורס" texts. Nothing secret here; cached for a minute.
const { getConfig, recList, json, COURSE_ROLES } = require('./_common');
const blobs = require('./_blobs');
exports.handler = async (event) => {
  let cfg; try { cfg = await getConfig(blobs(event)); } catch (e) { cfg = await getConfig({ get: async () => null }); }
  const info = {}, pdf = {};
  for (const c of COURSE_ROLES) { const x = cfg.courses[c]; if (x.info) info[c] = x.info; pdf[c] = x.pdf !== false; }
  return json(200, { rec: recList(cfg), pdf, info }, 'public, max-age=60');
};
