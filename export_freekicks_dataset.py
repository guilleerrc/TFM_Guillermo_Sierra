"""
Script consolidado para exportar dataset de freekicks con todas las métricas calculadas.

Uso:
    python export_freekicks_dataset.py

Input:
    - CSV preprocessed de cada liga en /Users/guillermosierradiaz-vargas/Desktop/RRC_analisis/Inputs/preprocessed_*.csv
    
Output:
    - CSV con un freekick por fila y todas las métricas calculadas
    - Guardado en: Outputs/freekicks_dataset.csv
"""

import pandas as pd
import numpy as np
import json
import os
import glob
from pathlib import Path


def extract_sequence_events(sequence_id, match_id, df):
    """
    Extrae todos los eventos de una secuencia específica de un partido.
    
    Args:
        sequence_id: ID de la secuencia a extraer
        match_id: ID del partido (para filtrar correctamente)
        df: DataFrame completo con todos los eventos
        
    Returns:
        Lista de diccionarios con información de cada evento de la secuencia
    """
    if pd.isna(sequence_id) or pd.isna(match_id):
        return []
    
    # IMPORTANTE: Filtrar por AMBOS matchId Y sequenceId
    # Los sequenceId se repiten entre partidos diferentes
    sequence_events = df[
        (df['matchId'] == match_id) & 
        (df['sequenceId'] == sequence_id)
    ].copy()
    
    if len(sequence_events) == 0:
        return []
    
    # Ordenar por eventId para mantener el orden temporal
    sequence_events = sequence_events.sort_values('eventId')
    
    # Extraer información relevante de cada evento
    events_list = []
    for _, event in sequence_events.iterrows():
        event_data = {
            'id': int(event['eventId']),
            'name': event.get('event_name', 'Unknown'),
            'player': event.get('jugador', 'Unknown'),
            'x': round(float(event['x']), 2) if pd.notna(event.get('x')) else None,
            'y': round(float(event['y']), 2) if pd.notna(event.get('y')) else None,
            'endX': round(float(event['endX']), 2) if pd.notna(event.get('endX')) else None,
            'endY': round(float(event['endY']), 2) if pd.notna(event.get('endY')) else None,
        }
        events_list.append(event_data)
    
    return events_list


def extract_cross_type(qualifiers_str):
    """Extrae el tipo de centro (Inswinger/Outswinger/Chipped) con jerarquía de prioridad"""
    if pd.isna(qualifiers_str):
        return None
    
    try:
        qualifiers = eval(qualifiers_str) if isinstance(qualifiers_str, str) else qualifiers_str
        
        has_inswinger = False
        has_outswinger = False
        has_chipped = False
        
        for q in qualifiers:
            q_value = q.get('type', {}).get('value')
            q_display = q.get('type', {}).get('displayName')
            
            if q_value == 223:
                has_inswinger = True
            elif q_value == 224:
                has_outswinger = True
            elif q_display == 'Chipped':
                has_chipped = True
        
        # Jerarquía: Inswinger > Outswinger > Chipped
        if has_inswinger:
            return 'Inswinger'
        elif has_outswinger:
            return 'Outswinger'
        elif has_chipped:
            return 'Chipped'
        
        return None
    except:
        return None


def extract_pass_target_player(pass_target_str, players_df):
    """
    Extrae el nombre del jugador desde passTarget.
    
    Args:
        pass_target_str: String JSON con información de passTarget
        players_df: DataFrame con información de jugadores (playerId -> jugador)
        
    Returns:
        str: Nombre del jugador o None
    """
    if pd.isna(pass_target_str):
        return None
    
    try:
        pass_target = json.loads(pass_target_str)
        
        if 'player' not in pass_target or len(pass_target['player']) == 0:
            return None
        
        # Tomar el primer jugador (normalmente solo hay uno)
        player_id = pass_target['player'][0].get('playerId')
        
        if player_id and players_df is not None:
            # Buscar en el dataframe de jugadores
            player_match = players_df[players_df['playerId'] == player_id]
            if not player_match.empty:
                return player_match.iloc[0]['jugador']
        
        return None
    except Exception as e:
        return None


