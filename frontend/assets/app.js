const $ = (id) => document.getElementById(id);

function show(el, yes = true) { el.classList.toggle('hidden', !yes); }
function fmt(n, digits = 0) { return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits }); }
function errorMessage(payload) {
  if (!payload) return 'Unknown error';
  if (typeof payload.detail === 'string') return payload.detail;
  if (payload.detail?.message) return payload.detail.message;
  return payload.message || JSON.stringify(payload);
}
async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(errorMessage(payload));
  return payload;
}

async function loadSystemInfo() {
  try {
    const info = await api('/api/system/info');
    $('api-status').textContent = info.api_key_configured ? 'API ready' : 'Demo ready · API key missing';
    $('model-label').textContent = `Model: ${info.model_default}`;
    $('stat-services').textContent = fmt(info.service_records);
    $('stat-policy').textContent = fmt(info.policy_chunks);
    $('stat-tools').textContent = info.tool_count;
    $('stat-eval').textContent = info.evaluation.ready ? `${info.evaluation.passed}/${info.evaluation.cases}` : '—';
  } catch (err) {
    $('api-status').textContent = 'API unavailable';
  }
}

function fillList(sectionId, listId, items) {
  const section = $(sectionId), list = $(listId);
  list.innerHTML = '';
  show(section, items.length > 0);
  items.forEach(item => {
    const li = document.createElement('li'); li.textContent = item; list.appendChild(li);
  });
}

function renderChat(data) {
  show($('answer-area'));
  $('answer').textContent = data.answer;
  $('grounding-badge').textContent = data.grounding_status === 'tool_grounded' ? 'Tool-grounded' : 'Boundary / interpretation';

  $('tools').innerHTML = '';
  show($('tools-section'), data.used_tools.length > 0);
  data.used_tools.forEach(name => {
    const span = document.createElement('span'); span.className = 'tool-badge'; span.textContent = name; $('tools').appendChild(span);
  });

  $('evidence').innerHTML = '';
  show($('evidence-section'), data.evidence.length > 0);
  data.evidence.forEach(item => {
    const card = document.createElement('div'); card.className = 'card';
    const title = document.createElement('div'); title.className = 'card-title'; title.textContent = item.source_tool;
    const body = document.createElement('div'); body.className = 'card-body'; body.textContent = item.claim;
    card.append(title, body); $('evidence').appendChild(card);
  });

  $('policy-sources').innerHTML = '';
  show($('policy-section'), data.policy_sources.length > 0);
  data.policy_sources.forEach(item => {
    const card = document.createElement('div'); card.className = 'card';
    const link = document.createElement('a'); link.href = item.source_url; link.target = '_blank'; link.rel = 'noreferrer'; link.className = 'card-title'; link.textContent = item.source_title;
    const meta = document.createElement('div'); meta.className = 'card-meta'; meta.textContent = `${item.chunk_id}${item.section ? ' · ' + item.section : ''}`;
    card.append(link, meta); $('policy-sources').appendChild(card);
  });

  fillList('method-section', 'methodology', data.methodology);
  fillList('limits-section', 'limitations', data.limitations);
  $('telemetry').textContent = `${data.model} · ${fmt(data.usage.total_tokens)} tokens · ${(data.latency_ms / 1000).toFixed(2)}s · ${data.used_tools.length} unique tool(s)`;
  $('tool-trace').textContent = JSON.stringify(data.tool_trace, null, 2);
}

async function runChat() {
  const message = $('prompt').value.trim();
  if (!message) return;
  show($('chat-error'), false); show($('chat-loading')); show($('answer-area'), false);
  $('analyse-btn').disabled = true;
  try {
    const data = await api('/api/chat', { method: 'POST', body: JSON.stringify({ message, strict_grounding: $('strict-grounding').checked }) });
    renderChat(data);
  } catch (err) {
    $('chat-error').textContent = err.message; show($('chat-error'));
  } finally {
    show($('chat-loading'), false); $('analyse-btn').disabled = false;
  }
}

async function runScenario() {
  show($('scenario-error'), false); show($('scenario-result'), false); $('scenario-btn').disabled = true;
  try {
    const payload = {
      transport_percentile: Number($('scenario-transport').value),
      capacity_percentile: Number($('scenario-capacity').value),
      state: $('scenario-state').value || null,
      urban_rural: $('scenario-area').value || null,
      minimum_gap_score: 3,
      changed_service_limit: 5,
    };
    const data = (await api('/api/scenario', { method: 'POST', body: JSON.stringify(payload) })).result;
    const scope = [data.scope.state, data.scope.urban_rural].filter(Boolean).join(' · ') || 'National';
    $('scenario-result').innerHTML = '';
    const title = document.createElement('div'); title.className = 'card-title'; title.textContent = `${scope} · P${Math.round(payload.transport_percentile*100)}/P${Math.round(payload.capacity_percentile*100)}`;
    const metrics = document.createElement('div'); metrics.className = 'scenario-metrics';
    [
      ['Baseline', data.baseline.priority_service_count],
      ['Scenario', data.scenario.priority_service_count],
      ['Change', data.change_count > 0 ? `+${data.change_count}` : data.change_count],
    ].forEach(([label, value]) => { const d = document.createElement('div'); d.className = 'mini-stat'; const s = document.createElement('strong'); s.textContent = value; const l = document.createElement('span'); l.textContent = label; d.append(s,l); metrics.appendChild(d); });
    const detail = document.createElement('div'); detail.className = 'card-body'; detail.textContent = `Transport cutoff ${data.scenario_thresholds.transport_cutoff_km.toFixed(3)} km · capacity cutoff ${data.scenario_thresholds.capacity_cutoff_places.toFixed(1)} places. ${data.interpretation_caveat}`;
    $('scenario-result').append(title, metrics, detail); show($('scenario-result'));
  } catch (err) { $('scenario-error').textContent = err.message; show($('scenario-error')); }
  finally { $('scenario-btn').disabled = false; }
}

async function lookupService() {
  const id = $('service-id').value.trim(); if (!id) return;
  show($('service-error'), false); show($('service-result'), false); $('service-btn').disabled = true;
  try {
    const p = (await api(`/api/services/${encodeURIComponent(id)}`)).profile;
    $('service-result').innerHTML = '';
    const title = document.createElement('div'); title.className = 'card-title'; title.textContent = p.service_name || p.service_approval_number;
    const meta = document.createElement('div'); meta.className = 'card-meta'; meta.textContent = `${p.service_approval_number} · ${p.state || '—'} · ${p.urban_rural || '—'} · ${p.service_type || '—'}`;
    const body = document.createElement('div'); body.className = 'card-body'; body.textContent = `${p.overall_rating || 'No rating'} · ${p.number_of_approved_places ?? '—'} approved places · ${p.nearest_public_transport_km != null ? p.nearest_public_transport_km.toFixed(1) + ' km to nearest public transport' : 'transport distance unavailable'}`;
    $('service-result').append(title, meta, body); show($('service-result'));
  } catch (err) { $('service-error').textContent = err.message; show($('service-error')); }
  finally { $('service-btn').disabled = false; }
}

document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click', () => { $('prompt').value = btn.dataset.prompt; $('prompt').focus(); }));
$('analyse-btn').addEventListener('click', runChat);
$('clear-btn').addEventListener('click', () => { $('prompt').value = ''; show($('answer-area'), false); show($('chat-error'), false); });
$('scenario-btn').addEventListener('click', runScenario);
$('service-btn').addEventListener('click', lookupService);
$('prompt').addEventListener('keydown', (e) => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') runChat(); });
loadSystemInfo();
