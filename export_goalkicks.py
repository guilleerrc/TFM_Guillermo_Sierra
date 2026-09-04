#!/usr/bin/env python3
"""
Exporta datos de GoalKicks desde CSVs a CSV y JSON sin comprimir.
Fuente de datos: todos los CSVs en Inputs/ (o solo los seleccionados con --ligas)

Uso:
  python3 export_goalkicks.py                         # todas las ligas
  python3 export_goalkicks.py --ligas SSD SSL SLL     # solo esas ligas
  python3 export_goalkicks.py --ligas SSD_25-26       # liga+temporada exacta

Salida:
  - goalkicks_dataset.csv (datos GoalKick sin comprimir)
  - goalkicks_sequences_final.json (secuencias sin comprimir)
"""
import csv, json, ast, math, re, os, glob, argparse, bisect

# ─── ARGS ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('--ligas', nargs='+', default=None,
    help='Códigos de liga a incluir (ej: SSD SSL FL2). Puede ser código de liga o código_temporada.')
args = parser.parse_args()

# ─── CONFIG ────────────────────────────────────────────────────────────────────
INPUTS_DIR  = os.path.expanduser("/Users/guillermosierradiaz-vargas/Desktop/RRC_analisis/Inputs")
OUTPUT_DIR  = os.path.expanduser("/Users/guillermosierradiaz-vargas/Desktop/RRC_analisis/Porteros")
OUTPUT_CSV  = os.path.join(OUTPUT_DIR, "goalkicks_dataset.csv")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "goalkicks_sequences_final.json")

# Validar que los directorios existan
if not os.path.isdir(INPUTS_DIR):
    print(f"❌ ERROR: INPUTS_DIR no existe: {INPUTS_DIR}")
    exit(1)
if not os.path.isdir(OUTPUT_DIR):
    print(f"❌ ERROR: OUTPUT_DIR no existe: {OUTPUT_DIR}")
    exit(1)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def has_qual_val(quals_str, val):
    try:
        quals = ast.literal_eval(quals_str)
        for q in quals:
            if q.get('type', {}).get('value') == val:
                return True
    except:
        pass
    return False

def has_longball_chipped(quals_str):
    # Longball-Chipped requires BOTH qualifiers in the same event.
    return has_qual_val(quals_str, 1) and has_qual_val(quals_str, 155)

def get_qual_float(quals_str, val):
    try:
        quals = ast.literal_eval(quals_str)
        for q in quals:
            if q.get('type', {}).get('value') == val and q.get('value') is not None:
                return float(q['value'])
    except:
        pass
    return None

def safe_float(v, default=None):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except:
        return default

def dist_m(x, y, ex, ey):
    try:
        dx = (float(ex) - float(x)) * 105 / 100
        dy = (float(ey) - float(y)) * 68 / 100
        return round(math.sqrt(dx*dx + dy*dy), 2)
    except:
        return None

def progression_m(x, ex):
    try:
        return round((float(ex) - float(x)) * 105 / 100, 2)
    except:
        return None

def angle_deg(x, y, ex, ey):
    """Compass: 0=toward Y=100 (left band), 90=forward (+X), 180=toward Y=0 (right band), 270=backward"""
    try:
        east_m  = (float(ex) - float(x)) * 105 / 100
        north_m = (float(ey) - float(y)) * 68  / 100
        deg = math.degrees(math.atan2(east_m, north_m))
        return round(((deg % 360) + 360) % 360, 1)
    except:
        return None

def get_pressure_level(pressure_str):
    try:
        p = json.loads(pressure_str)
        return p.get('pressureReceived', {}).get('value', None)
    except:
        return None

# ─── LOAD & PROCESS DATA (CSV por CSV para ahorrar memoria) ──────────────────
print("Exportando GoalKicks...")
print(f"  Buscando en: {INPUTS_DIR}")

# Usar listdir en lugar de glob para más robustez
try:
    all_files = os.listdir(INPUTS_DIR)
    csvs = sorted([os.path.join(INPUTS_DIR, f) for f in all_files if f.startswith('preprocessed_') and f.endswith('.csv')])
