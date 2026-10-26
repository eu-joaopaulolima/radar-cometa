#!/usr/bin/env python3
"""Gera o site estático do Radar de Concorrência Cometa.

Uso: python3 build.py <painel.html> <meta.json> <instagram.json> <google.json> <saida/index.html>
<painel.html> é o files/index.html do dashboard no Claude (mesmo código, roda aqui com um
adaptador que imita a API `dash`). Os dados ficam embutidos; o arquivo abre sem login.
"""
import json, sys, datetime, html

painel, fm, fi, fg, out = sys.argv[1:6]
body = open(painel, encoding='utf-8').read()
data = {
    'meta': json.load(open(fm, encoding='utf-8')),
    'instagram': json.load(open(fi, encoding='utf-8')),
    'google': json.load(open(fg, encoding='utf-8')),
}
datas = sorted({r.get('data', '') for k in data for r in data[k] if r.get('data')})
ref = datas[-1] if datas else datetime.date.today().isoformat()
ref_br = f"{ref[8:10]}/{ref[5:7]}/{ref[0:4]}"

HEAD = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Radar de Concorrência Cometa</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400&display=swap" rel="stylesheet">
<style>
:root {
  --font-anthropic-sans: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-anthropic-serif: "Source Serif 4", Georgia, serif;
  --cds-gap-xs: 6px; --cds-gap-sm: 10px; --cds-gap-md: 16px; --cds-gap-xl: 32px;
  --cds-pad-sm: 10px; --cds-pad-md: 16px; --cds-pad-lg: 20px; --cds-radius: 10px;
  --cds-font-size-title: 1.9rem; --cds-font-size-heading: 1.15rem; --cds-font-size-body: .95rem; --cds-font-size-caption: .8rem;
  --cds-font-weight-medium: 600; --cds-dur-slow: .3s;
  --color-bg: #faf9f6; --color-panel: #ffffff; --color-fg: #1f1e1c; --color-fg-muted: #6b6862;
  --color-border-line: #e4e1da; --color-bad: #b4372c; --color-ok: #2f7d4f;
  --cds-chart-muted: #b9b4aa; --accent: #2557c7;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #191917; --color-panel: #222220; --color-fg: #ecebe7; --color-fg-muted: #a19e97;
    --color-border-line: #36352f; --color-bad: #e2766b; --color-ok: #6cc08f; --cds-chart-muted: #6b675f; --accent: #6f9bff;
  }
}
:root[data-theme="dark"] {
  --color-bg: #191917; --color-panel: #222220; --color-fg: #ecebe7; --color-fg-muted: #a19e97;
  --color-border-line: #36352f; --color-bad: #e2766b; --color-ok: #6cc08f; --cds-chart-muted: #6b675f; --accent: #6f9bff;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); }
body { font-family: var(--font-anthropic-sans); }
main { max-width: 1180px; margin: 0 auto; padding: 24px 16px 48px; }
.dash-skeleton { color: transparent; }
footer { margin-top: 32px; color: var(--color-fg-muted); font-size: .78rem; }
</style>
</head>
<body>
<main>
"""

SHIM = """<script>
window.__DATA = __DATA_JSON__;
(function(){
  const nf = new Intl.NumberFormat('pt-BR'), nf1 = new Intl.NumberFormat('pt-BR', {minimumFractionDigits: 1, maximumFractionDigits: 1});
  window.d3 = {
    format: (s) => s.includes('.1f') ? (v) => nf1.format(v) : (v) => nf.format(v),
    max: (arr, fn) => arr.length ? Math.max(...arr.map(fn || (x => x))) : undefined
  };
  const D = window.__DATA, calcs = {}, cache = {}, cbs = [];
  const P0 = {praca: null, marca: null, concorrente: null};
  let P = {...P0};
  try { const u = new URLSearchParams(location.hash.slice(1)); ['praca','marca','concorrente'].forEach(k => { if (u.get(k)) P[k] = u.get(k); }); } catch (e) {}
  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#2557c7';
  const fire = () => {
    try { const u = new URLSearchParams(); Object.entries(P).forEach(([k, v]) => v && u.set(k, v)); history.replaceState(null, '', u.toString() ? '#' + u : location.pathname); } catch (e) {}
    cbs.forEach(f => f());
  };
  window.dash = {
    colors: [accent],
    calc(id, o) { calcs[id] = o; },
    data(id) {
      if (D[id]) return {status: 'ok', data: D[id]};
      if (calcs[id]) { if (!cache[id]) cache[id] = calcs[id].fn(...calcs[id].inputs.map(i => D[i] || [])); return {status: 'ok', data: cache[id]}; }
      return {status: 'error', data: []};
    },
    params() { return {...P}; },
    setParams(x) { Object.assign(P, x); fire(); },
    resetParams() { P = {...P0}; fire(); },
    onData(f) { cbs.push(f); f(); }
  };
})();
</script>
"""

FOOT = f"""<footer>Dados coletados em {ref_br}: Biblioteca de Anúncios da Meta, Central de Transparência de Anúncios do Google e perfis públicos do Instagram. Atualizado toda segunda-feira. Grupo Cometa · uso interno.</footer>
</main>
</body>
</html>
"""

payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
# o painel tem <style>...</style><div class="rc">...</div><script>...</script>; o shim precisa vir antes do script do painel
i = body.find('<script>')
doc = HEAD + body[:i] + SHIM.replace('__DATA_JSON__', payload) + body[i:] + FOOT
doc = doc.replace('<p class="muted">Cáceres (Volkswagen)', f'<p class="muted">Dados de {ref_br}. Cáceres (Volkswagen)', 1)
open(out, 'w', encoding='utf-8').write(doc)
print('ok', out, len(doc), 'bytes, dados de', ref_br)