def calculate_defensive_line_height(pass_option_str):
    """Calcula la media de los 3 valores más altos de positionX en passOption"""
    if pd.isna(pass_option_str):
        return None
    
    try:
        pass_option = json.loads(pass_option_str)
        
        if 'player' not in pass_option:
            return None
        
        positions = []
        for player in pass_option['player']:
            if 'positionX' in player:
                try:
                    positions.append(float(player['positionX']))
                except (ValueError, TypeError):
                    continue
        
        if len(positions) == 0:
            return None
        
        top_3 = sorted(positions, reverse=True)[:3]
        return round(sum(top_3) / len(top_3), 2)
    
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def calcular_desmarque(pass_target_str, end_x, end_y):
    """
    Calcula si hubo desmarque y retorna toda la información relevante.
    
    Returns:
        tuple: (tiene_desmarque, x_inicio, y_inicio, distancia_metros, angulo_grados)
    """
    if pd.isna(pass_target_str) or pd.isna(end_x) or pd.isna(end_y):
        return False, None, None, None, None
    
    try:
        pass_target = json.loads(pass_target_str)
        
        if 'player' not in pass_target or len(pass_target['player']) == 0:
            return False, None, None, None, None
        
        for player in pass_target['player']:
            pos_x = player.get('positionX')
            pos_y = player.get('positionY')
            
            if pos_x is not None and pos_y is not None:
                try:
                    x_inicio = float(pos_x)
                    y_inicio = float(pos_y)
                    x_fin = float(end_x)
                    y_fin = float(end_y)
                    
                    # Calcular diferencia en coordenadas Opta
                    dx = x_fin - x_inicio
                    dy = y_fin - y_inicio
                    
                    # Convertir a metros reales (Opta 100x100 -> Campo 105x68)
                    dx_metros = dx * 1.05
                    dy_metros = dy * 0.68
                    
                    # Distancia euclidiana
                    distancia = np.sqrt(dx_metros**2 + dy_metros**2)
                    
                    # Ángulo en grados (0° = horizontal derecha, 90° = vertical arriba)
                    angulo = np.degrees(np.arctan2(dy_metros, dx_metros))
                    
                    # Umbral de 4 metros para considerar desmarque
                    UMBRAL_DESMARQUE = 4.0
                    tiene_desmarque = distancia > UMBRAL_DESMARQUE
                    
                    return tiene_desmarque, x_inicio, y_inicio, round(distancia, 2), round(angulo, 2)
                except (ValueError, TypeError):
                    continue
        
        return False, None, None, None, None
    
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return False, None, None, None, None


def get_zone_from_coordinates(x, y):
    """
    Determina la zona basándose en las coordenadas x, y.
    
    Returns:
        str: Nombre de la zona (ej: 'zona 11') o None si no está en ninguna zona mapeada
    """
    if pd.isna(x) or pd.isna(y):
        return None
    
    # Mapeo de zonas (igual que en defensive_line_analysis.py)
    zone_mapping = {
        # Zonas 52-60 (zona 1-5)
        (52, 60, 0, 19): 'zona 1',
        (52, 60, 19, 37): 'zona 2',
        (52, 60, 37, 63): 'zona 3',
        (52, 60, 63, 81): 'zona 4',
        (52, 60, 81, 100): 'zona 5',
        # Zonas 60-68 (zona 6-10)
        (60, 68, 0, 19): 'zona 6',
        (60, 68, 19, 37): 'zona 7',
        (60, 68, 37, 63): 'zona 8',
        (60, 68, 63, 81): 'zona 9',
        (60, 68, 81, 100): 'zona 10',
        # Zonas 68-76 (zona 11-15)
        (68, 76, 0, 19): 'zona 11',
        (68, 76, 19, 37): 'zona 12',
        (68, 76, 37, 63): 'zona 13',
        (68, 76, 63, 81): 'zona 14',
        (68, 76, 81, 100): 'zona 15',
        # Zonas 76-84 (zona 16-19)
        (76, 84, 0, 19): 'zona 16',
        (76, 84, 19, 37): 'zona 17',
        (76, 84, 63, 81): 'zona 18',
        (76, 84, 81, 100): 'zona 19',
        # Zonas 84-92 (zona 20 y 23) - fusionando laterales
        (84, 92, 0, 19): 'zona 20',
        (84, 92, 19, 37): 'zona 20',
        (84, 92, 63, 81): 'zona 23',
        (84, 92, 81, 100): 'zona 23',
        # Zonas 92-100 (zona 24 y 27) - fusionando laterales
        (92, 100, 0, 19): 'zona 24',
        (92, 100, 19, 37): 'zona 24',
        (92, 100, 63, 81): 'zona 27',
        (92, 100, 81, 100): 'zona 27',
    }
    
    for (x_min, x_max, y_min, y_max), zona in zone_mapping.items():
        if x_min <= x < x_max and y_min <= y < y_max:
            return zona
    
    return None