except Exception as e:
    print(f"  ❌ Error listando archivos: {e}")
    csvs = []
    
print(f"  CSVs encontrados: {len(csvs)}")
if csvs:
    print(f"    - {csvs[0]}")
    if len(csvs) > 1:
        print(f"    - ... (y {len(csvs)-1} más)")

# Filtrar por --ligas si se especificó
if args.ligas and csvs:
    filtros = [f.upper() for f in args.ligas]
    def csv_matches(path):
        fname = os.path.basename(path)
        m = re.match(r'preprocessed_([A-Z0-9_\-]+)_(.+)\.csv', fname)
        if not m: return False
        liga = m.group(1)
        slug = f"{liga}_{m.group(2)}"
        return any(liga == f or slug.upper() == f for f in filtros)
    csvs = [c for c in csvs if csv_matches(c)]
    print(f"  Ligas seleccionadas ({len(csvs)} CSVs)")
    for c in csvs[:3]:
        print(f"    - {os.path.basename(c)}")
    if len(csvs) > 3:
        print(f"    - ... ({len(csvs)-3} más)")
elif csvs:
    print(f"  Cargando TODAS las ligas ({len(csvs)} CSVs)")
    for c in csvs[:3]:
        print(f"    - {os.path.basename(c)}")
    if len(csvs) > 3:
        print(f"    - ... ({len(csvs)-3} más)")

embedded_data = []
embedded_sequences = {}

