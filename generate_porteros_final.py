#!/usr/bin/env python3
"""
Genera Goalkicks_interactive.html a partir de datos sin comprimir.
Fuente de datos: goalkicks_dataset.csv y goalkicks_sequences_final.json

Lee los archivos exportados (sin comprimir) y genera el HTML con zlib+base64 compression.

Uso:
  python3 generate_porteros_final.py

Salida:
  - Goalkicks_interactive.html (HTML final con datos comprimidos)
"""
import csv, json, os, base64, zlib

# ─── CONFIG ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "/Users/guillermosierradiaz-vargas/Desktop/RRC_analisis/Porteros"
INPUT_CSV  = os.path.join(OUTPUT_DIR, "goalkicks_dataset.csv")
INPUT_JSON = os.path.join(OUTPUT_DIR, "goalkicks_sequences_final.json")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "Goalkicks_interactive.html")

# ─── LOAD DATA ─────────────────────────────────────────────────────────────────
print("Leyendo datos...")

# Leer CSV
with open(INPUT_CSV, 'r', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    embedded_data = []
    for row in reader:
        # Convertir tipos de datos apropiadamente
        row_data = [
            row.get('matchId'),
            row.get('liga'),
            float(row.get('sequenceId')) if row.get('sequenceId') else None,
            float(row.get('periodId')) if row.get('periodId') and row.get('periodId') != 'None' else None,
            float(row.get('minute')) if row.get('minute') else 0,
            float(row.get('second')) if row.get('second') else 0,
            row.get('jugador'),
            row.get('playerId'),
            row.get('equipo'),
            row.get('temporada'),
            row.get('rival'),
            row.get('fecha'),
            row.get('competencia'),
            float(row.get('x')) if row.get('x') and row.get('x') != 'None' else None,
            float(row.get('y')) if row.get('y') and row.get('y') != 'None' else None,
            float(row.get('endX')) if row.get('endX') and row.get('endX') != 'None' else None,
            float(row.get('endY')) if row.get('endY') and row.get('endY') != 'None' else None,
            row.get('tipo'),
            int(row.get('exitoso')) if row.get('exitoso') else 0,
            float(row.get('distancia')) if row.get('distancia') and row.get('distancia') != 'None' else None,
            float(row.get('progresion')) if row.get('progresion') and row.get('progresion') != 'None' else None,
            float(row.get('angulo')) if row.get('angulo') and row.get('angulo') != 'None' else None,
            float(row.get('seq_xg')) if row.get('seq_xg') else 0,
            float(row.get('xT')) if row.get('xT') else 0,
            float(row.get('xG')) if row.get('xG') else 0,
            float(row.get('xGoT')) if row.get('xGoT') else 0,
            int(row.get('linesBroken')) if row.get('linesBroken') else 0,
            int(row.get('lastLineBroken')) if row.get('lastLineBroken') else 0,
            row.get('pressure'),
            int(row.get('has_desmarque')) if row.get('has_desmarque') else 0,
            float(row.get('seq_xg')) if row.get('seq_xg') else 0,
            int(row.get('cambio_eje_50')) if row.get('cambio_eje_50') else 0,  # Nueva columna (por defecto 0)
            int(row.get('seq_acciones_total')) if row.get('seq_acciones_total') else 0,  # Nueva columna (por defecto 0)
            int(row.get('retencion_7s')) if row.get('retencion_7s') else 1,
            float(row.get('desmarque_run_dist')) if row.get('desmarque_run_dist') else 0,
            float(row.get('desmarque_x')) if row.get('desmarque_x') and row.get('desmarque_x') != 'None' else None,
            float(row.get('desmarque_y')) if row.get('desmarque_y') and row.get('desmarque_y') != 'None' else None,
            float(row.get('desmarque_angulo')) if row.get('desmarque_angulo') and row.get('desmarque_angulo') != 'None' else None,
            float(row.get('desmarque_distancia')) if row.get('desmarque_distancia') and row.get('desmarque_distancia') != 'None' else None,
            int(row.get('has_aerial_duel')) if row.get('has_aerial_duel') else 0,
            int(row.get('aerial_duel_won')) if row.get('aerial_duel_won') and row.get('aerial_duel_won') != 'None' else None,
            row.get('aerial_player'),
            row.get('lb_chip_cat', 'none'),  # Nueva columna (por defecto 'none')
        ]
        embedded_data.append(row_data)

print(f"  CSV cargado: {len(embedded_data)} acciones")

# Leer JSON de secuencias
with open(INPUT_JSON, 'r', encoding='utf-8') as fh:
    seq_json_data = json.load(fh)

embedded_sequences = {}
seq_schema = seq_json_data.pop('_s')
for key, value in seq_json_data.items():
    embedded_sequences[key] = value

print(f"  JSON cargado: {len(embedded_sequences)} secuencias")

# ─── SERIALIZE (formato columnar con compresión) ────────────────────────────
print("Comprimiendo datos...")

DATA_SCHEMA = ['matchId','liga','sequenceId','periodId','minute','second',
    'jugador','playerId','equipo','temporada','rival','fecha','competencia',
    'x','y','endX','endY','tipo','exitoso','distancia','progresion','angulo',
    'seq_xg','xT','xG','xGoT','linesBroken','lastLineBroken',
    'pressure','has_desmarque','seq_xg','cambio_eje_50','seq_acciones_total','retencion_7s','desmarque_run_dist',
    'desmarque_x','desmarque_y','desmarque_angulo','desmarque_distancia',
    'has_aerial_duel','aerial_duel_won','aerial_player','lb_chip_cat']

data_json = json.dumps([DATA_SCHEMA] + embedded_data, ensure_ascii=False, separators=(',',':'))
seq_json  = json.dumps({'_s': seq_schema, **embedded_sequences},
                       ensure_ascii=False, separators=(',',':'))

# Ultra-ligero: comprimir payloads de datos con zlib y codificarlos en base64
data_json_b64 = base64.b64encode(zlib.compress(data_json.encode('utf-8'), 9)).decode('ascii')
seq_json_b64  = base64.b64encode(zlib.compress(seq_json.encode('utf-8'), 9)).decode('ascii')
data_json_b64_js = json.dumps(data_json_b64)
seq_json_b64_js  = json.dumps(seq_json_b64)

print(f"  data_json: {len(data_json)//1024}KB -> {len(data_json_b64)//1024}KB (zlib+b64)")
print(f"  seq_json: {len(seq_json)//1024}KB -> {len(seq_json_b64)//1024}KB (zlib+b64)")

# ─── BUILD HTML ───────────────────────────────────────────────────────────────
print("Generando HTML...")

HTML_CONTENT = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análisis Interactivo — Pases de Porteros</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#0a0e14;--surface:#14181f;--surface-2:#1c2129;--surface-3:#252F40;
  --border:#2d3642;--text:#e6ebf1;--text-dim:#8e99ab;--text-muted:#636d7f;
  --accent:#74e2b5;--accent-dim:rgba(116,226,181,.12);
  --red:#f87171;--orange:#fb923c;--gold:#f4c542;--blue:#60a5fa;
  --indigo:#818cf8;--teal:#4ECDC4;
  --font-body:'DM Sans',system-ui,sans-serif;
  --font-serif:'Instrument Serif',Georgia,serif;
}}
html{{font-size:16px;scroll-behavior:smooth;}}
body{{background:var(--bg);color:var(--text);font-family:var(--font-body);line-height:1.6;overflow-x:hidden;}}

/* HEADER */
.rpt-header{{background:var(--surface);border-bottom:1px solid var(--border);padding:1.8rem 3rem;}}
.header-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;}}
.header-name{{font-family:var(--font-serif);font-size:2.2rem;font-weight:400;color:var(--text);}}
.header-name em{{color:var(--accent);font-style:italic;}}
.header-season{{font-size:.85rem;color:var(--text-dim);text-transform:uppercase;letter-spacing:.08em;}}
.stats-bar{{display:flex;gap:1rem;overflow-x:auto;padding:.5rem 0;}}
.stats-bar::-webkit-scrollbar{{height:4px;}}
.stats-bar::-webkit-scrollbar-thumb{{background:var(--border);border-radius:2px;}}
.stat-card{{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:.9rem 1.2rem;min-width:150px;position:relative;}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--accent);border-radius:8px 0 0 8px;}}
.stat-label{{font-size:.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem;}}
.stat-val{{font-size:1.6rem;font-weight:700;color:var(--accent);}}

/* MAIN */
main{{padding:0 3rem 3rem;}}
.dashboard{{display:grid;grid-template-columns:300px 1fr;gap:2rem;margin-top:2rem;}}

/* FILTROS */
.filtros{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.5rem;height:fit-content;}}
.filtros h2{{font-size:1.1rem;color:var(--text);margin-bottom:1.2rem;padding-bottom:.8rem;border-bottom:1px solid var(--border);}}
.filtro-group{{margin-bottom:1.5rem;}}
.filtro-group label{{display:block;font-size:.82rem;color:var(--text-dim);margin-bottom:.6rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;}}
.filtro-group input[type="range"]{{width:100%;margin:.6rem 0;accent-color:var(--accent);cursor:pointer;}}

.range-dual{{position:relative;height:30px;margin:.6rem 0;}}
.range-dual input[type="range"]{{position:absolute;width:100%;height:6px;pointer-events:none;-webkit-appearance:none;background:transparent;margin:0;top:50%;transform:translateY(-50%);}}
.range-dual input[type="range"]::-webkit-slider-thumb{{-webkit-appearance:none;pointer-events:auto;width:18px;height:18px;background:var(--accent);border:2px solid var(--bg);border-radius:50%;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.3);}}
.range-dual input[type="range"]::-moz-range-thumb{{pointer-events:auto;width:18px;height:18px;background:var(--accent);border:2px solid var(--bg);border-radius:50%;cursor:pointer;}}
.range-dual input[type="range"]::-webkit-slider-runnable-track{{width:100%;height:6px;background:var(--surface-2);border-radius:3px;}}
.range-dual input[type="range"]:nth-child(2)::-webkit-slider-runnable-track{{background:transparent;}}
.range-values{{display:flex;justify-content:space-between;font-size:.8rem;color:var(--text-muted);margin-top:.4rem;}}
.range-values strong{{color:var(--text);font-weight:700;}}

.checkbox-group{{display:flex;flex-direction:column;gap:.6rem;margin-top:.6rem;}}
.checkbox-group label{{display:flex;align-items:center;cursor:pointer;transition:color .15s;font-size:.85rem;text-transform:none;letter-spacing:0;}}
.checkbox-group label:hover{{color:var(--text);}}
.checkbox-group input[type="checkbox"]{{margin-right:.6rem;cursor:pointer;width:16px;height:16px;accent-color:var(--accent);}}

.equipo-list{{max-height:180px;overflow-y:auto;background:var(--surface-2);border:1px solid var(--border);border-radius:6px;padding:0.6rem;margin-top:0.6rem;scrollbar-width:thin;scrollbar-color:var(--accent) var(--surface-2);}}
.equipo-list::-webkit-scrollbar{{width:8px;}}
.equipo-list::-webkit-scrollbar-track{{background:var(--surface-2);}}
.equipo-list::-webkit-scrollbar-thumb{{background:var(--accent);border-radius:4px;}}
.equipo-list label{{display:flex;align-items:center;cursor:pointer;transition:color .15s;font-size:.8rem;margin-bottom:0.4rem;}}
.equipo-list input[type="checkbox"]{{margin-right:.6rem;cursor:pointer;width:14px;height:14px;accent-color:var(--accent);}}

.btn-reset{{width:100%;padding:0.9rem;margin-top:1rem;background:var(--accent);color:var(--bg);border:none;border-radius:8px;font-size:0.9rem;font-weight:700;cursor:pointer;transition:all 0.2s;text-transform:uppercase;letter-spacing:0.05em;}}
.btn-reset:hover{{background:var(--text);transform:translateY(-2px);box-shadow:0 4px 12px rgba(116,226,181,0.3);}}