def get_success_type(row, tiene_desmarque, tiene_remate):
    """
    Clasifica el tipo de éxito del freekick.
    
    Returns:
        str: Tipo de éxito
    """
    outcome = row.get('outcome_value')
    
    # Si no es successful, retornar directamente
    if outcome != 1:
        return 'no_exitoso'
    
    # Si tiene gol
    if row.get('primer_remate_gol', False):
        if tiene_desmarque:
            return 'gol_con_desmarque'
        else:
            return 'gol_estatico'
    
    # Si tiene remate
    if tiene_remate:
        if tiene_desmarque:
            return 'remate_con_desmarque'
        else:
            return 'remate_estatico'
    
    # Centro exitoso sin remate
    if tiene_desmarque:
        return 'centro_exitoso_con_desmarque'
    else:
        return 'centro_exitoso_estatico'


def calculate_30s_stats(fk_row, df_original):
    """
    Calcula estadísticas acumuladas en los 30 segundos siguientes al freekick.
    Filtra eventos por:
    - Mismo matchId
    - Mismo teamId (equipo sacador)
    - Mismo possessionId (si está disponible)
    - Dentro de la ventana de 30 segundos
    
    Returns:
        dict: Diccionario con todas las estadísticas acumuladas
    """
    fk_match_id = fk_row['matchId']
    fk_team_id = fk_row['teamId']
    fk_possession_id = fk_row.get('possessionId')
    fk_minute = fk_row['minute']
    fk_second = fk_row['second']
    
    # Calcular tiempo del freekick en segundos
    fk_time = fk_minute * 60 + fk_second
    
    # Filtrar eventos posteriores - base filter
    mask = (
        (df_original['matchId'] == fk_match_id) &
        (df_original['teamId'] == fk_team_id) &
        (df_original['minute'] * 60 + df_original['second'] > fk_time) &
        (df_original['minute'] * 60 + df_original['second'] <= fk_time + 30)
    )
    
    # Agregar filtro de possessionId solo si está disponible
    if pd.notna(fk_possession_id) and 'possessionId' in df_original.columns:
        mask = mask & (df_original['possessionId'] == fk_possession_id)
    
    eventos_posteriores = df_original[mask].copy()
    
    # Contar remates (eventos con xG/xGoT no nulos, isShot=True, o ShotOnPost)
    # IMPORTANTE: ShotOnPost siempre cuenta como remate aunque no tenga xG/xGoT
    remates = eventos_posteriores[
        (eventos_posteriores['xG'].notna()) | 
        (eventos_posteriores['xGoT'].notna()) |
        (eventos_posteriores['isShot'] == True) |
        (eventos_posteriores['event_name'] == 'ShotOnPost')
    ]
    
    num_remates = len(remates)
    xg_acumulado = eventos_posteriores['xG'].fillna(0).sum()
    xgot_acumulado = eventos_posteriores['xGoT'].fillna(0).sum()
    
    # Convertir isGoal a numérico para evitar errores con strings
    # Algunos CSVs tienen 'False'/'True' como strings, otros tienen 0/1
    goles_series = pd.to_numeric(eventos_posteriores['isGoal'], errors='coerce').fillna(0)
    goles = int(goles_series.sum())
    
    # Información del primer remate (si existe)
    primer_remate_info = {}
    if num_remates > 0:
        primer_remate = remates.iloc[0]
        # Convertir isGoal de forma segura (puede ser string 'False'/'1.0' o booleano)
        is_goal_val = primer_remate.get('isGoal', False)
        if isinstance(is_goal_val, str):
            # Si es string, convertir: '1.0' o 'True' -> True, resto -> False
            primer_remate_gol = is_goal_val in ['1.0', '1', 'True', 'true']
        else:
            primer_remate_gol = bool(is_goal_val)
        
        primer_remate_info = {
            'primer_remate_eventId': primer_remate.get('eventId'),
            'primer_remate_playerId': primer_remate.get('playerId'),
            'primer_remate_jugador': primer_remate.get('jugador'),
            'primer_remate_xG': round(primer_remate.get('xG', 0), 4) if pd.notna(primer_remate.get('xG')) else 0,
            'primer_remate_xGoT': round(primer_remate.get('xGoT', 0), 4) if pd.notna(primer_remate.get('xGoT')) else 0,
            'primer_remate_gol': primer_remate_gol,
            'primer_remate_x': round(primer_remate.get('x', 0), 2) if pd.notna(primer_remate.get('x')) else None,
            'primer_remate_y': round(primer_remate.get('y', 0), 2) if pd.notna(primer_remate.get('y')) else None,
        }
    else:
        primer_remate_info = {
            'primer_remate_eventId': None,
            'primer_remate_playerId': None,
            'primer_remate_jugador': None,
            'primer_remate_xG': 0,
            'primer_remate_xGoT': 0,
            'primer_remate_gol': False,
            'primer_remate_x': None,
            'primer_remate_y': None,
        }
    
    return {
        'num_remates_30s': num_remates,
        'xG_acumulado_30s': round(xg_acumulado, 4),
        'xGoT_acumulado_30s': round(xgot_acumulado, 4),
        'goles_30s': goles,  # Ya es int
        **primer_remate_info
    }


