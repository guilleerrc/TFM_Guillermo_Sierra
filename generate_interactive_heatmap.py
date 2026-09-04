"""
Genera un HTML interactivo standalone para visualizar freekicks con mapas de calor
"""
import pandas as pd
import json
import os
import re
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import io
import base64
import numpy as np


class NaNEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts NaN to null"""
    def encode(self, o):
        if isinstance(o, float):
            if np.isnan(o):
                return 'null'
        return super().encode(o)
    
    def iterencode(self, o, _one_shot=False):
        """Iterate encoding, converting NaN to null"""
        for chunk in super().iterencode(o, _one_shot):
            # Replace NaN with null in the JSON output
            yield chunk.replace(':NaN', ':null').replace(',NaN', ',null').replace('[NaN', '[null')

def generate_interactive_html():
    """
    Lee freekicks_dataset.csv y genera un HTML interactivo standalone
    """
    
    print("="*80)
    print("GENERANDO HTML INTERACTIVO DE FREEKICKS")
    print("="*80)
    
    # 1. Leer el CSV
    print("\n1. Leyendo freekicks_dataset.csv...")
    df = pd.read_csv('Outputs/freekicks_dataset.csv')
    print(f"   ✓ {len(df):,} freekicks cargados")
    
    # 2. Filtrar solo los que necesitamos para visualización (los que tienen coordenadas válidas)
    df_viz = df[
        df['x'].notna() & 
        df['y'].notna()
    ].copy()
    
    print(f"   ✓ {len(df_viz):,} freekicks con coordenadas válidas")
    
    # 3. Seleccionar columnas necesarias y preparar datos
    columns_needed = [
        'league', 'eventId', 'matchId', 'TeamName', 'TeamRival', 'jugador', 'fecha',
        'minute', 'second', 'freekick_type', 'x', 'y',
        'endX', 'endY', 'cross_type', 'outcome', 'defensive_line_height', 'delta',
        'tiene_desmarque', 'desmarque_x', 'desmarque_y', 'desmarque_angulo', 'desmarque_distancia',
        'num_remates_30s', 'xG_acumulado_30s', 'xGoT_acumulado_30s', 'goles_30s',
        'primer_remate_x', 'primer_remate_y', 'primer_remate_gol', 'primer_remate_jugador',
        'passTarget_jugador'
    ]
    
    # Asegurar que existan los campos
    for col in columns_needed:
        if col not in df_viz.columns:
            df_viz[col] = None
    
    df_viz = df_viz[columns_needed].copy()
    
    # Usar TODOS los freekicks
    print(f"\n📊 Usando TODOS los {len(df_viz):,} freekicks")
    
    # Convertir a registros para JSON
    print("\n2. Convirtiendo datos a JSON...")
    # Reemplazar NaN con None para JSON válido (CRÍTICO: NaN en JSON se convierte a NaN en JS, no null)
    df_viz = df_viz.where(pd.notna(df_viz), None)
    
    # Conversión explícita adicional: forzar None en columnas float con NaN
    for col in df_viz.columns:
        if df_viz[col].dtype in ['float64', 'float32']:
            df_viz[col] = df_viz[col].apply(lambda x: None if pd.isna(x) else x)
    
    # Limpiar strings problemáticos para JavaScript (solo para valores no-None)
    for col in df_viz.select_dtypes(include=['object']).columns:
        # Aplicar transformaciones solo a valores no nulos
        mask = df_viz[col].notna()
        if mask.any():
            df_viz.loc[mask, col] = df_viz.loc[mask, col].astype(str).str.replace('\\', '\\\\', regex=False)
            df_viz.loc[mask, col] = df_viz.loc[mask, col].str.replace('"', '\\"', regex=False)
    
    data_json = df_viz.to_dict(orient='records')
    
    print(f"   ✓ {len(data_json):,} registros preparados")
    
    # 4. Obtener rangos para los sliders
    x_min, x_max = df_viz['x'].min(), df_viz['x'].max()
    y_min, y_max = df_viz['y'].min(), df_viz['y'].max()
    dl_min = df_viz['defensive_line_height'].dropna().min()
    dl_max = df_viz['defensive_line_height'].dropna().max()
    
    # 5. Obtener opciones únicas para filtros
    leagues = sorted(df_viz['league'].dropna().unique().tolist())
    fk_types = sorted(df_viz['freekick_type'].dropna().unique().tolist())
    cross_types = sorted(df_viz['cross_type'].dropna().unique().tolist())
    
    print(f"\n✓ Opciones de filtros detectadas:")
    print(f"   FK Types: {fk_types}")
    print(f"   Cross Types: {cross_types}")
    print(f"   Leagues: {len(leagues)}")
    
    # Mapeo de códigos de liga a nombres legibles
    league_names = {
        'AB_24-25': 'Liga Austriaca 24-25',
        'AB_25-26': 'Liga Austriaca 25-26',
        'BJPL_24-25': 'Liga Belga 24-25',
        'BJPL_25-26': 'Liga Belga 25-26',
        'BCPL_24-25': 'Segunda Belga 24-25',
        'BSL_24-25': 'Liga Suiza 24-25',
        'BSL_25-26': 'Liga Suiza 25-26',
        'CPH_24-25': 'Liga Croata 24-25',
        'CPH_25-26': 'Liga Croata 25-26',
        'DE_24-25': 'Liga Holandesa 24-25',
        'DE_25-26': 'Liga Holandesa 25-26',
        'DS_24-25': 'Liga Danesa 24-25',
        'DS_25-26': 'Liga Danesa 25-26',
        'EFL-C_24-25': 'Segunda Inglesa 24-25',
        'EFL-C_25-26': 'Segunda Inglesa 25-26',
        'EPL_24-25': 'Liga Inglesa 24-25',
        'EPL_25-26': 'Liga Inglesa 25-26',
        'FL1_24-25': 'Liga Francesa 24-25',
        'FL1_25-26': 'Liga Francesa25-26',
        'FL2_24-25': 'Segunda Francesa 24-25',
        'FL2_25-26': 'Segunda Francesa 25-26',
        'GB_24-25': 'Liga Alemana 24-25',
        'GB_25-26': 'Liga Alemana 25-26',
        'ISA_24-25': 'Liga Italiana 24-25',
        'ISA_25-26': 'Liga Italiana 25-26',
        'ISB_24-25': 'Serie B Italiana 24-25',
        'ISB_25-26': 'Serie B Italiana 25-26',
        'NE_24': 'Liga Noruega 24-25',
        'NE_25': 'Liga Noruega 25-26',
        'PE_24-25': 'Liga Polaca 24-25',
        'PE_25-26': 'Liga Polaca 25-26',
        'PPL_24-25': 'Liga Portuguesa 24-25',
        'PPL_25-26': 'Liga Portugesa 25-26',
        'SA_24': 'Liga Sueca 24-25',
        'SA_25': 'Liga Sueca 25-26',
        'SLL_24-25': 'La Liga 24-25',
        'SLL_25-26': 'La Liga 25-26',
        'SSD_24-25': 'Segunda División 24-25',
        'SSD_25-26': 'Segunda División 25-26',
        'SSL_24-25': 'Liga Serbia 24-25',
        'SSL_25-26': 'Liga Serbia 25-26'
    }
    
    # Crear mapeo de liga a equipos
    teams_by_league = {}
    for league in leagues:
        league_teams = sorted(df_viz[df_viz['league'] == league]['TeamName'].dropna().unique().tolist())
        teams_by_league[league] = league_teams
    
    print(f"\n3. Rangos detectados:")
    print(f"   X: {x_min:.1f} - {x_max:.1f}")
    print(f"   Y: {y_min:.1f} - {y_max:.1f}")
    print(f"   Defensive Line: {dl_min:.1f} - {dl_max:.1f}")
    print(f"   Ligas: {len(leagues)}")
    print(f"   Tipos FK: {len(fk_types)}")
    print(f"   Tipos Cross: {len(cross_types)}")
    
    # 6. Generar campo de fútbol SVG usando mplsoccer
    print("\n4. Generando campo de fútbol con mplsoccer...")
    pitch = Pitch(pitch_type='opta', axis=False, label=False, 
                  line_color='#333', linewidth=2, line_zorder=2)
    fig, ax = pitch.draw(figsize=(12, 8))
    
    # Convertir a SVG string
    svg_io = io.StringIO()
    fig.savefig(svg_io, format='svg', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    svg_string = svg_io.getvalue()
    # Extraer solo el contenido del SVG (sin <?xml...?>)
    svg_start = svg_string.find('<svg')
    if svg_start != -1:
        pitch_svg = svg_string[svg_start:]
    else:
        pitch_svg = svg_string
    
    print("   ✓ Campo SVG generado")
    
    # 7. Generar HTML
    print("\n5. Generando HTML...")
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis Interactivo de Freekicks</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: #f0f0f0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 20px;
        }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 250px 1fr 80px 300px;
            gap: 20px;
            margin-bottom: 20px;
            position: relative;
        }}
        
        .filters-panel {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #ddd;
            height: fit-content;
            position: sticky;
            top: 20px;
        }}
        
        .filters-panel h3 {{
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 8px;
        }}
        
        .filter-group {{
            margin-bottom: 20px;
        }}
        
        .filter-group label {{
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
            color: #555;
        }}
        
        .filter-group select {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .filter-group select[multiple] {{
            height: 120px;
        }}
        
        .checkbox-group {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .checkbox-group label {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-weight: normal;
            cursor: pointer;
        }}
        
        .checkbox-group input[type="checkbox"] {{
            cursor: pointer;
        }}
        
        .pitch-container {{
            background: #fff;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 20px;
            position: relative;
        }}
        
        .pitch-wrapper {{
            position: relative;
            min-height: 500px;
        }}
        
        #pitch {{
            width: 100%;
            position: relative;
            display: block;
        }}
        
        #pitch svg {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        canvas {{
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
        }}
        
        #markersCanvas {{
            pointer-events: auto;
            cursor: pointer;
        }}
        
        #zoneCanvas {{
            z-index: 5;
        }}
        
        #heatmapCanvas {{
            opacity: 0.7;
            z-index: 10;
        }}
        
        #markersCanvas {{
            z-index: 20;
        }}
        
        .slider-y-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            padding-top: 80px;
            align-self: start;
        }}
        
        .slider-y-wrapper {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            height: 100%;
            justify-content: center;
            align-items: center;
        }}
        
        .slider-y-container input[type="range"] {{
            width: calc(100% - 20px);
            writing-mode: bt-lr;
            -webkit-appearance: slider-vertical;
            appearance: slider-vertical;
            height: 38%;
        }}
        
        .slider-y-container input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }}
        
        .slider-y-container input[type="range"]::-moz-range-thumb {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
            border: none;
        }}
        
        .slider-container {{
            margin: 15px 0;
        }}
        
        .slider-label {{
            font-weight: bold;
            margin-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }}
        
        .slider-wrapper {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        .slider-wrapper input[type="range"] {{
            flex: 1;
            height: 6px;
            border-radius: 3px;
            outline: none;
            background: #ddd;
        }}
        
        .slider-wrapper input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }}
        
        .slider-wrapper input[type="range"]::-moz-range-thumb {{
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
            border: none;
        }}
        
        .slider-wrapper span {{
            min-width: 50px;
            text-align: right;
            font-family: monospace;
            font-size: 12px;
        }}
        
        .stats-panel {{
            background: #fffbea;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #f39c12;
            height: fit-content;
            position: sticky;
            top: 20px;
        }}
        
        .stats-panel h3 {{
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #f39c12;
            padding-bottom: 8px;
        }}
        
        .stat-item {{
            margin-bottom: 12px;
            padding: 8px;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 2px;
        }}
        
        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            font-family: monospace;
        }}
        
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        
        .legend h4 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        
        .legend-symbol {{
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .btn-reset {{
            width: 100%;
            padding: 12px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
        }}
        
        .btn-reset:hover {{
            background: #c0392b;
        }}
        
        .btn-toggle-dl {{
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 6px rgba(52, 152, 219, 0.3);
        }}
        
        .btn-toggle-dl:hover {{
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(52, 152, 219, 0.5);
        }}
        
        .btn-toggle-dl.hidden {{
            background: #95a5a6;
            box-shadow: 0 2px 6px rgba(149, 165, 166, 0.3);
        }}
        
        .btn-toggle-dl.hidden:hover {{
            background: #7f8c8d;
            box-shadow: 0 4px 12px rgba(149, 165, 166, 0.5);
        }}
        
        .scatter-container {{
            background: #fff;
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 20px;
            margin: 40px auto 20px auto;
            max-width: 700px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            position: relative;
        }}
        
        .scatter-container h4 {{
            margin: 0 0 15px 0;
            font-size: 16px;
            color: #2c3e50;
            text-align: center;
            font-weight: 600;
        }}
        
        #scatterCanvas {{
            display: block;
            margin: 40px auto 0 auto;
            border: 1px solid #ddd;
        }}
        
        .play-report {{
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            display: none;
        }}
        
        .play-report.active {{
            display: block;
        }}
        
        .play-report h4 {{
            margin: 0 0 12px 0;
            color: #333;
            border-bottom: 2px solid #ffc107;
            padding-bottom: 6px;
            font-size: 14px;
        }}
        
        .play-report-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #f0e5a6;
            font-size: 12px;
        }}
        
        .play-report-item:last-child {{
            border-bottom: none;
        }}
        
        .play-report-label {{
            font-weight: bold;
            color: #666;
        }}
        
        .play-report-value {{
            color: #333;
            font-family: monospace;
        }}
        
        .top-performers-container {{
            background: #fff;
            border: 2px solid #27ae60;
            border-radius: 8px;
            padding: 20px;
            margin: 40px auto 20px auto;
            max-width: 900px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .top-performers-container h4 {{
            margin: 0 0 20px 0;
            font-size: 16px;
            color: #2c3e50;
            text-align: center;
            font-weight: 600;
        }}
        
        .top-performers-filters {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            justify-content: center;
            align-items: center;
        }}
        
        .top-performers-filters label {{
            display: flex;
            flex-direction: column;
            gap: 5px;
            font-size: 13px;
            font-weight: 600;
            color: #555;
        }}
        
        .top-performers-filters select {{
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
            background: white;
            cursor: pointer;
            min-width: 180px;
        }}
        
        .top-performers-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .top-performers-table th {{
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
        }}
        
        .top-performers-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
            font-size: 12px;
        }}
        
        .top-performers-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .top-performers-table .rank-cell {{
            font-weight: bold;
            color: #27ae60;
            text-align: center;
            width: 50px;
        }}
        
        .top-performers-table .player-cell {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .top-performers-table .team-cell {{
            color: #666;
            font-size: 11px;
        }}
        
        .top-performers-table .metric-cell {{
            text-align: right;
            font-weight: bold;
            color: #e74c3c;
            width: 120px;
        }}
        
        .top-performers-table .count-cell {{
            text-align: center;
            color: #3498db;
            font-size: 11px;
            width: 80px;
        }}
        
        /* Tabla de Clusters */
        #clusterTableContainer {{
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: none;
        }}
        
        #clusterTableContainer h3 {{
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 16px;
            text-align: center;
        }}
        
        .cluster-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}
        
        .cluster-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 8px;
            text-align: center;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #ddd;
        }}
        
        .cluster-table td {{
            padding: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
        }}
        
        .cluster-table tbody tr {{
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .cluster-table tbody tr:hover {{
            background: #f0f4ff;
            transform: scale(1.02);
        }}
        
        .cluster-table tbody tr.selected {{
            background: #d4edda;
            border: 2px solid #28a745;
        }}
        
        .cluster-color-cell {{
            width: 30px;
            padding: 4px !important;
        }}
        
        .cluster-color-box {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
            border: 2px solid #333;
            display: inline-block;
        }}
        
        .cluster-id-cell {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .cluster-metric-cell {{
            font-weight: bold;
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Análisis Interactivo de Freekicks - Campo 1</h1>
        
        <!-- Panel de Debug Visible -->
        <div id="debugPanel" style="background: #fffbea; border: 2px solid #f39c12; padding: 10px; margin-bottom: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 150px; overflow-y: auto;">
            <strong>🔍 Debug:</strong>
            <div id="debugMessages"></div>
        </div>
        
        <div class="main-content">
            <!-- Panel de Filtros (Izquierda) -->
            <div class="filters-panel">
                <h3>🔍 Filtros</h3>
                
                <div class="filter-group">
                    <label>Temporada:</label>
                    <select id="filterSeason" multiple>
                        <option value="24-25" selected>24-25</option>
                        <option value="25-26" selected>25-26</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Ligas:</label>
                    <select id="filterLeague" multiple>
                        {''.join(f'<option value="{league}" selected>{league_names.get(league, league)}</option>' for league in leagues)}
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Equipos:</label>
                    <select id="filterTeam" multiple>
                        <!-- Se llenará dinámicamente según las ligas seleccionadas -->
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Tipo de Freekick:</label>
                    <select id="filterFKType" multiple>
                        {''.join(f'<option value="{fk_type}" selected>{fk_type}</option>' for fk_type in fk_types)}
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Tipo de Cross:</label>
                    <select id="filterCrossType" multiple>
                        <option value="null" selected>Sin tipo (N/A)</option>
                        {''.join(f'<option value="{ct}" selected>{ct}</option>' for ct in cross_types)}
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Outcome:</label>
                    <div class="checkbox-group">
                        <label>
                            <input type="checkbox" id="outcomeSuccessful" checked>
                            Successful
                        </label>
                        <label>
                            <input type="checkbox" id="outcomeUnsuccessful" checked>
                            Unsuccessful
                        </label>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label>Desmarque:</label>
                    <div class="checkbox-group">
                        <label>
                            <input type="checkbox" id="desmarqueSi" checked>
                            Con desmarque
                        </label>
                        <label>
                            <input type="checkbox" id="desmarqueNo" checked>
                            Sin desmarque
                        </label>
                    </div>
                </div>
                
                <div class="filter-group">
                    <label>Mostrar en Campo:</label>
                    <select id="filterMarkerType" multiple>
                        <option value="shotsNormal" selected>⚪ Remates sin desmarque</option>
                        <option value="shotsRun" selected>⭐ Remates con desmarque</option>
                        <option value="goalsNormal" selected>⚫ Goles sin desmarque</option>
                        <option value="goalsRun" selected>★ Goles con desmarque</option>
                        <option value="crossesNormal" selected>● Centros sin remate</option>
                        <option value="crossesRun" selected>▲ Centros + desmarque</option>
                    </select>
                </div>
                
                <button class="btn-reset" onclick="resetFilters()">🔄 Resetear Filtros</button>
                
                <!-- Leyenda -->
                <div class="legend">
                    <h4>Leyenda</h4>
                    <div class="legend-item">
                        <div class="legend-symbol">⚪</div>
                        <span>Remates sin desmarque</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol">⭐</div>
                        <span>Remates con desmarque</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol">⚫</div>
                        <span>⚽ Goles sin desmarque</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol">★</div>
                        <span>⚽ Goles con desmarque</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol" style="color: #999;">●</div>
                        <span>Centros sin remate</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol" style="color: #90ee90;">▲</div>
                        <span>Centros sin remate + desmarque</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol" style="color: blue;">➜</div>
                        <span>Desmarque a remate</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol" style="color: red;">➜</div>
                        <span>Desmarque a gol</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-symbol" style="color: green;">➜</div>
                        <span>Desmarque a centro</span>
                    </div>
                </div>
                
                <!-- Reporte de Jugada Seleccionada -->
                <div id="playReport" class="play-report">
                    <h4>🎯 Jugada Seleccionada</h4>
                    <div class="play-report-item">
                        <span class="play-report-label">Partido:</span>
                        <span class="play-report-value" id="report-match">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Match ID:</span>
                        <span class="play-report-value" id="report-match-id" style="font-size: 10px;">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Sacador:</span>
                        <span class="play-report-value" id="report-player">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Rematador:</span>
                        <span class="play-report-value" id="report-shooter">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Fecha:</span>
                        <span class="play-report-value" id="report-date">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Tiempo:</span>
                        <span class="play-report-value" id="report-time">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Tipo Centro:</span>
                        <span class="play-report-value" id="report-cross-type">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Saque (X, Y):</span>
                        <span class="play-report-value" id="report-kick-coords">-</span>
                    </div>
                    <div class="play-report-item">
                        <span class="play-report-label">Llegada (X, Y):</span>
                        <span class="play-report-value" id="report-end-coords">-</span>
                    </div>
                    <button class="btn-reset" onclick="deselectPlay()" style="margin-top: 10px; padding: 8px;">✖ Deseleccionar</button>
                </div>
            </div>
            
            <!-- Campo de Fútbol (Centro) -->
            <div class="pitch-container">
                <!-- Controles encima del campo -->
                <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; justify-content: center;">
                    <button class="btn-toggle-dl" id="btnToggleDL" onclick="toggleDefensiveLine()" style="flex: 0 0 auto;">🔴 Ocultar Línea Defensiva</button>
                    <button onclick="setDLPreset(82, 84)" style="
                        padding: 8px 16px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.5)'" onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(102, 126, 234, 0.3)'">
                        📍 Área
                    </button>
                    <button onclick="setDLPreset(88, 90)" style="
                        padding: 8px 16px;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 6px rgba(240, 147, 251, 0.3);
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(240, 147, 251, 0.5)'" onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(240, 147, 251, 0.3)'">
                        🎯 Punto de Penalti
                    </button>
                    <button onclick="setDLPreset(94, 96)" style="
                        padding: 8px 16px;
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 6px rgba(79, 172, 254, 0.3);
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(79, 172, 254, 0.5)'" onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(79, 172, 254, 0.3)'">
                        🥅 Área Pequeña
                    </button>
                    <button class="btn-toggle-dl" id="btnToggleKMeans" onclick="toggleKMeansClustering()" style="
                        padding: 8px 16px;
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 6px rgba(255, 107, 107, 0.3);
                        flex: 0 0 auto;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 107, 0.5)'" onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(255, 107, 107, 0.3)'">
                        🔬 K-Means (K óptimo)
                    </button>
                    <button class="btn-toggle-dl" id="btnToggleSpectral" onclick="toggleSpectralClustering()" style="
                        padding: 8px 16px;
                        background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
                        color: white;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 12px;
                        transition: all 0.2s ease;
                        box-shadow: 0 2px 6px rgba(155, 89, 182, 0.3);
                        flex: 0 0 auto;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(155, 89, 182, 0.5)'" onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(155, 89, 182, 0.3)'">
                        🌀 Spectral (K óptimo)
                    </button>
                </div>
                
                <!-- Slider Altura de Línea Defensiva (arriba) -->
                <div class="slider-container">
                    <div class="slider-label">
                        <span>Altura de Línea Defensiva</span>
                        <span><span id="dlMinVal">{dl_min:.1f}</span> - <span id="dlMaxVal">{dl_max:.1f}</span></span>
                    </div>
                    <div class="slider-wrapper">
                        <input type="range" id="dlMin" min="{dl_min:.1f}" max="{dl_max:.1f}" value="{dl_min:.1f}" step="0.1">
                        <input type="range" id="dlMax" min="{dl_min:.1f}" max="{dl_max:.1f}" value="{dl_max:.1f}" step="0.1">
                        <div class="slider-input-wrapper">
                            <span>Min:</span>
                            <input type="number" id="dlMinInput" min="{dl_min:.1f}" max="{dl_max:.1f}" value="{dl_min:.1f}" step="0.1">
                            <span>Max:</span>
                            <input type="number" id="dlMaxInput" min="{dl_min:.1f}" max="{dl_max:.1f}" value="{dl_max:.1f}" step="0.1">
                        </div>
                    </div>
                </div>
                
                <!-- Campo -->
                <div class="pitch-wrapper">
                    <!-- Canvas del Campo -->
                    <div id="pitch">
                        {pitch_svg}
                        <canvas id="zoneCanvas"></canvas>
                        <canvas id="heatmapCanvas"></canvas>
                        <canvas id="markersCanvas"></canvas>
                    </div>
                </div>
                
                <!-- Tabla de Clusters -->
                <div id="clusterTableContainer">
                    <h3>📋 Análisis de Clusters (click para filtrar)</h3>
                    <table class="cluster-table" id="clusterTable">
                        <thead>
                            <tr>
                                <th>Color</th>
                                <th>Cluster</th>
                                <th>Nº</th>
                                <th>xGoT/acc</th>
                                <th>xG/acc</th>
                                <th>xGoT</th>
                                <th>xG</th>
                                <th>Goles</th>
                                <th>% Goles</th>
                                <th>Media x</th>
                                <th>Media y</th>
                                <th>Media ángulo</th>
                                <th>Media distancia</th>
                                <th>Centroide</th>
                            </tr>
                        </thead>
                        <tbody id="clusterTableBody">
                        </tbody>
                    </table>
                </div>
                
                <!-- Slider X (horizontal, abajo) -->
                <div class="slider-container" style="margin-top: 15px;">
                    <div class="slider-label">
                        <span>Coordenada X (horizontal)</span>
                        <span><span id="xMinVal">{x_min:.1f}</span> - <span id="xMaxVal">{x_max:.1f}</span></span>
                    </div>
                    <div class="slider-wrapper">
                        <input type="range" id="xMin" min="{x_min:.1f}" max="{x_max:.1f}" value="{x_min:.1f}" step="0.1">
                        <input type="range" id="xMax" min="{x_min:.1f}" max="{x_max:.1f}" value="{x_max:.1f}" step="0.1">
                        <div class="slider-input-wrapper">
                            <span>Min:</span>
                            <input type="number" id="xMinInput" min="{x_min:.1f}" max="{x_max:.1f}" value="{x_min:.1f}" step="0.1">
                            <span>Max:</span>
                            <input type="number" id="xMaxInput" min="{x_min:.1f}" max="{x_max:.1f}" value="{x_max:.1f}" step="0.1">
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Slider Y (columna separada) -->
            <div class="slider-y-container">
                <div style="writing-mode: vertical-rl; transform: rotate(180deg); font-weight: bold; font-size: 11px; margin-bottom: 10px;">
                    Y
                </div>
                <div class="slider-y-wrapper">
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 5px; margin-bottom: 5px;">
                        <span style="font-size: 9px;">Max:</span>
                        <input type="number" id="yMaxInput" min="{y_min:.1f}" max="{y_max:.1f}" value="{y_max:.1f}" step="0.1" style="width: 50px; padding: 2px; font-size: 10px; text-align: center;">
                    </div>
                    <span id="yMaxVal" style="font-size: 10px; font-family: monospace;">{y_max:.1f}</span>
                    <input type="range" id="yMax" min="{y_min:.1f}" max="{y_max:.1f}" value="{y_max:.1f}" step="0.1" orient="vertical">
                    <input type="range" id="yMin" min="{y_min:.1f}" max="{y_max:.1f}" value="{y_min:.1f}" step="0.1" orient="vertical">
                    <span id="yMinVal" style="font-size: 10px; font-family: monospace;">{y_min:.1f}</span>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 5px; margin-top: 5px;">
                        <span style="font-size: 9px;">Min:</span>
                        <input type="number" id="yMinInput" min="{y_min:.1f}" max="{y_max:.1f}" value="{y_min:.1f}" step="0.1" style="width: 50px; padding: 2px; font-size: 10px; text-align: center;">
                    </div>
                </div>
            </div>
            
            <!-- Panel de Estadísticas (Derecha) -->
            <div class="stats-panel">
                <h3>📈 Estadísticas</h3>
                
                <!-- Comparación Inswinger vs Outswinger -->
                <div id="comparisonContainer" style="
                    margin-bottom: 15px;
                    padding: 15px 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 8px;
                    color: white;
                    font-weight: 700;
                    text-align: center;
                    font-size: 15px;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                    letter-spacing: 0.3px;
                    transition: all 0.3s ease;
                ">
                    <div id="comparisonText">Cargando comparación...</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">Total Freekicks</div>
                    <div class="stat-value" id="statTotal">0</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">% Successful</div>
                    <div class="stat-value" id="statSuccessful">0.0%</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">% de remates</div>
                    <div class="stat-value" id="statRematesPrimeraAccion">0.0%</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">% de remates (con residuales)</div>
                    <div class="stat-value" id="statRemates">0.0%</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">xG Acumulado</div>
                    <div class="stat-value" id="statXG">0.000</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">xGoT Acumulado</div>
                    <div class="stat-value" id="statXGoT">0.000</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">xG/acción</div>
                    <div class="stat-value" id="statXGAccion">0.0000</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">xGoT/acción</div>
                    <div class="stat-value" id="statXGoTAccion">0.0000</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">Goles</div>
                    <div class="stat-value" id="statGoles">0</div>
                </div>
                
                <div class="stat-item">
                    <div class="stat-label">Goles/acción</div>
                    <div class="stat-value" id="statGolesAccion">0.0000</div>
                </div>
                
                <div class="stat-item" style="border-left-color: #e74c3c;">
                    <div class="stat-label">Δ Media</div>
                    <div class="stat-value" id="statDLMedia">0.0m</div>
                </div>
                
                <!-- Sección Inswinger -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 8px; margin: 15px -15px 10px -15px; text-align: center; font-weight: bold; font-size: 13px;">📈 INSWINGER</div>
                
                <div class="stat-item">
                    <div class="stat-label">% Inswinger</div>
                    <div class="stat-value" id="statPctInswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% Successful Inswinger</div>
                    <div class="stat-value" id="statPctSuccessfulInswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% de remate Inswinger</div>
                    <div class="stat-value" id="statPctRematesPrimeraAccionInswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% de remate (residuales) Inswinger</div>
                    <div class="stat-value" id="statPctRematesInswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG Inswinger</div>
                    <div class="stat-value" id="statXgInswinger">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT Inswinger</div>
                    <div class="stat-value" id="statXgotInswinger">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG/acc. Inswinger</div>
                    <div class="stat-value" id="statXgAccInswinger">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT/acc. Inswinger</div>
                    <div class="stat-value" id="statXgotAccInswinger">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles Inswinger</div>
                    <div class="stat-value" id="statGolesInswinger">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles/acc. Inswinger</div>
                    <div class="stat-value" id="statGolesAccInswinger">0.0000</div>
                </div>
                
                <!-- Sección Outswinger -->
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 8px; margin: 15px -15px 10px -15px; text-align: center; font-weight: bold; font-size: 13px;">📉 OUTSWINGER</div>
                
                <div class="stat-item">
                    <div class="stat-label">% Outswinger</div>
                    <div class="stat-value" id="statPctOutswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% Successful Outswinger</div>
                    <div class="stat-value" id="statPctSuccessfulOutswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% de remate Outswinger</div>
                    <div class="stat-value" id="statPctRematesPrimeraAccionOutswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">% de remate (residuales) Outswinger</div>
                    <div class="stat-value" id="statPctRematesOutswinger">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG Outswinger</div>
                    <div class="stat-value" id="statXgOutswinger">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT Outswinger</div>
                    <div class="stat-value" id="statXgotOutswinger">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG/acc. Outswinger</div>
                    <div class="stat-value" id="statXgAccOutswinger">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT/acc. Outswinger</div>
                    <div class="stat-value" id="statXgotAccOutswinger">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles Outswinger</div>
                    <div class="stat-value" id="statGolesOutswinger">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles/acc. Outswinger</div>
                    <div class="stat-value" id="statGolesAccOutswinger">0.0000</div>
                </div>
                
                <!-- Sección Con Desmarque -->
                <div style="background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; padding: 8px; margin: 15px -15px 10px -15px; text-align: center; font-weight: bold; font-size: 13px;">🏃 CON DESMARQUE</div>
                
                <div class="stat-item">
                    <div class="stat-label">% Con Desmarque</div>
                    <div class="stat-value" id="statPctDesmarque">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG Con Desmarque</div>
                    <div class="stat-value" id="statXgDesmarque">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT Con Desmarque</div>
                    <div class="stat-value" id="statXgotDesmarque">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG/acc. Con Desmarque</div>
                    <div class="stat-value" id="statXgAccDesmarque">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT/acc. Con Desmarque</div>
                    <div class="stat-value" id="statXgotAccDesmarque">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles Con Desmarque</div>
                    <div class="stat-value" id="statGolesDesmarque">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles/acc. Con Desmarque</div>
                    <div class="stat-value" id="statGolesAccDesmarque">0.0000</div>
                </div>
                
                <!-- Sección Sin Desmarque -->
                <div style="background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%); color: white; padding: 8px; margin: 15px -15px 10px -15px; text-align: center; font-weight: bold; font-size: 13px;">🚶 SIN DESMARQUE</div>
                
                <div class="stat-item">
                    <div class="stat-label">% Sin Desmarque</div>
                    <div class="stat-value" id="statPctSinDesmarque">0.0%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG Sin Desmarque</div>
                    <div class="stat-value" id="statXgSinDesmarque">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT Sin Desmarque</div>
                    <div class="stat-value" id="statXgotSinDesmarque">0.000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xG/acc. Sin Desmarque</div>
                    <div class="stat-value" id="statXgAccSinDesmarque">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">xGoT/acc. Sin Desmarque</div>
                    <div class="stat-value" id="statXgotAccSinDesmarque">0.0000</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles Sin Desmarque</div>
                    <div class="stat-value" id="statGolesSinDesmarque">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Goles/acc. Sin Desmarque</div>
                    <div class="stat-value" id="statGolesAccSinDesmarque">0.0000</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Top Performers Table -->
    <div style="clear: both; background: white; padding: 30px 20px;">
        <div class="top-performers-container" style="margin: 0 auto;">
            <h4>🏆 Top Performadores</h4>
            <div class="top-performers-filters">
                <label>
                    <span>👤 Rol:</span>
                    <select id="performerRole" onchange="updatePerformerRoleOptions()">
                        <option value="sacador">Sacadores</option>
                        <option value="rematador">Rematadores</option>
                    </select>
                </label>
                <label>
                    <span>📊 Métrica:</span>
                    <select id="performerMetric" onchange="updateTopPerformersTable()">
                        <option value="xgot_per_fk">xGoT / Freekick</option>
                        <option value="xgot_total">xGoT Acumulado</option>
                        <option value="xg_per_fk">xG / Freekick</option>
                        <option value="xg_total">xG Acumulado</option>
                        <option value="xgot_minus_xg">xGoT-xG Acumulado</option>
                        <option value="goals_per_fk">Goles / Freekick</option>
                        <option value="goals_total">Goles Acumulado</option>
                    </select>
                </label>
                <label>
                    <span>🔢 Mín. Freekicks:</span>
                    <input type="number" id="minFreekicks" value="5" min="1" max="100" step="1" 
                           onchange="updateTopPerformersTable()" 
                           style="padding: 8px 12px; border: 2px solid #ddd; border-radius: 4px; font-size: 13px; width: 80px;">
                </label>
            </div>
            <table class="top-performers-table">
                <thead>
                    <tr>
                        <th class="rank-cell">#</th>
                        <th class="player-cell">Jugador</th>
                        <th class="team-cell">Equipo</th>
                        <th class="count-cell">Freekicks</th>
                        <th class="metric-cell">Valor</th>
                    </tr>
                </thead>
                <tbody id="topPerformersTableBody">
                    <tr><td colspan="5" style="text-align: center; padding: 20px; color: #999;">Cargando...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Scatter Plot xG vs xGoT (completamente separado) -->
    <div style="clear: both; background: #f0f0f0; padding: 30px 20px; position: relative;">
        <div class="scatter-container">
            <h4>📊 xG vs xGoT (30s)</h4>
            <canvas id="scatterCanvas"></canvas>
        </div>
    </div>
    
    <script>
        // ============= DATOS =============
        const allData = {json.dumps(data_json, ensure_ascii=True, separators=(',', ':'), cls=NaNEncoder)};
        const teamsByLeague = {json.dumps(teams_by_league, ensure_ascii=True)};
        const leagueNames = {json.dumps(league_names, ensure_ascii=True)};
        const allLeagues = {json.dumps(leagues, ensure_ascii=True)};
        
        // ============= VARIABLES GLOBALES =============
        let selectedPlay = null;
        let markersData = [];
        let showDefensiveLine = true;
        let clusteringActive = false;
        let clusteringMethod = null;  // 'kmeans' o 'spectral'
        let clusterAssignments = null;
        let clusterCenters = null;
        let selectedCluster = null;  // Cluster seleccionado para filtrado
        let centroidVisible = false;  // Si se está mostrando un centroide
        let visibleCentroidClusterId = null;  // ID del cluster cuyo centroide se muestra
        
        // Rangos globales para reseteo de filtros
        const xMinGlobal = {x_min:.1f};
        const xMaxGlobal = {x_max:.1f};
        const yMinGlobal = {y_min:.1f};
        const yMaxGlobal = {y_max:.1f};
        const dlMinGlobal = {dl_min:.1f};
        const dlMaxGlobal = {dl_max:.1f};
        
        const CLUSTER_COLORS = [
            '#e74c3c', '#3498db', '#2ecc71', '#f39c12',
            '#9b59b6', '#1abc9c', '#e67e22', '#34495e',
            '#16a085', '#c0392b'
        ];
        
        // ============= DEBUG VISIBLE =============
        const originalLog = console.log;
        
        function debugLog(message) {{
            originalLog(message);  // Usar originalLog para evitar recursión
            const debugDiv = document.getElementById('debugMessages');
            const line = document.createElement('div');
            line.textContent = message;
            line.style.marginBottom = '3px';
            debugDiv.appendChild(line);
            debugDiv.scrollTop = debugDiv.scrollHeight;
        }}
        
        // Reemplazar console.log para capturar todos los mensajes
        console.log = function(...args) {{
            const message = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ');
            debugLog(message);
        }};
        
        // ============= CONFIGURACIÓN =============
        const PITCH_WIDTH = 105; // metros
        const PITCH_HEIGHT = 68; // metros
        
        // ============= ELEMENTOS DOM =============
        const pitchEl = document.getElementById('pitch');
        const zoneCanvas = document.getElementById('zoneCanvas');
        const heatmapCanvas = document.getElementById('heatmapCanvas');
        const markersCanvas = document.getElementById('markersCanvas');
        const zoneCtx = zoneCanvas.getContext('2d');
        const heatmapCtx = heatmapCanvas.getContext('2d');
        const markersCtx = markersCanvas.getContext('2d');
        
        // Configurar tamaño de canvas
        function resizeCanvases() {{
            const svg = pitchEl.querySelector('svg');
            if (!svg) {{
                console.error('❌ SVG no encontrado en resizeCanvases');
                return;
            }}
            const rect = svg.getBoundingClientRect();
            console.log('📐 Redimensionando canvas:', rect.width, 'x', rect.height);
            
            if (rect.width === 0 || rect.height === 0) {{
                console.warn('⚠️ SVG aún no tiene dimensiones, reintentando...');
                setTimeout(resizeCanvases, 200);
                return;
            }}
            
            zoneCanvas.width = rect.width;
            zoneCanvas.height = rect.height;
            heatmapCanvas.width = rect.width;
            heatmapCanvas.height = rect.height;
            markersCanvas.width = rect.width;
            markersCanvas.height = rect.height;
            console.log('✅ Canvas redimensionados correctamente');
            updateVisualization();
        }}
        
        window.addEventListener('resize', resizeCanvases);
        
        // ============= EVENT LISTENERS PARA SELECCIÓN =============
        markersCanvas.addEventListener('click', function(event) {{
            const rect = markersCanvas.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const clickY = event.clientY - rect.top;
            
            console.log('🖱️ Clic detectado en:', clickX, clickY);
            
            // Buscar marcador clickeado (de atrás hacia adelante para priorizar los de encima)
            let foundMarker = null;
            for (let i = markersData.length - 1; i >= 0; i--) {{
                const marker = markersData[i];
                const dx = clickX - marker.pos.x;
                const dy = clickY - marker.pos.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance <= marker.radius) {{
                    foundMarker = marker;
                    break;
                }}
            }}
            
            if (foundMarker) {{
                selectPlay(foundMarker.data);
            }} else {{
                deselectPlay();
            }}
        }});
        
        // También deseleccionar al hacer clic fuera del canvas (en cualquier parte del documento)
        document.addEventListener('click', function(event) {{
            // Solo deseleccionar si el clic NO fue en el markersCanvas ni en el panel de reporte
            if (!markersCanvas.contains(event.target) && !document.getElementById('playReport').contains(event.target)) {{
                if (selectedPlay) {{
                    deselectPlay();
                }}
            }}
        }});
        
        // ============= OBTENER ÁREA REAL DEL CAMPO =============
        function getPitchArea(svg) {{
            const svgRect = svg.getBoundingClientRect();
            
            // Márgenes aproximados del 4% para los ejes
            const marginX = svgRect.width * 0.04;
            const marginY = svgRect.height * 0.04;
            
            return {{
                x: marginX,
                y: marginY,
                width: svgRect.width - (marginX * 2),
                height: svgRect.height - (marginY * 2)
            }};
        }}
        
        // ============= FUNCIONES DE CONVERSIÓN =============
        function optaToPixel(x, y, rect, pitchArea) {{
            // Validar y limitar coordenadas al rango Opta (0-100)
            x = Math.max(0, Math.min(100, x));
            y = Math.max(0, Math.min(100, y));
            
            // Convertir a coordenadas del área real del campo
            const px = pitchArea.x + (x / 100.0) * pitchArea.width;
            // Invertir Y: en Opta Y=0 es abajo, Y=100 es arriba
            // En canvas Y=0 es arriba, por lo que invertimos
            const py = pitchArea.y + ((100 - y) / 100.0) * pitchArea.height;
            return {{x: px, y: py}};
        }}
        
        // ============= ACTUALIZAR FILTRO DE EQUIPOS =============
        function updateLeagueFilter() {{
            const selectedSeasons = Array.from(document.getElementById('filterSeason').selectedOptions).map(o => o.value);
            const leagueSelect = document.getElementById('filterLeague');
            
            // Filtrar ligas por temporada seleccionada
            let availableLeagues = [];
            if (selectedSeasons.length === 0) {{
                // Si no hay temporadas seleccionadas, no mostrar ligas
                availableLeagues = [];
            }} else {{
                availableLeagues = allLeagues.filter(league => {{
                    const leagueSeason = league.endsWith('_24-25') || league.endsWith('_24') ? '24-25' :
                                       league.endsWith('_25-26') || league.endsWith('_25') ? '25-26' : null;
                    return leagueSeason && selectedSeasons.includes(leagueSeason);
                }});
            }}
            
            // Guardar selección actual
            const currentSelection = Array.from(leagueSelect.selectedOptions).map(o => o.value);
            
            // Limpiar y rellenar el select
            leagueSelect.innerHTML = '';
            availableLeagues.forEach(league => {{
                const option = document.createElement('option');
                option.value = league;
                option.textContent = leagueNames[league] || league;
                // Mantener seleccionado si estaba previamente seleccionado y sigue disponible
                option.selected = currentSelection.includes(league);
                leagueSelect.appendChild(option);
            }});
            
            // Si no hay ligas seleccionadas, seleccionar todas
            if (Array.from(leagueSelect.selectedOptions).length === 0) {{
                Array.from(leagueSelect.options).forEach(opt => opt.selected = true);
            }}
            
            console.log('🔄 Filtro de ligas actualizado:', availableLeagues.length, 'ligas disponibles');
        }}
        
        function updateTeamFilter() {{
            const selectedLeagues = Array.from(document.getElementById('filterLeague').selectedOptions).map(o => o.value);
            const teamSelect = document.getElementById('filterTeam');
            
            // Obtener equipos de las ligas seleccionadas
            let availableTeams = [];
            selectedLeagues.forEach(league => {{
                if (teamsByLeague[league]) {{
                    availableTeams = availableTeams.concat(teamsByLeague[league]);
                }}
            }});
            
            // Eliminar duplicados y ordenar
            availableTeams = [...new Set(availableTeams)].sort();
            
            // Guardar selección actual
            const currentSelection = Array.from(teamSelect.selectedOptions).map(o => o.value);
            
            // Limpiar y rellenar el select
            teamSelect.innerHTML = '';
            availableTeams.forEach(team => {{
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                // Mantener seleccionado si estaba previamente seleccionado y sigue disponible
                option.selected = currentSelection.includes(team);
                teamSelect.appendChild(option);
            }});
            
            // Si no hay equipos seleccionados, seleccionar todos
            if (Array.from(teamSelect.selectedOptions).length === 0) {{
                Array.from(teamSelect.options).forEach(opt => opt.selected = true);
            }}
            
            console.log('🔄 Filtro de equipos actualizado:', availableTeams.length, 'equipos disponibles');
        }}
        
        // ============= FILTRADO DE DATOS =============
        function filterData() {{
            const xMin = parseFloat(document.getElementById('xMin').value);
            const xMax = parseFloat(document.getElementById('xMax').value);
            const yMin = parseFloat(document.getElementById('yMin').value);
            const yMax = parseFloat(document.getElementById('yMax').value);
            const dlMin = parseFloat(document.getElementById('dlMin').value);
            const dlMax = parseFloat(document.getElementById('dlMax').value);
            
            const selectedSeasons = Array.from(document.getElementById('filterSeason').selectedOptions).map(o => o.value);
            const selectedLeagues = Array.from(document.getElementById('filterLeague').selectedOptions).map(o => o.value);
            const selectedTeams = Array.from(document.getElementById('filterTeam').selectedOptions).map(o => o.value);
            const selectedFKTypes = Array.from(document.getElementById('filterFKType').selectedOptions).map(o => o.value);
            const selectedCrossTypes = Array.from(document.getElementById('filterCrossType').selectedOptions).map(o => o.value);
            
            const outcomeSuccessful = document.getElementById('outcomeSuccessful').checked;
            const outcomeUnsuccessful = document.getElementById('outcomeUnsuccessful').checked;
            
            const desmarqueSi = document.getElementById('desmarqueSi').checked;
            const desmarqueNo = document.getElementById('desmarqueNo').checked;
            
            console.log('🔍 Filtros activos:');
            console.log('   Temporadas:', selectedSeasons.length, selectedSeasons);
            console.log('   Ligas:', selectedLeagues.length, selectedLeagues);
            console.log('   Equipos:', selectedTeams.length, selectedTeams);
            console.log('   FK Types:', selectedFKTypes.length, selectedFKTypes);
            console.log('   Cross Types:', selectedCrossTypes.length, selectedCrossTypes);
            console.log('   Outcome S/U:', outcomeSuccessful, outcomeUnsuccessful);
            console.log('   Desmarque S/N:', desmarqueSi, desmarqueNo);
            
            const filtered = allData.filter(d => {{
                // Filtros de rango
                if (d.x < xMin || d.x > xMax) return false;
                if (d.y < yMin || d.y > yMax) return false;
                
                // Filtro de altura de línea defensiva
                if (d.defensive_line_height !== null) {{
                    if (d.defensive_line_height < dlMin || d.defensive_line_height > dlMax) return false;
                }}
                
                // Filtro de temporada (basado en el sufijo de la liga)
                if (selectedSeasons.length > 0) {{
                    const leagueSeason = d.league.endsWith('_24-25') || d.league.endsWith('_24') ? '24-25' : 
                                        d.league.endsWith('_25-26') || d.league.endsWith('_25') ? '25-26' : null;
                    if (!selectedSeasons.includes(leagueSeason)) return false;
                }}
                
                // Filtros de selección (solo aplicar si hay opciones seleccionadas)
                if (selectedLeagues.length > 0 && !selectedLeagues.includes(d.league)) return false;
                if (selectedTeams.length > 0 && !selectedTeams.includes(d.TeamName)) return false;
                if (selectedFKTypes.length > 0 && !selectedFKTypes.includes(d.freekick_type)) return false;
                
                // Cross type (manejar null)
                const crossType = d.cross_type === null ? 'null' : d.cross_type;
                if (selectedCrossTypes.length > 0 && !selectedCrossTypes.includes(crossType)) return false;
                
                // Outcome
                if (d.outcome === 'Successful' && !outcomeSuccessful) return false;
                if (d.outcome === 'Unsuccessful' && !outcomeUnsuccessful) return false;
                
                // Desmarque
                if (d.tiene_desmarque && !desmarqueSi) return false;
                if (!d.tiene_desmarque && !desmarqueNo) return false;
                
                return true;
            }});
            
            console.log('✅ Filtrado completo:', filtered.length, 'de', allData.length, 'freekicks');
            return filtered;
        }}
        
        // ============= FILTRAR POR TIPO DE MARCADOR =============
        function filterByMarkerType(data) {{
            const selectedMarkerTypes = Array.from(document.getElementById('filterMarkerType').selectedOptions).map(o => o.value);
            
            // Si están todos seleccionados, no filtrar
            if (selectedMarkerTypes.length === 6) {{
                return data;
            }}
            
            const showShotsNormal = selectedMarkerTypes.includes('shotsNormal');
            const showShotsRun = selectedMarkerTypes.includes('shotsRun');
            const showGoalsNormal = selectedMarkerTypes.includes('goalsNormal');
            const showGoalsRun = selectedMarkerTypes.includes('goalsRun');
            const showCrossesNormal = selectedMarkerTypes.includes('crossesNormal');
            const showCrossesRun = selectedMarkerTypes.includes('crossesRun');
            
            return data.filter(d => {{
                const hasShot = d.num_remates_30s && d.num_remates_30s > 0;
                const hasRun = d.tiene_desmarque;
                const isGoal = d.primer_remate_gol === true || d.primer_remate_gol === 1;
                const isSuccessful = d.outcome === 'Successful';
                
                // Filtrar remates donde endX/endY difiere del remate en más de 3 coordenadas
                const shotPositionValid = hasShot && d.primer_remate_x !== null && d.primer_remate_y !== null &&
                                         d.endX !== null && d.endY !== null &&
                                         Math.abs(d.endX - d.primer_remate_x) <= 3 &&
                                         Math.abs(d.endY - d.primer_remate_y) <= 3;
                
                // Categorizar
                if (shotPositionValid && isSuccessful) {{
                    if (isGoal) {{
                        return hasRun ? showGoalsRun : showGoalsNormal;
                    }} else {{
                        return hasRun ? showShotsRun : showShotsNormal;
                    }}
                }} else if (!hasShot && d.endX !== null && d.endY !== null && isSuccessful) {{
                    return hasRun ? showCrossesRun : showCrossesNormal;
                }}
                
                // Si no cumple ninguna categoría visible, no mostrar
                return false;
            }});
        }}
        
        // ============= CÁLCULO DE ESTADÍSTICAS =============
        function calculateStats(data) {{
            const n = data.length;
            if (n === 0) {{
                return {{
                    total: 0, pctSuccessful: 0, pctRemates: 0, pctRematesPrimeraAccion: 0,
                    xgAcum: 0, xgotAcum: 0, xgAccion: 0, xgotAccion: 0,
                    goles: 0, golesAccion: 0, deltaMedia: 0, dlMedia: 0,
                    // Inswinger
                    pctInswinger: 0, pctSuccessfulInswinger: 0, pctRematesInswinger: 0, pctRematesPrimeraAccionInswinger: 0,
                    xgInswinger: 0, xgotInswinger: 0,
                    xgAccInswinger: 0, xgotAccInswinger: 0, golesInswinger: 0, golesAccInswinger: 0,
                    // Outswinger
                    pctOutswinger: 0, pctSuccessfulOutswinger: 0, pctRematesOutswinger: 0, pctRematesPrimeraAccionOutswinger: 0,
                    xgOutswinger: 0, xgotOutswinger: 0,
                    xgAccOutswinger: 0, xgotAccOutswinger: 0, golesOutswinger: 0, golesAccOutswinger: 0,
                    // Con Desmarque
                    pctDesmarque: 0, xgDesmarque: 0, xgotDesmarque: 0,
                    xgAccDesmarque: 0, xgotAccDesmarque: 0, golesDesmarque: 0, golesAccDesmarque: 0,
                    // Sin Desmarque
                    pctSinDesmarque: 0, xgSinDesmarque: 0, xgotSinDesmarque: 0,
                    xgAccSinDesmarque: 0, xgotAccSinDesmarque: 0, golesSinDesmarque: 0, golesAccSinDesmarque: 0,
                    comparisonText: ''
                }};
            }}
            
            let numSuccessful = 0, numRemates = 0, numRematesPrimeraAccion = 0;
            let xgTotal = 0, xgotTotal = 0, golesTotal = 0;
            let deltaSum = 0, deltaCount = 0;
            
            // Inswinger
            let inswingerCount = 0, inswingerXG = 0, inswingerXGoT = 0, inswingerGoles = 0;
            let inswingerSuccessful = 0, inswingerRemates = 0, inswingerRematesPrimeraAccion = 0;
            // Outswinger
            let outswingerCount = 0, outswingerXG = 0, outswingerXGoT = 0, outswingerGoles = 0;
            let outswingerSuccessful = 0, outswingerRemates = 0, outswingerRematesPrimeraAccion = 0;
            // Con desmarque
            let desmarqueCount = 0, desmarqueXG = 0, desmarqueXGoT = 0, desmarqueGoles = 0;
            // Sin desmarque
            let sinDesmarqueCount = 0, sinDesmarqueXG = 0, sinDesmarqueXGoT = 0, sinDesmarqueGoles = 0;
            
            data.forEach(d => {{
                const xg = d.xG_acumulado_30s || 0;
                const xgot = d.xGoT_acumulado_30s || 0;
                const goles = d.goles_30s || 0;
                const crossType = (d.cross_type || '').trim();
                
                if (d.outcome === 'Successful') numSuccessful++;
                if (d.num_remates_30s && d.num_remates_30s > 0) numRemates++;
                
                // Contar remates en primera acción (donde endX/endY está cerca del primer remate)
                const hasShot = d.num_remates_30s && d.num_remates_30s > 0;
                const shotPositionValid = hasShot && d.primer_remate_x !== null && d.primer_remate_y !== null &&
                                         d.endX !== null && d.endY !== null &&
                                         Math.abs(d.endX - d.primer_remate_x) <= 3 &&
                                         Math.abs(d.endY - d.primer_remate_y) <= 3;
                if (shotPositionValid && d.outcome === 'Successful') numRematesPrimeraAccion++;
                
                xgTotal += xg;
                xgotTotal += xgot;
                golesTotal += goles;
                
                if (d.defensive_line_height !== null && !isNaN(d.defensive_line_height)) {{
                    deltaSum += d.defensive_line_height;
                    deltaCount++;
                }}
                
                // Por tipo de cross
                if (crossType === 'Inswinger') {{
                    inswingerCount++;
                    inswingerXG += xg;
                    inswingerXGoT += xgot;
                    inswingerGoles += goles;
                    if (d.outcome === 'Successful') inswingerSuccessful++;
                    if (hasShot) inswingerRemates++;
                    if (shotPositionValid && d.outcome === 'Successful') inswingerRematesPrimeraAccion++;
                }} else if (crossType === 'Outswinger') {{
                    outswingerCount++;
                    outswingerXG += xg;
                    outswingerXGoT += xgot;
                    outswingerGoles += goles;
                    if (d.outcome === 'Successful') outswingerSuccessful++;
                    if (hasShot) outswingerRemates++;
                    if (shotPositionValid && d.outcome === 'Successful') outswingerRematesPrimeraAccion++;
                }}
                
                // Por desmarque
                if (d.tiene_desmarque) {{
                    desmarqueCount++;
                    desmarqueXG += xg;
                    desmarqueXGoT += xgot;
                    desmarqueGoles += goles;
                }} else {{
                    sinDesmarqueCount++;
                    sinDesmarqueXG += xg;
                    sinDesmarqueXGoT += xgot;
                    sinDesmarqueGoles += goles;
                }}
            }});
            
            // Calcular comparación
            let comparisonText = '';
            console.log('📊 Comparación - Inswinger:', inswingerCount, 'FKs, xGoT total:', inswingerXGoT.toFixed(4));
            console.log('📊 Comparación - Outswinger:', outswingerCount, 'FKs, xGoT total:', outswingerXGoT.toFixed(4));
            
            if (inswingerCount > 0 && outswingerCount > 0) {{
                const inswingerXGoTPerAction = inswingerXGoT / inswingerCount;
                const outswingerXGoTPerAction = outswingerXGoT / outswingerCount;
                
                console.log('📊 Inswinger xGoT/acción:', inswingerXGoTPerAction.toFixed(4));
                console.log('📊 Outswinger xGoT/acción:', outswingerXGoTPerAction.toFixed(4));
                
                if (inswingerXGoTPerAction > outswingerXGoTPerAction) {{
                    const diffPct = ((inswingerXGoTPerAction - outswingerXGoTPerAction) / outswingerXGoTPerAction) * 100;
                    comparisonText = `⚡ Inswinger es ${{diffPct.toFixed(1)}}% más efectivo que Outswinger`;
                }} else if (outswingerXGoTPerAction > inswingerXGoTPerAction) {{
                    const diffPct = ((outswingerXGoTPerAction - inswingerXGoTPerAction) / inswingerXGoTPerAction) * 100;
                    comparisonText = `⚡ Outswinger es ${{diffPct.toFixed(1)}}% más efectivo que Inswinger`;
                }} else {{
                    comparisonText = '⚡ Inswinger y Outswinger tienen la misma efectividad';
                }}
                console.log('📊 Texto comparación:', comparisonText);
            }} else {{
                console.log('⚠️ No hay suficientes datos para comparación (necesita ambos tipos)');
            }}
            
            const pctSuccessful = (numSuccessful / n) * 100;
            const pctRemates = (numRemates / n) * 100;
            const pctRematesPrimeraAccion = (numRematesPrimeraAccion / n) * 100;
            const xgAccion = n > 0 ? xgTotal / n : 0;
            const xgotAccion = n > 0 ? xgotTotal / n : 0;
            const golesAccion = n > 0 ? golesTotal / n : 0;
            const dlMediaAltura = deltaCount > 0 ? deltaSum / deltaCount : 0;
            
            // Calcular estadísticas por categoría
            const pctInswinger = (inswingerCount / n) * 100;
            const pctSuccessfulInswinger = inswingerCount > 0 ? (inswingerSuccessful / inswingerCount) * 100 : 0;
            const pctRematesInswinger = inswingerCount > 0 ? (inswingerRemates / inswingerCount) * 100 : 0;
            const pctRematesPrimeraAccionInswinger = inswingerCount > 0 ? (inswingerRematesPrimeraAccion / inswingerCount) * 100 : 0;
            const xgAccInswinger = inswingerCount > 0 ? inswingerXG / inswingerCount : 0;
            const xgotAccInswinger = inswingerCount > 0 ? inswingerXGoT / inswingerCount : 0;
            const golesAccInswinger = inswingerCount > 0 ? inswingerGoles / inswingerCount : 0;
            
            const pctOutswinger = (outswingerCount / n) * 100;
            const pctSuccessfulOutswinger = outswingerCount > 0 ? (outswingerSuccessful / outswingerCount) * 100 : 0;
            const pctRematesOutswinger = outswingerCount > 0 ? (outswingerRemates / outswingerCount) * 100 : 0;
            const pctRematesPrimeraAccionOutswinger = outswingerCount > 0 ? (outswingerRematesPrimeraAccion / outswingerCount) * 100 : 0;
            const xgAccOutswinger = outswingerCount > 0 ? outswingerXG / outswingerCount : 0;
            const xgotAccOutswinger = outswingerCount > 0 ? outswingerXGoT / outswingerCount : 0;
            const golesAccOutswinger = outswingerCount > 0 ? outswingerGoles / outswingerCount : 0;
            
            const pctDesmarque = (desmarqueCount / n) * 100;
            const xgAccDesmarque = desmarqueCount > 0 ? desmarqueXG / desmarqueCount : 0;
            const xgotAccDesmarque = desmarqueCount > 0 ? desmarqueXGoT / desmarqueCount : 0;
            const golesAccDesmarque = desmarqueCount > 0 ? desmarqueGoles / desmarqueCount : 0;
            
            const pctSinDesmarque = (sinDesmarqueCount / n) * 100;
            const xgAccSinDesmarque = sinDesmarqueCount > 0 ? sinDesmarqueXG / sinDesmarqueCount : 0;
            const xgotAccSinDesmarque = sinDesmarqueCount > 0 ? sinDesmarqueXGoT / sinDesmarqueCount : 0;
            const golesAccSinDesmarque = sinDesmarqueCount > 0 ? sinDesmarqueGoles / sinDesmarqueCount : 0;
            
            return {{
                total: n,
                pctSuccessful: pctSuccessful,
                pctRemates: pctRemates,
                pctRematesPrimeraAccion: pctRematesPrimeraAccion,
                xgAcum: xgTotal,
                xgotAcum: xgotTotal,
                xgAccion: xgAccion,
                xgotAccion: xgotAccion,
                goles: golesTotal,
                golesAccion: golesAccion,
                dlMediaAltura: dlMediaAltura,
                comparisonText: comparisonText,
                // Inswinger
                pctInswinger: pctInswinger,
                pctSuccessfulInswinger: pctSuccessfulInswinger,
                pctRematesInswinger: pctRematesInswinger,
                pctRematesPrimeraAccionInswinger: pctRematesPrimeraAccionInswinger,
                xgInswinger: inswingerXG,
                xgotInswinger: inswingerXGoT,
                xgAccInswinger: xgAccInswinger,
                xgotAccInswinger: xgotAccInswinger,
                golesInswinger: inswingerGoles,
                golesAccInswinger: golesAccInswinger,
                // Outswinger
                pctOutswinger: pctOutswinger,
                pctSuccessfulOutswinger: pctSuccessfulOutswinger,
                pctRematesOutswinger: pctRematesOutswinger,
                pctRematesPrimeraAccionOutswinger: pctRematesPrimeraAccionOutswinger,
                xgOutswinger: outswingerXG,
                xgotOutswinger: outswingerXGoT,
                xgAccOutswinger: xgAccOutswinger,
                xgotAccOutswinger: xgotAccOutswinger,
                golesOutswinger: outswingerGoles,
                golesAccOutswinger: golesAccOutswinger,
                // Con Desmarque
                pctDesmarque: pctDesmarque,
                xgDesmarque: desmarqueXG,
                xgotDesmarque: desmarqueXGoT,
                xgAccDesmarque: xgAccDesmarque,
                xgotAccDesmarque: xgotAccDesmarque,
                golesDesmarque: desmarqueGoles,
                golesAccDesmarque: golesAccDesmarque,
                // Sin Desmarque
                pctSinDesmarque: pctSinDesmarque,
                xgSinDesmarque: sinDesmarqueXG,
                xgotSinDesmarque: sinDesmarqueXGoT,
                xgAccSinDesmarque: xgAccSinDesmarque,
                xgotAccSinDesmarque: xgotAccSinDesmarque,
                golesSinDesmarque: sinDesmarqueGoles,
                golesAccSinDesmarque: golesAccSinDesmarque
            }};
        }}
        
        // ============= ACTUALIZAR ESTADÍSTICAS =============
        function updateStats(data) {{
            const stats = calculateStats(data);
            
            // Estadísticas generales
            document.getElementById('statTotal').textContent = stats.total;
            document.getElementById('statSuccessful').textContent = stats.pctSuccessful.toFixed(1) + '%';
            document.getElementById('statRematesPrimeraAccion').textContent = stats.pctRematesPrimeraAccion.toFixed(1) + '%';
            document.getElementById('statRemates').textContent = stats.pctRemates.toFixed(1) + '%';
            document.getElementById('statXG').textContent = stats.xgAcum.toFixed(3);
            document.getElementById('statXGoT').textContent = stats.xgotAcum.toFixed(3);
            document.getElementById('statXGAccion').textContent = stats.xgAccion.toFixed(4);
            document.getElementById('statXGoTAccion').textContent = stats.xgotAccion.toFixed(4);
            document.getElementById('statGoles').textContent = stats.goles;
            document.getElementById('statGolesAccion').textContent = stats.golesAccion.toFixed(4);
            document.getElementById('statDLMedia').textContent = stats.dlMediaAltura.toFixed(1) + 'm';
            
            // Inswinger
            document.getElementById('statPctInswinger').textContent = stats.pctInswinger.toFixed(1) + '%';
            document.getElementById('statPctSuccessfulInswinger').textContent = stats.pctSuccessfulInswinger.toFixed(1) + '%';
            document.getElementById('statPctRematesPrimeraAccionInswinger').textContent = stats.pctRematesPrimeraAccionInswinger.toFixed(1) + '%';
            document.getElementById('statPctRematesInswinger').textContent = stats.pctRematesInswinger.toFixed(1) + '%';
            document.getElementById('statXgInswinger').textContent = stats.xgInswinger.toFixed(3);
            document.getElementById('statXgotInswinger').textContent = stats.xgotInswinger.toFixed(3);
            document.getElementById('statXgAccInswinger').textContent = stats.xgAccInswinger.toFixed(4);
            document.getElementById('statXgotAccInswinger').textContent = stats.xgotAccInswinger.toFixed(4);
            document.getElementById('statGolesInswinger').textContent = stats.golesInswinger;
            document.getElementById('statGolesAccInswinger').textContent = stats.golesAccInswinger.toFixed(4);
            
            // Outswinger
            document.getElementById('statPctOutswinger').textContent = stats.pctOutswinger.toFixed(1) + '%';
            document.getElementById('statPctSuccessfulOutswinger').textContent = stats.pctSuccessfulOutswinger.toFixed(1) + '%';
            document.getElementById('statPctRematesPrimeraAccionOutswinger').textContent = stats.pctRematesPrimeraAccionOutswinger.toFixed(1) + '%';
            document.getElementById('statPctRematesOutswinger').textContent = stats.pctRematesOutswinger.toFixed(1) + '%';
            document.getElementById('statXgOutswinger').textContent = stats.xgOutswinger.toFixed(3);
            document.getElementById('statXgotOutswinger').textContent = stats.xgotOutswinger.toFixed(3);
            document.getElementById('statXgAccOutswinger').textContent = stats.xgAccOutswinger.toFixed(4);
            document.getElementById('statXgotAccOutswinger').textContent = stats.xgotAccOutswinger.toFixed(4);
            document.getElementById('statGolesOutswinger').textContent = stats.golesOutswinger;
            document.getElementById('statGolesAccOutswinger').textContent = stats.golesAccOutswinger.toFixed(4);
            
            // Con Desmarque
            document.getElementById('statPctDesmarque').textContent = stats.pctDesmarque.toFixed(1) + '%';
            document.getElementById('statXgDesmarque').textContent = stats.xgDesmarque.toFixed(3);
            document.getElementById('statXgotDesmarque').textContent = stats.xgotDesmarque.toFixed(3);
            document.getElementById('statXgAccDesmarque').textContent = stats.xgAccDesmarque.toFixed(4);
            document.getElementById('statXgotAccDesmarque').textContent = stats.xgotAccDesmarque.toFixed(4);
            document.getElementById('statGolesDesmarque').textContent = stats.golesDesmarque;
            document.getElementById('statGolesAccDesmarque').textContent = stats.golesAccDesmarque.toFixed(4);
            
            // Sin Desmarque
            document.getElementById('statPctSinDesmarque').textContent = stats.pctSinDesmarque.toFixed(1) + '%';
            document.getElementById('statXgSinDesmarque').textContent = stats.xgSinDesmarque.toFixed(3);
            document.getElementById('statXgotSinDesmarque').textContent = stats.xgotSinDesmarque.toFixed(3);
            document.getElementById('statXgAccSinDesmarque').textContent = stats.xgAccSinDesmarque.toFixed(4);
            document.getElementById('statXgotAccSinDesmarque').textContent = stats.xgotAccSinDesmarque.toFixed(4);
            document.getElementById('statGolesSinDesmarque').textContent = stats.golesSinDesmarque;
            document.getElementById('statGolesAccSinDesmarque').textContent = stats.golesAccSinDesmarque.toFixed(4);
            
            // Actualizar comparación Inswinger vs Outswinger
            const comparisonContainer = document.getElementById('comparisonContainer');
            const comparisonText = document.getElementById('comparisonText');
            console.log('🔄 Actualizando comparación:', stats.comparisonText);
            if (stats.comparisonText) {{
                comparisonText.textContent = stats.comparisonText;
                // Color según quién sea mejor
                if (stats.comparisonText.includes('Inswinger es')) {{
                    // Inswinger mejor: gradiente verde azulado
                    comparisonContainer.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
                }} else if (stats.comparisonText.includes('Outswinger es')) {{
                    // Outswinger mejor: gradiente naranja rojizo
                    comparisonContainer.style.background = 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)';
                }} else {{
                    // Empate: morado original
                    comparisonContainer.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                }}
                console.log('✅ Comparación mostrada');
            }} else {{
                // Mostrar mensaje cuando no hay suficientes datos
                comparisonText.textContent = '⚠️ Se necesitan datos de Inswinger y Outswinger para comparar';
                comparisonContainer.style.background = 'linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%)';
                console.log('⚠️ Comparación sin datos suficientes');
            }}
        }}
        
        // ============= GAUSSIAN BLUR =============
        function gaussianBlur(grid, sigma = 2.0) {{
            const size = grid.length;
            const result = grid.map(row => [...row]);
            
            // Kernel size (3 sigma)
            const kernelSize = Math.ceil(3 * sigma);
            const kernel = [];
            let sum = 0;
            
            // Crear kernel 1D
            for (let i = -kernelSize; i <= kernelSize; i++) {{
                const val = Math.exp(-(i * i) / (2 * sigma * sigma));
                kernel.push(val);
                sum += val;
            }}
            
            // Normalizar kernel
            for (let i = 0; i < kernel.length; i++) {{
                kernel[i] /= sum;
            }}
            
            // Aplicar blur horizontal
            const temp = grid.map(row => [...row]);
            for (let i = 0; i < size; i++) {{
                for (let j = 0; j < size; j++) {{
                    let val = 0;
                    for (let k = -kernelSize; k <= kernelSize; k++) {{
                        const col = j + k;
                        if (col >= 0 && col < size) {{
                            val += grid[i][col] * kernel[k + kernelSize];
                        }}
                    }}
                    temp[i][j] = val;
                }}
            }}
            
            // Aplicar blur vertical
            for (let i = 0; i < size; i++) {{
                for (let j = 0; j < size; j++) {{
                    let val = 0;
                    for (let k = -kernelSize; k <= kernelSize; k++) {{
                        const row = i + k;
                        if (row >= 0 && row < size) {{
                            val += temp[row][j] * kernel[k + kernelSize];
                        }}
                    }}
                    result[i][j] = val;
                }}
            }}
            
            return result;
        }}
        
        // ============= COLOR MAP YlOrRd =============
        function getYlOrRdColor(value, maxValue) {{
            if (maxValue === 0 || value === 0) return 'rgba(255, 255, 255, 0)';
            
            const normalized = Math.min(value / maxValue, 1.0);
            
            // Paleta YlOrRd (Yellow-Orange-Red)
            const colors = [
                [255, 255, 204], // Amarillo muy claro
                [255, 237, 160],
                [254, 217, 118],
                [254, 178, 76],
                [253, 141, 60],
                [252, 78, 42],
                [227, 26, 28],
                [189, 0, 38],
                [128, 0, 38]  // Rojo oscuro
            ];
            
            const idx = normalized * (colors.length - 1);
            const lower = Math.floor(idx);
            const upper = Math.ceil(idx);
            const t = idx - lower;
            
            const c1 = colors[lower];
            const c2 = colors[upper];
            
            const r = Math.round(c1[0] + (c2[0] - c1[0]) * t);
            const g = Math.round(c1[1] + (c2[1] - c1[1]) * t);
            const b = Math.round(c1[2] + (c2[2] - c1[2]) * t);
            
            return `rgba(${{r}}, ${{g}}, ${{b}}, 0.5)`;
        }}
        
        // ============= DIBUJAR MAPA DE CALOR =============
        function drawHeatmap(data, rect, pitchArea) {{
            console.log('🔥 Dibujando heatmap con', data.length, 'eventos');
            
            if (data.length === 0) {{
                heatmapCtx.clearRect(0, 0, rect.width, rect.height);
                return;
            }}
            
            // Crear grid de bins (20x20 como en el PDF)
            const gridSize = 20;
            const grid = Array(gridSize).fill(0).map(() => Array(gridSize).fill(0));
            
            // Contar eventos en cada bin
            data.forEach(d => {{
                let x, y;
                
                // Priorizar coordenadas de remate, luego endX/endY
                if (d.primer_remate_x !== null && d.primer_remate_y !== null) {{
                    x = d.primer_remate_x;
                    y = d.primer_remate_y;
                }} else if (d.endX !== null && d.endY !== null) {{
                    x = d.endX;
                    y = d.endY;
                }} else {{
                    return;
                }}
                
                // Validar y limitar coordenadas al rango Opta (0-100)
                x = Math.max(0, Math.min(100, x));
                y = Math.max(0, Math.min(100, y));
                
                // Convertir coordenadas Opta (0-100) a índices de grid (0-19)
                const binX = Math.floor((x / 100) * gridSize);
                // Invertir Y: en Opta Y=0 es abajo, en grid[0] queremos que sea abajo también
                const binY = Math.floor(((100 - y) / 100) * gridSize);
                
                if (binX >= 0 && binX < gridSize && binY >= 0 && binY < gridSize) {{
                    grid[binY][binX]++;
                }}
            }});
            
            // Aplicar gaussian blur (sigma=2.0 como en el PDF)
            const smoothed = gaussianBlur(grid, 2.0);
            
            // Encontrar valor máximo para normalizar
            let maxValue = 0;
            for (let i = 0; i < gridSize; i++) {{
                for (let j = 0; j < gridSize; j++) {{
                    if (smoothed[i][j] > maxValue) {{
                        maxValue = smoothed[i][j];
                    }}
                }}
            }}
            
            console.log('Heatmap max value:', maxValue);
            
            // Dibujar heatmap usando el área real del campo
            heatmapCtx.clearRect(0, 0, rect.width, rect.height);
            
            const cellWidth = pitchArea.width / gridSize;
            const cellHeight = pitchArea.height / gridSize;
            
            for (let i = 0; i < gridSize; i++) {{
                for (let j = 0; j < gridSize; j++) {{
                    if (smoothed[i][j] > 0) {{
                        const color = getYlOrRdColor(smoothed[i][j], maxValue);
                        heatmapCtx.fillStyle = color;
                        heatmapCtx.fillRect(
                            pitchArea.x + j * cellWidth,
                            pitchArea.y + i * cellHeight,
                            cellWidth,
                            cellHeight
                        );
                    }}
                }}
            }}
            
            console.log('✅ Heatmap dibujado');
        }}
        
        // ============= DIBUJAR ZONA DE SAQUE =============
        function drawZoneRectangle(xMin, xMax, yMin, yMax, rect, pitchArea) {{
            zoneCtx.clearRect(0, 0, rect.width, rect.height);
            
            // Validar y limitar coordenadas al rango Opta (0-100)
            xMin = Math.max(0, Math.min(100, xMin));
            xMax = Math.max(0, Math.min(100, xMax));
            yMin = Math.max(0, Math.min(100, yMin));
            yMax = Math.max(0, Math.min(100, yMax));
            
            // Convertir coordenadas Opta a píxeles usando el área real del campo
            const x1 = pitchArea.x + (xMin / 100) * pitchArea.width;
            const x2 = pitchArea.x + (xMax / 100) * pitchArea.width;
            
            // Y se invierte: yMin=0 es abajo, yMax=100 es arriba
            const y1 = pitchArea.y + ((100 - yMax) / 100) * pitchArea.height;
            const y2 = pitchArea.y + ((100 - yMin) / 100) * pitchArea.height;
            
            const zoneWidth = x2 - x1;
            const zoneHeight = y2 - y1;
            
            // Dibujar rectángulo relleno (facecolor)
            zoneCtx.fillStyle = 'rgba(255, 107, 107, 0.3)'; // #FF6B6B con alpha 0.3
            zoneCtx.fillRect(x1, y1, zoneWidth, zoneHeight);
            
            // Dibujar borde (edgecolor)
            zoneCtx.strokeStyle = '#E74C3C';
            zoneCtx.lineWidth = 3;
            zoneCtx.strokeRect(x1, y1, zoneWidth, zoneHeight);
            
            console.log('✅ Zona de saque dibujada:', xMin, '-', xMax, 'x', yMin, '-', yMax);
        }}
        
        // ============= DIBUJAR LÍNEA DEFENSIVA MEDIA =============
        function drawDefensiveLine(defensiveLineAvg, rect, pitchArea) {{
            if (!defensiveLineAvg || defensiveLineAvg === 0) {{
                return; // No hay datos
            }}
            
            // Convertir altura de línea defensiva (0-100 Opta X) a coordenada X de píxeles
            // La línea defensiva es una posición X vertical
            const xPixel = pitchArea.x + (defensiveLineAvg / 100) * pitchArea.width;
            
            // Dibujar línea VERTICAL discontinua roja
            zoneCtx.strokeStyle = '#FF0000'; // Rojo
            zoneCtx.lineWidth = 3;
            zoneCtx.setLineDash([10, 5]); // Discontinua: 10px línea, 5px espacio
            
            zoneCtx.beginPath();
            zoneCtx.moveTo(xPixel, pitchArea.y);
            zoneCtx.lineTo(xPixel, pitchArea.y + pitchArea.height);
            zoneCtx.stroke();
            
            // Restaurar línea continua para otros dibujos
            zoneCtx.setLineDash([]);
            
            console.log('✅ Línea defensiva media dibujada en X =', defensiveLineAvg.toFixed(1), 'm');
        }}
        
        // ============= DIBUJAR MARCADORES =============
        function drawMarkers(data, rect, pitchArea) {{
            markersCtx.clearRect(0, 0, rect.width, rect.height);
            markersData = []; // Limpiar datos de marcadores
            
            console.log('🎯 DrawMarkers llamado con', data.length, 'eventos');
            
            if (data.length === 0) {{
                console.warn('⚠️ No hay datos para dibujar');
                return;
            }}
            
            // Leer filtros de visualización
            const selectedMarkerTypes = Array.from(document.getElementById('filterMarkerType').selectedOptions).map(o => o.value);
            const showShotsNormal = selectedMarkerTypes.includes('shotsNormal');
            const showShotsRun = selectedMarkerTypes.includes('shotsRun');
            const showGoalsNormal = selectedMarkerTypes.includes('goalsNormal');
            const showGoalsRun = selectedMarkerTypes.includes('goalsRun');
            const showCrossesNormal = selectedMarkerTypes.includes('crossesNormal');
            const showCrossesRun = selectedMarkerTypes.includes('crossesRun');
            
            // Categorizar freekicks
            const shotsNormal = [];
            const shotsActiveRun = [];
            const goalsNormal = [];
            const goalsActiveRun = [];
            const crossesNoShot = [];
            const crossesNoShotRun = [];
            
            data.forEach((d, index) => {{
                // Filtrar por cluster si hay uno seleccionado
                if (selectedCluster !== null && clusterAssignments && clusterAssignments[index] !== selectedCluster) {{
                    return; // Skip este freekick si no pertenece al cluster seleccionado
                }}
                
                const hasShot = d.num_remates_30s && d.num_remates_30s > 0;
                const hasRun = d.tiene_desmarque;
                const isGoal = d.primer_remate_gol === true || d.primer_remate_gol === 1;
                const isSuccessful = d.outcome === 'Successful';
                
                // Filtrar remates donde endX/endY difiere del remate en más de 3 coordenadas
                const shotPositionValid = hasShot && d.primer_remate_x !== null && d.primer_remate_y !== null &&
                                         d.endX !== null && d.endY !== null &&
                                         Math.abs(d.endX - d.primer_remate_x) <= 3 &&
                                         Math.abs(d.endY - d.primer_remate_y) <= 3;
                
                // Filtrar jugadas fuera del área (y < 21 o y > 79)
                const finalY = hasShot ? d.primer_remate_y : d.endY;
                if (finalY !== null && (finalY < 21 || finalY > 79)) return;
                
                if (shotPositionValid && isSuccessful) {{
                    const pos = optaToPixel(d.primer_remate_x, d.primer_remate_y, rect, pitchArea);
                    const arrow = hasRun && d.desmarque_x !== null && d.desmarque_y !== null ? 
                                  optaToPixel(d.desmarque_x, d.desmarque_y, rect, pitchArea) : null;
                    
                    if (isGoal) {{
                        if (hasRun) {{
                            goalsActiveRun.push({{pos, arrow, data: d, index: index}});
                            markersData.push({{pos, radius: 9, type: 'goalRun', data: d}});
                        }} else {{
                            goalsNormal.push({{pos, data: d, index: index}});
                            markersData.push({{pos, radius: 7, type: 'goal', data: d}});
                        }}
                    }} else {{
                        if (hasRun) {{
                            shotsActiveRun.push({{pos, arrow, data: d, index: index}});
                            markersData.push({{pos, radius: 8, type: 'shotRun', data: d}});
                        }} else {{
                            shotsNormal.push({{pos, data: d, index: index}});
                            markersData.push({{pos, radius: 6, type: 'shot', data: d}});
                        }}
                    }}
                }} else if (!hasShot && d.endX !== null && d.endY !== null && isSuccessful) {{
                    const pos = optaToPixel(d.endX, d.endY, rect, pitchArea);
                    const arrow = hasRun && d.desmarque_x !== null && d.desmarque_y !== null ? 
                                  optaToPixel(d.desmarque_x, d.desmarque_y, rect, pitchArea) : null;
                    
                    if (hasRun) {{
                        crossesNoShotRun.push({{pos, arrow, data: d, index: index}});
                        markersData.push({{pos, radius: 6, type: 'crossRun', data: d}});
                    }} else {{
                        crossesNoShot.push({{pos, data: d, index: index}});
                        markersData.push({{pos, radius: 5, type: 'cross', data: d}});
                    }}
                }}
            }});
            
            console.log('📦 markersData almacenado:', markersData.length, 'marcadores');
            
            // Función auxiliar para obtener opacidad según selección
            function getOpacity(itemData) {{
                if (!selectedPlay) return 1.0; // Sin selección: todos visibles
                return itemData.eventId === selectedPlay.eventId ? 1.0 : 0.2; // Seleccionado: visible, resto: desvanecido
            }}
            
            // Funcion auxiliar para obtener color de marcador segun clustering
            function getMarkerColor(itemData, defaultColor, index) {{
                // SEGURIDAD: Verificar TODOS los estados
                if (!clusteringActive) return defaultColor;
                if (clusterAssignments === null) return defaultColor;
                if (clusterAssignments === undefined) return defaultColor;
                if (index >= clusterAssignments.length) return defaultColor;
                if (clusterAssignments[index] === undefined) return defaultColor;
                
                // Si todo OK, usar color de cluster
                const colorIdx = clusterAssignments[index] % CLUSTER_COLORS.length;
                return CLUSTER_COLORS[colorIdx];
            }}
            
            // Función auxiliar para dibujar flecha
            function drawArrow(from, to, color, lineWidth = 2) {{
                markersCtx.strokeStyle = color;
                markersCtx.fillStyle = color;
                markersCtx.lineWidth = lineWidth;
                
                const angle = Math.atan2(to.y - from.y, to.x - from.x);
                const headlen = 4;
                
                markersCtx.beginPath();
                markersCtx.moveTo(from.x, from.y);
                markersCtx.lineTo(to.x, to.y);
                markersCtx.stroke();
                
                markersCtx.beginPath();
                markersCtx.moveTo(to.x, to.y);
                markersCtx.lineTo(to.x - headlen * Math.cos(angle - Math.PI / 6), 
                                 to.y - headlen * Math.sin(angle - Math.PI / 6));
                markersCtx.lineTo(to.x - headlen * Math.cos(angle + Math.PI / 6), 
                                 to.y - headlen * Math.sin(angle + Math.PI / 6));
                markersCtx.closePath();
                markersCtx.fill();
            }}
            
            // 1. Dibujar flechas primero (detrás)
            // Flechas verdes (centros sin remate)
            if (showCrossesRun) {{
                crossesNoShotRun.forEach(item => {{
                    if (item.arrow) {{
                        drawArrow(item.arrow, item.pos, 'rgba(0, 128, 0, 0.6)', 1.5);
                    }}
                }});
            }}
            
            // Flechas azules (remates)
            if (showShotsRun) {{
                shotsActiveRun.forEach(item => {{
                    if (item.arrow) {{
                        drawArrow(item.arrow, item.pos, 'rgba(0, 0, 255, 0.7)', 1.5);
                    }}
                }});
            }}
            
            // Flechas rojas (goles)
            if (showGoalsRun) {{
                goalsActiveRun.forEach(item => {{
                    if (item.arrow) {{
                        drawArrow(item.arrow, item.pos, 'rgba(255, 0, 0, 0.8)', 2);
                    }}
                }});
            }}
            
            // 2. Dibujar puntos encima
            console.log('🔵 Dibujando marcadores:');
            console.log('   - Centros sin remate:', crossesNoShot.length);
            console.log('   - Centros con desmarque:', crossesNoShotRun.length);
            console.log('   - Remates normales:', shotsNormal.length);
            console.log('   - Remates con desmarque:', shotsActiveRun.length);
            console.log('   - Goles normales:', goalsNormal.length);
            console.log('   - Goles con desmarque:', goalsActiveRun.length);
            
            // Centros sin remate (grises)
            if (showCrossesNormal) {{
                crossesNoShot.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'lightgray', item.index);
                    markersCtx.strokeStyle = 'black';
                    markersCtx.lineWidth = 1;
                    markersCtx.beginPath();
                    markersCtx.arc(item.pos.x, item.pos.y, 5, 0, 2 * Math.PI);
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Centros sin remate con desmarque (triángulos verdes)
            if (showCrossesRun) {{
                crossesNoShotRun.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'lightgreen', item.index);
                    markersCtx.strokeStyle = 'darkgreen';
                    markersCtx.lineWidth = 1;
                    markersCtx.beginPath();
                    markersCtx.moveTo(item.pos.x, item.pos.y - 6);
                    markersCtx.lineTo(item.pos.x - 5, item.pos.y + 4);
                    markersCtx.lineTo(item.pos.x + 5, item.pos.y + 4);
                    markersCtx.closePath();
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Remates normales (blancos)
            if (showShotsNormal) {{
                shotsNormal.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'white', item.index);
                    markersCtx.strokeStyle = 'black';
                    markersCtx.lineWidth = 1.5;
                    markersCtx.beginPath();
                    markersCtx.arc(item.pos.x, item.pos.y, 6, 0, 2 * Math.PI);
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Remates con desmarque (estrellas amarillas)
            if (showShotsRun) {{
                shotsActiveRun.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'yellow', item.index);
                    markersCtx.strokeStyle= 'black';
                    markersCtx.lineWidth = 1;
                    drawStar(markersCtx, item.pos.x, item.pos.y, 5, 8, 4);
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Goles sin desmarque (negros con borde rojo)
            if (showGoalsNormal) {{
                goalsNormal.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'black', item.index);
                    markersCtx.strokeStyle = 'red';
                    markersCtx.lineWidth = 1.5;
                    markersCtx.beginPath();
                    markersCtx.arc(item.pos.x, item.pos.y, 7, 0, 2 * Math.PI);
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Goles con desmarque (estrellas negras con borde rojo)
            if (showGoalsRun) {{
                goalsActiveRun.forEach(item => {{
                    markersCtx.globalAlpha = getOpacity(item.data);
                    markersCtx.fillStyle = getMarkerColor(item.data, 'black', item.index);
                    markersCtx.strokeStyle = 'red';
                    markersCtx.lineWidth = 1.5;
                    drawStar(markersCtx, item.pos.x, item.pos.y, 5, 9, 4.5);
                    markersCtx.fill();
                    markersCtx.stroke();
                }});
            }}
            
            // Restaurar opacidad
            markersCtx.globalAlpha = 1.0;
        }}
        
        // Función auxiliar para dibujar estrella
        function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius) {{
            let rot = Math.PI / 2 * 3;
            let x = cx;
            let y = cy;
            const step = Math.PI / spikes;
            
            ctx.beginPath();
            ctx.moveTo(cx, cy - outerRadius);
            
            for (let i = 0; i < spikes; i++) {{
                x = cx + Math.cos(rot) * outerRadius;
                y = cy + Math.sin(rot) * outerRadius;
                ctx.lineTo(x, y);
                rot += step;
                
                x = cx + Math.cos(rot) * innerRadius;
                y = cy + Math.sin(rot) * innerRadius;
                ctx.lineTo(x, y);
                rot += step;
            }}
            
            ctx.lineTo(cx, cy - outerRadius);
            ctx.closePath();
        }}
        
        // ============= DIBUJAR SCATTER xG vs xGoT =============
        function drawScatter(data) {{
            const canvas = document.getElementById('scatterCanvas');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            // Canvas cuadrado de 600x600px para evitar pixelación
            canvas.width = 600;
            canvas.height = 600;
            
            // Limpiar canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            if (data.length === 0) {{
                ctx.fillStyle = '#999';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos para mostrar', canvas.width/2, canvas.height/2);
                return;
            }}
            
            // AGRUPAR POR EQUIPO: Sumar xG y xGoT de todas las freekicks de cada equipo
            const teamStats = {{}};
            data.forEach(d => {{
                const team = d.TeamName || 'Desconocido';
                const xg = d.xG_acumulado_30s || 0;
                const xgot = d.xGoT_acumulado_30s || 0;
                
                if (!teamStats[team]) {{
                    teamStats[team] = {{
                        team: team,
                        league: d.league || '?',
                        xg_total: 0,
                        xgot_total: 0,
                        count: 0
                    }};
                }}
                
                teamStats[team].xg_total += xg;
                teamStats[team].xgot_total += xgot;
                teamStats[team].count += 1;
            }});
            
            // Convertir a array
            const teamsArray = Object.values(teamStats);
            
            if (teamsArray.length === 0) {{
                ctx.fillStyle = '#999';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('No hay equipos para mostrar', canvas.width/2, canvas.height/2);
                return;
            }}
            
            // Márgenes para canvas 600x600 (más espacio para etiquetas)
            const margin = {{top: 60, right: 120, bottom: 70, left: 80}};
            const width = canvas.width - margin.left - margin.right;
            const height = canvas.height - margin.top - margin.bottom;
            
            // Obtener rangos de datos (ahora de equipos)
            const xValues = teamsArray.map(d => d.xg_total);
            const yValues = teamsArray.map(d => d.xgot_total);
            
            // Usar la MISMA escala en ambos ejes
            const maxValue = Math.max(Math.max(...xValues, 0.1), Math.max(...yValues, 0.1));
            
            // Escalas (ambos ejes usan maxValue)
            const xScale = (val) => margin.left + (val / maxValue) * width;
            const yScale = (val) => margin.top + height - (val / maxValue) * height;
            
            // Dibujar ejes
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(margin.left, margin.top);
            ctx.lineTo(margin.left, margin.top + height);
            ctx.lineTo(margin.left + width, margin.top + height);
            ctx.stroke();
            
            // ESCALAS NUMÉRICAS - EJE X
            ctx.font = '11px Arial';
            ctx.fillStyle = '#666';
            ctx.textAlign = 'center';
            const xTicks = 5;
            for (let i = 0; i <= xTicks; i++) {{
                const val = (maxValue / xTicks) * i;
                const x = xScale(val);
                // Tick mark
                ctx.beginPath();
                ctx.moveTo(x, margin.top + height);
                ctx.lineTo(x, margin.top + height + 5);
                ctx.strokeStyle = '#666';
                ctx.lineWidth = 1;
                ctx.stroke();
                // Label
                ctx.fillText(val.toFixed(2), x, margin.top + height + 20);
            }}
            
            // ESCALAS NUMÉRICAS - EJE Y
            ctx.textAlign = 'right';
            const yTicks = 5;
            for (let i = 0; i <= yTicks; i++) {{
                const val = (maxValue / yTicks) * i;
                const y = yScale(val);
                // Tick mark
                ctx.beginPath();
                ctx.moveTo(margin.left - 5, y);
                ctx.lineTo(margin.left, y);
                ctx.strokeStyle = '#666';
                ctx.lineWidth = 1;
                ctx.stroke();
                // Label
                ctx.fillText(val.toFixed(2), margin.left - 10, y + 4);
            }}
            
            // Labels de ejes
            ctx.fillStyle = '#333';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('xG acumulado (30s)', margin.left + width/2, canvas.height - 25);
            
            ctx.save();
            ctx.translate(25, margin.top + height/2);
            ctx.rotate(-Math.PI/2);
            ctx.fillText('xGoT acumulado (30s)', 0, 0);
            ctx.restore();
            
            // LÍNEA DIAGONAL xG = xGoT (referencia)
            const maxDiag = maxValue * 1.05;
            ctx.strokeStyle = '#999';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(xScale(0), yScale(0));
            ctx.lineTo(xScale(maxDiag), yScale(maxDiag));
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Etiqueta de la línea diagonal
            ctx.font = '10px Arial';
            ctx.fillStyle = '#999';
            ctx.textAlign = 'left';
            ctx.fillText('xG = xGoT', xScale(maxDiag * 0.85), yScale(maxDiag * 0.85) - 5);
            
            // Identificar top 5 equipos por xGoT total
            const top5Teams = [...teamsArray]
                .sort((a, b) => b.xgot_total - a.xgot_total)
                .slice(0, 5);
            const top5Names = new Set(top5Teams.map(t => t.team));
            
            // Dibujar puntos (equipos)
            teamsArray.forEach(team => {{
                const x = xScale(team.xg_total);
                const y = yScale(team.xgot_total);
                
                const isTop5 = top5Names.has(team.team);
                
                // Color único para todos los equipos (azul)
                ctx.fillStyle = isTop5 ? 'rgba(52, 152, 219, 0.9)' : 'rgba(52, 152, 219, 0.5)';
                
                ctx.beginPath();
                ctx.arc(x, y, isTop5 ? 6 : 4, 0, 2 * Math.PI);
                ctx.fill();
                
                // Borde para top 5
                if (isTop5) {{
                    ctx.strokeStyle = '#000';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }}
            }});
            
            // Dibujar etiquetas para top 5 equipos
            ctx.font = 'bold 10px Arial';
            top5Teams.forEach((team, idx) => {{
                const x = xScale(team.xg_total);
                const y = yScale(team.xgot_total);
                
                // Crear etiqueta con recuadro amarillo
                const label = `${{team.team}} (${{team.count}} FK)`;
                
                // Fondo amarillo
                ctx.fillStyle = 'rgba(255, 235, 59, 0.9)';
                const textWidth = ctx.measureText(label).width;
                ctx.fillRect(x + 8, y - 18, textWidth + 6, 14);
                
                // Borde negro
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 1;
                ctx.strokeRect(x + 8, y - 18, textWidth + 6, 14);
                
                // Texto negro
                ctx.fillStyle = '#000';
                ctx.textAlign = 'left';
                ctx.fillText(label, x + 11, y - 8);
            }});
            
            // Leyenda
            ctx.font = '11px Arial';
            ctx.fillStyle = '#333';
            ctx.textAlign = 'left';
            ctx.fillText(`Equipos: ${{teamsArray.length}} | Top 5 etiquetados`, margin.left + 10, 20);
            
            // Círculo azul de ejemplo
            ctx.fillStyle = 'rgba(52, 152, 219, 0.7)';
            ctx.beginPath();
            ctx.arc(margin.left + 10, 32, 4, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillStyle = '#333';
            ctx.fillText('= Equipo', margin.left + 20, 36);
        }}
        
        // ============= TOP PERFORMERS =============
        function updatePerformerRoleOptions() {{
            const role = document.getElementById('performerRole').value;
            const metricSelect = document.getElementById('performerMetric');
            const currentMetric = metricSelect.value;
            
            // Obtener todas las opciones
            const options = metricSelect.querySelectorAll('option');
            
            if (role === 'rematador') {{
                // Deshabilitar opciones "per_fk" para rematadores
                options.forEach(option => {{
                    if (option.value.includes('_per_fk')) {{
                        option.disabled = true;
                        option.style.color = '#ccc';
                    }} else {{
                        option.disabled = false;
                        option.style.color = '';
                    }}
                }});
                
                // Si la métrica actual es "per_fk", cambiar a acumulada
                if (currentMetric.includes('_per_fk')) {{
                    metricSelect.value = currentMetric.replace('_per_fk', '_total');
                }}
            }} else {{
                // Habilitar todas las opciones para sacadores
                options.forEach(option => {{
                    option.disabled = false;
                    option.style.color = '';
                }});
            }}
            
            // Actualizar tabla
            updateTopPerformersTable();
        }}
        
        function calculateTopPerformers(data, role, metric) {{
            const performers = {{}};
            
            console.log('🏆 Calculando top performers con', data.length, 'freekicks filtrados');
            console.log('   Rol:', role, '| Métrica:', metric);
            
            data.forEach(d => {{
                let player = null;
                let isRelevant = false;
                
                if (role === 'sacador') {{
                    // Para sacadores: contar freekicks centrados (tipo Cross)
                    if (d.freekick_type === 'Cross' && d.jugador) {{
                        player = d.jugador;
                        isRelevant = true;
                    }}
                }} else if (role === 'rematador') {{
                    // Para rematadores: contar solo si hay remate
                    if (d.num_remates_30s > 0 && d.passTarget_jugador) {{
                        player = d.passTarget_jugador;
                        isRelevant = true;
                    }}
                }}
                
                if (!isRelevant || !player) return;
                
                if (!performers[player]) {{
                    performers[player] = {{
                        player: player,
                        team: d.TeamName || '?',
                        count: 0,
                        xg_total: 0,
                        xgot_total: 0,
                        goals_total: 0
                    }};
                }}
                
                performers[player].count += 1;
                
                // Asegurar conversión a número y manejo de nulls
                const xg = parseFloat(d.xG_acumulado_30s);
                const xgot = parseFloat(d.xGoT_acumulado_30s);
                
                performers[player].xg_total += isNaN(xg) ? 0 : xg;
                performers[player].xgot_total += isNaN(xgot) ? 0 : xgot;
                
                // Contar goles
                if (d.primer_remate_gol === true || d.primer_remate_gol === 1) {{
                    performers[player].goals_total += 1;
                }}
            }});
            
            console.log('   Jugadores encontrados:', Object.keys(performers).length);
            if (Object.keys(performers).length > 0) {{
                const sample = Object.values(performers)[0];
                console.log('   Ejemplo:', sample.player, '- Count:', sample.count, '- xG:', sample.xg_total, '- xGoT:', sample.xgot_total);
            }}
            
            // Convertir a array y calcular métricas por acción
            const performersArray = Object.values(performers).map(p => ({{
                ...p,
                xg_per_fk: p.count > 0 ? p.xg_total / p.count : 0,
                xgot_per_fk: p.count > 0 ? p.xgot_total / p.count : 0,
                goals_per_fk: p.count > 0 ? p.goals_total / p.count : 0,
                xgot_minus_xg: p.xgot_total - p.xg_total
            }}));
            
            // Filtrar por mínimo de freekicks
            const minFreekicks = parseInt(document.getElementById('minFreekicks').value) || 1;
            const filteredArray = performersArray.filter(p => p.count >= minFreekicks);
            
            console.log('   Después de filtrar por mínimo', minFreekicks, 'freekicks:', filteredArray.length, 'jugadores');
            
            // Ordenar según la métrica seleccionada
            filteredArray.sort((a, b) => b[metric] - a[metric]);
            
            // Retornar top 10
            return filteredArray.slice(0, 10);
        }}
        
        function updateTopPerformersTable(dataOverride = null) {{
            const data = dataOverride || filterByMarkerType(filterData());
            const role = document.getElementById('performerRole').value;
            const metric = document.getElementById('performerMetric').value;
            
            const topPerformers = calculateTopPerformers(data, role, metric);
            const tbody = document.getElementById('topPerformersTableBody');
            
            if (topPerformers.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #999;">No hay datos disponibles</td></tr>';
                return;
            }}
            
            // Determinar etiqueta de métrica
            const metricLabels = {{
                'xgot_per_fk': 'xGoT/FK',
                'xgot_total': 'xGoT Total',
                'xg_per_fk': 'xG/FK',
                'xg_total': 'xG Total',
                'xgot_minus_xg': 'xGoT-xG',
                'goals_per_fk': 'Goles/FK',
                'goals_total': 'Goles Total'
            }};
            
            // Actualizar header de métrica
            const metricHeader = document.querySelector('.top-performers-table .metric-cell');
            metricHeader.textContent = metricLabels[metric] || 'Valor';
            
            // Generar filas
            tbody.innerHTML = topPerformers.map((p, index) => {{
                const metricValue = metric.includes('_per_fk') 
                    ? p[metric].toFixed(3)
                    : p[metric].toFixed(2);
                
                return `
                    <tr>
                        <td class="rank-cell">${{index + 1}}</td>
                        <td class="player-cell">${{p.player}}</td>
                        <td class="team-cell">${{p.team}}</td>
                        <td class="count-cell">${{p.count}}</td>
                        <td class="metric-cell">${{metricValue}}</td>
                    </tr>
                `;
            }}).join('');
        }}
        
        // ============= ACTUALIZAR VISUALIZACIÓN =============
        function updateVisualization() {{
            const svg = pitchEl.querySelector('svg');
            if (!svg) {{
                console.error('❌ SVG no encontrado');
                return;
            }}
            const rect = svg.getBoundingClientRect();
            const pitchArea = getPitchArea(svg);
            let filtered = filterData();
            
            // Aplicar filtro de tipo de marcador para estadísticas
            const filteredForStats = filterByMarkerType(filtered);
            
            // Obtener valores actuales de los sliders
            const xMin = parseFloat(document.getElementById('xMin').value);
            const xMax = parseFloat(document.getElementById('xMax').value);
            const yMin = parseFloat(document.getElementById('yMin').value);
            const yMax = parseFloat(document.getElementById('yMax').value);
            
            console.log('🔄 Actualizando visualización con', filtered.length, 'freekicks filtrados');
            console.log('📊 Filtrados para stats:', filteredForStats.length, 'freekicks');
            console.log('📍 Área del campo:', pitchArea);
            
            const stats = calculateStats(filteredForStats);
            updateStats(filteredForStats);
            
            drawZoneRectangle(xMin, xMax, yMin, yMax, rect, pitchArea);
            
            // Dibujar línea defensiva promedio (solo si está habilitada)
            if (showDefensiveLine) {{
                const dlMedia = parseFloat(stats.dlMediaAltura);
                drawDefensiveLine(dlMedia, rect, pitchArea);
            }}
            
            drawHeatmap(filtered, rect, pitchArea);
            drawMarkers(filtered, rect, pitchArea);
            
            // Dibujar centroide como VECTOR si está visible
            if (centroidVisible && visibleCentroidClusterId !== null && clusterCenters) {{
                console.log('🔍 Intentando dibujar centroide...');
                const centroid = clusterCenters[visibleCentroidClusterId];
                
                if (centroid) {{
                    const inicioPosX = centroid[0];
                    const inicioPosY = centroid[1];
                    const angulo = centroid[2];
                    const distanciaMetros = centroid[3];
                    
                    console.log(`   📍 Inicio: x=${{inicioPosX}}, y=${{inicioPosY}}`);
                    console.log(`   ➡️ Vector: ángulo=${{angulo}}°, distancia=${{distanciaMetros}}m`);
                    
                    const anguloRad = angulo * Math.PI / 180;
                    const dx_metros = distanciaMetros * Math.cos(anguloRad);
                    const dy_metros = distanciaMetros * Math.sin(anguloRad);
                    const dx_opta = dx_metros / 1.05;
                    const dy_opta = dy_metros / 0.68;
                    const rematePosX = inicioPosX + dx_opta;
                    const rematePosY = inicioPosY + dy_opta;
                    
                    const inicioPixel = optaToPixel(inicioPosX, inicioPosY, rect, pitchArea);
                    const rematePixel = optaToPixel(rematePosX, rematePosY, rect, pitchArea);
                    const centroidColor = CLUSTER_COLORS[visibleCentroidClusterId % CLUSTER_COLORS.length];
                    
                    // Dibujar FLECHA VECTORIAL
                    markersCtx.globalAlpha = 1.0;
                    markersCtx.strokeStyle = centroidColor;
                    markersCtx.fillStyle = centroidColor;
                    markersCtx.lineWidth = 6;
                    
                    const angle = Math.atan2(rematePixel.y - inicioPixel.y, rematePixel.x - inicioPixel.x);
                    const headlen = 15;
                    
                    markersCtx.beginPath();
                    markersCtx.moveTo(inicioPixel.x, inicioPixel.y);
                    markersCtx.lineTo(rematePixel.x, rematePixel.y);
                    markersCtx.stroke();
                    
                    markersCtx.beginPath();
                    markersCtx.moveTo(rematePixel.x, rematePixel.y);
                    markersCtx.lineTo(rematePixel.x - headlen * Math.cos(angle - Math.PI / 6), 
                                     rematePixel.y - headlen * Math.sin(angle - Math.PI / 6));
                    markersCtx.lineTo(rematePixel.x - headlen * Math.cos(angle + Math.PI / 6), 
                                     rematePixel.y - headlen * Math.sin(angle + Math.PI / 6));
                    markersCtx.closePath();
                    markersCtx.fill();
                    
                    // Círculo en posición INICIAL
                    markersCtx.fillStyle = centroidColor;
                    markersCtx.strokeStyle = 'white';
                    markersCtx.lineWidth = 4;
                    markersCtx.beginPath();
                    markersCtx.arc(inicioPixel.x, inicioPixel.y, 10, 0, 2 * Math.PI);
                    markersCtx.fill();
                    markersCtx.stroke();
                    
                    markersCtx.strokeStyle = 'black';
                    markersCtx.lineWidth = 2;
                    markersCtx.beginPath();
                    markersCtx.arc(inicioPixel.x, inicioPixel.y, 10, 0, 2 * Math.PI);
                    markersCtx.stroke();
                    
                    // Estrella en posición de REMATE
                    markersCtx.fillStyle = centroidColor;
                    markersCtx.strokeStyle = 'white';
                    markersCtx.lineWidth = 3;
                    drawStar(markersCtx, rematePixel.x, rematePixel.y, 8, 12, 6);
                    markersCtx.fill();
                    markersCtx.stroke();
                    
                    markersCtx.strokeStyle = 'black';
                    markersCtx.lineWidth = 1.5;
                    drawStar(markersCtx, rematePixel.x, rematePixel.y, 8, 12, 6);
                    markersCtx.stroke();
                    
                    // Etiqueta "CENTROIDE"
                    markersCtx.globalAlpha = 1.0;
                    markersCtx.fillStyle = 'white';
                    markersCtx.strokeStyle = 'black';
                    markersCtx.lineWidth = 3;
                    markersCtx.font = 'bold 14px Arial';
                    markersCtx.textAlign = 'center';
                    markersCtx.textBaseline = 'bottom';
                    markersCtx.strokeText('CENTROIDE', rematePixel.x, rematePixel.y - 25);
                    markersCtx.fillText('CENTROIDE', rematePixel.x, rematePixel.y - 25);
                    
                    console.log('   ✅ Centroide dibujado correctamente');
                }}
            }}
            
            drawScatter(filteredForStats);
            
            // Filtrar por cluster si hay uno seleccionado para la tabla de Top Performers
            let performersData = filteredForStats;
            if (selectedCluster !== null && clusterAssignments) {{
                performersData = filteredForStats.filter((d, index) => clusterAssignments[index] === selectedCluster);
                console.log('📊 Top Performers filtrado por cluster ' + (selectedCluster + 1) + ': ' + performersData.length + ' jugadas');
            }}
            
            updateTopPerformersTable(performersData);
        }}
        
        // ============= SELECCIÓN DE JUGADAS =============
        function selectPlay(playData) {{
            selectedPlay = playData;
            
            // Mostrar panel de reporte
            const reportPanel = document.getElementById('playReport');
            reportPanel.classList.add('active');
            
            // Rellenar datos
            document.getElementById('report-match').textContent = 
                `${{playData.TeamName || 'N/A'}} vs ${{playData.TeamRival || 'N/A'}}`;
            document.getElementById('report-match-id').textContent = playData.matchId || 'N/A';
            document.getElementById('report-player').textContent = playData.jugador || 'N/A';
            
            // Rematador: mostrar jugador si hay remate, o receptor de passTarget si es Successful sin remate
            let shooterText;
            if (playData.primer_remate_jugador) {{
                shooterText = playData.primer_remate_jugador;
            }} else if (playData.outcome === 'Successful' && playData.passTarget_jugador) {{
                shooterText = playData.passTarget_jugador + ' (receptor)';
            }} else if (playData.outcome === 'Successful') {{
                shooterText = 'Controlado (sin remate)';
            }} else {{
                shooterText = 'Sin remate';
            }}
            document.getElementById('report-shooter').textContent = shooterText;
            
            document.getElementById('report-date').textContent = playData.fecha || 'N/A';
            document.getElementById('report-time').textContent = 
                `${{playData.minute ?? '?'}}' ${{playData.second ?? '?'}}\"`;
            document.getElementById('report-cross-type').textContent = playData.cross_type || 'N/A';
            document.getElementById('report-kick-coords').textContent = 
                `(${{playData.x?.toFixed(1) ?? '?'}}, ${{playData.y?.toFixed(1) ?? '?'}})`;
            
            const endX = playData.num_remates_30s > 0 ? playData.primer_remate_x : playData.endX;
            const endY = playData.num_remates_30s > 0 ? playData.primer_remate_y : playData.endY;
            document.getElementById('report-end-coords').textContent = 
                `(${{endX?.toFixed(1) ?? '?'}}, ${{endY?.toFixed(1) ?? '?'}})`;
            
            // Redibujar marcadores con opacidad
            updateVisualization();
            
            console.log('✅ Jugada seleccionada:', playData.eventId);
        }}
        
        // ============= TOGGLE LÍNEA DEFENSIVA =============
        function toggleDefensiveLine() {{
            showDefensiveLine = !showDefensiveLine;
            const btn = document.getElementById('btnToggleDL');
            
            if (showDefensiveLine) {{
                btn.textContent = '🔴 Ocultar Línea Defensiva';
                btn.classList.remove('hidden');
                console.log('✅ Línea defensiva activada');
            }} else {{
                btn.textContent = '⚪ Mostrar Línea Defensiva';
                btn.classList.add('hidden');
                console.log('❌ Línea defensiva desactivada');
            }}
            
            updateVisualization();
        }}
        
        // ============= PRESETS DE DELTA =============
        function setDLPreset(minVal, maxVal) {{
            // Establecer valores en los sliders
            document.getElementById('dlMin').value = minVal.toFixed(1);
            document.getElementById('dlMax').value = maxVal.toFixed(1);
            
            // Actualizar displays de valores
            document.getElementById('dlMinVal').textContent = minVal.toFixed(1);
            document.getElementById('dlMaxVal').textContent = maxVal.toFixed(1);
            
            // Actualizar inputs numéricos
            document.getElementById('dlMinInput').value = minVal.toFixed(1);
            document.getElementById('dlMaxInput').value = maxVal.toFixed(1);
            
            console.log(`🎯 Preset aplicado: Delta ${{minVal}}-${{maxVal}}m`);
            
            // Actualizar visualización
            updateVisualization();
        }}
        
        function deselectPlay() {{
            selectedPlay = null;
            
            // Ocultar panel de reporte
            const reportPanel = document.getElementById('playReport');
            reportPanel.classList.remove('active');
            
            // Redibujar marcadores sin opacidad
            updateVisualization();
            
            console.log('✅ Jugada deseleccionada');
        }}
        
        // ============= RESETEAR FILTROS =============
        function resetFilters() {{
            console.log('🔄 Reseteando todos los filtros...');
            
            // Resetear sliders X, Y, Delta
            document.getElementById('xMin').value = xMinGlobal;
            document.getElementById('xMax').value = xMaxGlobal;
            document.getElementById('yMin').value = yMinGlobal;
            document.getElementById('yMax').value = yMaxGlobal;
            document.getElementById('dlMin').value = dlMinGlobal;
            document.getElementById('dlMax').value = dlMaxGlobal;
            
            // Resetear inputs numéricos
            document.getElementById('xMinInput').value = xMinGlobal.toFixed(1);
            document.getElementById('xMaxInput').value = xMaxGlobal.toFixed(1);
            document.getElementById('yMinInput').value = yMinGlobal.toFixed(1);
            document.getElementById('yMaxInput').value = yMaxGlobal.toFixed(1);
            document.getElementById('dlMinInput').value = dlMinGlobal.toFixed(1);
            document.getElementById('dlMaxInput').value = dlMaxGlobal.toFixed(1);
            
            // Resetear labels
            updateSliderLabels();
            
            // Seleccionar todas las opciones en selectores
            selectAllOptions('filterSeason');
            selectAllOptions('filterLeague');
            selectAllOptions('filterTeam');
            selectAllOptions('filterFKType');
            selectAllOptions('filterCrossType');
            selectAllOptions('filterMarkerType');
            
            // Resetear checkboxes
            document.getElementById('outcomeSuccessful').checked = true;
            document.getElementById('outcomeUnsuccessful').checked = true;
            document.getElementById('desmarqueSi').checked = true;
            document.getElementById('desmarqueNo').checked = true;
            
            // Deseleccionar jugada si hay
            if (selectedPlay) {{
                deselectPlay();
            }}
            
            // Desactivar clustering si está activo
            if (clusteringActive) {{
                if (clusteringMethod === 'kmeans') {{
                    toggleKMeansClustering();
                }} else if (clusteringMethod === 'spectral') {{
                    toggleSpectralClustering();
                }}
            }}
            
            console.log('✅ Todos los filtros reseteados');
            updateVisualization();
        }}
        
        // ============= CLUSTERING K-MEANS =============
        function toggleKMeansClustering() {{
            const btnKmeans = document.getElementById('btnToggleKMeans');
            const btnSpectral = document.getElementById('btnToggleSpectral');
            
            if (clusteringActive && clusteringMethod === 'kmeans') {{
                // Desactivar - LIMPIAR TODO
                clusteringActive = false;
                clusteringMethod = null;
                btnKmeans.textContent = '🔬 K-Means (K optimo)';
                btnKmeans.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)';
                clusterAssignments = null;
                clusterCenters = null;
                selectedCluster = null;
                centroidVisible = false;
                visibleCentroidClusterId = null;
                document.getElementById('clusterTableContainer').style.display = 'none';
                
                // Limpiar AMBOS canvas explícitamente ANTES de redibujar
                console.log('🧹 Limpiando canvas de heatmap, marcadores y zona...');
                heatmapCtx.clearRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
                markersCtx.clearRect(0, 0, markersCanvas.width, markersCanvas.height);
                zoneCtx.clearRect(0, 0, zoneCanvas.width, zoneCanvas.height);
                
                console.log('K-Means desactivado completamente');
                updateVisualization();
            }} else {{
                // Activar K-Means (desactivar Spectral si está activo)
                if (clusteringActive && clusteringMethod === 'spectral') {{
                    btnSpectral.textContent = '🌀 Spectral (K óptimo)';
                    btnSpectral.style.background = 'linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)';
                }}
                clusteringActive = true;
                clusteringMethod = 'kmeans';
                btnKmeans.textContent = '❌ Desactivar K-Means';
                btnKmeans.style.background = 'linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)';
                runKMeansClustering();
            }}
        }}
        
        function toggleSpectralClustering() {{
            const btnKmeans = document.getElementById('btnToggleKMeans');
            const btnSpectral = document.getElementById('btnToggleSpectral');
            
            if (clusteringActive && clusteringMethod === 'spectral') {{
                // Desactivar - LIMPIAR TODO
                clusteringActive = false;
                clusteringMethod = null;
                btnSpectral.textContent = '🌀 Spectral (K optimo)';
                btnSpectral.style.background = 'linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)';
                clusterAssignments = null;
                clusterCenters = null;
                selectedCluster = null;
                centroidVisible = false;
                visibleCentroidClusterId = null;
                document.getElementById('clusterTableContainer').style.display = 'none';
                
                // Limpiar AMBOS canvas explícitamente ANTES de redibujar
                console.log('🧹 Limpiando canvas de heatmap, marcadores y zona...');
                heatmapCtx.clearRect(0, 0, heatmapCanvas.width, heatmapCanvas.height);
                markersCtx.clearRect(0, 0, markersCanvas.width, markersCanvas.height);
                zoneCtx.clearRect(0, 0, zoneCanvas.width, zoneCanvas.height);
                
                console.log('Spectral Clustering desactivado completamente');
                updateVisualization();
            }} else {{
                // Activar Spectral (desactivar K-Means si está activo)
                if (clusteringActive && clusteringMethod === 'kmeans') {{
                    btnKmeans.textContent = '🔬 K-Means (K óptimo)';
                    btnKmeans.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)';
                }}
                clusteringActive = true;
                clusteringMethod = 'spectral';
                btnSpectral.textContent = '❌ Desactivar Spectral';
                btnSpectral.style.background = 'linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)';
                runSpectralClustering();
            }}
        }}
        
        function runKMeansClustering() {{
            const data = filterByMarkerType(filterData());
            
            if (data.length < 2) {{
                alert('No hay suficientes freekicks para clustering.');
                return;
            }}
            
            // Limpiar clustering anterior ANTES de comenzar
            clusterAssignments = null;
            clusterCenters = null;
            selectedCluster = null;
            centroidVisible = false;
            visibleCentroidClusterId = null;
            
            console.log('🔍 Optimizando K automáticamente sobre ' + data.length + ' freekicks (K-Means)...');
            
            // Preparar datos para clustering: [x_rematador, y_rematador, angulo, distancia]
            const points = data.map(d => [
                d.desmarque_x || 0,
                d.desmarque_y || 0,
                d.desmarque_angulo || 0,
                d.desmarque_distancia || 0
            ]);
            
            // Normalizar datos (estandarización)
            const normalized = normalizeData(points);
            
            // Usar los mismos datos normalizados para buscar K
            const k = findOptimalKClustered(normalized.data, data, 'kmeans');
            console.log('K optimo encontrado: ' + k);
            
            // Ejecutar K-means con los datos normalizados
            const result = kmeans(normalized.data, k);
            clusterAssignments = result.assignments;
            
            // Calcular centroides CORRECTAMENTE usando posiciones inicio y fin
            clusterCenters = [];
            for (let c = 0; c < k; c++) {{
                const clusterData = data.filter((d, i) => clusterAssignments[i] === c);
                
                if (clusterData.length === 0) {{
                    clusterCenters.push([0, 0, 0, 0]);
                    continue;
                }}
                
                // Calcular promedio de posiciones INICIALES
                let sum_x_inicio = 0;
                let sum_y_inicio = 0;
                
                // Calcular promedio de posiciones FINALES
                let sum_x_fin = 0;
                let sum_y_fin = 0;
                
                for (let d of clusterData) {{
                    // Posición inicial
                    sum_x_inicio += (d.desmarque_x || 0);
                    sum_y_inicio += (d.desmarque_y || 0);
                    
                    // Posición final (primer_remate o endX)
                    const x_fin = (d.num_remates_30s > 0 && d.primer_remate_x) ? d.primer_remate_x : (d.endX || 0);
                    const y_fin = (d.num_remates_30s > 0 && d.primer_remate_y) ? d.primer_remate_y : (d.endY || 0);
                    
                    sum_x_fin += x_fin;
                    sum_y_fin += y_fin;
                }}
                
                const n = clusterData.length;
                const centroid_x_inicio = sum_x_inicio / n;
                const centroid_y_inicio = sum_y_inicio / n;
                const centroid_x_fin = sum_x_fin / n;
                const centroid_y_fin = sum_y_fin / n;
                
                // Calcular vector ENTRE los centroides de inicio y fin
                const dx_opta = centroid_x_fin - centroid_x_inicio;
                const dy_opta = centroid_y_fin - centroid_y_inicio;
                
                // Convertir a metros para calcular distancia y ángulo
                const dx_metros = dx_opta * 1.05;
                const dy_metros = dy_opta * 0.68;
                
                const distancia = Math.sqrt(dx_metros * dx_metros + dy_metros * dy_metros);
                const angulo = Math.atan2(dy_metros, dx_metros) * 180 / Math.PI;
                
                clusterCenters.push([centroid_x_inicio, centroid_y_inicio, angulo, distancia]);
            }}
            
            console.log('✅ Clustering completado. Clusters:', clusterCenters.length);
            console.log('📍 Centroides recalculados con posiciones promedio de inicio y fin');
            
            // Calcular y mostrar Silhouette Score
            const silhouette = calculateSilhouetteScore(normalized.data, clusterAssignments, k);
            console.log('📊 Silhouette Score: ' + silhouette.toFixed(3) + ' (cuanto más cerca de 1, mejor)');
            
            // Resincronizar canvas ANTES de redibujar
            resizeCanvases();
            
            // Redibujar con colores de cluster
            updateVisualization();
            
            // Generar tabla de clusters
            generateClusterTable(data, k);
        }}
        
        function runSpectralClustering() {{
            const data = filterByMarkerType(filterData());
            
            if (data.length < 2) {{
                alert('No hay suficientes freekicks para clustering.');
                return;
            }}
            
            // Limpiar clustering anterior ANTES de comenzar
            clusterAssignments = null;
            clusterCenters = null;
            selectedCluster = null;
            centroidVisible = false;
            visibleCentroidClusterId = null;
            
            // Mostrar mensaje de procesamiento
            document.getElementById('clusterTableContainer').style.display = 'block';
            document.getElementById('clusterTableBody').innerHTML = '<tr><td colspan="10" style="text-align:center; padding:20px;"><strong>Procesando Spectral Clustering (' + data.length + ' datos filtrados)... Por favor espera</strong></td></tr>';
            
            // Usar TODOS los datos filtrados (no limitado a 5000)
            // Esto asegura que K se calcula y aplica sobre el MISMO dataset
            console.log('Optimizando K automáticamente sobre ' + data.length + ' freekicks de los datos filtrados (Spectral)...');
            const k = findOptimalK(data, 'spectral');
            console.log('✨ K óptimo encontrado: ' + k);
            
            // Preparar datos para clustering: [x_rematador, y_rematador, angulo, distancia]
            const points = data.map(d => [
                d.desmarque_x || 0,
                d.desmarque_y || 0,
                d.desmarque_angulo || 0,
                d.desmarque_distancia || 0
            ]);
            
            // Normalizar datos (estandarización)
            const normalized = normalizeData(points);
            
            // Ejecutar Spectral Clustering
            const result = spectralClustering(normalized.data, k);
            clusterAssignments = result.assignments;
            
            // Calcular centroides CORRECTAMENTE usando posiciones inicio y fin
            clusterCenters = [];
            for (let c = 0; c < k; c++) {{
                const clusterData = data.filter((d, i) => clusterAssignments[i] === c);
                
                if (clusterData.length === 0) {{
                    clusterCenters.push([0, 0, 0, 0]);
                    continue;
                }}
                
                // Calcular promedio de posiciones INICIALES
                let sum_x_inicio = 0;
                let sum_y_inicio = 0;
                
                // Calcular promedio de posiciones FINALES
                let sum_x_fin = 0;
                let sum_y_fin = 0;
                
                for (let d of clusterData) {{
                    // Posición inicial
                    sum_x_inicio += (d.desmarque_x || 0);
                    sum_y_inicio += (d.desmarque_y || 0);
                    
                    // Posición final (primer_remate o endX)
                    const x_fin = (d.num_remates_30s > 0 && d.primer_remate_x) ? d.primer_remate_x : (d.endX || 0);
                    const y_fin = (d.num_remates_30s > 0 && d.primer_remate_y) ? d.primer_remate_y : (d.endY || 0);
                    
                    sum_x_fin += x_fin;
                    sum_y_fin += y_fin;
                }}
                
                const n = clusterData.length;
                const centroid_x_inicio = sum_x_inicio / n;
                const centroid_y_inicio = sum_y_inicio / n;
                const centroid_x_fin = sum_x_fin / n;
                const centroid_y_fin = sum_y_fin / n;
                
                // Calcular vector ENTRE los centroides de inicio y fin
                const dx_opta = centroid_x_fin - centroid_x_inicio;
                const dy_opta = centroid_y_fin - centroid_y_inicio;
                
                // Convertir a metros para calcular distancia y ángulo
                const dx_metros = dx_opta * 1.05;
                const dy_metros = dy_opta * 0.68;
                
                const distancia = Math.sqrt(dx_metros * dx_metros + dy_metros * dy_metros);
                const angulo = Math.atan2(dy_metros, dx_metros) * 180 / Math.PI;
                
                clusterCenters.push([centroid_x_inicio, centroid_y_inicio, angulo, distancia]);
            }}
            
            console.log('✅ Spectral Clustering completado. Clusters:', k);
            console.log('📍 Centroides recalculados con posiciones promedio de inicio y fin');
            
            // Calcular y mostrar Silhouette Score
            const silhouette = calculateSilhouetteScore(normalized.data, clusterAssignments, k);
            console.log('📊 Silhouette Score: ' + silhouette.toFixed(3) + ' (cuanto más cerca de 1, mejor)');
            
            // Resincronizar canvas ANTES de redibujar
            resizeCanvases();
            
            // Redibujar con colores de cluster
            updateVisualization();
            
            // Generar tabla de clusters
            generateClusterTable(data, k);
        }}
        
        function generateClusterTable(data, k) {{
            // Calcular estadísticas por cluster
            const clusterStats = [];
            
            for (let c = 0; c < k; c++) {{
                const clusterData = data.filter((d, i) => clusterAssignments[i] === c);
                
                if (clusterData.length === 0) continue;
                
                const xgot = clusterData.reduce((sum, d) => sum + (d.xGoT_acumulado_30s || 0), 0);
                const xg = clusterData.reduce((sum, d) => sum + (d.xG_acumulado_30s || 0), 0);
                const goles = clusterData.filter(d => d.primer_remate_gol === true || d.primer_remate_gol === 1).length;
                
                // Calcular medias de desmarque
                const desmarqueXSum = clusterData.reduce((sum, d) => sum + (d.desmarque_x || 0), 0);
                const desmarqueYSum = clusterData.reduce((sum, d) => sum + (d.desmarque_y || 0), 0);
                const desmarqueDistanciaSum = clusterData.reduce((sum, d) => sum + (d.desmarque_distancia || 0), 0);
                
                // Promedio circular para ángulo (en grados, 0 a 360)
                const desmarqueAnguloRadians = clusterData
                    .map(d => (d.desmarque_angulo || 0) * Math.PI / 180)
                    .filter(d => d !== 0); // Excluir valores faltantes (0 por defecto)
                const sumSin = desmarqueAnguloRadians.reduce((sum, r) => sum + Math.sin(r), 0);
                const sumCos = desmarqueAnguloRadians.reduce((sum, r) => sum + Math.cos(r), 0);
                const mediaDesmarqueAngulo = ((Math.atan2(sumSin, sumCos) * 180 / Math.PI) + 360) % 360;
                
                const mediaDesmarqueX = desmarqueXSum / clusterData.length;
                const mediaDesmarqueY = desmarqueYSum / clusterData.length;
                const mediaDesmarqueDistancia = desmarqueDistanciaSum / clusterData.length;
                
                clusterStats.push({{
                    id: c,
                    count: clusterData.length,
                    xgot: xgot,
                    xg: xg,
                    goles: goles,
                    xgotAcc: xgot / clusterData.length,
                    xgAcc: xg / clusterData.length,
                    pctGoles: (goles / clusterData.length) * 100,
                    mediaDesmarqueX: mediaDesmarqueX,
                    mediaDesmarqueY: mediaDesmarqueY,
                    mediaDesmarqueAngulo: mediaDesmarqueAngulo,
                    mediaDesmarqueDistancia: mediaDesmarqueDistancia
                }});
            }}
            
            // Ordenar por xGoT/acción (descendente)
            clusterStats.sort((a, b) => b.xgotAcc - a.xgotAcc);
            
            // Generar HTML de la tabla
            const tbody = document.getElementById('clusterTableBody');
            tbody.innerHTML = '';
            
            clusterStats.forEach(stat => {{
                const row = document.createElement('tr');
                row.dataset.cluster = stat.id;
                row.onclick = () => selectCluster(stat.id);
                
                const color = CLUSTER_COLORS[stat.id % CLUSTER_COLORS.length];
                
                row.innerHTML = `
                    <td class="cluster-color-cell">
                        <div class="cluster-color-box" style="background-color: ${{color}};"></div>
                    </td>
                    <td class="cluster-id-cell">${{stat.id + 1}}</td>
                    <td>${{stat.count}}</td>
                    <td class="cluster-metric-cell">${{stat.xgotAcc.toFixed(4)}}</td>
                    <td>${{stat.xgAcc.toFixed(4)}}</td>
                    <td>${{stat.xgot.toFixed(3)}}</td>
                    <td>${{stat.xg.toFixed(3)}}</td>
                    <td>${{stat.goles}}</td>
                    <td>${{stat.pctGoles.toFixed(1)}}%</td>
                    <td>${{stat.mediaDesmarqueX.toFixed(2)}}</td>
                    <td>${{stat.mediaDesmarqueY.toFixed(2)}}</td>
                    <td>${{stat.mediaDesmarqueAngulo.toFixed(1)}}°</td>
                    <td>${{stat.mediaDesmarqueDistancia.toFixed(2)}}</td>
                    <td>
                        <button 
                            onclick="event.stopPropagation(); toggleCentroidView(${{stat.id}});" 
                            class="btn-centroid" 
                            id="btnCentroid${{stat.id}}"
                            style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">
                            👁️ Ver
                        </button>
                    </td>
                `;
                
                tbody.appendChild(row);
            }});
            
            // Mostrar la tabla
            document.getElementById('clusterTableContainer').style.display = 'block';
            console.log('📊 Tabla de clusters generada con ' + k + ' clusters');
            
            // IMPORTANTE: Redimensionar canvas cuando la tabla aparece (cambia tamaño del pitch)
            setTimeout(() => resizeCanvases(), 50);
        }}
        
        function selectCluster(clusterId) {{
            // Toggle selection
            if (selectedCluster === clusterId) {{
                selectedCluster = null;
                console.log('🔓 Cluster deseleccionado');
            }} else {{
                selectedCluster = clusterId;
                console.log('🔒 Cluster ' + (clusterId + 1) + ' seleccionado');
            }}
            
            // Actualizar estilos de la tabla
            document.querySelectorAll('.cluster-table tbody tr').forEach(row => {{
                row.classList.remove('selected');
            }});
            
            if (selectedCluster !== null) {{
                const selectedRow = document.querySelector(`tr[data-cluster="${{selectedCluster}}"]`);
                if (selectedRow) {{
                    selectedRow.classList.add('selected');
                }}
            }}
            
            // Redibujar visualización
            updateVisualization();
        }}
        
        function toggleCentroidView(clusterId) {{
            // Toggle: si ya está visible este centroide, ocultarlo
            if (centroidVisible && visibleCentroidClusterId === clusterId) {{
                centroidVisible = false;
                visibleCentroidClusterId = null;
                console.log('👁️ Centroide ocultado');
                
                // Restaurar texto de todos los botones
                document.querySelectorAll('.btn-centroid').forEach(btn => {{
                    btn.textContent = '👁️ Ver';
                    btn.style.background = 'linear-gradient(135deg, #3498db 0%, #2980b9 100%)';
                }});
            }} else {{
                centroidVisible = true;
                visibleCentroidClusterId = clusterId;
                console.log('👁️ Mostrando centroide del cluster ' + (clusterId + 1));
                
                // Actualizar botones
                document.querySelectorAll('.btn-centroid').forEach(btn => {{
                    btn.textContent = '👁️ Ver';
                    btn.style.background = 'linear-gradient(135deg, #3498db 0%, #2980b9 100%)';
                }});
                
                const activeBtn = document.getElementById('btnCentroid' + clusterId);
                if (activeBtn) {{
                    activeBtn.textContent = '✖️ Ocultar';
                    activeBtn.style.background = 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)';
                }}
            }}
            
            // Redibujar visualización
            updateVisualization();
        }}
        
        // Funcion auxiliar: encontrar K optimo con datos ya normalizados (para K-Means)
        function findOptimalKClustered(normalizedData, originalData, method='kmeans', minK=2) {{
            let maxK;
            if (normalizedData.length < 50) {{
                maxK = 2;
            }} else if (normalizedData.length < 100) {{
                maxK = 3;
            }} else if (normalizedData.length < 500) {{
                maxK = 5;
            }} else if (normalizedData.length < 2000) {{
                maxK = 7;
            }} else {{
                maxK = 10;
            }}
            
            const maxKActual = Math.min(maxK, Math.floor(normalizedData.length / 3));
            
            if (method === 'kmeans') {{
                console.log('K-MEANS: Seleccion por Silhouette Score');
                console.log('Probando K=2-' + maxKActual + '...');
                
                let bestK = minK;
                let bestScore = -1;
                for (let k = minK; k <= maxKActual; k++) {{
                    const result = kmeans(normalizedData, k);
                    const score = calculateSilhouetteScore(normalizedData, result.assignments, k);
                    console.log('   K=' + k + ': Silhouette=' + score.toFixed(3));
                    
                    if (score > bestScore) {{
                        bestScore = score;
                        bestK = k;
                    }}
                }}
                
                console.log('Mejor K: ' + bestK + ' (Silhouette: ' + bestScore.toFixed(3) + ')');
                return bestK;
            }}
            
            return minK;
        }}
        
        function findOptimalK(data, method='kmeans', minK=2) {{
            // Preparar datos: [x_desmarque, y_desmarque, angulo, distancia]
            const points = data.map(d => [
                d.desmarque_x || 0,
                d.desmarque_y || 0,
                d.desmarque_angulo || 0,
                d.desmarque_distancia || 0
            ]);
            
            const normalized = normalizeData(points);
            
            // Límites inteligentes de K según tamaño de datos
            let maxK;
            if (data.length < 50) {{
                maxK = 2;
            }} else if (data.length < 100) {{
                maxK = 3;
            }} else if (data.length < 500) {{
                maxK = 5;
            }} else if (data.length < 2000) {{
                maxK = 7;
            }} else {{
                maxK = 10;
            }}
            
            const maxKActual = Math.min(maxK, Math.floor(data.length / 3));
            
            if (method === 'spectral') {{
                console.log('   🎯 SPECTRAL CLUSTERING: Selección por Eigengap');
                console.log('   ⚡ Calculando Eigengap para K=2-' + maxKActual + '...');
                
                // PASO 1: Calcular eigengaps para todos los K
                const gamma = 1.0;
                const n = normalized.data.length;
                const affinity = Array(n).fill(null).map(() => Array(n).fill(0));
                
                for (let i = 0; i < n; i++) {{
                    for (let j = i; j < n; j++) {{
                        if (i === j) {{
                            affinity[i][j] = 1.0;
                        }} else {{
                            const dist = euclideanDistance(normalized.data[i], normalized.data[j]);
                            const sim = Math.exp(-gamma * dist * dist);
                            affinity[i][j] = sim;
                            affinity[j][i] = sim;
                        }}
                    }}
                }}
                
                const degree = Array(n).fill(0);
                for (let i = 0; i < n; i++) {{
                    degree[i] = affinity[i].reduce((sum, val) => sum + val, 0);
                }}
                
                const laplacian = Array(n).fill(null).map(() => Array(n).fill(0));
                for (let i = 0; i < n; i++) {{
                    const d_i_sqrt = Math.sqrt(degree[i]);
                    for (let j = 0; j < n; j++) {{
                        const d_j_sqrt = Math.sqrt(degree[j]);
                        if (i === j) {{
                            laplacian[i][j] = 1.0 - (affinity[i][j] / (d_i_sqrt * d_j_sqrt));
                        }} else {{
                            laplacian[i][j] = -(affinity[i][j] / (d_i_sqrt * d_j_sqrt));
                        }}
                    }}
                }}
                
                const eigenvalues = approximateEigenvalues(laplacian, maxKActual + 1);
                
                // PASO 2: Calcular eigengaps y elegir el K con mayor eigengap
                let bestK = minK;
                let maxGap = 0;
                
                console.log('   📊 Eigengaps calculados:');
                for (let k = minK; k <= maxKActual; k++) {{
                    const gap = Math.abs(eigenvalues[k] - eigenvalues[k-1]);
                    console.log('   K=' + k + ': Eigengap=' + gap.toFixed(4));
                    
                    if (gap > maxGap) {{
                        maxGap = gap;
                        bestK = k;
                    }}
                }}
                
                console.log('   🏆 Mejor K por Eigengap: ' + bestK + ' (Gap=' + maxGap.toFixed(4) + ')');
                return bestK;
            }} else {{
                // K-Means: usar Silhouette Score
                console.log('   Probando K desde ' + minK + ' hasta ' + maxKActual + '...');
                
                let bestK = minK;
                let bestScore = -1;
                for (let k = minK; k <= maxKActual; k++) {{
                    const result = kmeans(normalized.data, k);
                    const score = calculateSilhouetteScore(normalized.data, result.assignments, k);
                    console.log('   K=' + k + ': Silhouette=' + score.toFixed(3));
                    
                    if (score > bestScore) {{
                        bestScore = score;
                        bestK = k;
                    }}
                }}
                
                console.log('   🏆 Mejor K: ' + bestK + ' (Silhouette: ' + bestScore.toFixed(3) + ')');
                return bestK;
            }}
        }}
        
        function calculateSilhouetteScore(points, labels, k) {{
            if (k === 1 || points.length < 2) return 0;
            
            // Agrupar puntos por cluster
            const clusters = Array.from({{ length: k }}, () => []);
            points.forEach((point, i) => {{
                clusters[labels[i]].push({{ point: point, index: i }});
            }});
            
            let totalSilhouette = 0;
            let validPoints = 0;
            
            points.forEach((point, i) => {{
                const ownCluster = labels[i];
                const ownSize = clusters[ownCluster].length;
                
                if (ownSize === 1) return; // Skip singleton clusters
                
                // a(i): distancia promedio a puntos en mismo cluster
                let a = 0;
                clusters[ownCluster].forEach(item => {{
                    if (item.index !== i) {{
                        a += euclideanDistance(point, item.point);
                    }}
                }});
                a /= (ownSize - 1);
                
                // b(i): distancia promedio al cluster más cercano
                let b = Infinity;
                for (let c = 0; c < k; c++) {{
                    if (c === ownCluster || clusters[c].length === 0) continue;
                    
                    let dist = 0;
                    clusters[c].forEach(item => {{
                        dist += euclideanDistance(point, item.point);
                    }});
                    dist /= clusters[c].length;
                    
                    b = Math.min(b, dist);
                }}
                
                // Silhouette para este punto
                const s = (b - a) / Math.max(a, b);
                totalSilhouette += s;
                validPoints++;
            }});
            
            return validPoints > 0 ? totalSilhouette / validPoints : 0;
        }}
        
        function calculateARI(labels1, labels2) {{
            // Adjusted Rand Index: mide similaridad entre dos asignaciones de clusters
            // Rango: [-1, 1] donde 1 = coincidencia perfecta, 0 = random, -1 = total desacuerdo
            const n = labels1.length;
            if (n !== labels2.length || n === 0) return -1;
            
            // Contar pares de puntos en mismo cluster en ambas asignaciones
            let sameInBoth = 0;  // TP (True Positives)
            let sameIn1 = 0;     // Pares en mismo cluster en labels1
            let sameIn2 = 0;     // Pares en mismo cluster en labels2
            
            for (let i = 0; i < n; i++) {{
                for (let j = i + 1; j < n; j++) {{
                    const sameCluster1 = labels1[i] === labels1[j];
                    const sameCluster2 = labels2[i] === labels2[j];
                    
                    if (sameCluster1) sameIn1++;
                    if (sameCluster2) sameIn2++;
                    if (sameCluster1 && sameCluster2) sameInBoth++;
                }}
            }}
            
            const totalPairs = n * (n - 1) / 2;
            const expectedAgreement = (sameIn1 * sameIn2) / totalPairs;
            const maxAgreement = (sameIn1 + sameIn2) / 2;
            
            if (maxAgreement === expectedAgreement) return 1.0;
            
            const ari = (sameInBoth - expectedAgreement) / (maxAgreement - expectedAgreement);
            return Math.max(-1, Math.min(1, ari));
        }}
        
        function calculateCalinskyHarabasz(points, labels, k) {{
            // Calinski-Harabasz Index (Variance Ratio Criterion)
            // Mayor valor = mejor separación. Rango: [0, ∞)
            // Formula: (SS_B / SS_W) * ((n - k) / (k - 1))
            // SS_B: suma de cuadrados entre clusters
            // SS_W: suma de cuadrados dentro de clusters
            
            const n = points.length;
            const d = points[0].length;
            
            if (k === 1 || k === n) return 0;
            
            // Calcular centroide global
            const globalCentroid = new Array(d).fill(0);
            points.forEach(point => {{
                point.forEach((val, i) => {{
                    globalCentroid[i] += val;
                }});
            }});
            globalCentroid.forEach((_, i) => {{
                globalCentroid[i] /= n;
            }});
            
            // Agrupar puntos por cluster
            const clusters = Array.from({{ length: k }}, () => []);
            points.forEach((point, i) => {{
                clusters[labels[i]].push(point);
            }});
            
            // Calcular SS_W (suma cuadrados dentro)
            let ssWithin = 0;
            for (let c = 0; c < k; c++) {{
                if (clusters[c].length === 0) continue;
                
                const clusterCentroid = new Array(d).fill(0);
                clusters[c].forEach(point => {{
                    point.forEach((val, i) => {{
                        clusterCentroid[i] += val;
                    }});
                }});
                clusterCentroid.forEach((_, i) => {{
                    clusterCentroid[i] /= clusters[c].length;
                }});
                
                clusters[c].forEach(point => {{
                    const dist = euclideanDistance(point, clusterCentroid);
                    ssWithin += dist * dist;
                }});
            }}
            
            // Calcular SS_B (suma cuadrados entre)
            let ssBetween = 0;
            for (let c = 0; c < k; c++) {{
                if (clusters[c].length === 0) continue;
                
                const clusterCentroid = new Array(d).fill(0);
                clusters[c].forEach(point => {{
                    point.forEach((val, i) => {{
                        clusterCentroid[i] += val;
                    }});
                }});
                clusterCentroid.forEach((_, i) => {{
                    clusterCentroid[i] /= clusters[c].length;
                }});
                
                const distToCentroid = euclideanDistance(clusterCentroid, globalCentroid);
                ssBetween += clusters[c].length * distToCentroid * distToCentroid;
            }}
            
            if (ssWithin === 0) return 0;
            return (ssBetween / ssWithin) * ((n - k) / (k - 1));
        }}
        
        function calculateDaviesBouldin(points, labels, k) {{
            // Davies-Bouldin Index: mide separación y compacidad
            // Menor valor = mejor clustering. Rango: [0, ∞)
            // Formula: promedio de (max(R_ij)) para cada cluster i
            // R_ij = (S_i + S_j) / d_ij
            
            const n = points.length;
            const d = points[0].length;
            
            if (k === 1) return 0;
            
            // Agrupar puntos por cluster
            const clusters = Array.from({{ length: k }}, () => []);
            points.forEach((point, i) => {{
                clusters[labels[i]].push(point);
            }});
            
            // Calcular centroides y S_i (radio promedio de cada cluster)
            const centroids = [];
            const radii = [];
            
            for (let c = 0; c < k; c++) {{
                if (clusters[c].length === 0) {{
                    centroids.push(new Array(d).fill(0));
                    radii.push(0);
                    continue;
                }}
                
                const centroid = new Array(d).fill(0);
                clusters[c].forEach(point => {{
                    point.forEach((val, i) => {{
                        centroid[i] += val;
                    }});
                }});
                centroid.forEach((_, i) => {{
                    centroid[i] /= clusters[c].length;
                }});
                centroids.push(centroid);
                
                // S_i: distancia promedio dentro del cluster
                let radius = 0;
                clusters[c].forEach(point => {{
                    radius += euclideanDistance(point, centroid);
                }});
                radius /= clusters[c].length;
                radii.push(radius);
            }}
            
            // Calcular DB index
            let dbIndex = 0;
            for (let i = 0; i < k; i++) {{
                let maxR = 0;
                for (let j = 0; j < k; j++) {{
                    if (i === j) continue;
                    
                    const distCentroids = euclideanDistance(centroids[i], centroids[j]);
                    if (distCentroids === 0) continue;
                    
                    const R_ij = (radii[i] + radii[j]) / distCentroids;
                    maxR = Math.max(maxR, R_ij);
                }}
                dbIndex += maxR;
            }}
            
            return dbIndex / k;
        }}
        
        function normalizeData(data) {{
            const numFeatures = data[0].length;
            const mean = new Array(numFeatures).fill(0);
            const std = new Array(numFeatures).fill(0);
            
            // Calcular media
            data.forEach(point => {{
                point.forEach((val, i) => {{
                    mean[i] += val;
                }});
            }});
            mean.forEach((val, i) => {{
                mean[i] = val / data.length;
            }});
            
            // Calcular desviación estándar
            data.forEach(point => {{
                point.forEach((val, i) => {{
                    std[i] += Math.pow(val - mean[i], 2);
                }});
            }});
            std.forEach((val, i) => {{
                std[i] = Math.sqrt(val / data.length) || 1; // Evitar división por 0
            }});
            
            // Normalizar
            const normalized = data.map(point =>
                point.map((val, i) => (val - mean[i]) / std[i])
            );
            
            return {{ data: normalized, mean: mean, std: std }};
        }}
        
        function kmeans(points, k, maxIterations = 100) {{
            // Inicializar centroides aleatoriamente (k-means++)
            let centroids = initializeCentroidsKMeansPlusPlus(points, k);
            let assignments = new Array(points.length);
            let changed = true;
            let iterations = 0;
            
            while (changed && iterations < maxIterations) {{
                changed = false;
                iterations++;
                
                // Asignar cada punto al centroide más cercano
                points.forEach((point, idx) => {{
                    const distances = centroids.map(centroid => euclideanDistance(point, centroid));
                    const closest = distances.indexOf(Math.min(...distances));
                    
                    if (assignments[idx] !== closest) {{
                        assignments[idx] = closest;
                        changed = true;
                    }}
                }});
                
                // Recalcular centroides
                const newCentroids = Array(k).fill(null).map(() => Array(points[0].length).fill(0));
                const counts = Array(k).fill(0);
                
                points.forEach((point, idx) => {{
                    const cluster = assignments[idx];
                    counts[cluster]++;
                    point.forEach((val, i) => {{
                        newCentroids[cluster][i] += val;
                    }});
                }});
                
                centroids = newCentroids.map((centroid, i) =>
                    counts[i] > 0 ? centroid.map(val => val / counts[i]) : centroid
                );
            }}
            
            console.log('K-means convergió en', iterations, 'iteraciones');
            return {{ centroids: centroids, assignments: assignments }};
        }}
        
        function initializeCentroidsKMeansPlusPlus(points, k) {{
            const centroids = [];
            
            // Primer centroide aleatorio
            centroids.push(points[Math.floor(Math.random() * points.length)]);
            
            // Seleccionar k-1 centroides restantes
            for (let i = 1; i < k; i++) {{
                const distances = points.map(point => {{
                    const minDist = Math.min(...centroids.map(c => euclideanDistance(point, c)));
                    return minDist * minDist;
                }});
                
                const sum = distances.reduce((a, b) => a + b, 0);
                const probabilities = distances.map(d => d / sum);
                
                // Selección ponderada
                const rand = Math.random();
                let cumulative = 0;
                let selectedIdx = 0;
                
                for (let j = 0; j < probabilities.length; j++) {{
                    cumulative += probabilities[j];
                    if (rand <= cumulative) {{
                        selectedIdx = j;
                        break;
                    }}
                }}
                
                centroids.push(points[selectedIdx]);
            }}
            
            return centroids;
        }}
        
        function euclideanDistance(p1, p2) {{
            return Math.sqrt(p1.reduce((sum, val, i) => sum + Math.pow(val - p2[i], 2), 0));
        }}
        
        function spectralClustering(points, k) {{
            const n = points.length;
            console.log('🌀 Iniciando Spectral Clustering con ' + n + ' puntos y k=' + k);
            
            // 1. Construir matriz de afinidad usando kernel RBF (Gaussian)
            const gamma = 1.0; // Parámetro del kernel (puede ajustarse)
            const affinity = Array(n).fill(null).map(() => Array(n).fill(0));
            
            console.log('   📐 Calculando matriz de afinidad...');
            for (let i = 0; i < n; i++) {{
                for (let j = i; j < n; j++) {{
                    if (i === j) {{
                        affinity[i][j] = 1.0;
                    }} else {{
                        const dist = euclideanDistance(points[i], points[j]);
                        const sim = Math.exp(-gamma * dist * dist);
                        affinity[i][j] = sim;
                        affinity[j][i] = sim;
                    }}
                }}
            }}
            
            // 2. Calcular matriz de grado D (diagonal)
            const degree = Array(n).fill(0);
            for (let i = 0; i < n; i++) {{
                degree[i] = affinity[i].reduce((sum, val) => sum + val, 0);
            }}
            
            // 3. Calcular Laplacian normalizado: L = D^(-1/2) * (D - W) * D^(-1/2)
            // Simplificado: L_norm = I - D^(-1/2) * W * D^(-1/2)
            console.log('   📐 Calculando Laplacian normalizado...');
            const laplacian = Array(n).fill(null).map(() => Array(n).fill(0));
            
            for (let i = 0; i < n; i++) {{
                const d_i_sqrt = Math.sqrt(degree[i]);
                for (let j = 0; j < n; j++) {{
                    const d_j_sqrt = Math.sqrt(degree[j]);
                    if (i === j) {{
                        laplacian[i][j] = 1.0 - (affinity[i][j] / (d_i_sqrt * d_j_sqrt));
                    }} else {{
                        laplacian[i][j] = -(affinity[i][j] / (d_i_sqrt * d_j_sqrt));
                    }}
                }}
            }}
            
            // 4. Calcular k eigenvectors más pequeños usando método de potencias inverso
            console.log('   📐 Calculando eigenvectors (aproximación)...');
            const eigenvectors = approximateEigenvectors(laplacian, k);
            
            // 5. Normalizar eigenvectors por filas
            const embeddings = Array(n).fill(null).map(() => Array(k).fill(0));
            for (let i = 0; i < n; i++) {{
                // Obtener fila i de todos los eigenvectors
                const row = eigenvectors.map(ev => ev[i]);
                const norm = Math.sqrt(row.reduce((sum, val) => sum + val * val, 0));
                for (let j = 0; j < k; j++) {{
                    embeddings[i][j] = row[j] / (norm || 1);
                }}
            }}
            
            // 6. Aplicar K-means sobre los embeddings
            console.log('   📐 Aplicando K-means sobre embeddings...');
            const result = kmeans(embeddings, k, 50); // Menos iteraciones
            
            return {{
                assignments: result.assignments,
                centroids: result.centroids
            }};
        }}
        
        function approximateEigenvectors(matrix, k, maxIterations=20) {{
            // Método simplificado para aproximar los k eigenvectors principales
            // Usa iteración de potencias con deflación
            const n = matrix.length;
            const eigenvectors = [];
            
            for (let ev = 0; ev < k; ev++) {{
                // Inicializar vector aleatorio
                let vector = Array(n).fill(0).map(() => Math.random() - 0.5);
                
                // Iterar para encontrar eigenvector dominante
                for (let iter = 0; iter < maxIterations; iter++) {{
                    // Multiplicar matriz por vector
                    const newVector = Array(n).fill(0);
                    for (let i = 0; i < n; i++) {{
                        for (let j = 0; j < n; j++) {{
                            newVector[i] += matrix[i][j] * vector[j];
                        }}
                    }}
                    
                    // Ortogonalizar contra eigenvectors anteriores
                    for (let prevEv of eigenvectors) {{
                        const dot = newVector.reduce((sum, val, i) => sum + val * prevEv[i], 0);
                        for (let i = 0; i < n; i++) {{
                            newVector[i] -= dot * prevEv[i];
                        }}
                    }}
                    
                    // Normalizar
                    const norm = Math.sqrt(newVector.reduce((sum, val) => sum + val * val, 0));
                    vector = newVector.map(v => v / (norm || 1));
                }}
                
                eigenvectors.push(vector);
            }}
            
            return eigenvectors;
        }}
        
        function approximateEigenvalues(matrix, k, maxIterations=30) {{
            // Calcular eigenvalores usando método de potencias
            const n = matrix.length;
            const eigenvalues = [];
            const eigenvectors = [];
            
            for (let ev = 0; ev < k; ev++) {{
                // Inicializar vector aleatorio
                let vector = Array(n).fill(0).map(() => Math.random() - 0.5);
                let eigenvalue = 0;
                
                // Iterar para encontrar eigenvector y eigenvalor dominante
                for (let iter = 0; iter < maxIterations; iter++) {{
                    // Multiplicar matriz por vector
                    const newVector = Array(n).fill(0);
                    for (let i = 0; i < n; i++) {{
                        for (let j = 0; j < n; j++) {{
                            newVector[i] += matrix[i][j] * vector[j];
                        }}
                    }}
                    
                    // Ortogonalizar contra eigenvectors anteriores
                    for (let prevEv of eigenvectors) {{
                        const dot = newVector.reduce((sum, val, i) => sum + val * prevEv[i], 0);
                        for (let i = 0; i < n; i++) {{
                            newVector[i] -= dot * prevEv[i];
                        }}
                    }}
                    
                    // Calcular norma antes de normalizar (aproximación del eigenvalor)
                    const norm = Math.sqrt(newVector.reduce((sum, val) => sum + val * val, 0));
                    eigenvalue = norm;
                    
                    // Normalizar
                    vector = newVector.map(v => v / (norm || 1));
                }}
                
                // Calcular eigenvalor más preciso: λ = v^T * A * v
                const Av = Array(n).fill(0);
                for (let i = 0; i < n; i++) {{
                    for (let j = 0; j < n; j++) {{
                        Av[i] += matrix[i][j] * vector[j];
                    }}
                }}
                eigenvalue = vector.reduce((sum, val, i) => sum + val * Av[i], 0);
                
                eigenvalues.push(eigenvalue);
                eigenvectors.push(vector);
            }}
            
            return eigenvalues;
        }}
        // ============= ACTUALIZAR ETIQUETAS DE SLIDERS =============
        function updateSliderLabels() {{
            document.getElementById('xMinVal').textContent = parseFloat(document.getElementById('xMin').value).toFixed(1);
            document.getElementById('xMaxVal').textContent = parseFloat(document.getElementById('xMax').value).toFixed(1);
            document.getElementById('yMinVal').textContent = parseFloat(document.getElementById('yMin').value).toFixed(1);
            document.getElementById('yMaxVal').textContent = parseFloat(document.getElementById('yMax').value).toFixed(1);
            document.getElementById('dlMinVal').textContent = parseFloat(document.getElementById('dlMin').value).toFixed(1);
            document.getElementById('dlMaxVal').textContent = parseFloat(document.getElementById('dlMax').value).toFixed(1);
            
            // Sincronizar inputs numéricos
            document.getElementById('xMinInput').value = parseFloat(document.getElementById('xMin').value).toFixed(1);
            document.getElementById('xMaxInput').value = parseFloat(document.getElementById('xMax').value).toFixed(1);
            document.getElementById('yMinInput').value = parseFloat(document.getElementById('yMin').value).toFixed(1);
            document.getElementById('yMaxInput').value = parseFloat(document.getElementById('yMax').value).toFixed(1);
            document.getElementById('dlMinInput').value = parseFloat(document.getElementById('dlMin').value).toFixed(1);
            document.getElementById('dlMaxInput').value = parseFloat(document.getElementById('dlMax').value).toFixed(1);
        }}
        
        // ============= EVENT LISTENERS =============
        // Sliders
        document.getElementById('xMin').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        document.getElementById('xMax').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        document.getElementById('yMin').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        document.getElementById('yMax').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        document.getElementById('dlMin').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        document.getElementById('dlMax').addEventListener('input', () => {{
            updateSliderLabels();
            updateVisualization();
        }});
        
        // Inputs numéricos manuales
        document.getElementById('xMinInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('xMin').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        document.getElementById('xMaxInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('xMax').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        document.getElementById('yMinInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('yMin').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        document.getElementById('yMaxInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('yMax').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        document.getElementById('dlMinInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('dlMin').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        document.getElementById('dlMaxInput').addEventListener('change', (e) => {{
            const val = parseFloat(e.target.value);
            if (!isNaN(val)) {{
                document.getElementById('dlMax').value = val;
                updateSliderLabels();
                updateVisualization();
            }}
        }});
        
        // Filtros
        document.getElementById('filterSeason').addEventListener('change', () => {{
            updateLeagueFilter();
            updateTeamFilter();
            updateVisualization();
        }});
        document.getElementById('filterLeague').addEventListener('change', () => {{
            updateTeamFilter();
            updateVisualization();
        }});
        document.getElementById('filterTeam').addEventListener('change', updateVisualization);
        document.getElementById('filterFKType').addEventListener('change', updateVisualization);
        document.getElementById('filterCrossType').addEventListener('change', updateVisualization);
        document.getElementById('outcomeSuccessful').addEventListener('change', updateVisualization);
        document.getElementById('outcomeUnsuccessful').addEventListener('change', updateVisualization);
        document.getElementById('desmarqueSi').addEventListener('change', updateVisualization);
        document.getElementById('desmarqueNo').addEventListener('change', updateVisualization);
        
        // Filtro de visualización de marcadores
        document.getElementById('filterMarkerType').addEventListener('change', updateVisualization);
        
        // ============= INICIALIZACIÓN =============
        // Seleccionar todas las opciones en los selects múltiples
        function selectAllOptions(selectId) {{
            const select = document.getElementById(selectId);
            for (let i = 0; i < select.options.length; i++) {{
                select.options[i].selected = true;
            }}
        }}
        
        selectAllOptions('filterSeason');
        updateLeagueFilter();  // Initialize league filter based on selected seasons
        selectAllOptions('filterFKType');
        selectAllOptions('filterCrossType');
        selectAllOptions('filterMarkerType');
        
        // Inicializar filtro de equipos
        updateTeamFilter();
        
        updateSliderLabels();
        
        // Esperar a que el SVG esté completamente renderizado
        setTimeout(() => {{
            console.log('🚀 Iniciando carga de visualización...');
            resizeCanvases();
            
            // Fijar altura del pitch para evitar que se expanda cuando aparezca la tabla
            const svg = pitchEl.querySelector('svg');
            if (svg) {{
                const rect = svg.getBoundingClientRect();
                const pitchWrapper = document.querySelector('.pitch-wrapper');
                if (pitchWrapper) {{
                    pitchWrapper.style.height = rect.height + 'px';
                    console.log('🔒 Altura del pitch fijada en', rect.height, 'px');
                }}
            }}
            
            console.log('✅ Visualización interactiva cargada');
            console.log(`📊 Total de freekicks: ${{allData.length}}`);
        }}, 300);
    </script>
</body>
</html>
"""
    
    # 7. Guardar HTML
    output_file = 'Outputs/interactive_freekicks_heatmap.html'
    os.makedirs('Outputs', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML generado exitosamente:")
    print(f"   📄 Archivo: {output_file}")
    print(f"   📊 Tamaño: {os.path.getsize(output_file) / 1024:.1f} KB")
    print(f"\n🌐 Abre el archivo en tu navegador para ver la visualización interactiva")
    print("="*80)


if __name__ == '__main__':
    generate_interactive_html()