print("\n📊 Procesando CSVs liga por liga...\n")
for idx, csv_path in enumerate(csvs, 1):
    fname = os.path.basename(csv_path)
    m = re.match(r'preprocessed_([A-Z0-9_\-]+)_(.+)\.csv', fname)
    liga_code   = m.group(1) if m else fname
    season_code = m.group(2) if m else ''
    
    print(f"  [{idx}/{len(csvs)}] Procesando {fname}...", end='', flush=True)

    with open(csv_path, newline='', encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))

    # Pre-computar xG acumulado por secuencia (suma de xG de disparos en esa secuencia)
    seq_xg_map = {}
    seq_xa_map = {}  # Acumular xA de pases en la secuencia
    for _r in rows:
        try:
            _sid = int(float(_r.get('sequenceId', '') or 0))
            _mid = _r.get('matchId', '')
            if not _mid:
                continue
            _k = f"{_mid}|{_sid}"
            if _r.get('isShot', '0') == '1' or str(_r.get('isShot', '')).lower() == 'true':
                seq_xg_map[_k] = round(seq_xg_map.get(_k, 0) + (safe_float(_r.get('xG'), 0) or 0), 4)
            if _r.get('event_name', '') == 'Pass':
                seq_xa_map[_k] = round(seq_xa_map.get(_k, 0) + (safe_float(_r.get('xA'), 0) or 0), 4)
        except Exception:
            pass

    # Construir índice de eventos por partido para duelos aéreos
    match_events_aerial = {}
    for _r in rows:
        _mid = _r.get('matchId', '')
        _ts  = safe_float(_r.get('time_seconds'), 0) or 0
        _sid = safe_float(_r.get('sequenceId'))
        _ev  = _r.get('event_name', '')
        _team= _r.get('TeamName', '')
        _jug = _r.get('jugador', '')
        if _mid:
            match_events_aerial.setdefault(_mid, []).append((_ts, _sid, _ev, _team, _jug))
    for _mid in match_events_aerial:
        match_events_aerial[_mid].sort(key=lambda x: x[0])

    # Construir índice de eventos por partido+período para retención 7s
    match_period_events = {}
    for _r in rows:
        _mid = _r.get('matchId', '')
        _pid = _r.get('period_id', '')
        _ts  = safe_float(_r.get('time_seconds'), 0) or 0
        _team = _r.get('TeamName', '')
        if _mid and _team:
            match_period_events.setdefault(_mid, {}).setdefault(_pid, []).append((_ts, _team))
    for _mid in match_period_events:
        for _pid in match_period_events[_mid]:
            match_period_events[_mid][_pid].sort()

    # Index rápido: timestamps de passes Longball-Chipped y distance>=50 por secuencia.
    seq_lbchip_pass_ts = {}
    seq_longball_pass_ts = {}  # Pases con distance >= 50 (con o sin Chipped)
    for _r in rows:
      _mid = _r.get('matchId', '')
      _sid = safe_float(_r.get('sequenceId'))
      if not _mid or _sid is None:
        continue
      if _r.get('event_name', '') != 'Pass':
        continue
      _key = f"{_mid}|{int(_sid)}"
      _ts = safe_float(_r.get('time_seconds'), 0) or 0
      _quals = _r.get('qualifiers', '') or ''
      
      # Índice para Longball+Chipped (original)
      if has_longball_chipped(_quals):
        seq_lbchip_pass_ts.setdefault(_key, []).append(_ts)
      
      # Índice para pases con distance >= 50
      _dist = get_qual_float(_quals, 212) or dist_m(
        safe_float(_r.get('x')),
        safe_float(_r.get('y')),
        safe_float(_r.get('endX')),
        safe_float(_r.get('endY'))
      )
      if _dist is not None and _dist >= 50:
        seq_longball_pass_ts.setdefault(_key, []).append(_ts)
    
    for _k in seq_lbchip_pass_ts:
      seq_lbchip_pass_ts[_k].sort()
    for _k in seq_longball_pass_ts:
      seq_longball_pass_ts[_k].sort()

    # Métricas de secuencia por equipo del saque:
    # - cambio_eje_50: cruza de un lado al otro del eje y=50 (ambos sentidos)
    # - seq_acciones_total: pases + conducciones (>=4 coords) entre pases consecutivos
    seq_team_metrics = {}
    seq_axis_state = {}
    seq_passes = {}
    for _r in rows:
      _mid = _r.get('matchId', '')
      _sid = safe_float(_r.get('sequenceId'))
      _team = _r.get('TeamName', '')
      if not _mid or _sid is None or not _team:
        continue
      _key = f"{_mid}|{int(_sid)}|{_team}"

      _ts = safe_float(_r.get('time_seconds'), 0) or 0
      _y = safe_float(_r.get('y'))
      _st = seq_axis_state.get(_key)
      if _st is None:
        _st = {'start_ts': None, 'start_y': None, 'has_above': False, 'has_below': False}
        seq_axis_state[_key] = _st
      if _y is not None:
        if _st['start_ts'] is None or _ts < _st['start_ts']:
          _st['start_ts'] = _ts
          _st['start_y'] = _y
        if _y > 50:
          _st['has_above'] = True
        if _y < 50:
          _st['has_below'] = True

      if _r.get('event_name', '') == 'Pass':
        seq_passes.setdefault(_key, []).append((
          _ts,
          safe_float(_r.get('x')),
          safe_float(_r.get('y')),
          safe_float(_r.get('endX')),
          safe_float(_r.get('endY')),
        ))

    for _key in set(list(seq_axis_state.keys()) + list(seq_passes.keys())):
      _st = seq_axis_state.get(_key, {'start_y': None, 'has_above': False, 'has_below': False})
      _start_y = _st.get('start_y')
      _cambio_eje_50 = 0
      if _start_y is not None:
        if _start_y < 50 and _st.get('has_above'):
          _cambio_eje_50 = 1
        elif _start_y > 50 and _st.get('has_below'):
          _cambio_eje_50 = 1

      _p = seq_passes.get(_key, [])
      _p.sort(key=lambda t: t[0])
      _acciones = len(_p)
      for i in range(1, len(_p)):
        _prev = _p[i - 1]
        _curr = _p[i]
        _prev_ex, _prev_ey = _prev[3], _prev[4]
        _curr_x, _curr_y = _curr[1], _curr[2]
        if None in (_prev_ex, _prev_ey, _curr_x, _curr_y):
          continue
        _d = math.sqrt((_curr_x - _prev_ex) ** 2 + (_curr_y - _prev_ey) ** 2)
        if _d >= 4:
          _acciones += 1

      seq_team_metrics[_key] = {
        'cambio_eje_50': _cambio_eje_50,
        'seq_acciones_total': _acciones,
      }

    gk_actions = [r for r in rows if r.get('position', '') == 'GK'
                  and r.get('event_name', '') in ('Pass', 'Clearance')]

    # ── EMBEDDED_DATA ────────────────────────────────────────────────────────
    gk_match_seqs_float = set()
    gk_with_qualifier_124 = 0  # contador de acciones con qualifier 124
    for r in gk_actions:
        q     = r.get('qualifiers', '')
        
        # FILTRO: Solo GoalKicks (qualifier 124)
        if not has_qual_val(q, 124):
            continue
        
        gk_with_qualifier_124 += 1
        
        ename = r.get('event_name', '')
        x  = safe_float(r.get('x'))
        y  = safe_float(r.get('y'))
        ex = safe_float(r.get('endX'))
        ey = safe_float(r.get('endY'))
        
        tipo = 'GoalKick'

        dist    = get_qual_float(q, 212) or dist_m(x, y, ex, ey)
        ang_rad = get_qual_float(q, 213)
        ang     = round(math.degrees(ang_rad) % 360, 1) if ang_rad is not None else angle_deg(x, y, ex, ey)
        prog    = progression_m(x, ex)
        successful = (r.get('outcome_type', '').lower() == 'successful')

        reception_x = reception_y = None
        rec_player_id = None
        try:
            rec = json.loads(r.get('reception', '') or '{}')
            reception_x = safe_float(rec.get('receivingX'))
            reception_y = safe_float(rec.get('receivingY'))
            rec_player_id = rec.get('player', {}).get('playerId', '')
        except:
            pass

        pressure_level = get_pressure_level(r.get('pressure', ''))

        UMBRAL_DESMARQUE = 4.0
        has_desmarque = 0
        desmarque_run_dist = 0.0
        desmarque_x = None
        desmarque_y = None
        desmarque_angulo = None
        desmarque_distancia = None
        try:
            pt_raw = r.get('passTarget', '') or '{}'
            pt_players = json.loads(pt_raw).get('player', [])
            for pl in pt_players:
                px = safe_float(pl.get('positionX'))
                py = safe_float(pl.get('positionY'))
                if px is None or py is None or reception_x is None or reception_y is None:
                    continue
                dx_m = (reception_x - px) * 1.05
                dy_m = (reception_y - py) * 0.68
                d = math.sqrt(dx_m ** 2 + dy_m ** 2)
                if d > UMBRAL_DESMARQUE:
                    has_desmarque = 1
                if d > desmarque_run_dist:
                    desmarque_run_dist = d
                    # Guardar coordenadas y calcular ángulo
                    desmarque_x = round(px, 2)  # posición esperada X
                    desmarque_y = round(py, 2)  # posición esperada Y
                    desmarque_distancia = round(d, 2)  # distancia real
                    desmarque_angulo = round(math.degrees(math.atan2(reception_y - py, reception_x - px)), 1)
                break  # passTarget solo tiene 1 jugador
        except:
            pass
        desmarque_run_dist = round(desmarque_run_dist, 1)

        sid = safe_float(r.get('sequenceId'))
        mid = r.get('matchId', '')
        if mid and sid is not None:
            gk_match_seqs_float.add((mid, sid))
        seq_xg_val = round(seq_xg_map.get(f"{mid}|{int(sid)}", 0), 3) if sid is not None else 0.0
        seq_xa_val = round(seq_xa_map.get(f"{mid}|{int(sid)}", 0), 3) if sid is not None else 0.0

        # Detección duelo aéreo
        has_aerial_duel = 0
        aerial_duel_won = None
        aerial_player = ''
        try:
            t0_aerial = safe_float(r.get('time_seconds'), 0) or 0
            sid_int = int(sid) if sid is not None else None
            gk_team_aerial = r.get('TeamName', '')
            if mid and sid_int is not None and mid in match_events_aerial:
                candidates = [
                    ev for ev in match_events_aerial[mid]
                    if ev[0] > t0_aerial and
                       ev[1] is not None and (int(ev[1]) == sid_int or int(ev[1]) == sid_int + 1)
                ]
                candidates = candidates[:2]
                if candidates:
                    ev1 = candidates[0]
                    ev2 = candidates[1] if len(candidates) > 1 else None
                    ev1_name, ev1_team = ev1[2], ev1[3]
                    if ev1_name == 'Aerial':
                        has_aerial_duel = 1
                        aerial_duel_won = 1 if ev1_team == gk_team_aerial else 0
                        aerial_player = ev1[4]
                    elif ev1_name in ('Interception', 'Clearance') and ev1_team != gk_team_aerial:
                        has_aerial_duel = 1
                        aerial_duel_won = 0
                        aerial_player = ev1[4]
                    elif ev2 is not None:
                        ev2_name, ev2_team, ev2_jug = ev2[2], ev2[3], ev2[4]
                        if ev1_name == 'Pass' and ev2_name == 'Aerial' and ev2_jug == ev1[4]:
                            has_aerial_duel = 1
                            aerial_duel_won = 1 if ev2_team == gk_team_aerial else 0
                            aerial_player = ev2_jug
                        elif ev1_name != 'Pass' and ev2_name == 'Aerial':
                            has_aerial_duel = 1
                            aerial_duel_won = 1 if ev2_team == gk_team_aerial else 0
                            aerial_player = ev2_jug
                        elif ev1_name != 'Pass' and ev2_name in ('Interception', 'Clearance') and ev2_team != gk_team_aerial:
                            has_aerial_duel = 1
                            aerial_duel_won = 0
                            aerial_player = ev2_jug
        except:
            pass

        # Retención 7 segundos
        t0_s = safe_float(r.get('time_seconds'), 0) or 0
        gk_pid = r.get('period_id', '')
        gk_team = r.get('TeamName', '')
        retencion_7s = 1
        if mid in match_period_events and gk_pid in match_period_events[mid]:
            for _ts, _team in match_period_events[mid][gk_pid]:
                if _ts <= t0_s:
                    continue
                if _ts > t0_s + 7:
                    break
                if _team and _team != gk_team:
                    retencion_7s = 0
                    break

        # Métricas de secuencia y categoría Longball-Chipped
        seq_team_key = f"{mid}|{int(sid)}|{r.get('TeamName', '')}" if (mid and sid is not None and r.get('TeamName', '')) else None
        seq_metric = seq_team_metrics.get(seq_team_key, {'cambio_eje_50': 0, 'seq_acciones_total': 0}) if seq_team_key else {'cambio_eje_50': 0, 'seq_acciones_total': 0}

        # Longball-Chipped category (3 mutually exclusive states, priority order).
        # 1. gk_lb_chip: GoalKick con (Longball+Chipped) OR (distance >= 50)
        # 2. seq_lb_chip: Secuencia posterior con (Longball+Chipped) OR (distance >= 50)
        # 3. none: ninguno de los anteriores
        lb_chip_cat = 'none'
        t0_seq = safe_float(r.get('time_seconds'), 0) or 0
        _sid_here = safe_float(r.get('sequenceId'))
        _mid_here = r.get('matchId', '')
        
        # Verificar si el GoalKick cumple: (Longball+Chipped) OR (distance >= 50)
        is_gk_longball = has_longball_chipped(q) or (dist is not None and dist >= 50)
        if is_gk_longball:
          lb_chip_cat = 'gk_lb_chip'
        else:
          seq_key = f"{_mid_here}|{int(_sid_here)}" if (_mid_here and _sid_here is not None) else None
          if seq_key:
            # Buscar en secuencia posterior: (Longball+Chipped) OR (distance >= 50)
            has_seq_lb = False
            
            # Buscar en índice de Longball+Chipped
            _pass_ts = seq_lbchip_pass_ts.get(seq_key)
            if _pass_ts:
              _idx = bisect.bisect_right(_pass_ts, t0_seq)
              if _idx < len(_pass_ts):
                has_seq_lb = True
            
            # Buscar en índice de distance >= 50
            if not has_seq_lb:
              _pass_ts_dist = seq_longball_pass_ts.get(seq_key)
              if _pass_ts_dist:
                _idx = bisect.bisect_right(_pass_ts_dist, t0_seq)
                if _idx < len(_pass_ts_dist):
                  has_seq_lb = True
            
            if has_seq_lb:
              lb_chip_cat = 'seq_lb_chip'

        embedded_data.append([
            mid,
            liga_code,
            sid,
            safe_float(r.get('period_id')),
            safe_float(r.get('minute'), 0),
            safe_float(r.get('second'), 0),
            r.get('jugador', ''),
            r.get('playerId', ''),
            r.get('TeamName', ''),
            r.get('Temporada', ''),
            r.get('TeamRival', ''),
            r.get('fecha', ''),
            r.get('Competencia', ''),
            round(x, 2) if x is not None else None,
            round(y, 2) if y is not None else None,
            round(ex, 2) if ex is not None else None,
            round(ey, 2) if ey is not None else None,
            tipo,
            1 if successful else 0,
            round(dist, 1) if dist is not None else None,
            round(prog, 1) if prog is not None else None,
            ang,
            0.0,  # seq_xa: xA acumulado de la secuencia (TODO: calcular luego)
            round(safe_float(r.get('xT'), 0) or 0, 4),
            round(safe_float(r.get('xG'), 0) or 0, 4),
            round(safe_float(r.get('xGoT'), 0) or 0, 4),
            int(safe_float(r.get('linesBroken'), 0) or 0),
            int(safe_float(r.get('lastLineBroken'), 0) or 0),
            pressure_level,
            has_desmarque,
            seq_xg_val,
            retencion_7s,
            desmarque_run_dist,
            desmarque_x,
            desmarque_y,
            desmarque_angulo,
            desmarque_distancia,
            has_aerial_duel,
            aerial_duel_won,
            aerial_player,
            int(seq_metric.get('cambio_eje_50', 0) or 0),
            int(seq_metric.get('seq_acciones_total', 0) or 0),
            lb_chip_cat,
        ])

    # ── EMBEDDED_SEQUENCES ───────────────────────────────────────────────────
    seq_events_raw = {}
    for r in rows:
        mid = r.get('matchId', '')
        try:
            sid = float(r.get('sequenceId', ''))
        except:
            continue
        if (mid, sid) in gk_match_seqs_float:
            key = f"{mid}|{int(sid)}"
            seq_events_raw.setdefault(key, []).append(r)

    for key, evs in seq_events_raw.items():
        evs_sorted = sorted(evs, key=lambda r: safe_float(r.get('time_seconds', 0), 0))
        team_names = []
        for ev in evs_sorted:
            tn = ev.get('TeamName', '')
            if tn and tn not in team_names:
                team_names.append(tn)
        team_idx = {t: i for i, t in enumerate(team_names)}
        seq = []
        for ev in evs_sorted:
            desmk = []
            is_gk_ev = (ev.get('position', '') == 'GK' and ev.get('event_name', '') in ('Pass', 'Clearance'))
            if is_gk_ev:
                try:
                    rec2 = json.loads(ev.get('reception', '') or '{}')
                    rx2 = safe_float(rec2.get('receivingX'))
                    ry2 = safe_float(rec2.get('receivingY'))
                    pt2 = json.loads(ev.get('passTarget', '') or '{}').get('player', [])
                    for pl in pt2:
                        px2 = safe_float(pl.get('positionX'))
                        py2 = safe_float(pl.get('positionY'))
                        if px2 is None or py2 is None or rx2 is None or ry2 is None:
                            break
                        dx_m2 = (rx2 - px2) * 1.05
                        dy_m2 = (ry2 - py2) * 0.68
                        if math.sqrt(dx_m2 ** 2 + dy_m2 ** 2) > 4.0:
                            desmk.append([px2, py2, rx2, ry2])
                        break
                except:
                    pass
            outcome_str = ev.get('outcome_type', '').lower()
            outcome_int = 1 if 'successful' in outcome_str else (0 if outcome_str else None)
            press = get_pressure_level(ev.get('pressure', ''))
            press_int = {'low': 1, 'medium': 2, 'high': 3}.get(press, 0) if press else 0
            seq.append([
                ev.get('event_name', ''),
                round(safe_float(ev.get('x')) or 0, 2),
                round(safe_float(ev.get('y')) or 0, 2),
                round(safe_float(ev.get('endX')) or 0, 2) if safe_float(ev.get('endX')) is not None else None,
                round(safe_float(ev.get('endY')) or 0, 2) if safe_float(ev.get('endY')) is not None else None,
                int(safe_float(ev.get('minute'), 0) or 0),
                int(safe_float(ev.get('second'), 0) or 0),
                team_idx.get(ev.get('TeamName', ''), 0),
                1 if (ev.get('isShot','0')=='1' or str(ev.get('isShot','')).lower()=='true') else 0,
                1 if (ev.get('isGoal','0')=='1' or str(ev.get('isGoal','')).lower()=='true') else 0,
                outcome_int,
                press_int,
                desmk if desmk else None,
                1 if (ev.get('position','')=='GK' and ev.get('event_name','') in ('Pass','Clearance')) else 0,
            ])
        embedded_sequences[key] = [team_names] + seq

    print(f"  {fname}: {gk_with_qualifier_124} GoalKicks, {len(seq_events_raw)} secuencias")
    del rows, gk_actions, seq_events_raw, gk_with_qualifier_124