def classify_freekick_type(row):
    """
    Clasifica un freekick en Shot, Cross, ShortPass o LongPass.
    
    Args:
        row: Fila del DataFrame con el evento freekick
        
    Returns:
        str: 'Shot', 'Cross', 'ShortPass' o 'LongPass'
    """
    qualifiers_str = str(row.get('qualifiers', ''))
    
    # 1. Si tiene qualifier value=26 (Freekick) Y isShot=True -> Shot directo
    if "'value': 26" in qualifiers_str and row.get('isShot', False) == True:
        return 'Shot'
    
    # 2. Si tiene qualifier Cross -> es un Cross
    if "displayName': 'Cross" in qualifiers_str:
        return 'Cross'
    
    # 3. Si no es Shot ni Cross, clasificar por distancia del pase
    try:
        x_start = row['x']
        x_end = row.get('endX')
        
        if pd.notna(x_end):
            distance = abs(x_end - x_start)
            if distance < 15:
                return 'ShortPass'
            else:
                return 'LongPass'
        else:
            # Si no tiene endX, asumir ShortPass
            return 'ShortPass'
    except:
        return 'ShortPass'


def process_freekicks(df, league_name):
    """
    Procesa todos los freekicks de una liga y extrae todas las métricas.
    
    Args:
        df: DataFrame con los datos preprocessed de la liga
        league_name: Nombre de la liga
        
    Returns:
        DataFrame con un freekick por fila y todas las columnas calculadas
    """
    print(f"  Procesando {league_name}...")
    
    # Paso 1: Filtrar TODOS los freekicks
    # Debe tener: qualifier value=26 (Freekick) O qualifier FreekickTaken
    all_freekicks = df[
        (df['qualifiers'].astype(str).str.contains("'value': 26", na=False)) |
        (df['qualifiers'].astype(str).str.contains("FreekickTaken", na=False))
    ].copy()
    
    print(f"    - Total de freekicks encontrados: {len(all_freekicks)}")
    
    if len(all_freekicks) == 0:
        return pd.DataFrame()
    
    # Paso 2: Clasificar cada freekick por tipo
    all_freekicks['freekick_type'] = all_freekicks.apply(classify_freekick_type, axis=1)
    
    # Contar por tipo (antes de filtrar)
    type_counts = all_freekicks['freekick_type'].value_counts()
    print(f"    - Shots: {type_counts.get('Shot', 0)}")
    print(f"    - Crosses: {type_counts.get('Cross', 0)}")
    print(f"    - ShortPass: {type_counts.get('ShortPass', 0)}")
    print(f"    - LongPass: {type_counts.get('LongPass', 0)}")
    
    # Paso 2.1: Filtrar freekicks sin passOption (excepto Shots)
    # Los Shots no tienen passOption porque son remates directos, no pases
    # Los pases (Cross, ShortPass, LongPass) SÍ deben tener passOption
    freekicks_before_filter = len(all_freekicks)
    all_freekicks = all_freekicks[
        (all_freekicks['freekick_type'] == 'Shot') |  # Mantener todos los Shots
        (all_freekicks['passOption'].notna())           # Para pases, solo los que tienen passOption
    ].copy()
    
    freekicks_after_filter = len(all_freekicks)
    filtered_out = freekicks_before_filter - freekicks_after_filter
    print(f"    - Eliminados {filtered_out} freekicks sin passOption (faltas, no ejecuciones)")
    
    # Contar por tipo después de filtrar
    type_counts_after = all_freekicks['freekick_type'].value_counts()
    print(f"    - Freekicks válidos: {len(all_freekicks)}")
    print(f"      • Shots: {type_counts_after.get('Shot', 0)}")
    print(f"      • Crosses: {type_counts_after.get('Cross', 0)}")
    print(f"      • ShortPass: {type_counts_after.get('ShortPass', 0)}")
    print(f"      • LongPass: {type_counts_after.get('LongPass', 0)}")
    
    if len(all_freekicks) == 0:
        print(f"    ⚠️  No hay freekicks válidos después del filtro")
        return pd.DataFrame()
    
    # Paso 3: Procesar TODOS los freekicks con análisis detallado
    freekicks_list = []
    total_to_process = len(all_freekicks)
    
    print(f"    - Procesando análisis detallado para {total_to_process} freekicks...")
    
    for idx_count, (idx, fk) in enumerate(all_freekicks.iterrows(), 1):
        if idx_count % 100 == 0:
            print(f"      Progreso: {idx_count}/{total_to_process}")
        
        # Información descriptiva básica (para TODOS los freekicks)
        fk_data = {
            'league': league_name,
            'matchId': fk['matchId'],
            'eventId': fk['eventId'],
            'sequenceId': fk.get('sequenceId'),  # Añadido sequenceId
            'fecha': fk.get('fecha'),
            'teamId': fk['teamId'],
            'TeamName': fk.get('TeamName'),
            'TeamRival': fk.get('TeamRival'),
            'playerId': fk['playerId'],
            'jugador': fk.get('jugador'),
            'minute': fk['minute'],
            'second': fk['second'],
            'x': round(fk['x'], 2),
            'y': round(fk['y'], 2),
            'possessionId': fk.get('possessionId') if 'possessionId' in fk else None,
            'freekick_type': fk['freekick_type'],
        }
        
        # Zona de origen (para todos)
        fk_data['zona_origen'] = get_zone_from_coordinates(fk['x'], fk['y'])
        
        # ANÁLISIS DETALLADO PARA TODOS LOS FREEKICKS
        # Características del evento
        fk_data['cross_type'] = extract_cross_type(fk.get('qualifiers')) if fk['freekick_type'] == 'Cross' else None
        fk_data['outcome'] = 'Successful' if fk.get('outcome_value') == 1 else 'Unsuccessful'
        fk_data['endX'] = round(fk['endX'], 2) if pd.notna(fk.get('endX')) else None
        fk_data['endY'] = round(fk['endY'], 2) if pd.notna(fk.get('endY')) else None
        fk_data['defensive_line_height'] = calculate_defensive_line_height(fk.get('passOption'))
        
        # Delta: diferencia entre altura línea defensiva y coordenada X del freekick
        fk_data['delta'] = round(fk_data['defensive_line_height'] - fk_data['x'], 2) if fk_data['defensive_line_height'] is not None else None
        
        # Zona de llegada (para todos)
        fk_data['zona_llegada'] = get_zone_from_coordinates(fk.get('endX'), fk.get('endY'))
        
        # Información de desmarque (intentar para todos, devuelve None si no aplica)
        tiene_desmarque, desm_x, desm_y, desm_dist, desm_ang = calcular_desmarque(
            fk.get('passTarget'), fk.get('endX'), fk.get('endY')
        )
        
        fk_data['tiene_desmarque'] = tiene_desmarque
        fk_data['desmarque_x'] = desm_x
        fk_data['desmarque_y'] = desm_y
        fk_data['desmarque_distancia'] = desm_dist
        fk_data['desmarque_angulo'] = desm_ang
        
        # Extraer jugador receptor desde passTarget (para jugadas successful sin remate)
        fk_data['passTarget_jugador'] = extract_pass_target_player(fk.get('passTarget'), df)
        
        # Estadísticas acumuladas en 30s (para todos)
        stats_30s = calculate_30s_stats(fk, df)
        fk_data.update(stats_30s)
        
        # Clasificación de éxito (para todos)
        tiene_remate = stats_30s['num_remates_30s'] > 0
        fk_data['tipo_exito'] = get_success_type(fk, tiene_desmarque, tiene_remate)
        
        # Extraer todos los eventos de la secuencia
        sequence_id = fk.get('sequenceId')
        match_id = fk.get('matchId')
        sequence_events = extract_sequence_events(sequence_id, match_id, df)
        fk_data['sequence_events'] = json.dumps(sequence_events, ensure_ascii=False) if sequence_events else None
        
        freekicks_list.append(fk_data)
    
    print(f"    - Freekicks procesados: {len(freekicks_list)}")
    
    return pd.DataFrame(freekicks_list)


