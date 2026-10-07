/* Same-origin, failure-safe public feed; no localhost calls, auth or uploads. */
'use strict';
const base = document.body.dataset.base || '';
const byId = id => document.getElementById(id);
const finiteScore = value => typeof value === 'number' && Number.isFinite(value) ? value.toFixed(4) : 'not available';
function text(node, value) { if (node) node.textContent = value; }
function link(url, label) {
  const node = document.createElement('a');
  try { const checked = new URL(url, location.href); if (checked.protocol !== 'https:' && checked.origin !== location.origin) throw Error(); node.href = checked.href; }
  catch { const fallback = document.createElement('span'); fallback.textContent = label; return fallback; }
  node.textContent = label; return node;
}
function makeTable(headers, rows) {
  const wrap = document.createElement('div'); wrap.className = 'table-scroll';
  const table = document.createElement('table');
  const head = document.createElement('thead'); const top = document.createElement('tr');
  headers.forEach(h => { const cell = document.createElement('th'); cell.scope = 'col'; cell.textContent = h; top.append(cell); }); head.append(top); table.append(head);
  const body = document.createElement('tbody');
  rows.forEach(row => { const tr = document.createElement('tr'); row.forEach(v => { const cell = document.createElement('td'); if (v instanceof Node) cell.append(v); else cell.textContent = v == null ? '—' : String(v); tr.append(cell); }); body.append(tr); });
  table.append(body); wrap.append(table); return wrap;
}
document.querySelectorAll('[data-copy-id]').forEach(button => button.addEventListener('click', async () => {
  const target = byId(button.dataset.copyId); if (!target) return;
  const original = button.textContent;
  try { if (!navigator.clipboard) throw Error('no clipboard'); await navigator.clipboard.writeText(target.textContent.trim()); button.textContent = 'Copied ✓'; }
  catch { const selection = window.getSelection(); const range = document.createRange(); range.selectNodeContents(target); selection.removeAllRanges(); selection.addRange(range); button.textContent = 'Selected — copy this text'; }
  setTimeout(() => { button.textContent = original; }, 2400);
}));
async function refreshFeed() {
  try {
    const response = await fetch(`${base}data/source-feed.json`, {cache: 'no-store'});
    if (!response.ok) throw Error(`HTTP ${response.status}`);
    let feed = await response.json();
    try {
      const runsResponse = await fetch('https://api.github.com/repos/buffedlizard55-lab/GEMSDOE47/actions/workflows/site.yml/runs?branch=arena%2F50b2a166-gemsdoe47&status=success&per_page=1', {cache:'no-store', headers:{Accept:'application/vnd.github+json'}});
      if (!runsResponse.ok) throw Error('public feed run unavailable');
      const feedSha = (await runsResponse.json()).workflow_runs?.[0]?.head_sha;
      if (!feedSha || !/^[0-9a-f]{40}$/.test(feedSha)) throw Error('no completed feed publication');
      const checkResponse = await fetch(`https://api.github.com/repos/buffedlizard55-lab/GEMSDOE47/commits/${feedSha}/check-runs?check_name=Permitted%20public%20source%20feed&filter=latest`, {cache:'no-store', headers:{Accept:'application/vnd.github+json'}});
      if (checkResponse.ok) {
        const checks = (await checkResponse.json()).check_runs || [];
        const latest = checks.find(check => check.name === 'Permitted public source feed' && check.status === 'completed' && check.output?.summary?.includes('```base64json\n'));
        if (latest) {
          const encoded = latest.output.summary.split('```base64json\n')[1].split('\n```')[0].trim();
          const bytes = Uint8Array.from(atob(encoded), ch => ch.charCodeAt(0));
          feed = JSON.parse(new TextDecoder().decode(bytes));
          if (byId('feed-timestamp')) byId('feed-timestamp').dataset.receiptUrl = latest.html_url;
        }
      }
    } catch { /* Retain same-origin dated fallback, never invent a fresh observation. */ }
    const board = feed.leaderboard || {};
    const observed = board.observed_utc || board.observed_date || 'not retained';
    const stale = board.status !== 'FRESH_OFFICIAL_PARTICIPANT_OBSERVATION' || (board.observed_utc && Date.now() - Date.parse(board.observed_utc) > 36 * 3600 * 1000);
    const rows = Array.isArray(board.rows) ? board.rows : [];
    text(byId('feed-status'), `${stale ? 'Dated / stale observation — not a fresh live score.' : 'Official participant table freshly fetched.'} Last observation: ${observed}. ${feed.permission_boundary || ''} ${feed.fetch_failures || 0} fetch/parser failures; ${feed.policy_skips || 0} permission-policy skips.`);
    text(byId('feed-timestamp'), `Last automation run: ${feed.generated_utc || feed.generated_date || 'not recorded'}. Daily scheduled refresh via public GitHub Checks receipt. This does not re-run models or authorize submissions.`);
    if (rows.length && typeof rows[0].score === 'number') document.querySelectorAll('.live-top-score').forEach(node => text(node, finiteScore(rows[0].score)));
    if (byId('leaderboard-table')) byId('leaderboard-table').replaceChildren(makeTable(['Rank','Participant / team','Public score'], rows.map(row => [row.rank, row.profile_url ? link(row.profile_url,row.participant || 'name not retained') : row.participant || 'name not retained', finiteScore(row.score)])));
    if (byId('source-feed-table')) byId('source-feed-table').replaceChildren(makeTable(['Source / evidence class','Last attempt / status','Last successful fetch / content SHA-256'], (feed.sources || []).map(source => {
      const name = document.createElement('div'); name.append(link(source.url, source.title)); const kind = document.createElement('div'); kind.className='tag'; kind.textContent=source.evidence_class; name.append(document.createElement('br'),kind);
      const state = document.createElement('div'); state.textContent = source.status || 'no result'; const when = document.createElement('div'); when.className='hash-tiny'; when.textContent=source.last_attempt_utc || source.policy_checked_utc || 'not recorded'; state.append(when); if (source.error_type) { const error=document.createElement('small'); error.textContent=source.error_type; state.append(error); }
      const proof = document.createElement('div'); proof.className='hash-tiny'; proof.textContent=`${source.last_success_utc || 'no successful automated fetch'}\n${source.content_sha256 || 'no content hash acquired'}`;
      return [name,state,proof];
    })));
  } catch (error) {
    text(byId('feed-status'), 'Automatic feed unavailable in this viewer. The dated 6 October 2026 observation is retained; no fresh score is inferred. Open the deployed Pages site or its JSON receipt.');
    text(byId('feed-timestamp'), `Feed request failed: ${error.message}.`);
  }
}
async function showProbes() {
  if (!byId('official-probe-results')) return;
  try {
    const response = await fetch(`${base}data/official-download-probes.json`, {cache:'no-store'});
    if (!response.ok) throw Error(); const data=await response.json();
    byId('official-probe-results').replaceChildren(makeTable(['Official data source','Actual result','Geometry / footprint coverage'],(data.sources || []).map(source=>[
      link(source.source_page,source.id),source.status,source.layers && source.layers.length ? source.layers.map(layer=>`${layer.layer}: ${layer.pixels_in_template_footprint ?? 'not verified'} pixels; ${layer.geometry_types?.join('/') || layer.status}`).join('; ') : source.error_type || 'no geometry count verified'
    ])));
  } catch { text(byId('official-probe-results'),'No deployed probe receipt could be loaded. Source links alone are not byte or coverage verification.'); }
}
refreshFeed(); showProbes();