print(f"  Total GoalKicks exportados: {len(embedded_data)} acciones")
print(f"  Total secuencias: {len(embedded_sequences)}")

# ─── EXPORT TO CSV ─────────────────────────────────────────────────────────────
print("\nExportando a CSV...")
CSV_HEADERS = ['matchId','liga','sequenceId','periodId','minute','second',
    'jugador','playerId','equipo','temporada','rival','fecha','competencia',
    'x','y','endX','endY','tipo','exitoso','distancia','progresion','angulo',
    'seq_xa','xT','xG','xGoT','linesBroken','lastLineBroken',
    'pressure','has_desmarque','seq_xg','retencion_7s','desmarque_run_dist',
    'desmarque_x','desmarque_y','desmarque_angulo','desmarque_distancia',
    'has_aerial_duel','aerial_duel_won','aerial_player','cambio_eje_50','seq_acciones_total','lb_chip_cat']

with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.writer(fh)
    writer.writerow(CSV_HEADERS)
    for row in embedded_data:
        writer.writerow(row)

csv_size_kb = os.path.getsize(OUTPUT_CSV) / 1024
print(f"✅ CSV exportado: {OUTPUT_CSV}")
print(f"   Tamaño: {csv_size_kb:.1f} KB ({len(embedded_data)} filas)")

# ─── EXPORT TO JSON ───────────────────────────────────────────────────────────
print("Exportando a JSON...")
SEQ_SCHEMA = ['event','x','y','endX','endY','minute','second',
    'team','isShot','isGoal','outcome','pressure','desmarques','is_gk_pass']

seq_json_data = {'_s': SEQ_SCHEMA, **{k: v for k, v in embedded_sequences.items()}}
seq_json_str = json.dumps(seq_json_data, ensure_ascii=False, separators=(',', ':'))

with open(OUTPUT_JSON, 'w', encoding='utf-8') as fh:
    fh.write(seq_json_str)

json_size_kb = os.path.getsize(OUTPUT_JSON) / 1024
print(f"✅ JSON exportado: {OUTPUT_JSON}")
print(f"   Tamaño: {json_size_kb:.1f} KB ({len(embedded_sequences)} secuencias)")

print("\n✅ Exportación completada")
print(f"   Listos para usar con: python3 generate_porteros_final.py")