def main():
    """Función principal que procesa todas las ligas y genera el dataset final"""
    
    print("="*80)
    print("EXPORTACIÓN DE DATASET DE FREEKICKS")
    print("="*80)
    
    # Buscar todos los archivos preprocessed
    input_pattern = "/Users/guillermosierradiaz-vargas/Desktop/RRC_analisis/Inputs/preprocessed_*.csv"
    csv_files = glob.glob(input_pattern)
    
    if len(csv_files) == 0:
        print(f"\n⚠️  No se encontraron archivos CSV en: {input_pattern}")
        return
    
    print(f"\nArchivos encontrados: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")
    
    # Procesar cada liga
    all_freekicks = []
    
    for csv_file in csv_files:
        league_name = os.path.basename(csv_file).replace('preprocessed_', '').replace('.csv', '')
        
        try:
            # Leer CSV
            print(f"\nLeyendo {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file, low_memory=False)
            print(f"  - Eventos totales: {len(df):,}")
            
            # Procesar freekicks
            freekicks_df = process_freekicks(df, league_name)
            all_freekicks.append(freekicks_df)
            
        except Exception as e:
            print(f"  ✗ Error al procesar {league_name}: {str(e)}")
            continue
    
    # Consolidar todos los freekicks
    if len(all_freekicks) == 0:
        print("\n⚠️  No se procesaron freekicks en ninguna liga")
        return
    
    final_df = pd.concat(all_freekicks, ignore_index=True)
    
    print("\n" + "="*80)
    print("ESTADÍSTICAS FINALES")
    print("="*80)
    print(f"Total de freekicks: {len(final_df):,}")
    print(f"Ligas procesadas: {final_df['league'].nunique()}")
    print(f"\nDistribución por tipo de centro:")
    print(final_df['cross_type'].value_counts())
    print(f"\nDistribución por outcome:")
    print(final_df['outcome'].value_counts())
    print(f"\nDistribución por tipo de éxito:")
    print(final_df['tipo_exito'].value_counts())
    print(f"\nFreekicks con desmarque: {final_df['tiene_desmarque'].sum():,} ({final_df['tiene_desmarque'].sum()/len(final_df)*100:.2f}%)")
    print(f"\nEstadísticas de delta (defensive_line_height - x):")
    print(f"  - Con delta: {final_df['delta'].notna().sum():,} ({final_df['delta'].notna().sum()/len(final_df)*100:.1f}%)")
    print(f"  - Sin delta: {final_df['delta'].isna().sum():,} (Shots sin passOption)")
    print(f"  - Media: {final_df['delta'].mean():.2f} | Mediana: {final_df['delta'].median():.2f}")
    
    # Guardar CSV
    output_file = "Outputs/freekicks_dataset.csv"
    os.makedirs("Outputs", exist_ok=True)
    final_df.to_csv(output_file, index=False)
    
    print(f"\n✓ Dataset exportado exitosamente: {output_file}")
    print(f"  - Tamaño del archivo: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
    print(f"  - Columnas: {len(final_df.columns)}")
    print(f"  - Filas: {len(final_df):,}")
    
    print("\n" + "="*80)
    print("COLUMNAS DEL DATASET:")
    print("="*80)
    for i, col in enumerate(final_df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print("\n✓ Proceso completado exitosamente!")


if __name__ == '__main__':
    main()