.btn-cluster{{padding:8px 14px;background:#64748b;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:13px;transition:all 0.2s;box-shadow:0 2px 4px rgba(0,0,0,0.2);}}
.btn-cluster:hover{{background:#475569;transform:scale(1.05);}}
.btn-cluster.active{{background:#8b5cf6;box-shadow:0 0 12px rgba(139,92,246,0.5);}}

.clustering-report{{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-top:1rem;}}
.clustering-report h4{{color:var(--accent);margin-bottom:.8rem;font-size:1rem;}}
.clustering-metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1rem;}}
.clustering-metric{{background:var(--surface);padding:.8rem;border-radius:6px;text-align:center;}}
.clustering-metric-label{{font-size:.8rem;color:var(--text-muted);text-transform:uppercase;margin-bottom:.4rem;}}
.clustering-metric-value{{font-size:1.6rem;font-weight:700;color:var(--accent);}}

.clustering-table{{width:100%;border-collapse:collapse;font-size:.85rem;margin-top:.8rem;}}
.clustering-table th{{background:var(--surface);color:var(--accent);padding:.8rem;text-align:left;font-weight:600;border-bottom:1px solid var(--border);}}
.clustering-table td{{padding:.7rem;border-bottom:1px solid var(--border);}}
.clustering-table tbody tr:hover{{background:var(--surface-2);}}
.cluster-badge{{display:inline-block;padding:.3rem .6rem;border-radius:4px;font-size:.8rem;font-weight:600;color:white;}}

.stats-box{{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:1rem;text-align:center;margin-top:1rem;}}
.stats-box h3{{font-size:.8rem;color:var(--text-muted);margin-bottom:.5rem;text-transform:uppercase;letter-spacing:.05em;}}
.stats-box .stat-value{{font-size:1.8rem;font-weight:700;color:var(--accent);}}

/* KPI TABLE */
.kpi-table{{width:100%;border-collapse:collapse;margin-top:1rem;font-size:.85rem;}}
.kpi-table thead{{background:var(--surface-2);}}
.kpi-table th{{padding:.8rem;text-align:left;font-weight:600;color:var(--text-dim);text-transform:uppercase;font-size:.75rem;letter-spacing:.05em;border-bottom:2px solid var(--border);}}
.kpi-table td{{padding:.8rem;color:var(--text);border-bottom:1px solid var(--border);}}
.kpi-table tbody tr:hover{{background:var(--surface-2);}}
.kpi-table .kpi-color{{width:8px;height:40px;border-radius:2px;}}
.kpi-table .kpi-number{{font-family:'Courier New',monospace;font-weight:600;color:var(--accent);}}

/* EQUIPO TABLE */
.equipo-table{{width:100%;border-collapse:collapse;font-size:.8rem;}}
.equipo-table thead{{background:var(--surface-2);position:sticky;top:0;z-index:10;}}
.equipo-table th{{padding:.7rem .5rem;text-align:left;font-weight:600;color:var(--text-dim);text-transform:uppercase;font-size:.7rem;letter-spacing:.04em;border-bottom:2px solid var(--border);}}
.equipo-table th.num{{text-align:right;}}
.equipo-table td{{padding:.7rem .5rem;color:var(--text);border-bottom:1px solid var(--border);}}
.equipo-table td.num{{text-align:right;font-family:'Courier New',monospace;font-size:.75rem;}}
.equipo-table tbody tr:hover{{background:var(--surface-2);}}
.equipo-table .rank{{color:var(--accent);font-weight:700;}}
.table-scroll{{max-height:500px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--accent) var(--surface-2);}}
.table-scroll::-webkit-scrollbar{{width:8px;}}
.table-scroll::-webkit-scrollbar-track{{background:var(--surface-2);}}
.table-scroll::-webkit-scrollbar-thumb{{background:var(--accent);border-radius:4px;}}

/* VISUALIZACION */
.visualizacion{{display:flex;flex-direction:column;gap:1.5rem;}}
.plot-container{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;}}
.plot-header{{padding:1rem 1.5rem;border-bottom:1px solid var(--border);background:var(--surface-2);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;}}
.plot-header h3{{font-size:1rem;color:var(--text);font-weight:600;}}
.plot-body{{padding:1.2rem;}}
.legend{{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;padding:1rem 1.5rem;border-top:1px solid var(--border);background:var(--surface-2);}}
.legend-item{{display:flex;align-items:center;gap:.6rem;font-size:.82rem;}}
.legend-color{{width:24px;height:4px;border-radius:2px;flex-shrink:0;}}

/* SEQ PANEL */
#pitch-seq-layout{{display:flex;gap:1.5rem;transition:all 0.3s ease;}}
#pitch-seq-layout.has-seq #main-pitch-wrapper{{flex:0 0 48%;}}
#main-pitch-wrapper{{flex:1;transition:flex 0.3s ease;}}
.seq-panel{{flex:0 0 50%;background:#f8f9fa;border:2px solid #1a4d2e;border-radius:12px;overflow:hidden;display:flex;flex-direction:column;max-height:650px;box-shadow:0 6px 12px rgba(0,0,0,0.15);}}
.seq-header{{padding:1.2rem 1.5rem;background:linear-gradient(135deg,#1a4d2e 0%,#2d5c3e 100%);border-bottom:none;display:flex;justify-content:space-between;align-items:center;}}
.seq-header h4{{font-size:1.15rem;font-weight:700;margin:0;color:white;text-shadow:0 1px 2px rgba(0,0,0,0.2);}}
.btn-close-seq{{background:#ff4444;color:white;border:none;border-radius:6px;width:32px;height:32px;cursor:pointer;font-size:18px;font-weight:bold;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}}
.btn-close-seq:hover{{transform:scale(1.1);background:#ff0000;}}
.seq-content{{padding:1.5rem;overflow-y:auto;flex:1;background:#f8f9fa;}}
.seq-canvas-wrap{{margin-bottom:1.5rem;background:white;padding:1.2rem;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.08);}}
.seq-canvas-wrap h5{{font-size:1rem;margin:0 0 0.5rem 0;color:#1a4d2e;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;}}
#seq-subtitle{{font-size:0.9rem;color:#555;font-weight:500;text-transform:none;letter-spacing:normal;margin-bottom:0.8rem;line-height:1.8;padding:0.6rem 0;border-bottom:1px solid #e0e0e0;}}
.seq-subtitle-item{{display:inline-block;margin-right:1.5rem;white-space:nowrap;}}
.seq-subtitle-label{{color:#888;font-weight:400;margin-right:0.3rem;}}
#seq-canvas{{border:2px solid #1a4d2e;border-radius:8px;background:#1a4d2e;width:100%;height:auto;box-shadow:0 4px 6px rgba(0,0,0,0.1);}}
.seq-events h5{{font-size:1rem;margin:0 0 0.8rem 0;color:#1a4d2e;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;}}
#seq-events-list{{font-size:0.9rem;max-height:300px;overflow-y:auto;}}
.seq-event-item{{padding:0.8rem 1rem;border-left:4px solid #4ECDC4;background:white;margin-bottom:0.6rem;border-radius:6px;transition:all 0.2s;box-shadow:0 1px 3px rgba(0,0,0,0.08);}}
.seq-event-item:hover{{transform:translateX(3px);box-shadow:0 2px 6px rgba(0,0,0,0.12);}}
.seq-event-item.shot{{border-left-color:#ff3333;background:#fff8f8;}}
.seq-event-item.goal{{border-left-color:#00cc00;background:#f0fff0;font-weight:700;}}
.seq-event-item.pressure-high{{border-left-color:#ff6600;}}
.seq-event-time{{color:#666;font-size:0.75rem;font-weight:600;}}
.seq-event-detail{{color:#333;margin-top:0.3rem;font-weight:500;}}
.pressure-badge{{display:inline-block;padding:1px 6px;border-radius:4px;font-size:.7rem;font-weight:700;margin-left:6px;}}
.pressure-high{{background:#ff660022;color:#cc4400;}}
.pressure-medium{{background:#ffa50022;color:#885500;}}
.pressure-low{{background:#ffff0022;color:#777700;}}

@media(max-width:960px){{.dashboard{{grid-template-columns:1fr;}} main{{padding:0 1.5rem 2rem;}} .rpt-header{{padding:1.5rem;}}}}
</style>
</head>
<body>

<!-- HEADER -->
<header class="rpt-header">
  <div class="header-top">
    <div>
      <div class="header-season">Análisis de Porteros · Pases</div>
      <h1 class="header-name">GoalKick <em>Dashboard</em></h1>
    </div>
  </div>
  <div class="stats-bar">
    <div class="stat-card"><div class="stat-label">GoalKicks</div><div class="stat-val" id="total-goalkicks">---</div></div>
    <div class="stat-card"><div class="stat-label">Dist. Media</div><div class="stat-val" id="avg-dist">---</div></div>
    <div class="stat-card"><div class="stat-label">xA Total</div><div class="stat-val" id="total-xa">---</div></div>
    <div class="stat-card"><div class="stat-label">% Exitosos</div><div class="stat-val" id="pct-exitosos">---</div></div>
    <div class="stat-card"><div class="stat-label">% Retención 7s</div><div class="stat-val" id="pct-retencion">---</div></div>
    <div class="stat-card"><div class="stat-label">✈️ Duelos Aéreos</div><div class="stat-val" id="pct-aerial" style="font-size:1rem;">---</div></div>
  </div>
</header>

<!-- MAIN -->
<main>
<div class="dashboard">

  <!-- FILTROS -->
  <div class="filtros">
    <h2>🎛️ Filtros</h2>

    <div class="filtro-group">
      <label>📍 Zona X del Pase (0=portería propia)</label>
      <div class="range-dual">
        <input type="range" id="slider-x-min" min="0" max="100" value="0" step="1">
        <input type="range" id="slider-x-max" min="0" max="100" value="100" step="1">
      </div>
      <div class="range-values"><span>Rango: <strong id="x-min-val">0</strong> – <strong id="x-max-val">100</strong></span></div>
    </div>

    <div class="filtro-group">
      <label>↕️ Zona Y del Pase (0=banda derecha, 100=banda izquierda)</label>
      <div class="range-dual">
        <input type="range" id="slider-y-min" min="0" max="100" value="0" step="1">
        <input type="range" id="slider-y-max" min="0" max="100" value="100" step="1">
      </div>
      <div class="range-values"><span>Rango: <strong id="y-min-val">0</strong> – <strong id="y-max-val">100</strong></span></div>
    </div>

    <div class="filtro-group">
      <label>📏 Distancia (metros)</label>
      <div class="range-dual">
        <input type="range" id="slider-dist-min" min="0" max="80" value="0" step="0.5">
        <input type="range" id="slider-dist-max" min="0" max="80" value="80" step="0.5">
      </div>
      <div class="range-values"><span>Rango: <strong id="dist-min-val">0</strong>m – <strong id="dist-max-val">80</strong>m</span></div>
    </div>

    <div class="filtro-group">
      <label>⚡ Progresión (metros)</label>
      <div class="range-dual">
        <input type="range" id="slider-prog-min" min="-105" max="105" value="-105" step="1">
        <input type="range" id="slider-prog-max" min="-105" max="105" value="105" step="1">
      </div>
      <div class="range-values"><span>Rango: <strong id="prog-min-val">-105</strong>m – <strong id="prog-max-val">105</strong>m</span></div>
      <div class="range-values" style="font-size:.8em;margin-top:4px;color:#aaa;"><span>Negativo = hacia portería propia</span></div>
    </div>

    <div class="filtro-group">
      <label>🔄 Ángulo (grados, 0–360°)</label>
      <div style="display:flex;flex-direction:column;align-items:center;margin:.6rem 0;">
        <canvas id="angulo-canvas" width="160" height="160" style="cursor:crosshair;"></canvas>
        <div style="display:flex;gap:1rem;margin-top:.6rem;width:100%;">
          <div style="flex:1;">
            <div style="font-size:.72rem;color:var(--text-muted);margin-bottom:.3rem;">Desde</div>
            <input type="number" id="angulo-min-input" min="0" max="360" value="0" step="1"
              style="width:100%;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-size:.9rem;text-align:center;">
          </div>
          <div style="flex:1;">
            <div style="font-size:.72rem;color:var(--text-muted);margin-bottom:.3rem;">Hasta</div>
            <input type="number" id="angulo-max-input" min="0" max="360" value="360" step="1"
              style="width:100%;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:5px 8px;font-size:.9rem;text-align:center;">
          </div>
        </div>
        <div style="font-size:.75rem;color:var(--text-muted);margin-top:.4rem;text-align:center;">Si Desde &gt; Hasta → rango circular (ej. 315°→45°)</div>
      </div>
    </div>

    <div class="filtro-group">
      <label>✅ Resultado</label>
      <div class="checkbox-group">
        <label><input type="checkbox" class="filtro-resultado" value="1" checked>✅ Exitoso</label>
        <label><input type="checkbox" class="filtro-resultado" value="0" checked>❌ Fallido</label>
      </div>
    </div>

    <div class="filtro-group">
      <label>✈️ Duelo Aéreo</label>
      <div class="checkbox-group">
        <label><input type="checkbox" class="filtro-aerial" value="none" checked>— Sin duelo aéreo</label>
        <label><input type="checkbox" class="filtro-aerial" value="won" checked>🟢 Duelo ganado</label>
        <label><input type="checkbox" class="filtro-aerial" value="lost" checked>🔴 Duelo perdido</label>
      </div>
    </div>

    <div class="filtro-group">
      <label>🔄 Cambio de Eje (cruza y=50)</label>
      <div class="checkbox-group">
        <label><input type="checkbox" class="filtro-eje" value="1" checked>✅ Sí cruza eje</label>
        <label><input type="checkbox" class="filtro-eje" value="0" checked>❌ No cruza eje</label>
      </div>
    </div>

    <div class="filtro-group">
      <label>�️ LONGBALL-CHIPPED</label>
      <div class="checkbox-group">
        <label><input type="checkbox" class="filtro-lbchip" value="gk_lb_chip" checked>🚀 GoalKick LB-Chip</label>
        <label><input type="checkbox" class="filtro-lbchip" value="seq_lb_chip" checked>⚡ Seq. LB-Chip</label>
        <label><input type="checkbox" class="filtro-lbchip" value="none" checked>⚽ Normal</label>
      </div>
    </div>

    <div class="filtro-group">
      <label>�🏃 Desmarque receptor</label>
      <div class="checkbox-group">
        <label><input type="checkbox" class="filtro-desmarque" value="1" checked>🟣 Sí (desmarque &gt;4m)</label>
        <label><input type="checkbox" class="filtro-desmarque" value="0" checked>⚪ No</label>
      </div>
    </div>

    <div class="filtro-group">
      <label>📊 Máx. Acciones en Secuencia</label>
      <div class="range-single">
        <input type="range" id="slider-acc-max" min="1" max="30" value="30" step="1" style="width:100%;">
        <div class="range-value"><span id="acc-max-val">30</span> acciones</div>
      </div>
    </div>

    <div class="filtro-group">
      <label>📈 xG Acumulado en Secuencia</label>
      <div class="range-dual">
        <input type="range" id="slider-xgseq-min" min="0" max="1.5" value="0" step="0.01">
        <input type="range" id="slider-xgseq-max" min="0" max="1.5" value="1.5" step="0.01">
      </div>
      <div class="range-values"><span>Rango: <strong id="xgseq-min-val">0.00</strong> – <strong id="xgseq-max-val">1.50</strong> xG</span></div>
      <div class="range-values" style="font-size:.8em;margin-top:4px;color:#aaa;"><span>xG total de disparos en la misma secuencia</span></div>
    </div>

    <div class="filtro-group">
      <label>🏃 Distancia de Desmarque (metros)</label>
      <div class="range-dual">
        <input type="range" id="slider-desmrun-min" min="0" max="100" value="0" step="0.5">
        <input type="range" id="slider-desmrun-max" min="0" max="100" value="100" step="0.5">
      </div>
      <div class="range-values"><span>Rango: <strong id="desmrun-min-val">0.0</strong>m – <strong id="desmrun-max-val">100.0</strong>m</span></div>
      <div class="range-values" style="font-size:.8em;margin-top:4px;color:#aaa;"><span>Distancia del receptor desde su posición inicial hasta el punto de recepción (0 si no hay desmarque &gt;4m)</span></div>
    </div>

    <div class="filtro-group">
      <label>🏆 Liga</label>
      <div style="margin-bottom:5px;">
        <button onclick="seleccionarTodasLigas(true)" style="font-size:11px;padding:2px 6px;margin-right:5px;">✓ Todas</button>
        <button onclick="seleccionarTodasLigas(false)" style="font-size:11px;padding:2px 6px;">✗ Ninguna</button>
      </div>
      <div class="equipo-list" id="filtro-liga-container"></div>
    </div>

    <div class="filtro-group">
      <label>🏆 Equipo-Temporada</label>
      <div style="margin-bottom:5px;">
        <button onclick="seleccionarTodosEquipos(true)" style="font-size:11px;padding:2px 6px;margin-right:5px;">✓ Todos</button>
        <button onclick="seleccionarTodosEquipos(false)" style="font-size:11px;padding:2px 6px;">✗ Ninguno</button>
      </div>
      <div class="equipo-list" id="filtro-equipo-container"></div>
    </div>

    <button class="btn-reset" id="btn-resetear">🔄 Resetear Filtros</button>

    <div class="stats-box"><h3>Filtrados</h3><div class="stat-value" id="count-filtered">0</div></div>
    <div class="stats-box"><h3>xA Filtrado</h3><div class="stat-value" id="xa-total">0.000</div></div>
    <div class="stats-box"><h3>xT Filtrado</h3><div class="stat-value" id="xt-total">0.000</div></div>
    <div class="stats-box"><h3>% Exitosos</h3><div class="stat-value" id="pct-filtrado">0%</div></div>
  </div>

  <!-- VISUALIZACIONES -->
  <div class="visualizacion">

    <!-- CAMPOGRAMA -->
    <div class="plot-container">
      <div class="plot-header">
        <h3>Campograma OPTA — Pases de Portero
          <span id="acciones-count" style="margin-left:10px;font-size:13px;font-weight:400;color:#74e2b5;"></span>
          <span id="seq-indicator" style="display:none;margin-left:12px;font-size:13px;color:#aaa;">| Haz click en una flecha para ver la secuencia</span>
        </h3>
        <div style="display:flex;gap:.5rem;">
          <label style="font-size:.8rem;color:var(--text-dim);display:flex;align-items:center;gap:5px;">
            <input type="checkbox" id="toggle-labels" onchange="actualizarVistas()"> Etiquetas
          </label>
        </div>
      </div>
      <div id="pitch-seq-layout" class="plot-body">
        <div id="main-pitch-wrapper">
          <canvas id="campograma" style="width:100%;height:600px;"></canvas>
        </div>
        <div id="seq-panel" class="seq-panel" style="display:none;">
          <div class="seq-header">
            <h4 id="seq-title">Secuencia Completa</h4>
            <button onclick="cerrarSecuencia()" class="btn-close-seq">✕</button>
          </div>
          <div class="seq-content">
            <div class="seq-canvas-wrap">
              <h5>Eventos de la Secuencia</h5>
              <div id="seq-subtitle"></div>
              <canvas id="seq-canvas" width="700" height="450"></canvas>
            </div>
            <div class="seq-events">
              <h5>Detalle de Eventos</h5>
              <div id="seq-events-list"></div>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- BOTONES CLUSTERING -->
    <div style="display:flex;gap:12px;margin:15px 0;padding:0 15px;">
      <button id="btn-kmeans" class="btn-cluster">📊 K-Means Clustering</button>
      <button id="btn-spectral" class="btn-cluster">🌐 Spectral Clustering</button>
    </div>

    <!-- TABLA REPORTE CLUSTERING -->
    <div id="clustering-report-container" style="display:none;margin:15px;"></div>

    <!-- TABLA EQUIPOS -->
    <div class="plot-container">
      <div class="plot-header"><h3>🏆 Ranking por Equipo-Temporada</h3></div>
      <div class="plot-body">
        <div class="table-scroll">
          <table class="equipo-table">
            <thead>
              <tr>
                <th>#</th><th>Equipo</th>
                <th class="num">Acciones</th><th class="num">% Éxito</th>
                <th class="num">Dist. Med.</th><th class="num">GoalKicks</th>
                <th class="num">Longballs</th><th class="num">xA Total</th><th class="num">% Ret. 7s</th><th class="num">Duelo Aéreo</th>
              </tr>
            </thead>
            <tbody id="equipo-table-body"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- DUELOS AÉREOS TABLE -->
    <div class="plot-container">
      <div class="plot-header"><h3>✈️ Ranking Duelos Aéreos — Jugadores de Campo</h3></div>
      <div class="plot-body">
        <div class="table-scroll">
          <table class="equipo-table" id="aerial-table">
            <thead>
              <tr>
                <th>#</th><th>Jugador</th><th>Equipo</th>
                <th class="num">Duelos</th>
                <th class="num">Ganados</th>
                <th class="num">Perdidos</th>
                <th class="num">% Ganados</th>
              </tr>
            </thead>
            <tbody id="aerial-table-body"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SCATTER -->
    <div class="plot-container">
      <div class="plot-header" style="flex-direction:column;align-items:flex-start;gap:.8rem;">
        <h3>🔵 Comparativa por Equipo-Temporada</h3>
        <div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;">
          <label style="font-size:.82rem;color:var(--text-dim);display:flex;align-items:center;gap:6px;">Eje X:
            <select id="scatter-axis-x" style="background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:5px 10px;font-size:.82rem;cursor:pointer;">
              <option value="total_acciones">Volumen acciones</option>
              <option value="pct_exito">% Exitosos</option>
              <option value="dist_media">Distancia media (m)</option>
              <option value="prog_media">Progresión media (m)</option>
              <option value="xa_total" selected>xA Total</option>
              <option value="xt_total">xT Total</option>
              <option value="goalkicks">GoalKicks</option>
              <option value="longballs">Longballs</option>
              <option value="pct_retencion_7s">% Ret. 7s</option>
            </select>
          </label>
          <label style="font-size:.82rem;color:var(--text-dim);display:flex;align-items:center;gap:6px;">Eje Y:
            <select id="scatter-axis-y" style="background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:5px 10px;font-size:.82rem;cursor:pointer;">
              <option value="total_acciones">Volumen acciones</option>
              <option value="pct_exito">% Exitosos</option>
              <option value="dist_media" selected>Distancia media (m)</option>
              <option value="prog_media">Progresión media (m)</option>
              <option value="xa_total">xA Total</option>
              <option value="xt_total">xT Total</option>
              <option value="goalkicks">GoalKicks</option>
              <option value="longballs">Longballs</option>
              <option value="pct_retencion_7s">% Ret. 7s</option>
            </select>
          </label>
        </div>
      </div>
      <div class="plot-body"><canvas id="scatterChart" style="width:100%;height:450px;"></canvas></div>
    </div>

    <!-- SONAR ANGULOS -->
    <div class="plot-container">
      <div class="plot-header"><h3>🎯 Sonar de Ángulos del Saque</h3></div>
      <div class="plot-body" style="display:flex;justify-content:center;align-items:center;padding:1rem 0;">
        <canvas id="sonar-canvas" style="width:380px;height:380px;"></canvas>
      </div>
    </div>

  </div><!-- fin visualizacion -->
</div><!-- fin dashboard -->
</main>

<script>
// ── UTILIDADES DE DESCOMPRESIÓN ───────────────────────────────────────────────
function b64ToUint8Array(b64str) {{
  const bstr = atob(b64str);
  const bytes = new Uint8Array(bstr.length);
  for (let i = 0; i < bstr.length; i++) {{
    bytes[i] = bstr.charCodeAt(i);
  }}
  return bytes;
}}

// ── DATOS ─────────────────────────────────────────────────────────────────────
(function(){{
  const _raw_b64 = {data_json_b64_js};
  const _seqRaw_b64 = {seq_json_b64_js};
  
  console.log('🔧 Descomprimiendo datos...');
  console.log('  _raw_b64 length:', _raw_b64.length);
  console.log('  _seqRaw_b64 length:', _seqRaw_b64.length);
  console.log('  pako disponible:', typeof pako !== 'undefined');
  
  let _raw_json, _seqRaw_json;
  try {{
    _raw_json = JSON.parse(new TextDecoder().decode(pako.inflate(b64ToUint8Array(_raw_b64))));
    _seqRaw_json = JSON.parse(new TextDecoder().decode(pako.inflate(b64ToUint8Array(_seqRaw_b64))));
    
    console.log('✅ Datos descomprimidos correctamente');
    console.log('  _raw_json length:', _raw_json.length);
    console.log('  _seqRaw_json keys:', Object.keys(_seqRaw_json).length);
  }} catch(e) {{
    console.error('❌ Error descomprimiendo:', e.message);
    throw e;
  }}
  
  const _raw = _raw_json;
  const _seqRaw = _seqRaw_json;
  const _schema = _raw[0];
  const _seqSchema = _seqRaw['_s'];
  
  console.log('✅ Schema cargado:', _schema.length, 'campos');
  console.log('  Campos de clustering en schema:');
  console.log('    desmarque_x @', _schema.indexOf('desmarque_x'));
  console.log('    desmarque_y @', _schema.indexOf('desmarque_y'));
  console.log('    desmarque_angulo @', _schema.indexOf('desmarque_angulo'));
  console.log('    desmarque_distancia @', _schema.indexOf('desmarque_distancia'));

  window.EMBEDDED_DATA = _raw.slice(1).map(r => {{
    const d = {{}};
    _schema.forEach((k,i) => d[k] = r[i]);
    d.exitoso       = d.exitoso === 1;
    d.is_clearance  = d.tipo === 'Clearance';
    d.is_goal_kick  = d.tipo === 'GoalKick';
    d.is_keeper_throw = d.tipo === 'KeeperThrow';
    d.is_gk_kick_hands = d.tipo === 'Volea';
    d.is_longball   = d.tipo === 'Longball';
    d.is_normal_pass = d.tipo === 'Pase Normal';
    d.aerial_cat = d.aerial_duel_won === null ? 'none' : (d.aerial_duel_won === 1 ? 'won' : 'lost');
    
    // Convertir campos numéricos a numbers
    const numericFields = ['x','y','endX','endY','distancia','progresion','angulo','seq_xg','xT','xG','xGoT','pressure',
                           'seq_xg','desmarque_run_dist','desmarque_x','desmarque_y','desmarque_angulo','desmarque_distancia',
                           'reception_x','reception_y','sequenceId','periodId','minute','second','has_desmarque','seq_acciones_total',
                           'retencion_7s','has_aerial_duel','aerial_duel_won','cambio_eje_50','seq_goals'];
    numericFields.forEach(f => {{
      if(d[f] !== null && d[f] !== undefined && d[f] !== '') {{
        const num = Number(d[f]);
        d[f] = isNaN(num) ? null : num;
      }}
    }});
    
    return d;
  }});

  console.log('✅ Datos convertidos a objetos:', window.EMBEDDED_DATA.length, 'registros');
  
  // Debug: primeros 3 registros con clustering
  const firstWithDesmarque = window.EMBEDDED_DATA.filter(d => d.has_desmarque === 1).slice(0, 3);
  console.log('📍 Primeros 3 con has_desmarque=1:');
  firstWithDesmarque.forEach((d, idx) => {{
    console.log(`  [${{idx}}]`, {{
      desmarque_x: {{ valor: d.desmarque_x, tipo: typeof d.desmarque_x }},
      desmarque_y: {{ valor: d.desmarque_y, tipo: typeof d.desmarque_y }},
      desmarque_angulo: {{ valor: d.desmarque_angulo, tipo: typeof d.desmarque_angulo }},
      desmarque_distancia: {{ valor: d.desmarque_distancia, tipo: typeof d.desmarque_distancia }}
    }});
  }});

  const PRESSURE_LABELS = [null,'low','medium','high'];
  window.EMBEDDED_SEQUENCES = {{}};
  Object.keys(_seqRaw).forEach(k => {{
    if (k === '_s') return;
    const raw = _seqRaw[k];
    const teamNames = raw[0];
    window.EMBEDDED_SEQUENCES[k] = raw.slice(1).map(r => {{
      const ev = {{}};
      _seqSchema.forEach((f,i) => ev[f] = r[i]);
      ev.team = teamNames[ev.team] || ev.team;
      ev.isShot = ev.isShot === 1;
      ev.isGoal = ev.isGoal === 1;
      ev.is_gk_pass = ev.is_gk_pass === 1;
      ev.pressure = PRESSURE_LABELS[ev.pressure] || null;
      ev.outcome = ev.outcome === 1 ? 'Successful' : (ev.outcome === 0 ? 'Unsuccessful' : null);
      ev.desmarques = ev.desmarques ? ev.desmarques.map(d => ({{x:d[0],y:d[1],rx:d[2],ry:d[3]}})) : [];
      return ev;
    }});
  }});
}})();

const TIPO_COLORES = {{
  'GoalKick':   '#60a5fa',
  'KeeperThrow':'#4ECDC4',
  'Volea':      '#fb923c',
  'Longball':   '#f4c542',
  'Pase Normal':'#74e2b5',
  'Clearance':  '#f87171',
}};
const TIPO_LABELS = {{
  'GoalKick':    'GoalKick',
  'KeeperThrow': 'Saque de Mano',
  'Volea':       'Volea',
  'Longball':    'Longball',
  'Pase Normal': 'Pase Normal',
  'Clearance':   'Clearance',
}};

let scatterChartInst = null;
let secuenciaActual = null;
let mostrarLabels = false;

// ──── CLUSTERING VARIABLES ────
let kmeansMode = false;
let kmeansData = null;
let spectralMode = false;
let spectralData = null;
let currentClusteringData = null;  // Almacena el clustering activo para visualizar en campograma
let selectedClusterIdx = null;  // Índice del cluster seleccionado en la tabla
let showCentroids = false;  // Mostrar centroides en el campograma
const K_CONFIG = {{ maxIter: 100, tol: 1e-4, colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B88B', '#A8D8EA'] }};

let _filtrosCache = {{
  tiposOK: new Set(),
  resOK: new Set(),
  desmarqueOK: new Set(),
  retencionOK: new Set(),
  aerialOK: new Set(),
  ejeOK: new Set(),
  lbchipOK: new Set(),
  ligasOK: new Set(),
  equiposOK: new Set(),
}};

function actualizarFiltrosCacheados() {{
  _filtrosCache.tiposOK = new Set(Array.from(document.querySelectorAll('.filtro-tipo:checked')).map(c=>c.value));
  _filtrosCache.resOK = new Set(Array.from(document.querySelectorAll('.filtro-resultado:checked')).map(c=>+c.value));
  _filtrosCache.desmarqueOK = new Set(Array.from(document.querySelectorAll('.filtro-desmarque:checked')).map(c=>+c.value));
  _filtrosCache.retencionOK = new Set(Array.from(document.querySelectorAll('.filtro-retencion:checked')).map(c=>+c.value));
  _filtrosCache.aerialOK = new Set(Array.from(document.querySelectorAll('.filtro-aerial:checked')).map(c=>c.value));
  _filtrosCache.ejeOK = new Set(Array.from(document.querySelectorAll('.filtro-eje:checked')).map(c=>+c.value));
  _filtrosCache.lbchipOK = new Set(Array.from(document.querySelectorAll('.filtro-lbchip:checked')).map(c=>c.value));
  _filtrosCache.ligasOK = new Set(Array.from(document.querySelectorAll('.filtro-liga:checked')).map(c=>c.value));
  _filtrosCache.equiposOK = new Set(Array.from(document.querySelectorAll('.filtro-equipo:checked')).map(c=>c.value));
}}

function obtenerDatosFiltrados() {{
  const xMin     = +document.getElementById('slider-x-min').value;
  const xMax     = +document.getElementById('slider-x-max').value;
  const yMin     = +document.getElementById('slider-y-min').value;
  const yMax     = +document.getElementById('slider-y-max').value;
  const distMin  = +document.getElementById('slider-dist-min').value;
  const distMax  = +document.getElementById('slider-dist-max').value;
  const progMin  = +document.getElementById('slider-prog-min').value;
  const progMax  = +document.getElementById('slider-prog-max').value;
  const angMin   = +document.getElementById('angulo-min-input').value;
  const angMax   = +document.getElementById('angulo-max-input').value;
  const xgSeqMin = +document.getElementById('slider-xgseq-min').value;
  const xgSeqMax = +document.getElementById('slider-xgseq-max').value;
  const desmRunMin = +document.getElementById('slider-desmrun-min').value;
  const desmRunMax = +document.getElementById('slider-desmrun-max').value;
  const accMax   = +document.getElementById('slider-acc-max').value;

  return EMBEDDED_DATA.filter(d => {{
    if (d.x === null || d.x === undefined) return false;
    if (d.x < xMin || d.x > xMax) return false;
    if (d.y !== null && d.y !== undefined && (d.y < yMin || d.y > yMax)) return false;
    if (d.distancia !== null && (d.distancia < distMin || d.distancia > distMax)) return false;
    if (d.progresion !== null && (d.progresion < progMin || d.progresion > progMax)) return false;
    if (d.angulo !== null) {{
      const a = d.angulo;
      const inRange = angMin <= angMax ? (a >= angMin && a <= angMax) : (a >= angMin || a <= angMax);
      if (!inRange) return false;
    }}
    const xgVal = d.seq_xg || 0;
    if (xgVal < xgSeqMin || xgVal > xgSeqMax) return false;
    const accTotal = d.seq_acciones_total || 0;
    if (accTotal > accMax) return false;
    const desmRun = d.desmarque_run_dist || 0;
    if (desmRun < desmRunMin || desmRun > desmRunMax) return false;
    if (_filtrosCache.tiposOK.size > 0 && !_filtrosCache.tiposOK.has(d.tipo)) return false;
    if (_filtrosCache.resOK.size > 0 && !_filtrosCache.resOK.has(d.exitoso ? 1 : 0)) return false;
    if (_filtrosCache.desmarqueOK.size > 0 && !_filtrosCache.desmarqueOK.has(d.has_desmarque ? 1 : 0)) return false;
    if (_filtrosCache.retencionOK.size > 0 && !_filtrosCache.retencionOK.has(d.retencion_7s || 0)) return false;
    if (_filtrosCache.aerialOK.size > 0 && !_filtrosCache.aerialOK.has(d.aerial_cat)) return false;
    if (_filtrosCache.ejeOK.size > 0 && !_filtrosCache.ejeOK.has(d.cambio_eje_50 ? 1 : 0)) return false;
    if (_filtrosCache.lbchipOK.size > 0 && !_filtrosCache.lbchipOK.has(d.lb_chip_cat)) return false;
    if (_filtrosCache.ligasOK.size > 0 && !_filtrosCache.ligasOK.has(d.liga)) return false;
    if (_filtrosCache.equiposOK.size > 0) {{
      const key = d.equipo + ' (' + d.temporada + ')';
      if (!_filtrosCache.equiposOK.has(key)) return false;
    }}
    return true;
  }});
}}

function actualizarVistas() {{
  actualizarFiltrosCacheados();
  mostrarLabels = document.getElementById('toggle-labels').checked;
  const datos = obtenerDatosFiltrados();
  actualizarStats(datos);
  
  // Si K-Means está activo, hacer clustering
  if(kmeansMode) {{
    const desmarques = datos.filter(d => 
      d.desmarque_x !== null && d.desmarque_y !== null && 
      d.desmarque_angulo !== null && d.desmarque_distancia !== null
    );
    console.log('📍 Desmarques filtrados:', desmarques.length, 'de', datos.length);
    
    if(desmarques.length >= 2) {{
      // Verificar que todos los puntos tienen valores válidos
      const validos = desmarques.filter(d => 
        typeof d.desmarque_x === 'number' && !isNaN(d.desmarque_x) &&
        typeof d.desmarque_y === 'number' && !isNaN(d.desmarque_y) &&
        typeof d.desmarque_angulo === 'number' && !isNaN(d.desmarque_angulo) &&
        typeof d.desmarque_distancia === 'number' && !isNaN(d.desmarque_distancia)
      );
      console.log('✅ Desmarques válidos:', validos.length);
      
      if(validos.length >= 2) {{
        try {{
          const {{data, stats}} = normalizeData(validos, ['desmarque_x','desmarque_y','desmarque_angulo','desmarque_distancia']);
          console.log('📊 Data normalizado:', data.length, 'puntos');
          
          if(data && data.length >= 2) {{
            const k = findOptimalK(data);
            const {{centroids, clusters}} = kmeans(data, k);
            kmeansData = {{k, centroids, clusters, data, stats, desmarques: validos}};
            console.log('✅✅ K-Means ÉXITO: K=' + k + ' desmarques=' + validos.length);
            generarReporteClustering('kmeans', kmeansData, validos);
            dibujarCampograma(datos);
            return;
          }} else {{
            console.warn('❌ Data vacío después de normalizar:', data.length);
          }}
        }} catch(e) {{
          console.error('❌ Error en K-Means:', e.message);
        }}
      }} else {{
        console.warn('⚠️ Desmarques inválidos (NaN/tipos):', validos.length, 'vs', desmarques.length);
      }}
    }} else {{
      console.warn('⚠️ No hay desmarques para clustering:', desmarques.length);
    }}
  }}
  
  // Si Spectral está activo, hacer clustering
  if(spectralMode) {{
    const desmarques = datos.filter(d => 
      d.desmarque_x !== null && d.desmarque_y !== null && 
      d.desmarque_angulo !== null && d.desmarque_distancia !== null
    );
    console.log('📍 Desmarques filtrados:', desmarques.length, 'de', datos.length);
    
    if(desmarques.length >= 2) {{
      // Verificar que todos los puntos tienen valores válidos
      const validos = desmarques.filter(d => 
        typeof d.desmarque_x === 'number' && !isNaN(d.desmarque_x) &&
        typeof d.desmarque_y === 'number' && !isNaN(d.desmarque_y) &&
        typeof d.desmarque_angulo === 'number' && !isNaN(d.desmarque_angulo) &&
        typeof d.desmarque_distancia === 'number' && !isNaN(d.desmarque_distancia)
      );
      console.log('✅ Desmarques válidos:', validos.length);
      
      if(validos.length >= 2) {{
        try {{
          const {{data, stats}} = normalizeData(validos, ['desmarque_x','desmarque_y','desmarque_angulo','desmarque_distancia']);
          console.log('📊 Data normalizado:', data.length, 'puntos');
          
          if(data && data.length >= 2) {{
            const k = findOptimalKSpectral(data);
            const {{clusters}} = spectralClustering(data, k);
            spectralData = {{k, clusters, data, stats, desmarques: validos}};
            console.log('✅✅ Spectral ÉXITO: K=' + k + ' desmarques=' + validos.length);
            generarReporteClustering('spectral', spectralData, validos);
            dibujarCampograma(datos);
            return;
          }} else {{
            console.warn('❌ Data vacío después de normalizar:', data.length);
          }}
        }} catch(e) {{
          console.error('❌ Error en Spectral:', e.message);
        }}
      }} else {{
        console.warn('⚠️ Desmarques inválidos (NaN/tipos):', validos.length, 'vs', desmarques.length);
      }}
    }} else {{
      console.warn('⚠️ No hay desmarques para clustering:', desmarques.length);
    }}
  }}
  
  // Modo normal: dibujar datos normales
  dibujarCampograma(datos);
  actualizarEquipoTable(datos);
  actualizarAerialTable(datos);
  
  setTimeout(() => {{
    actualizarScatter(datos);
    actualizarSonar(datos);
  }}, 100);
}}

function actualizarStats(datos) {{
  const n = datos.length;
  const passes = datos.filter(d=>!d.is_clearance).length;
  const gks    = datos.filter(d=>d.is_goal_kick).length;
  const exitosos= datos.filter(d=>d.exitoso).length;
  const pct    = n>0 ? Math.round(exitosos/n*100) : 0;
  const xaSum  = datos.reduce((s,d)=>s+(d.seq_xg||0),0);
  const xtSum  = datos.reduce((s,d)=>s+(d.xT||0),0);
  const dists  = datos.filter(d=>d.distancia!==null).map(d=>d.distancia);
  const avgD   = dists.length>0 ? (dists.reduce((s,v)=>s+v,0)/dists.length).toFixed(1) : '—';

  document.getElementById('count-filtered').textContent  = n.toLocaleString();
  document.getElementById('xa-total').textContent        = xaSum.toFixed(3);
  document.getElementById('xt-total').textContent        = xtSum.toFixed(3);
  document.getElementById('pct-filtrado').textContent    = pct+'%';


  document.getElementById('total-goalkicks').textContent = EMBEDDED_DATA.filter(d=>d.is_goal_kick).length.toLocaleString();
  const allDists = EMBEDDED_DATA.filter(d=>d.distancia!==null).map(d=>d.distancia);
  document.getElementById('avg-dist').textContent = (allDists.reduce((s,v)=>s+v,0)/allDists.length).toFixed(1)+'m';
  const allXA = EMBEDDED_DATA.reduce((s,d)=>s+(d.seq_xg||0),0);
  document.getElementById('total-xa').textContent = allXA.toFixed(2);
  const allEx = EMBEDDED_DATA.filter(d=>d.exitoso).length;
  document.getElementById('pct-exitosos').textContent = Math.round(allEx/EMBEDDED_DATA.length*100)+'%';
  const allRet = EMBEDDED_DATA.filter(d=>d.retencion_7s===1).length;
  document.getElementById('pct-retencion').textContent = Math.round(allRet/EMBEDDED_DATA.length*100)+'%';
  const allAerial = EMBEDDED_DATA.filter(d=>d.has_aerial_duel===1);
  const elA = document.getElementById('pct-aerial');
  if (elA) {{
    const wonA = allAerial.filter(d=>d.aerial_duel_won===1).length;
    elA.textContent = allAerial.length+' ('+Math.round(wonA/Math.max(1,allAerial.length)*100)+'% G)';
  }}
}}

function dibujarCampograma(datos) {{
  const canvas = document.getElementById('campograma');
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width  = rect.width  * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const w = rect.width, h = rect.height;

  const aspectRatio = 105/68;
  let fieldW, fieldH, offsetX, offsetY;
  if (w/h > aspectRatio) {{
    fieldH = h * 0.9; fieldW = fieldH * aspectRatio;
  }} else {{
    fieldW = w * 0.9; fieldH = fieldW / aspectRatio;
  }}
  offsetX = (w-fieldW)/2; offsetY = (h-fieldH)/2;

  function toC(ox, oy) {{
    return {{ x: offsetX + (ox/100)*fieldW, y: offsetY + fieldH - (oy/100)*fieldH }};
  }}

  ctx.fillStyle = '#2d5c2e';
  ctx.fillRect(0,0,w,h);
  ctx.strokeStyle='white'; ctx.lineWidth=2;

  const corners = [toC(0,0),toC(100,0),toC(100,100),toC(0,100)];
  ctx.beginPath(); ctx.moveTo(corners[0].x,corners[0].y);
  corners.slice(1).forEach(c=>ctx.lineTo(c.x,c.y)); ctx.closePath(); ctx.stroke();
  const mT=toC(50,0),mB=toC(50,100);
  ctx.beginPath();ctx.moveTo(mT.x,mT.y);ctx.lineTo(mB.x,mB.y);ctx.stroke();
  const cen=toC(50,50);
  const radC=(9.15/0.68/100)*fieldH;
  ctx.beginPath();ctx.arc(cen.x,cen.y,radC,0,2*Math.PI);ctx.stroke();
  ctx.strokeRect(offsetX, offsetY+(21.1/100)*fieldH, (16.5/100)*fieldW, (57.8/100)*fieldH);
  ctx.strokeRect(offsetX+(83.5/100)*fieldW, offsetY+(21.1/100)*fieldH, (16.5/100)*fieldW, (57.8/100)*fieldH);
  ctx.strokeRect(offsetX, offsetY+(36.8/100)*fieldH, (5.5/100)*fieldW, (26.4/100)*fieldH);
  ctx.strokeRect(offsetX+(94.5/100)*fieldW, offsetY+(36.8/100)*fieldH, (5.5/100)*fieldW, (26.4/100)*fieldH);

  // Si estamos en modo K-Means, dibujar desmarques por cluster
  if(kmeansMode && kmeansData) {{
    const {{k, clusters, centroids, desmarques}} = kmeansData;
    ctx.globalAlpha = 0.7;
    
    desmarques.forEach((d, idx) => {{
      if(d.desmarque_x === null || d.desmarque_y === null || d.endX === null || d.endY === null) return;
      
      // Encontrar cluster del desmarque
      let clusterIdx = 0;
      for(let c = 0; c < clusters.length; c++) {{
        if(clusters[c].includes(idx)) {{
          clusterIdx = c;
          break;
        }}
      }}
      
      // Si hay un cluster seleccionado, solo dibujar ese cluster
      if(selectedClusterIdx !== null && clusterIdx !== selectedClusterIdx) return;
      
      const p1 = toC(d.desmarque_x, d.desmarque_y);
      const p2 = toC(d.endX, d.endY);
      const color = K_CONFIG.colors[clusterIdx % K_CONFIG.colors.length];
      
      // Dibujar flecha de desmarque
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
      
      // Punta de flecha
      const dx = p2.x - p1.x, dy = p2.y - p1.y;
      const len = Math.sqrt(dx*dx + dy*dy);
      if(len > 4) {{
        const ux = dx/len, uy = dy/len;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(p2.x, p2.y);
        ctx.lineTo(p2.x - 8*ux + 4*uy, p2.y - 8*uy - 4*ux);
        ctx.lineTo(p2.x - 8*ux - 4*uy, p2.y - 8*uy + 4*ux);
        ctx.closePath();
        ctx.fill();
      }}
    }});
    
    // Dibujar centroides como vectores si está activado
    if(showCentroids && centroids) {{
      ctx.globalAlpha = 1;
      centroids.forEach((centroid, idx) => {{
        // Desnormalizar centroide usando stats
        const stats = kmeansData.stats;
        const x_denorm = centroid[0] * stats[0].std + stats[0].mean;
        const y_denorm = centroid[1] * stats[1].std + stats[1].mean;
        const angle_denorm = centroid[2] * stats[2].std + stats[2].mean;
        const dist_denorm = centroid[3] * stats[3].std + stats[3].mean;
        
        const pos = toC(x_denorm, y_denorm);
        const color = K_CONFIG.colors[idx % K_CONFIG.colors.length];
        
        // Calcular punto final del vector basado en ángulo y distancia
        const angleRad = (angle_denorm * Math.PI) / 180;
        const endX = x_denorm + (dist_denorm * Math.cos(angleRad)) / 2;
        const endY = y_denorm + (dist_denorm * Math.sin(angleRad)) / 2;
        const endPos = toC(endX, endY);
        
        // Dibujar vector (flecha)
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(endPos.x, endPos.y);
        ctx.stroke();
        
        // Punta de flecha del centroide
        const dx = endPos.x - pos.x, dy = endPos.y - pos.y;
        const len = Math.sqrt(dx*dx + dy*dy);
        if(len > 4) {{
          const ux = dx/len, uy = dy/len;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.moveTo(endPos.x, endPos.y);
          ctx.lineTo(endPos.x - 8*ux + 4*uy, endPos.y - 8*uy - 4*ux);
          ctx.lineTo(endPos.x - 8*ux - 4*uy, endPos.y - 8*uy + 4*ux);
          ctx.closePath();
          ctx.fill();
        }}
        
        // Círculo en el origen del vector - más grande con borde negro
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 12, 0, 2*Math.PI);
        ctx.fill();
        
        // Borde negro grueso
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 3;
        ctx.stroke();
        
        // Borde blanco interior
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Número del cluster
        ctx.fillStyle = 'white';
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(idx + 1, pos.x, pos.y);
      }});
    }}
    
    ctx.globalAlpha = 1;
    document.getElementById('seq-indicator').style.display = 'none';
    return;
  }}
  
  // Si estamos en modo Spectral, dibujar desmarques por cluster
  if(spectralMode && spectralData) {{
    const {{k, clusters, centroids, desmarques}} = spectralData;
    ctx.globalAlpha = 0.7;
    
    desmarques.forEach((d, idx) => {{
      if(d.desmarque_x === null || d.desmarque_y === null || d.endX === null || d.endY === null) return;
      
      // Encontrar cluster del desmarque
      let clusterIdx = 0;
      for(let c = 0; c < clusters.length; c++) {{
        if(clusters[c].includes(idx)) {{
          clusterIdx = c;
          break;
        }}
      }}
      
      // Si hay un cluster seleccionado, solo dibujar ese cluster
      if(selectedClusterIdx !== null && clusterIdx !== selectedClusterIdx) return;
      
      const p1 = toC(d.desmarque_x, d.desmarque_y);
      const p2 = toC(d.endX, d.endY);
      const color = K_CONFIG.colors[clusterIdx % K_CONFIG.colors.length];
      
      // Dibujar flecha de desmarque
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
      
      // Punta de flecha
      const dx = p2.x - p1.x, dy = p2.y - p1.y;
      const len = Math.sqrt(dx*dx + dy*dy);
      if(len > 4) {{
        const ux = dx/len, uy = dy/len;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(p2.x, p2.y);
        ctx.lineTo(p2.x - 8*ux + 4*uy, p2.y - 8*uy - 4*ux);
        ctx.lineTo(p2.x - 8*ux - 4*uy, p2.y - 8*uy + 4*ux);
        ctx.closePath();
        ctx.fill();
      }}
    }});
    
    // Dibujar medias de clusters como vectores si está activado
    if(showCentroids && clusters) {{
      ctx.globalAlpha = 1;
      const stats = spectralData.stats;
      
      // Calcular medias de cada cluster
      clusters.forEach((clusterIndices, clusterIdx) => {{
        if(clusterIndices.length === 0) return;
        
        const clusterData = clusterIndices.map(i => desmarques[i]);
        let sum_x = 0, sum_y = 0, sum_angle = 0, sum_dist = 0, count = 0;
        
        clusterData.forEach(d => {{
          if(d.desmarque_x !== null && d.desmarque_y !== null && 
             d.desmarque_angulo !== null && d.desmarque_distancia !== null) {{
            sum_x += d.desmarque_x;
            sum_y += d.desmarque_y;
            sum_angle += d.desmarque_angulo;
            sum_dist += d.desmarque_distancia;
            count++;
          }}
        }});
        
        if(count === 0) return;
        
        const mean_x = sum_x / count;
        const mean_y = sum_y / count;
        const mean_angle = sum_angle / count;
        const mean_dist = sum_dist / count;
        
        const pos = toC(mean_x, mean_y);
        const color = K_CONFIG.colors[clusterIdx % K_CONFIG.colors.length];
        
        // Calcular punto final del vector basado en ángulo y distancia
        const angleRad = (mean_angle * Math.PI) / 180;
        const endX = mean_x + (mean_dist * Math.cos(angleRad)) / 2;
        const endY = mean_y + (mean_dist * Math.sin(angleRad)) / 2;
        const endPos = toC(endX, endY);
        
        // Dibujar vector (flecha)
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(endPos.x, endPos.y);
        ctx.stroke();
        
        // Punta de flecha
        const dx = endPos.x - pos.x, dy = endPos.y - pos.y;
        const len = Math.sqrt(dx*dx + dy*dy);
        if(len > 4) {{
          const ux = dx/len, uy = dy/len;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.moveTo(endPos.x, endPos.y);
          ctx.lineTo(endPos.x - 8*ux + 4*uy, endPos.y - 8*uy - 4*ux);
          ctx.lineTo(endPos.x - 8*ux - 4*uy, endPos.y - 8*uy + 4*ux);
          ctx.closePath();
          ctx.fill();
        }}
        
        // Círculo en el origen del vector - más grande con borde negro
        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 12, 0, 2*Math.PI);
        ctx.fill();
        
        // Borde negro grueso
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 3;
        ctx.stroke();
        
        // Borde blanco interior
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Número del cluster
        ctx.fillStyle = 'white';
        ctx.font = 'bold 11px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(clusterIdx + 1, pos.x, pos.y);
      }});
    }}
    
    ctx.globalAlpha = 1;
    document.getElementById('seq-indicator').style.display = 'none';
    return;
  }}
  
  // Modo normal: dibujar acciones normales (no desmarques)
  canvas._toC = toC;
  canvas._datos = datos;

  const activeSeqKey = secuenciaActual
    ? secuenciaActual.matchId + '|' + Math.round(secuenciaActual.sequenceId)
    : null;

  function dibujarFlecha(d, isActive) {{
    if (d.x===null||d.endX===null||d.y===null||d.endY===null) return;
    const p0 = toC(d.x, d.y);
    const p1 = toC(d.endX, d.endY);
    const color = TIPO_COLORES[d.tipo] || '#ffffff';
    const dx=p1.x-p0.x, dy=p1.y-p0.y;
    const len=Math.sqrt(dx*dx+dy*dy);
    const ux=len>0?dx/len:0, uy=len>0?dy/len:0;

    if (!isActive) {{
      ctx.strokeStyle=color; ctx.lineWidth=1; ctx.globalAlpha=0.10;
      ctx.setLineDash([]);
      ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();
      if(len>4){{ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p1.x-6*ux+3*uy,p1.y-6*uy-3*ux);ctx.lineTo(p1.x-6*ux-3*uy,p1.y-6*uy+3*ux);ctx.closePath();ctx.fill();}}
      ctx.globalAlpha=1; return;
    }}

    if (activeSeqKey) {{
      ctx.strokeStyle='rgba(255,255,255,0.35)'; ctx.lineWidth=7; ctx.globalAlpha=1;
      ctx.setLineDash([]);
      ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();
    }}

    ctx.strokeStyle=color;
    ctx.lineWidth = activeSeqKey ? 3.5 : (d.exitoso ? 2 : 1);
    ctx.globalAlpha = 1;
    ctx.setLineDash(d.exitoso ? [] : [4,3]);
    ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();
    ctx.setLineDash([]);

    if (len>4) {{
      const al = activeSeqKey ? 12 : 8;
      const aw = activeSeqKey ? 6 : 4;
      ctx.fillStyle=color; ctx.globalAlpha=1;
      ctx.beginPath();ctx.moveTo(p1.x,p1.y);
      ctx.lineTo(p1.x-al*ux+aw*uy,p1.y-al*uy-aw*ux);
      ctx.lineTo(p1.x-al*ux-aw*uy,p1.y-al*uy+aw*ux);
      ctx.closePath();ctx.fill();
    }}

    const r = activeSeqKey ? 6 : 3;
    ctx.fillStyle='white'; ctx.globalAlpha=1;
    ctx.beginPath();ctx.arc(p0.x,p0.y,r,0,2*Math.PI);ctx.fill();
    if (activeSeqKey) {{
      ctx.strokeStyle=color; ctx.lineWidth=2;
      ctx.beginPath();ctx.arc(p0.x,p0.y,r,0,2*Math.PI);ctx.stroke();
    }}

    if (mostrarLabels) {{
      ctx.globalAlpha=0.9; ctx.fillStyle='white';
      ctx.font='bold 9px DM Sans,sans-serif'; ctx.textAlign='center';
      ctx.fillText((d.distancia||'?')+'m',(p0.x+p1.x)/2,(p0.y+p1.y)/2-5);
    }}
    ctx.globalAlpha=1;
  }}

  // Dos pasadas: primero dimmed, luego activas
  if (activeSeqKey) {{
    datos.forEach((d, idx) => {{
      const seqKey=d.matchId+'|'+Math.round(d.sequenceId);
      if (seqKey!==activeSeqKey) {{
        dibujarFlecha(d, false);
      }}
    }});
  }}
  datos.forEach((d, idx) => {{
    const seqKey=d.matchId+'|'+Math.round(d.sequenceId);
    if (!activeSeqKey||seqKey===activeSeqKey) {{
      dibujarFlecha(d, true);
    }}
  }});
  ctx.globalAlpha=1;
  document.getElementById('seq-indicator').style.display = datos.length ? 'inline' : 'none';
  const countEl = document.getElementById('acciones-count');
  if (countEl) countEl.textContent = datos.length ? datos.length.toLocaleString('es-ES') + ' acciones' : '';
}}

document.getElementById('campograma').addEventListener('click', function(e) {{
  const rect = this.getBoundingClientRect();
  const mx = (e.clientX - rect.left);
  const my = (e.clientY - rect.top);
  const datos = this._datos || [];
  const toC   = this._toC;
  if (!toC) return;

  function distPtSeg(px,py,ax,ay,bx,by) {{
    const dx=bx-ax, dy=by-ay;
    const len2=dx*dx+dy*dy;
    if (len2===0) return Math.sqrt((px-ax)**2+(py-ay)**2);
    const t=Math.max(0,Math.min(1,((px-ax)*dx+(py-ay)*dy)/len2));
    return Math.sqrt((px-(ax+t*dx))**2+(py-(ay+t*dy))**2);
  }}

  let best=null, bestDist=18;
  datos.forEach(d => {{
    if (d.x===null||d.endX===null) return;
    const p0=toC(d.x,d.y), p1=toC(d.endX,d.endY);
    const dd=distPtSeg(mx,my,p0.x,p0.y,p1.x,p1.y);
    if (dd<bestDist) {{ bestDist=dd; best=d; }}
  }});
  if (best) abrirSecuencia(best);
}});

function abrirSecuencia(d) {{
  secuenciaActual = d;
  const seqKey = d.matchId + '|' + Math.round(d.sequenceId);
  const eventos = EMBEDDED_SEQUENCES[seqKey];

  document.getElementById('seq-panel').style.display='flex';
  document.getElementById('pitch-seq-layout').classList.add('has-seq');
  document.getElementById('seq-title').textContent = d.equipo + ' vs ' + d.rival;

  const min2 = String(Math.round(d.minute)).padStart(2,'0');
  const sec2 = String(Math.round(d.second)).padStart(2,'0');
  document.getElementById('seq-subtitle').innerHTML = `
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Fecha:</span> ${{d.fecha}}</span>
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Portero:</span> ${{d.jugador}}</span>
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Min:</span> ${{min2}}:${{sec2}}</span>
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Tipo:</span> <strong>${{d.tipo}}</strong></span>
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Distancia:</span> ${{d.distancia ? d.distancia.toFixed(1)+'m' : '—'}}</span>
    <span class="seq-subtitle-item"><span class="seq-subtitle-label">Resultado:</span> ${{d.exitoso ? '\u2705 Exitoso' : '\u274c Fallido'}}</span>
    ${{(d.seq_xg||0) > 0 ? '<span class="seq-subtitle-item"><span class="seq-subtitle-label">xG secuencia:</span> <strong style="color:#f4c542;">'+((d.seq_xg||0).toFixed(3))+'</strong></span>' : ''}}
    ${{d.has_desmarque ? '<span class="seq-subtitle-item"><span class="seq-subtitle-label">Dist. desmarque:</span> <strong style="color:#a78bfa;">'+((d.desmarque_run_dist||0).toFixed(1))+'m</strong></span>' : ''}}
    ${{d.retencion_7s===1 ? '<span class="seq-subtitle-item"><span class="seq-subtitle-label">Retención 7s:</span> <strong style="color:#4ade80;">\u2705 Sí</strong></span>' : '<span class="seq-subtitle-item"><span class="seq-subtitle-label">Retención 7s:</span> <strong style="color:#f87171;">\u274c No</strong></span>'}}
    ${{d.has_aerial_duel===1 ? '<span class="seq-subtitle-item"><span class="seq-subtitle-label">Duelo aéreo:</span> <strong style="color:'+(d.aerial_duel_won===1?'#4ade80':'#f87171')+';"> '+(d.aerial_duel_won===1?'\u2705 Ganado':'\u274c Perdido')+'</strong></span>' : ''}}
  `;

  const _wrapper=document.getElementById('main-pitch-wrapper');
  function _onEnd(ev){{if(ev.target!==_wrapper)return;_wrapper.removeEventListener('transitionend',_onEnd);const df=obtenerDatosFiltrados();dibujarCampograma(df);}}
  _wrapper.addEventListener('transitionend',_onEnd);
  setTimeout(()=>{{_wrapper.removeEventListener('transitionend',_onEnd);const df=obtenerDatosFiltrados();dibujarCampograma(df);}},350);

  if (!eventos || eventos.length===0) {{
    const c=document.getElementById('seq-canvas');
    const cx=c.getContext('2d'); cx.clearRect(0,0,c.width,c.height);
    cx.fillStyle='#1a4d2e'; cx.fillRect(0,0,c.width,c.height);
    cx.fillStyle='rgba(255,255,255,.5)'; cx.font='bold 14px DM Sans,sans-serif';
    cx.textAlign='center'; cx.fillText('Secuencia no disponible',c.width/2,c.height/2);
    document.getElementById('seq-events-list').innerHTML='';
    return;
  }}
  dibujarSecuenciaCanvas(eventos, d);
  mostrarListaEventos(eventos, d);
}}

function cerrarSecuencia() {{
  secuenciaActual=null;
  document.getElementById('seq-panel').style.display='none';
  const layout=document.getElementById('pitch-seq-layout');
  layout.classList.remove('has-seq');
  const wrapper=document.getElementById('main-pitch-wrapper');
  function onEnd(ev){{if(ev.target!==wrapper)return;wrapper.removeEventListener('transitionend',onEnd);const df=obtenerDatosFiltrados();dibujarCampograma(df);}}
  wrapper.addEventListener('transitionend',onEnd);
  setTimeout(()=>{{wrapper.removeEventListener('transitionend',onEnd);const df=obtenerDatosFiltrados();dibujarCampograma(df);}},350);
}}

function dibujarSecuenciaCanvas(eventos, situacion) {{
  const canvas=document.getElementById('seq-canvas');
  const ctx=canvas.getContext('2d');
  const W=canvas.width, H=canvas.height;

  const aspectRatio=105/68;
  let fW,fH,oX,oY;
  if(W/H>aspectRatio){{fH=H*0.9;fW=fH*aspectRatio;}}
  else{{fW=W*0.9;fH=fW/aspectRatio;}}
  oX=(W-fW)/2; oY=(H-fH)/2;

  function toC(ox,oy){{return{{x:oX+(ox/100)*fW, y:oY+fH-(oy/100)*fH}};}}

  ctx.fillStyle='#1a4d2e';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='rgba(255,255,255,0.8)';ctx.lineWidth=1.5;
  const corn=[toC(0,0),toC(100,0),toC(100,100),toC(0,100)];
  ctx.beginPath();ctx.moveTo(corn[0].x,corn[0].y);
  corn.slice(1).forEach(c=>ctx.lineTo(c.x,c.y));ctx.closePath();ctx.stroke();
  const mT=toC(50,0),mB=toC(50,100);
  ctx.beginPath();ctx.moveTo(mT.x,mT.y);ctx.lineTo(mB.x,mB.y);ctx.stroke();
  const cen=toC(50,50),radC=(9.15/0.68/100)*fH;
  ctx.beginPath();ctx.arc(cen.x,cen.y,radC,0,2*Math.PI);ctx.stroke();
  ctx.strokeRect(oX,oY+(21.1/100)*fH,(16.5/100)*fW,(57.8/100)*fH);
  ctx.strokeRect(oX+(83.5/100)*fW,oY+(21.1/100)*fH,(16.5/100)*fW,(57.8/100)*fH);
  ctx.strokeRect(oX,oY+(36.8/100)*fH,(5.5/100)*fW,(26.4/100)*fH);
  ctx.strokeRect(oX+(94.5/100)*fW,oY+(36.8/100)*fH,(5.5/100)*fW,(26.4/100)*fH);

  const teamColors={{}};
  const teams=[...new Set(eventos.map(e=>e.team))];
  const palette=['#74e2b5','#60a5fa','#fb923c','#f87171','#f4c542','#c084fc'];
  teams.forEach((t,i)=>teamColors[t]=palette[i%palette.length]);

  const CARRY_COLOR = '#f59e0b';
  eventos.forEach((ev,idx)=>{{
    if (idx===0) return;
    const prev=eventos[idx-1];
    if (prev.endX===null||prev.endY===null||ev.x===null||ev.y===null) return;
    const distM=Math.sqrt(((prev.endX-ev.x)*105/100)**2+((prev.endY-ev.y)*68/100)**2);
    if (distM<0.8) return;
    const pA=toC(prev.endX,prev.endY);
    const pB=toC(ev.x,ev.y);
    const dx=pB.x-pA.x, dy=pB.y-pA.y, len=Math.sqrt(dx*dx+dy*dy);
    if (len<3) return;
    const ux=dx/len, uy=dy/len;

    ctx.strokeStyle='rgba(245,158,11,0.25)'; ctx.lineWidth=5; ctx.globalAlpha=1;
    ctx.setLineDash([]);
    ctx.beginPath();ctx.moveTo(pA.x,pA.y);ctx.lineTo(pB.x,pB.y);ctx.stroke();

    ctx.strokeStyle=CARRY_COLOR; ctx.lineWidth=2.2; ctx.globalAlpha=0.9;
    ctx.setLineDash([6,2]);
    ctx.beginPath();ctx.moveTo(pA.x,pA.y);ctx.lineTo(pB.x,pB.y);ctx.stroke();
    ctx.setLineDash([]);

    const al=9, aw=5;
    ctx.fillStyle=CARRY_COLOR; ctx.globalAlpha=1;
    ctx.beginPath();ctx.moveTo(pB.x,pB.y);
    ctx.lineTo(pB.x-al*ux+aw*uy,pB.y-al*uy-aw*ux);
    ctx.lineTo(pB.x-al*ux-aw*uy,pB.y-al*uy+aw*ux);
    ctx.closePath();ctx.fill();

    ctx.fillStyle=CARRY_COLOR; ctx.globalAlpha=0.9;
    ctx.beginPath();ctx.arc(pA.x,pA.y,3,0,2*Math.PI);ctx.fill();

    ctx.globalAlpha=0.85; ctx.fillStyle=CARRY_COLOR;
    ctx.font='bold 8px DM Sans,sans-serif'; ctx.textAlign='center';
    ctx.fillText(distM.toFixed(1)+'m', (pA.x+pB.x)/2, (pA.y+pB.y)/2-5);
    ctx.globalAlpha=1;
  }});

  eventos.forEach((ev,idx)=>{{
    if(ev.x===null||ev.y===null) return;
    const p0=toC(ev.x,ev.y);
    const col=teamColors[ev.team]||'#ffffff';
    const isPressure=ev.pressure==='high'||ev.pressure==='medium';

    const GK_PASS_COLOR = '#facc15';
    if(ev.endX!==null&&ev.endY!==null){{
      const p1=toC(ev.endX,ev.endY);
      const lineColor = ev.isShot ? '#ff3333' : (ev.is_gk_pass ? GK_PASS_COLOR : col);
      if(ev.is_gk_pass) {{
        ctx.strokeStyle='rgba(250,204,21,0.3)'; ctx.lineWidth=8; ctx.globalAlpha=1;
        ctx.setLineDash([]);
        ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();
      }}
      ctx.strokeStyle=lineColor;
      ctx.lineWidth=ev.isShot?2.5:(ev.is_gk_pass?2.8:1.8);
      ctx.globalAlpha=ev.is_gk_pass?1:0.85;
      ctx.setLineDash([]);
      ctx.beginPath();ctx.moveTo(p0.x,p0.y);ctx.lineTo(p1.x,p1.y);ctx.stroke();
      const dx=p1.x-p0.x,dy=p1.y-p0.y,len=Math.sqrt(dx*dx+dy*dy);
      if(len>3){{
        const ux=dx/len,uy=dy/len;
        const al=ev.is_gk_pass?10:6, aw=ev.is_gk_pass?5:3;
        ctx.globalAlpha=1;
        ctx.fillStyle=lineColor;
        ctx.beginPath();ctx.moveTo(p1.x,p1.y);
        ctx.lineTo(p1.x-al*ux+aw*uy,p1.y-al*uy-aw*ux);
        ctx.lineTo(p1.x-al*ux-aw*uy,p1.y-al*uy+aw*ux);
        ctx.closePath();ctx.fill();
      }}
      ctx.globalAlpha=1;
      if(ev.isGoal){{ctx.fillStyle='#00ff00';ctx.beginPath();ctx.arc(p1.x,p1.y,6,0,2*Math.PI);ctx.fill();}}
    }}
    ctx.globalAlpha=1;
    ctx.fillStyle=isPressure?'#ff6600':col;
    ctx.beginPath();ctx.arc(p0.x,p0.y,isPressure?5:3.5,0,2*Math.PI);ctx.fill();
    ctx.fillStyle='white';ctx.font='bold 8px DM Sans,sans-serif';ctx.textAlign='center';
    ctx.fillText(idx+1,p0.x,p0.y-6);

    if(ev.is_gk_pass&&ev.desmarques&&ev.desmarques.length){{  
      const RUN_COLOR='#a78bfa';
      ev.desmarques.forEach(dm=>{{  
        if(dm.x===null||dm.y===null||dm.rx===null||dm.ry===null)return;
        const pd=toC(dm.x,dm.y);
        const pt=toC(dm.rx,dm.ry);
        const rdx=pt.x-pd.x, rdy=pt.y-pd.y, rlen=Math.sqrt(rdx*rdx+rdy*rdy);

        if(rlen>4){{
          const rux=rdx/rlen,ruy=rdy/rlen;
          ctx.strokeStyle=RUN_COLOR; ctx.lineWidth=1.5; ctx.globalAlpha=0.75;
          ctx.setLineDash([3,3]);
          ctx.beginPath();ctx.moveTo(pd.x,pd.y);ctx.lineTo(pt.x,pt.y);ctx.stroke();
          ctx.setLineDash([]);
          const ral=7,raw=3.5;
          ctx.fillStyle=RUN_COLOR; ctx.globalAlpha=0.85;
          ctx.beginPath();ctx.moveTo(pt.x,pt.y);
          ctx.lineTo(pt.x-ral*rux+raw*ruy,pt.y-ral*ruy-raw*rux);
          ctx.lineTo(pt.x-ral*rux-raw*ruy,pt.y-ral*ruy+raw*rux);
          ctx.closePath();ctx.fill();
        }}
        ctx.globalAlpha=0.9;
        ctx.fillStyle=RUN_COLOR;
        ctx.beginPath();ctx.arc(pd.x,pd.y,6,0,2*Math.PI);ctx.fill();
        ctx.strokeStyle='white';ctx.lineWidth=1.2;
        ctx.beginPath();ctx.arc(pd.x,pd.y,6,0,2*Math.PI);ctx.stroke();
        ctx.fillStyle='white';ctx.font='bold 7px DM Sans,sans-serif';ctx.textAlign='center';
        ctx.fillText('R',pd.x,pd.y+2.5);
        ctx.fillStyle=RUN_COLOR; ctx.globalAlpha=0.8;
        ctx.beginPath();ctx.arc(pt.x,pt.y,3.5,0,2*Math.PI);ctx.fill();
        ctx.globalAlpha=1;
      }});
    }}

  }});
  ctx.globalAlpha=1;

  ctx.font='bold 10px DM Sans,sans-serif'; ctx.textAlign='left';
  Object.entries(teamColors).forEach(([t,c],i)=>{{
    ctx.fillStyle=c; ctx.fillRect(oX+5,oY+5+i*16,12,10);
    ctx.fillStyle='white'; ctx.fillText(t,oX+21,oY+13+i*16);
  }});
  const lx=oX+fW-130, ly=oY+5;
  ctx.strokeStyle=CARRY_COLOR; ctx.lineWidth=2; ctx.setLineDash([5,2]);
  ctx.beginPath();ctx.moveTo(lx,ly+5);ctx.lineTo(lx+22,ly+5);ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle=CARRY_COLOR;
  ctx.beginPath();ctx.moveTo(lx+22,ly+5);ctx.lineTo(lx+16,ly+2);ctx.lineTo(lx+16,ly+8);ctx.closePath();ctx.fill();
  ctx.fillStyle='white'; ctx.font='9px DM Sans,sans-serif';
  ctx.fillText('Conducción con balón',lx+26,ly+9);
  ctx.strokeStyle='#a78bfa'; ctx.lineWidth=1.5; ctx.setLineDash([3,3]);
  ctx.beginPath();ctx.moveTo(lx,ly+22);ctx.lineTo(lx+22,ly+22);ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle='#a78bfa';
  ctx.beginPath();ctx.arc(lx+3,ly+22,5,0,2*Math.PI);ctx.fill();
  ctx.fillStyle='white';ctx.font='bold 7px DM Sans,sans-serif';ctx.textAlign='center';
  ctx.fillText('R',lx+3,ly+24.5);
  ctx.fillStyle='white';ctx.font='9px DM Sans,sans-serif';ctx.textAlign='left';
  ctx.fillText('Desmarque receptor',lx+26,ly+26);
  ctx.strokeStyle='#facc15'; ctx.lineWidth=2.5; ctx.setLineDash([]);
  ctx.beginPath();ctx.moveTo(lx,ly+39);ctx.lineTo(lx+22,ly+39);ctx.stroke();
  ctx.fillStyle='#facc15';
  ctx.beginPath();ctx.moveTo(lx+22,ly+39);ctx.lineTo(lx+16,ly+36);ctx.lineTo(lx+16,ly+42);ctx.closePath();ctx.fill();
  ctx.fillStyle='white';ctx.font='9px DM Sans,sans-serif';ctx.textAlign='left';
  ctx.fillText('Pase portero',lx+26,ly+43);

}}

function mostrarListaEventos(eventos, situacion) {{
  const container=document.getElementById('seq-events-list');
  container.innerHTML='';
  eventos.forEach((ev,idx)=>{{
    const div=document.createElement('div');
    div.className='seq-event-item'+(ev.isGoal?' goal':ev.isShot?' shot':ev.pressure==='high'?' pressure-high':'');
    const min2=String(Math.round(ev.minute)).padStart(2,'0');
    const sec2=String(Math.round(ev.second)).padStart(2,'0');
    let pressHTML='';
    if(ev.pressure){{
      pressHTML=`<span class="pressure-badge pressure-${{ev.pressure}}">${{ev.pressure}}</span>`;
    }}
    div.innerHTML=`
      <div class="seq-event-time">${{idx+1}}. ${{min2}}:${{sec2}} — ${{ev.team}}${{pressHTML}}</div>
      <div class="seq-event-detail">${{ev.event}} · ${{ev.outcome||''}}
        ${{ev.isGoal?'<strong>⚽ GOL</strong>':ev.isShot?'🎯 Disparo':''}}
      </div>
    `;
    container.appendChild(div);
  }});
}}

function actualizarSonar(datos) {{
  const canvas = document.getElementById('sonar-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const W = Math.round(rect.width) || 380;
  const H = Math.round(rect.height) || 380;
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  ctx.scale(dpr, dpr);
  const cx = W / 2, cy = H / 2;
  const maxR = Math.min(cx, cy) - 42;

  ctx.fillStyle = '#1a2332';
  ctx.fillRect(0, 0, W, H);

  const N = 12, degPerSec = 360 / N;
  const sectors = Array.from({{length: N}}, () => ({{total: 0, exitosos: 0}}));
  const withAngle = datos.filter(d => d.angulo !== null && d.angulo !== undefined);
  withAngle.forEach(d => {{
    const sec = Math.floor(((d.angulo % 360) + 360) % 360 / degPerSec) % N;
    sectors[sec].total++;
    if (d.exitoso) sectors[sec].exitosos++;
  }});
  const maxCount = Math.max(...sectors.map(s => s.total), 1);

  [0.25, 0.5, 0.75, 1.0].forEach(f => {{
    const r = maxR * f;
    ctx.strokeStyle = f < 1 ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.22)';
    ctx.lineWidth = f < 1 ? 1 : 1.5;
    ctx.setLineDash(f < 1 ? [3, 3] : []);
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI); ctx.stroke();
    ctx.setLineDash([]);
    if (f < 1) {{
      ctx.fillStyle = 'rgba(255,255,255,0.3)';
      ctx.font = '8px DM Sans,sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'bottom';
      ctx.fillText(Math.round(maxCount * f), cx + r + 3, cy - 2);
    }}
  }});

  for (let i = 0; i < N; i++) {{
    const angle = (i * degPerSec - 90) * Math.PI / 180;
    ctx.strokeStyle = 'rgba(255,255,255,0.1)';
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.lineTo(cx + maxR * Math.cos(angle), cy + maxR * Math.sin(angle));
    ctx.stroke(); ctx.setLineDash([]);
  }}

  sectors.forEach((s, i) => {{
    if (s.total === 0) return;
    const pct = s.exitosos / s.total;
    const rr = pct < 0.5 ? 220 : Math.round((1 - (pct - 0.5) * 2) * 220);
    const gg = Math.round(pct < 0.5 ? pct * 2 * 200 : 200);
    const sectorR = maxR * (s.total / maxCount);
    const startA = (i * degPerSec - 90 - degPerSec / 2) * Math.PI / 180;
    const endA   = (i * degPerSec - 90 + degPerSec / 2) * Math.PI / 180;
    ctx.fillStyle = `rgba(${{rr}},${{gg}},80,0.85)`;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, sectorR, startA, endA);
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 0.8;
    ctx.stroke();
  }});

  const labelR = maxR + 26;
  ctx.fillStyle = 'rgba(255,255,255,0.65)';
  ctx.font = '9px DM Sans,sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (let i = 0; i < N; i++) {{
    const deg = i * degPerSec;
    const angle = (deg - 90) * Math.PI / 180;
    ctx.fillText(deg + '°', cx + labelR * Math.cos(angle), cy + labelR * Math.sin(angle));
  }}

  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.font = 'bold 9px DM Sans,sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('n=' + withAngle.length, cx, cy);

  const lgX = 10, lgY = H - 28, lgW = 100, lgH = 8;
  const grad = ctx.createLinearGradient(lgX, lgY, lgX + lgW, lgY);
  grad.addColorStop(0, 'rgba(220,0,80,0.9)');
  grad.addColorStop(0.5, 'rgba(220,200,80,0.9)');
  grad.addColorStop(1, 'rgba(0,200,80,0.9)');
  ctx.fillStyle = grad; ctx.fillRect(lgX, lgY, lgW, lgH);
  ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth = 0.5;
  ctx.strokeRect(lgX, lgY, lgW, lgH);
  ctx.fillStyle = 'rgba(255,255,255,0.6)';
  ctx.font = '8px DM Sans,sans-serif'; ctx.textBaseline = 'top';
  ctx.textAlign = 'left'; ctx.fillText('0% éxito', lgX, lgY + 11);
  ctx.textAlign = 'right'; ctx.fillText('100%', lgX + lgW, lgY + 11);
}}

function actualizarEquipoTable(datos) {{
  const equipos={{}};
  datos.forEach(d=>{{
    const k=d.equipo+' ('+d.temporada+')';
    if(!equipos[k]) equipos[k]={{total:0,exitosos:0,dists:[],goalkicks:0,longballs:0,xa:0,retencion:0,aerialTotal:0,aerialWon:0}};
    equipos[k].total++;
    if(d.exitoso) equipos[k].exitosos++;
    if(d.distancia!==null) equipos[k].dists.push(d.distancia);
    if(d.is_goal_kick) equipos[k].goalkicks++;
    if(d.is_longball) equipos[k].longballs++;
    equipos[k].xa+=(d.xA||0);
    if(d.retencion_7s===1) equipos[k].retencion++;
    if(d.has_aerial_duel===1) {{ equipos[k].aerialTotal++; if(d.aerial_duel_won===1) equipos[k].aerialWon++; }}
  }});
  const sorted=Object.entries(equipos).sort((a,b)=>b[1].total-a[1].total);
  const tbody=document.getElementById('equipo-table-body');
  tbody.innerHTML='';
  sorted.forEach(([k,v],i)=>{{
    const avgD=v.dists.length?(v.dists.reduce((s,x)=>s+x,0)/v.dists.length).toFixed(1):'-';
    const pct=v.total?Math.round(v.exitosos/v.total*100):0;
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td class="rank">${{i+1}}</td>
      <td>${{k}}</td>
      <td class="num">${{v.total}}</td>
      <td class="num">${{pct}}%</td>
      <td class="num">${{avgD}}m</td>
      <td class="num">${{v.goalkicks}}</td>
      <td class="num">${{v.longballs}}</td>
      <td class="num">${{v.xa.toFixed(3)}}</td>
      <td class="num">${{v.total?Math.round(v.retencion/v.total*100):0}}%</td>
      <td class="num">${{v.aerialTotal ? v.aerialTotal+' ('+Math.round(v.aerialWon/v.aerialTotal*100)+'% G)' : '—'}}</td>
    `;
    tbody.appendChild(tr);
  }});
}}

function actualizarAerialTable(datos) {{
  const tbody = document.getElementById('aerial-table-body');
  if (!tbody) return;
  const jugadores = {{}};
  datos.filter(d => d.has_aerial_duel === 1 && d.aerial_player).forEach(d => {{
    const k = d.aerial_player + '||' + d.equipo + '||' + d.temporada;
    if (!jugadores[k]) jugadores[k] = {{
      jugador: d.aerial_player,
      equipo: d.equipo + ' (' + d.temporada + ')',
      aerialTotal: 0, aerialWon: 0, aerialLost: 0
    }};
    jugadores[k].aerialTotal++;
    if (d.aerial_duel_won === 1) jugadores[k].aerialWon++;
    else jugadores[k].aerialLost++;
  }});
  const sorted = Object.values(jugadores)
    .sort((a, b) => b.aerialTotal - a.aerialTotal);
  tbody.innerHTML = '';
  sorted.forEach((v, i) => {{
    const pctG = Math.round(v.aerialWon / v.aerialTotal * 100);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="rank">${{i+1}}</td>
      <td style="font-weight:600;">${{v.jugador}}</td>
      <td>${{v.equipo}}</td>
      <td class="num" style="font-weight:700;">${{v.aerialTotal}}</td>
      <td class="num" style="color:#4ade80;">${{v.aerialWon}}</td>
      <td class="num" style="color:#f87171;">${{v.aerialLost}}</td>
      <td class="num">
        <div style="display:flex;align-items:center;gap:6px;">
          <div style="width:80px;height:10px;border-radius:4px;overflow:hidden;background:#f87171;display:flex;">
            <div style="width:${{pctG}}%;background:#4ade80;"></div>
          </div>
          <span style="font-weight:700;color:${{pctG>=50?'#4ade80':'#f87171'}}">${{pctG}}%</span>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  }});
  if (sorted.length === 0) {{
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-dim);padding:1.5rem;">Sin datos de duelos aéreos para los filtros actuales</td></tr>';
  }}
}}

// ──── CLUSTERING FUNCTIONS ────────────────────────────────────────────────
function normalizeData(points, features) {{
  const data = [];
  const stats = features.map(f => ({{mean: 0, std: 1}}));
  
  features.forEach((f, i) => {{
    const vals = points.filter(p => p[f] !== null && p[f] !== undefined).map(p => p[f]);
    if(vals.length===0) return;
    stats[i].mean = vals.reduce((a, b) => a + b, 0) / vals.length;
  }});
  
  features.forEach((f, i) => {{
    const vals = points.filter(p => p[f] !== null && p[f] !== undefined).map(p => p[f]);
    if(vals.length===0) return;
    const variance = vals.reduce((sum, v) => sum + Math.pow(v - stats[i].mean, 2), 0) / vals.length;
    stats[i].std = Math.sqrt(variance) || 1;
  }});
  
  points.forEach(p => {{
    if(features.some(f => p[f] === null || p[f] === undefined)) return;
    const normalized = features.map((f, i) => (p[f] - stats[i].mean) / stats[i].std);
    data.push(normalized);
  }});
  
  return {{ data, stats }};
}}

function euclideanDistance(p1, p2) {{
  return Math.sqrt(p1.reduce((sum, v, i) => sum + Math.pow(v - p2[i], 2), 0));
}}

function kmeanspp(data, k) {{
  if(!data || data.length === 0) return [];
  if(data.length < k) k = data.length;
  const centroids = [[...data[Math.floor(Math.random() * data.length)]]];
  for (let i = 1; i < k; i++) {{
    const dists = data.map(p => Math.min(...centroids.map(c => euclideanDistance(p, c))) ** 2);
    const sumDists = dists.reduce((a, b) => a + b, 0);
    if(sumDists === 0) break;
    let r = Math.random() * sumDists, acc = 0;
    for (let j = 0; j < data.length; j++) {{
      acc += dists[j];
      if (acc >= r) {{ centroids.push([...data[j]]); break; }}
    }}
  }}
  return centroids;
}}

function kmeans(data, k) {{
  if(!data || data.length < k || k < 1) return {{ centroids: [], clusters: [] }};
  let centroids = kmeanspp(data, k);
  if(centroids.length === 0) return {{ centroids: [], clusters: [] }};
  
  for (let iter = 0; iter < K_CONFIG.maxIter; iter++) {{
    const clusters = Array(k).fill(0).map(() => []);
    data.forEach((p, i) => {{
      let closest = 0, minDist = Infinity;
      centroids.forEach((c, j) => {{
        const dist = euclideanDistance(p, c);
        if (dist < minDist) {{ minDist = dist; closest = j; }}
      }});
      clusters[closest].push(i);
    }});
    
    const newCentroids = clusters.map((c, i) => 
      c.length ? data[0].map((v, j) => c.reduce((sum, idx) => sum + data[idx][j], 0) / c.length) 
               : [...centroids[i]]
    );
    
    const moved = centroids.reduce((sum, c, i) => sum + euclideanDistance(c, newCentroids[i]), 0);
    centroids = newCentroids;
    if (moved < K_CONFIG.tol) break;
  }}
  
  const clusters = Array(k).fill(0).map(() => []);
  data.forEach((p, i) => {{
    let closest = 0, minDist = Infinity;
    centroids.forEach((c, j) => {{
      const dist = euclideanDistance(p, c);
      if (dist < minDist) {{ minDist = dist; closest = j; }}
    }});
    clusters[closest].push(i);
  }});
  
  return {{ centroids, clusters }};
}}

function silhouetteScore(data, clusters) {{
  if (clusters.length < 2) return -1;
  let totalScore = 0, count = 0;
  
  clusters.forEach((cluster, i) => {{
    cluster.forEach(idx => {{
      const p = data[idx];
      const a = cluster.length > 1 ? cluster.filter(j => j !== idx).reduce((sum, j) => sum + euclideanDistance(p, data[j]), 0) / (cluster.length - 1) : 0;
      
      let b = Infinity;
      clusters.forEach((other, j) => {{
        if (i !== j) {{
          const dist = other.length > 0 ? other.reduce((sum, k) => sum + euclideanDistance(p, data[k]), 0) / other.length : 0;
          b = Math.min(b, dist);
        }}
      }});
      
      const score = Math.max(a, b) > 0 ? (b - a) / Math.max(a, b) : 0;
      totalScore += score;
      count++;
    }});
  }});
  
  return totalScore / Math.max(1, count);
}}

function findOptimalK(data) {{
  let bestK = 2, bestScore = -Infinity;
  const maxK = Math.min(10, Math.floor(data.length / 2));
  
  for (let k = 2; k <= maxK; k++) {{
    const result = kmeans(data, k);
    const score = silhouetteScore(data, result.clusters);
    if (score > bestScore) {{ bestScore = score; bestK = k; }}
  }}
  
  return bestK;
}}

function rbfKernel(dist, gamma = 0.5) {{
  return Math.exp(-gamma * dist * dist);
}}

function computeAffinityMatrix(data) {{
  const n = data.length;
  const W = Array(n).fill(0).map(() => Array(n).fill(0));
  const gamma = 0.5;
  for (let i = 0; i < n; i++) {{
    for (let j = i + 1; j < n; j++) {{
      const dist = euclideanDistance(data[i], data[j]);
      const similarity = rbfKernel(dist, gamma);
      W[i][j] = similarity;
      W[j][i] = similarity;
    }}
  }}
  return W;
}}

function computeLaplacianEigenvectors(W, k) {{
  const n = W.length;
  const D = Array(n).fill(0).map(() => Array(n).fill(0));
  
  for (let i = 0; i < n; i++) {{
    let degree = 0;
    for (let j = 0; j < n; j++) degree += W[i][j];
    D[i][i] = Math.max(degree, 1e-6);
  }}
  
  const L = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      L[i][j] = (i === j ? D[i][i] : 0) - W[i][j];
    }}
  }}
  
  const D_inv_sqrt = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    D_inv_sqrt[i][i] = 1.0 / Math.sqrt(D[i][i]);
  }}
  
  let temp = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      for (let p = 0; p < n; p++) {{
        temp[i][j] += D_inv_sqrt[i][i] * L[i][p];
      }}
    }}
  }}
  
  let L_norm = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      for (let p = 0; p < n; p++) {{
        L_norm[i][j] += temp[i][p] * D_inv_sqrt[p][j];
      }}
    }}
  }}
  
  const eigenvectors = [];
  for (let vec = 0; vec < Math.min(k, n); vec++) {{
    let v = Array(n).fill(0).map(() => Math.random());
    let norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
    v = v.map(x => x / norm);
    
    for (let iter = 0; iter < 30; iter++) {{
      let Lv = Array(n).fill(0);
      for (let i = 0; i < n; i++) {{
        for (let j = 0; j < n; j++) {{
          Lv[i] += L_norm[i][j] * v[j];
        }}
      }}
      
      norm = Math.sqrt(Lv.reduce((s, x) => s + x * x, 0));
      if (norm < 1e-6) break;
      v = Lv.map(x => x / norm);
    }}
    
    eigenvectors.push(v);
    
    for (let i = 0; i < n; i++) {{
      for (let j = 0; j < n; j++) {{
        L_norm[i][j] -= v[i] * v[j];
      }}
    }}
  }}
  
  return eigenvectors;
}}

function spectralClustering(data, k) {{
  if (!data || data.length < k || k < 1) return {{ clusters: [] }};
  
  const W = computeAffinityMatrix(data);
  const eigenvecs = computeLaplacianEigenvectors(W, k);
  
  const spectralData = Array(data.length).fill(0).map((_, i) =>
    eigenvecs.map(ev => ev[i])
  );
  
  const kmResult = kmeans(spectralData, k);
  return kmResult;
}}

// Calcular eigenvalores aproximados usando power iteration
function approximateEigenvalues(laplacianMatrix, numEigenvalues) {{
  const n = laplacianMatrix.length;
  const eigenvalues = [];
  let L = laplacianMatrix.map(row => [...row]);  // Copia
  
  // Calcular eigenvalores por power iteration
  for (let ev = 0; ev < Math.min(numEigenvalues, n); ev++) {{
    let v = Array(n).fill(0).map(() => Math.random());
    let norm = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
    v = v.map(x => x / norm);
    
    let lambda = 0;
    
    // Power iteration (15 iteraciones)
    for (let iter = 0; iter < 15; iter++) {{
      let Lv = Array(n).fill(0);
      for (let i = 0; i < n; i++) {{
        for (let j = 0; j < n; j++) {{
          Lv[i] += L[i][j] * v[j];
        }}
      }}
      
      const newLambda = v.reduce((sum, vi, i) => sum + vi * Lv[i], 0);
      lambda = newLambda;
      
      norm = Math.sqrt(Lv.reduce((s, x) => s + x * x, 0));
      if (norm < 1e-6) break;
      v = Lv.map(x => x / norm);
    }}
    
    eigenvalues.push(Math.abs(lambda));
    
    // Deflation: actualizar L eliminando este eigenvalor
    for (let i = 0; i < n; i++) {{
      for (let j = 0; j < n; j++) {{
        L[i][j] -= lambda * v[i] * v[j];
      }}
    }}
  }}
  
  return eigenvalues.sort((a, b) => a - b);
}}

// Seleccionar K óptimo usando Eigengap Heuristic
function findOptimalKSpectralByEigengap(data) {{
  // Determinar maxK adaptativo según tamaño
  let maxK = 10;
  if (data.length < 50) maxK = 2;
  else if (data.length < 100) maxK = 3;
  else if (data.length < 500) maxK = 5;
  else if (data.length < 2000) maxK = 7;
  
  // Calcular matriz de afinidad y Laplacian
  const W = computeAffinityMatrix(data);
  const n = W.length;
  
  // Matriz de grado
  const D = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    let degree = 0;
    for (let j = 0; j < n; j++) degree += W[i][j];
    D[i][i] = Math.max(degree, 1e-6);
  }}
  
  // Laplacian L = D - W
  const L = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      L[i][j] = (i === j ? D[i][i] : 0) - W[i][j];
    }}
  }}
  
  // Laplacian normalizado
  const D_inv_sqrt = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    D_inv_sqrt[i][i] = 1.0 / Math.sqrt(D[i][i]);
  }}
  
  let temp = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      for (let p = 0; p < n; p++) {{
        temp[i][j] += D_inv_sqrt[i][i] * L[i][p];
      }}
    }}
  }}
  
  let L_norm = Array(n).fill(0).map(() => Array(n).fill(0));
  for (let i = 0; i < n; i++) {{
    for (let j = 0; j < n; j++) {{
      for (let p = 0; p < n; p++) {{
        L_norm[i][j] += temp[i][p] * D_inv_sqrt[p][j];
      }}
    }}
  }}
  
  // Calcular eigenvalores para diferentes K
  const eigenvalues = approximateEigenvalues(L_norm, maxK + 1);
  
  // Calcular eigengaps y encontrar máximo
  let bestK = 2, maxEigengap = 0;
  
  for (let k = 2; k <= Math.min(maxK, eigenvalues.length - 1); k++) {{
    const eigengap = eigenvalues[k] - eigenvalues[k - 1];
    console.log(`  Eigengap[K=${{k}}] = ${{eigengap.toFixed(4)}}`);
    if (eigengap > maxEigengap) {{
      maxEigengap = eigengap;
      bestK = k;
    }}
  }}
  
  console.log(`🎯 Spectral: K óptimo = ${{bestK}} (eigengap = ${{maxEigengap.toFixed(4)}})`);
  return bestK;
}}

function findOptimalKSpectral(data) {{
  return findOptimalKSpectralByEigengap(data);
}}

function generarReporteClustering(mode, clusteredData, datosOriginales) {{
  const container = document.getElementById('clustering-report-container');
  
  if(!clusteredData) {{
    container.style.display = 'none';
    return;
  }}
  
  container.style.display = 'block';
  
  const {{k, clusters}} = clusteredData;
  
  let html = `<div class="clustering-report">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
      <h4>${{mode === 'kmeans' ? '📊 Reporte K-Means' : '🌐 Reporte Spectral Clustering'}}</h4>
      <button onclick="toggleCentroides()" style="padding:6px 12px;background:#4ECDC4;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;">👁️ Ver Centroides</button>
    </div>
    <div class="clustering-metrics">
      <div class="clustering-metric">
        <div class="clustering-metric-label">Número de Clusters</div>
        <div class="clustering-metric-value">${{k}}</div>
      </div>`;
  
  html += `<div class="clustering-metric">
        <div class="clustering-metric-label">Total de Datos</div>
        <div class="clustering-metric-value">${{datosOriginales.length}}</div>
      </div>
    </div>
    
    <table class="clustering-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Cluster</th>
          <th>Tamaño</th>
          <th>xA Promedio</th>
          <th>Progr. Media</th>
          <th>Ángulo Media</th>
          <th>Long. Desm.</th>
          <th>Desm. Media X</th>
          <th>Desm. Media Y</th>
          <th>% Cambio Eje</th>
          <th>Nº Medio Acc.</th>
        </tr>
      </thead>
      <tbody>`;
  
  clusters.forEach((clusterIndices, clusterIdx) => {{
    if(clusterIndices.length === 0) return;
    
    const clusterData = clusterIndices.map(i => datosOriginales[i]);
    
    const xaTotal = clusterData.reduce((sum, d) => sum + (d.seq_xg || 0), 0);
    const xaPromedio = (xaTotal / clusterData.length).toFixed(3);
    
    const progs = clusterData.filter(d => d.progresion !== null && d.progresion !== undefined).map(d => d.progresion);
    const progMedia = progs.length > 0 ? (progs.reduce((a,b) => a+b, 0) / progs.length).toFixed(2) : '—';
    
    const angulosDes = clusterData.filter(d => d.angulo !== null && d.angulo !== undefined && d.has_desmarque === 1).map(d => d.angulo);
    const anguloMedia = angulosDes.length > 0 ? (angulosDes.reduce((a,b) => a+b, 0) / angulosDes.length).toFixed(2) : '—';
    
    const desmarques = clusterData.filter(d => d.desmarque_run_dist !== null && d.desmarque_run_dist !== undefined && d.has_desmarque === 1).map(d => d.desmarque_run_dist);
    const longDes = desmarques.length > 0 ? (desmarques.reduce((a,b) => a+b, 0) / desmarques.length).toFixed(2) : '—';
    
    const desmarqueXs = clusterData.filter(d => d.desmarque_x !== null && d.desmarque_x !== undefined).map(d => d.desmarque_x);
    const desmarqueXMedia = desmarqueXs.length > 0 ? (desmarqueXs.reduce((a,b) => a+b, 0) / desmarqueXs.length).toFixed(2) : '—';
    
    const desmarqueYs = clusterData.filter(d => d.desmarque_y !== null && d.desmarque_y !== undefined).map(d => d.desmarque_y);
    const desmarqueYMedia = desmarqueYs.length > 0 ? (desmarqueYs.reduce((a,b) => a+b, 0) / desmarqueYs.length).toFixed(2) : '—';
    
    const cambioEje = clusterData.filter(d => d.cambio_eje_50 === 1).length;
    const pctCambioEje = clusterData.length > 0 ? Math.round((cambioEje / clusterData.length) * 100) : 0;
    
    const acciones = clusterData.filter(d => d.seq_acciones_total !== null && d.seq_acciones_total !== undefined).map(d => d.seq_acciones_total);
    const numMedioAcc = acciones.length > 0 ? (acciones.reduce((a,b) => a+b, 0) / acciones.length).toFixed(2) : '—';
    
    const color = K_CONFIG.colors[clusterIdx % K_CONFIG.colors.length];
    
    html += `<tr style="cursor:pointer;" onclick="filtrarClusterCampograma(${{clusterIdx}})" id="cluster-row-${{clusterIdx}}">
      <td>${{clusterIdx + 1}}</td>
      <td><span class="cluster-badge" style="background-color:${{color}};">Cluster ${{clusterIdx + 1}}</span></td>
      <td>${{clusterIndices.length}}</td>
      <td>${{xaPromedio}}</td>
      <td>${{progMedia}}m</td>
      <td>${{anguloMedia}}°</td>
      <td>${{longDes}}m</td>
      <td>${{desmarqueXMedia}}</td>
      <td>${{desmarqueYMedia}}</td>
      <td>${{pctCambioEje}}%</td>
      <td>${{numMedioAcc}}</td>
    </tr>`;
  }});
  
  html += `</tbody></table></div>`;
  container.innerHTML = html;
}}

function filtrarClusterCampograma(clusterIdx) {{
  const currentData = kmeansMode ? kmeansData : (spectralMode ? spectralData : null);
  if(!currentData) return;
  
  // Remover resaltado anterior
  const prevSelected = document.querySelector('.clustering-table tr[style*="background"]');
  if(prevSelected) prevSelected.style.backgroundColor = '';
  
  // Si ya está seleccionado, deseleccionar (toggle)
  if(selectedClusterIdx === clusterIdx) {{
    selectedClusterIdx = null;
  }} else {{
    // Seleccionar nuevo cluster
    selectedClusterIdx = clusterIdx;
    const row = document.getElementById(`cluster-row-${{clusterIdx}}`);
    if(row) row.style.backgroundColor = 'rgba(78, 205, 196, 0.2)';
  }}
  
  // Redibujar campograma
  dibujarCampograma([]);
}}

function toggleCentroides() {{
  showCentroids = !showCentroids;
  const currentData = kmeansMode ? kmeansData : (spectralMode ? spectralData : null);
  if(currentData) {{
    dibujarCampograma([]);  // Redibujar con centroides
  }}
}}

function actualizarScatter(datos) {{
  const axX=document.getElementById('scatter-axis-x').value;
  const axY=document.getElementById('scatter-axis-y').value;
  const labels={{
    total_acciones:'Acciones',pct_exito:'% Exitosos',dist_media:'Dist. Media (m)',
    prog_media:'Progr. Media (m)',xa_total:'xG Total',xt_total:'xT Total',
    goalkicks:'GoalKicks',longballs:'Longballs',pct_retencion_7s:'% Ret. 7s'
  }};

  const equipos={{}};
  datos.forEach(d=>{{
    const k=d.equipo+' ('+d.temporada+')';
    if(!equipos[k]) equipos[k]={{total:0,exitosos:0,dists:[],progs:[],xa:0,xt:0,goalkicks:0,longballs:0,retencion:0}};
    equipos[k].total++;
    if(d.exitoso) equipos[k].exitosos++;
    if(d.distancia!==null) equipos[k].dists.push(d.distancia);
    if(d.progresion!==null) equipos[k].progs.push(d.progresion);
    equipos[k].xa+=(d.seq_xg||0);
    equipos[k].xt+=(d.xT||0);
    if(d.is_goal_kick) equipos[k].goalkicks++;
    if(d.is_longball) equipos[k].longballs++;
    if(d.retencion_7s===1) equipos[k].retencion++;
  }});

  function getVal(v,key){{
    if(key==='total_acciones') return v.total;
    if(key==='pct_exito') return v.total?Math.round(v.exitosos/v.total*100):0;
    if(key==='dist_media') return v.dists.length?+(v.dists.reduce((s,x)=>s+x,0)/v.dists.length).toFixed(1):0;
    if(key==='prog_media') return v.progs.length?+(v.progs.reduce((s,x)=>s+x,0)/v.progs.length).toFixed(1):0;
    if(key==='xa_total') return +v.xa.toFixed(3);
    if(key==='xt_total') return +v.xt.toFixed(3);
    if(key==='goalkicks') return v.goalkicks;
    if(key==='longballs') return v.longballs;
    if(key==='pct_retencion_7s') return v.total?Math.round(v.retencion/v.total*100):0;
    return 0;
  }}

  const points=Object.entries(equipos).map(([k,v])=>({{
    x:getVal(v,axX),y:getVal(v,axY),label:k
  }}));

  if(scatterChartInst) scatterChartInst.destroy();
  scatterChartInst = new Chart(document.getElementById('scatterChart'),{{
    type:'scatter',
    data:{{datasets:[{{
      data:points,
      backgroundColor:'rgba(116,226,181,0.7)',
      borderColor:'#74e2b5',
      pointRadius:7,
      pointHoverRadius:10,
    }}]}},
    options:{{
      responsive:true,maintainAspectRatio:false,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          callbacks:{{
            label:ctx=>{{
              const p=ctx.raw;
              return `${{p.label}}: (${{p.x}}, ${{p.y}})`;
            }}
          }},
          backgroundColor:'#14181f',borderColor:'#2d3642',borderWidth:1,
          titleColor:'#74e2b5',bodyColor:'#e6ebf1'
        }}
      }},
      scales:{{
        x:{{title:{{display:true,text:labels[axX],color:'#8e99ab'}},ticks:{{color:'#8e99ab'}},grid:{{color:'#2d3642'}}}},
        y:{{title:{{display:true,text:labels[axY],color:'#8e99ab'}},ticks:{{color:'#8e99ab'}},grid:{{color:'#2d3642'}}}}
      }}
    }}
  }});
}}

function initLigas() {{
  const ligas=[...new Set(EMBEDDED_DATA.map(d=>d.liga))].sort();
  const container=document.getElementById('filtro-liga-container');
  ligas.forEach(lg=>{{
    const lbl=document.createElement('label');
    const cb=document.createElement('input');
    cb.type='checkbox'; cb.className='filtro-liga'; cb.value=lg; cb.checked=true;
    cb.addEventListener('change', actualizarVistas);
    lbl.appendChild(cb); lbl.append(' '+lg);
    container.appendChild(lbl);
  }});
}}

function seleccionarTodasLigas(val) {{
  document.querySelectorAll('.filtro-liga').forEach(c=>c.checked=val);
  actualizarVistas();
}}

function initEquipos() {{
  const equipos=[...new Set(EMBEDDED_DATA.map(d=>d.equipo+' ('+d.temporada+')'))].sort();
  const container=document.getElementById('filtro-equipo-container');
  equipos.forEach(eq=>{{
    const lbl=document.createElement('label');
    const cb=document.createElement('input');
    cb.type='checkbox'; cb.className='filtro-equipo'; cb.value=eq; cb.checked=true;
    cb.addEventListener('change', actualizarVistas);
    lbl.appendChild(cb); lbl.append(' '+eq);
    container.appendChild(lbl);
  }});
}}

function seleccionarTodosEquipos(val) {{
  document.querySelectorAll('.filtro-equipo').forEach(c=>c.checked=val);
  actualizarVistas();
}}

function dibujarAnguloCanvas() {{
  const canvas = document.getElementById('angulo-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W/2, cy = H/2, R = W/2 - 14, rIn = R - 20;
  ctx.clearRect(0,0,W,H);

  const angMin = +document.getElementById('angulo-min-input').value;
  const angMax = +document.getElementById('angulo-max-input').value;

  ctx.fillStyle = '#1c2129';
  ctx.beginPath(); ctx.arc(cx,cy,R+12,0,2*Math.PI); ctx.fill();

  ctx.strokeStyle = '#2d3642'; ctx.lineWidth = 18;
  ctx.beginPath(); ctx.arc(cx,cy,R,0,2*Math.PI); ctx.stroke();

  function degToRad(d) {{ return -d * Math.PI / 180; }}

  ctx.strokeStyle = '#74e2b5'; ctx.lineWidth = 18;
  ctx.beginPath();
  ctx.arc(cx,cy,R, degToRad(angMin), degToRad(angMax), true);
  ctx.stroke();

  [['0° ►',0],['90° ▲',90],['180° ◄',180],['270° ▼',270]].forEach(([lbl,deg])=>{{
    const a = degToRad(deg);
    const x1 = cx + (R-10)*Math.cos(a), y1 = cy + (R-10)*Math.sin(a);
    const x2 = cx + (R+10)*Math.cos(a), y2 = cy + (R+10)*Math.sin(a);
    ctx.strokeStyle='#636d7f'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
    const tx = cx + (R+22)*Math.cos(a), ty = cy + (R+22)*Math.sin(a);
    ctx.fillStyle = (deg===0||deg===90) ? '#74e2b5' : '#8e99ab';
    ctx.font = (deg===0||deg===90) ? 'bold 9px DM Sans,sans-serif' : 'bold 8px DM Sans,sans-serif';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(lbl, tx, ty);
  }});

  const hS = degToRad(angMin);
  ctx.fillStyle='#60a5fa';
  ctx.beginPath(); ctx.arc(cx+R*Math.cos(hS), cy+R*Math.sin(hS), 8,0,2*Math.PI); ctx.fill();
  const hE = degToRad(angMax);
  ctx.fillStyle='#74e2b5';
  ctx.beginPath(); ctx.arc(cx+R*Math.cos(hE), cy+R*Math.sin(hE), 8,0,2*Math.PI); ctx.fill();

  ctx.fillStyle='#e6ebf1'; ctx.font='bold 11px DM Sans,sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
  const wrap = angMin > angMax ? ' ↻' : '';
  ctx.fillText(angMin+'°'+wrap, cx, cy-8);
  ctx.fillText('→ '+angMax+'°', cx, cy+8);
}}

(function() {{
  let dragging = null;
  function getCanvasAngle(canvas, e) {{
    const rect = canvas.getBoundingClientRect();
    const ex = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
    const ey = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
    const dx = ex - rect.width/2, dy = ey - rect.height/2;
    let deg = -Math.atan2(dy, dx) * 180 / Math.PI;
    return ((deg % 360) + 360) % 360;
  }}
  function setupCanvas() {{
    const canvas = document.getElementById('angulo-canvas');
    if (!canvas) return;
    function onDown(e) {{
      const ang = getCanvasAngle(canvas, e);
      const vMin = +document.getElementById('angulo-min-input').value;
      const vMax = +document.getElementById('angulo-max-input').value;
      const dMin = Math.abs(ang - vMin), dMax = Math.abs(ang - vMax);
      dragging = dMin <= dMax ? 'min' : 'max';
      e.preventDefault();
    }}
    function onMove(e) {{
      if (!dragging) return;
      const ang = Math.round(getCanvasAngle(canvas, e));
      if (dragging === 'min') document.getElementById('angulo-min-input').value = ang;
      else document.getElementById('angulo-max-input').value = ang;
      dibujarAnguloCanvas(); actualizarVistas();
      e.preventDefault();
    }}
    function onUp() {{ dragging = null; }}
    canvas.addEventListener('mousedown', onDown);
    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseup', onUp);
    canvas.addEventListener('touchstart', onDown, {{passive:false}});
    canvas.addEventListener('touchmove', onMove, {{passive:false}});
    canvas.addEventListener('touchend', onUp);
  }}
  document.addEventListener('DOMContentLoaded', setupCanvas);
  setTimeout(setupCanvas, 100);
}})();

document.addEventListener('DOMContentLoaded', function() {{
  const mi = document.getElementById('angulo-min-input');
  const ma = document.getElementById('angulo-max-input');
  if (mi) mi.addEventListener('input', () => {{ dibujarAnguloCanvas(); actualizarVistas(); }});
  if (ma) ma.addEventListener('input', () => {{ dibujarAnguloCanvas(); actualizarVistas(); }});
}});

function initSliders() {{
  const pairs=[
    ['slider-x-min','slider-x-max','x-min-val','x-max-val',''],
    ['slider-y-min','slider-y-max','y-min-val','y-max-val',''],
    ['slider-dist-min','slider-dist-max','dist-min-val','dist-max-val','m'],
    ['slider-prog-min','slider-prog-max','prog-min-val','prog-max-val','m'],
  ];
  pairs.forEach(([minId,maxId,minLbl,maxLbl,unit])=>{{
    const sMin=document.getElementById(minId);
    const sMax=document.getElementById(maxId);
    function upd(){{
      let v0=+sMin.value, v1=+sMax.value;
      if(v0>v1){{ if(this===sMin) sMin.value=v1; else sMax.value=v0; v0=+sMin.value; v1=+sMax.value; }}
      document.getElementById(minLbl).textContent=v0+unit;
      document.getElementById(maxLbl).textContent=v1+unit;
      actualizarVistas();
    }}
    sMin.addEventListener('input',upd); sMax.addEventListener('input',upd);
    upd.call(sMin);
  }});
  const sXgMin = document.getElementById('slider-xgseq-min');
  const sXgMax = document.getElementById('slider-xgseq-max');
  if (sXgMin && sXgMax) {{
    function updXg() {{
      let v0 = +sXgMin.value, v1 = +sXgMax.value;
      if (v0 > v1) {{ if (this === sXgMin) sXgMin.value = v1; else sXgMax.value = v0; v0 = +sXgMin.value; v1 = +sXgMax.value; }}
      document.getElementById('xgseq-min-val').textContent = v0.toFixed(2);
      document.getElementById('xgseq-max-val').textContent = v1.toFixed(2);
      actualizarVistas();
    }}
    sXgMin.addEventListener('input', updXg); sXgMax.addEventListener('input', updXg);
    updXg.call(sXgMin);
  }}
  const sDesmMin = document.getElementById('slider-desmrun-min');
  const sDesmMax = document.getElementById('slider-desmrun-max');
  if (sDesmMin && sDesmMax) {{
    function updDesm() {{
      let v0 = +sDesmMin.value, v1 = +sDesmMax.value;
      if (v0 > v1) {{ if (this === sDesmMin) sDesmMin.value = v1; else sDesmMax.value = v0; v0 = +sDesmMin.value; v1 = +sDesmMax.value; }}
      document.getElementById('desmrun-min-val').textContent = v0.toFixed(1);
      document.getElementById('desmrun-max-val').textContent = v1.toFixed(1);
      actualizarVistas();
    }}
    sDesmMin.addEventListener('input', updDesm); sDesmMax.addEventListener('input', updDesm);
    updDesm.call(sDesmMin);
  }}
  const sAccMax = document.getElementById('slider-acc-max');
  if (sAccMax) {{
    function updAcc() {{
      document.getElementById('acc-max-val').textContent = sAccMax.value;
      actualizarVistas();
    }}
    sAccMax.addEventListener('input', updAcc);
    updAcc.call(sAccMax);
  }}
  dibujarAnguloCanvas();
}}

document.getElementById('btn-resetear').addEventListener('click',()=>{{
  document.getElementById('slider-x-min').value=0;
  document.getElementById('slider-x-max').value=100;
  document.getElementById('slider-y-min').value=0;
  document.getElementById('slider-y-max').value=100;
  document.getElementById('slider-dist-min').value=0;
  document.getElementById('slider-dist-max').value=80;
  document.getElementById('slider-prog-min').value=-105;
  document.getElementById('slider-prog-max').value=105;
  document.getElementById('angulo-min-input').value=0;
  document.getElementById('angulo-max-input').value=360;
  dibujarAnguloCanvas();
  document.getElementById('slider-xgseq-min').value=0;
  document.getElementById('slider-xgseq-max').value=1.5;
  document.getElementById('xgseq-min-val').textContent='0.00';
  document.getElementById('xgseq-max-val').textContent='1.50';
  document.getElementById('slider-desmrun-min').value=0;
  document.getElementById('slider-desmrun-max').value=100;
  document.getElementById('desmrun-min-val').textContent='0.0';
  document.getElementById('desmrun-max-val').textContent='100.0';
  document.getElementById('slider-acc-max').value=30;
  document.getElementById('acc-max-val').textContent='30';
  document.querySelectorAll('.filtro-tipo').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-resultado').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-desmarque').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-retencion').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-aerial').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-eje').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-lbchip').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-liga').forEach(c=>c.checked=true);
  document.querySelectorAll('.filtro-equipo').forEach(c=>c.checked=true);
  document.getElementById('toggle-labels').checked=false;
  mostrarLabels=false;
  kmeansMode=false;
  kmeansData=null;
  spectralMode=false;
  spectralData=null;
  currentClusteringData=null;
  document.getElementById('btn-kmeans').classList.remove('active');
  document.getElementById('btn-spectral').classList.remove('active');
  document.getElementById('clustering-report-container').style.display='none';
  initSliders();
  actualizarVistas();
}});

// ──── CLUSTERING BUTTONS ────
document.getElementById('btn-kmeans').addEventListener('click',()=>{{
  if(kmeansMode){{
    kmeansMode=false;
    kmeansData=null;
    currentClusteringData=null;
    selectedClusterIdx=null;
    showCentroids=false;
    document.getElementById('btn-kmeans').classList.remove('active');
    document.getElementById('clustering-report-container').style.display='none';
    actualizarVistas();  // ← Redibujar saques normales
  }}else{{
    spectralMode=false;
    document.getElementById('btn-spectral').classList.remove('active');
    selectedClusterIdx=null;
    showCentroids=false;
    kmeansMode=true;
    document.getElementById('btn-kmeans').classList.add('active');
    actualizarVistas();
  }}
}});

document.getElementById('btn-spectral').addEventListener('click',()=>{{
  if(spectralMode){{
    spectralMode=false;
    spectralData=null;
    currentClusteringData=null;
    selectedClusterIdx=null;
    showCentroids=false;
    document.getElementById('btn-spectral').classList.remove('active');
    document.getElementById('clustering-report-container').style.display='none';
    actualizarVistas();  // ← Redibujar saques normales
  }}else{{
    kmeansMode=false;
    document.getElementById('btn-kmeans').classList.remove('active');
    selectedClusterIdx=null;
    showCentroids=false;
    spectralMode=true;
    document.getElementById('btn-spectral').classList.add('active');
    actualizarVistas();
  }}
}});

document.querySelectorAll('.filtro-tipo,.filtro-resultado,.filtro-desmarque,.filtro-retencion,.filtro-aerial,.filtro-eje,.filtro-lbchip').forEach(c=>c.addEventListener('change',actualizarVistas));
document.getElementById('scatter-axis-x').addEventListener('change',()=>actualizarScatter(obtenerDatosFiltrados()));
document.getElementById('scatter-axis-y').addEventListener('change',()=>actualizarScatter(obtenerDatosFiltrados()));
window.addEventListener('resize',()=>{{const df=obtenerDatosFiltrados();dibujarCampograma(df);}});

initLigas();
initEquipos();
initSliders();
actualizarVistas();
</script>
</body>
</html>"""

with open(OUTPUT_HTML, 'w', encoding='utf-8') as fh:
    fh.write(HTML_CONTENT)

size_mb = os.path.getsize(OUTPUT_HTML) / 1024 / 1024
print(f"\n✅ HTML generado: {OUTPUT_HTML}")
print(f"   Tamaño: {size_mb:.1f} MB")
print(f"\n✅ Pipeline completado:")
print(f"   1. {INPUT_CSV}")
print(f"   2. {INPUT_JSON}")
print(f"   3. {OUTPUT_HTML}")
