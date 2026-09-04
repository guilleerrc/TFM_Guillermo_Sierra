"""
Generador de Dataset Sintético para Freekicks
Filtra solo CROSSES, anonimiza jerárquicamente (Liga-Temporada-Equipo-Jugador)
y genera datos sintéticos preservando correlaciones con Copula + ruido espacial
"""

import pandas as pd
import numpy as np
import json
import hashlib
from scipy.stats import gaussian_kde, ks_2samp, wasserstein_distance, rankdata, norm
from scipy.special import erfinv
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("GENERADOR DE DATASET SINTÉTICO - FREEKICKS (SOLO CROSSES)")
print("="*80)

# ============================================================================
# 1. CARGAR Y FILTRAR DATOS
# ============================================================================
print("\n1️⃣ CARGANDO Y FILTRANDO DATOS...")
df = pd.read_csv('Outputs/freekicks_dataset.csv')
print(f"   ✓ Dataset original: {len(df):,} filas")

# Filtrar solo Crosses para anonimización, pero mantener el dataset completo para tipo_exito
df_crosses = df[df['freekick_type'] == 'Cross'].copy()
print(f"   ✓ Crosses filtrados: {len(df_crosses):,} filas (para anonimización)")

if len(df_crosses) == 0:
    print("❌ ERROR: No hay Crosses en el dataset")
    exit(1)

# Mapeo de tipo_exito: eventId + matchId -> tipo_exito desde dataset completo
# Usar combinación de claves para ser exactos en el merge
tipo_exito_map = df[['eventId', 'matchId', 'tipo_exito']].drop_duplicates(
    subset=['eventId', 'matchId'], keep='first'
)
print(f"   ✓ Mapeo de tipo_exito creado para {len(tipo_exito_map):,} combinaciones (eventId, matchId)")

# ============================================================================
# 2. CREAR MAPEO DE ANONIMIZACIÓN JERÁRQUICO
# ============================================================================
print("\n2️⃣ CREANDO MAPEO DE ANONIMIZACIÓN...")

# Crear mapeos
league_map = {}
team_map = {}
player_map = {}

league_counter = 0
team_counter_by_league = {}
player_counter_by_team = {}

for league in df_crosses['league'].unique():
    league_counter += 1
    league_id = f"League{league_counter}"
    league_map[league] = league_id
    team_counter_by_league[league_id] = 0
    
    # Equipos en esta liga
    teams_in_league = df_crosses[df_crosses['league'] == league]['TeamName'].unique()
    for team in teams_in_league:
        team_counter_by_league[league_id] += 1
        team_id = f"{league_id}_Team{team_counter_by_league[league_id]}"
        team_map[(league, team)] = team_id
        player_counter_by_team[team_id] = 0
        
        # Jugadores en este equipo
        players_in_team = df_crosses[
            (df_crosses['league'] == league) & 
            (df_crosses['TeamName'] == team)
        ]['jugador'].unique()
        
        for player in players_in_team:
            player_counter_by_team[team_id] += 1
            player_id = f"{team_id}_Player{player_counter_by_team[team_id]}"
            player_map[(league, team, player)] = player_id

print(f"   ✓ Ligas únicas: {len(league_map)}")
print(f"   ✓ Equipos totales: {len(team_map)}")
print(f"   ✓ Jugadores totales: {len(player_map)}")

# Aplicar anonimización
def anonimize_row(row):
    league = row['league']
    team = row['TeamName']
    player = row['jugador']
    
    league_id = league_map.get(league, 'UnknownLeague')
    team_id = team_map.get((league, team), f"{league_id}_UnknownTeam")
    player_id = player_map.get((league, team, player), f"{team_id}_UnknownPlayer")
    
    return league_id, team_id, player_id

df_crosses[['league_anon', 'TeamName_anon', 'jugador_anon']] = pd.DataFrame(
    [anonimize_row(row) for _, row in df_crosses.iterrows()],
    columns=['league_anon', 'TeamName_anon', 'jugador_anon'],
    index=df_crosses.index
)

# Equipo rival también anonimizar
def anonimize_rival(row):
    league = row['league']
    rival_team = row['TeamRival']
    rival_id = team_map.get((league, rival_team), 'UnknownRival')
    return rival_id

df_crosses['TeamRival_anon'] = df_crosses.apply(anonimize_rival, axis=1)

print("   ✓ Anonimización aplicada")

# ============================================================================
# 3. IDENTIFICAR VARIABLES NUMÉRICAS Y CATEGÓRICAS
# ============================================================================
print("\n3️⃣ IDENTIFICANDO VARIABLES...")

# Variables numéricas que sintetizaremos con Copula Gaussiana
# Solo las variables que funcionan bien (<25% diferencia)
numeric_vars_to_synthesize = [
    'x', 'y', 'endX', 'endY',
    'defensive_line_height', 'delta',
    'desmarque_x', 'desmarque_y'
]

# Variables que copiaremos del original (sin síntesis)
numeric_vars_original = [
    'primer_remate_x', 'primer_remate_y',
    'num_remates_30s', 'xG_acumulado_30s', 'xGoT_acumulado_30s', 'goles_30s',
    'primer_remate_xG', 'primer_remate_xGoT'
]

# Filtrar solo que existan
numeric_vars_to_synthesize = [v for v in numeric_vars_to_synthesize if v in df_crosses.columns]
numeric_vars_original = [v for v in numeric_vars_original if v in df_crosses.columns]

# Variables que se recalcularán (no se sintetizan directamente)
numeric_vars_derived = ['desmarque_distancia', 'desmarque_angulo']

print(f"   ✓ Variables a sintetizar con Copula: {len(numeric_vars_to_synthesize)}")
print(f"     {numeric_vars_to_synthesize}")
print(f"   ✓ Variables copiadas del original: {len(numeric_vars_original)}")
print(f"     {numeric_vars_original}")
print(f"   ✓ Variables derivadas (recalculadas): {len(numeric_vars_derived)}")
print(f"     {numeric_vars_derived}")

# ============================================================================
# 4. COPULA GAUSSIANA - GENERAR DATOS SINTÉTICOS (PASOS PUROS)
# ============================================================================
print(f"\n4️⃣ GENERANDO DATOS CON COPULA GAUSSIANA (PASOS PUROS)...")

# Seleccionar SOLO los datos numéricos que sintetizaremos
df_numeric = df_crosses[numeric_vars_to_synthesize].copy()

# Reemplazar NaN con mediana
for col in numeric_vars_to_synthesize:
    median_val = df_numeric[col].median()
    df_numeric[col].fillna(median_val, inplace=True)

print(f"   ✓ Matriz numérica: {df_numeric.shape}")

# ============================================================================
# PASO 1: CDF EMPÍRICA
# ============================================================================
print(f"\n   PASO 1️⃣: Calculando CDF empírica...")

# Para cada variable, calcular U_j = F̂(X_j) ∈ (0,1)
df_uniform = pd.DataFrame(index=df_numeric.index)

for col in numeric_vars_to_synthesize:
    # rankdata devuelve el rango de cada valor (1 a n)
    # Normalizamos a (0,1) usando la fórmula: rank / (n+1)
    ranks = rankdata(df_numeric[col].values)
    n = len(df_numeric[col])
    df_uniform[col] = ranks / (n + 1)

print(f"   ✓ CDF empírica calculada: U_j ∈ (0,1)")

# ============================================================================
# PASO 2: TRANSFORMACIÓN AL ESPACIO GAUSSIANO
# ============================================================================
print(f"\n   PASO 2️⃣: Transformando a espacio gaussiano...")

# Para cada variable, calcular Z_j = Φ⁻¹(U_j) ~ N(0,1)
df_normal = pd.DataFrame(index=df_uniform.index)

for col in numeric_vars_to_synthesize:
    # norm.ppf es Φ⁻¹ (inverse CDF de normal estándar)
    df_normal[col] = norm.ppf(df_uniform[col].values)

print(f"   ✓ Variables transformadas a N(0,1): Z_j = Φ⁻¹(U_j)")

# ============================================================================
# PASO 3: ESTIMACIÓN DE MATRIZ DE CORRELACIÓN
# ============================================================================
print(f"\n   PASO 3️⃣: Estimando matriz de correlación...")

# Σ = Corr(Z_1, ..., Z_p)
# Esta es la correlación de Spearman de los datos originales
correlation_matrix = df_normal.corr().fillna(0)

print(f"   ✓ Matriz de correlación (Spearman): {len(numeric_vars_to_synthesize)}×{len(numeric_vars_to_synthesize)}")
print(f"     Diagonal: {np.diag(correlation_matrix).round(3).tolist()}")

# ============================================================================
# PASO 4: DESCOMPOSICIÓN DE CHOLESKY
# ============================================================================
print(f"\n   PASO 4️⃣: Descomposición de Cholesky...")

# Σ = L L^T
try:
    L = np.linalg.cholesky(correlation_matrix)
    print(f"   ✓ Cholesky exitoso (matriz positiva definida)")
except np.linalg.LinAlgError:
    print(f"   ⚠️ Matriz singular, usando eigendecomposición...")
    eigvals, eigvecs = np.linalg.eigh(correlation_matrix)
    eigvals[eigvals < 1e-10] = 0
    L = eigvecs @ np.diag(np.sqrt(eigvals))

# ============================================================================
# PASO 5: GENERACIÓN DE DATOS NORMALES CORRELACIONADOS
# ============================================================================
print(f"\n   PASO 5️⃣: Generando datos normales correlacionados...")

# ε ~ N(0,I)
np.random.seed(42)
n_samples = len(df_crosses)
epsilon = np.random.randn(n_samples, len(numeric_vars_to_synthesize))

# Z_new = ε L^T, así Z_new ~ N(0, Σ)
Z_new = epsilon @ L.T

print(f"   ✓ {n_samples} muestras generadas: Z_new ~ N(0, Σ)")

# ============================================================================
# PASO 6: VOLVER AL ESPACIO UNIFORME
# ============================================================================
print(f"\n   PASO 6️⃣: Transformando al espacio uniforme...")

# U_new,j = Φ(Z_new,j)
df_uniform_new = pd.DataFrame(index=df_normal.index)

for i, col in enumerate(numeric_vars_to_synthesize):
    # norm.cdf es Φ (CDF de normal estándar)
    df_uniform_new[col] = norm.cdf(Z_new[:, i])

print(f"   ✓ Datos transformados al espacio uniforme: U_new ∈ (0,1)")

# ============================================================================
# PASO 7: VOLVER A DISTRIBUCIONES MARGINALES ORIGINALES
# ============================================================================
print(f"\n   PASO 7️⃣: Volviendo a distribuciones marginales originales...")

# X_new,j = F̂^(-1)(U_new,j) usando cuantiles de datos originales
df_synthetic = pd.DataFrame(index=df_crosses.index)

for col in numeric_vars_to_synthesize:
    # Obtener los valores originales ordenados
    original_values = df_numeric[col].values
    original_sorted = np.sort(original_values)
    
    # Para cada U_new, encontrar el cuantil correspondiente
    # Si U_new = 0.75, buscar el valor al 75º percentil
    quantile_indices = (df_uniform_new[col].values * (len(original_sorted) - 1)).astype(int)
    quantile_indices = np.clip(quantile_indices, 0, len(original_sorted) - 1)
    
    df_synthetic[col] = original_sorted[quantile_indices]

print(f"   ✓ Variables regresadas a escala original: X_new = F̂⁻¹(U_new)")
print(f"   ✓ Copula Gaussiana COMPLETA (7 pasos puros)")


# ============================================================================
# 5. APLICAR RUIDO ESPACIAL
# ============================================================================
print("\n5️⃣ APLICANDO RUIDO ESPACIAL (±5%)...")

# Aplicar ruido gaussiano ±5% a coordenadas con clipping [0, 100]
noise_scale = 0.05
spatial_cols = ['x', 'y', 'endX', 'endY', 'defensive_line_height', 'desmarque_x', 'desmarque_y']

for col in spatial_cols:
    if col in df_synthetic.columns:
        col_std = df_synthetic[col].std()
        noise = np.random.normal(0, col_std * noise_scale, len(df_synthetic))
        df_synthetic[col] = np.clip(df_synthetic[col] + noise, 0, 100)

print(f"   ✓ Ruido ±5% aplicado a coordenadas sintéticas con clipping [0, 100]")

# ============================================================================
# 6. RECALCULAR VARIABLES DERIVADAS
# ============================================================================
print("\n6️⃣ RECALCULANDO VARIABLES DERIVADAS...")

# Nota: delta ahora se sintetiza con la Copula Gaussiana, no como resta

# desmarque_distancia: distancia euclidiana desde (x,y) a (desmarque_x, desmarque_y)
mask_desmarque = (df_crosses['tiene_desmarque'] == True) & \
                 (df_synthetic['desmarque_x'].notna()) & \
                 (df_synthetic['desmarque_y'].notna())

df_synthetic['desmarque_distancia'] = np.nan
if mask_desmarque.any():
    dx = df_synthetic.loc[mask_desmarque, 'desmarque_x'] - df_synthetic.loc[mask_desmarque, 'x']
    dy = df_synthetic.loc[mask_desmarque, 'desmarque_y'] - df_synthetic.loc[mask_desmarque, 'y']
    df_synthetic.loc[mask_desmarque, 'desmarque_distancia'] = np.sqrt(dx**2 + dy**2)

# desmarque_angulo: ángulo desde (x,y) a (desmarque_x, desmarque_y)
df_synthetic['desmarque_angulo'] = np.nan
if mask_desmarque.any():
    dx = df_synthetic.loc[mask_desmarque, 'desmarque_x'] - df_synthetic.loc[mask_desmarque, 'x']
    dy = df_synthetic.loc[mask_desmarque, 'desmarque_y'] - df_synthetic.loc[mask_desmarque, 'y']
    df_synthetic.loc[mask_desmarque, 'desmarque_angulo'] = np.degrees(np.arctan2(dy, dx))

print(f"   ✓ Variables derivadas recalculadas: desmarque_distancia, desmarque_angulo")

# Agregar variables originales (no sintetizadas) - garantizar alineación por índice
for col in numeric_vars_original:
    if col in df_crosses.columns:
        # Usar .loc para garantizar alineación correcta por índice
        df_synthetic[col] = df_crosses.loc[df_synthetic.index, col].values

print(f"   ✓ Variables originales (eventos raros) agregadas sin modificación")

# ============================================================================
# 7. CONSTRUIR DATASET SINTÉTICO FINAL
# ============================================================================
print("\n7️⃣ CONSTRUYENDO DATASET FINAL...")

# Definir columnas a EXCLUIR (no queremos estas en el sintético)
cols_to_exclude = {
    'fecha', 'teamId', 'playerId', 'minute', 'second', 
    'primer_remate_jugador', 'sequence_events',
    'tipo_exito',  # tipo_exito se agregará por merge
    'league', 'TeamName', 'TeamRival', 'jugador'  # Excluir originals, usar anonimizadas
}

# Definir columnas que se sintetizan o derivan (no se copian del original)
cols_synthetic_derived = set(numeric_vars_to_synthesize + numeric_vars_derived)

# Determinar qué columnas copiar del original
cols_to_copy = [col for col in df_crosses.columns 
                if col not in cols_to_exclude 
                and col not in cols_synthetic_derived
                and col not in ['league_anon', 'TeamName_anon', 'TeamRival_anon', 'jugador_anon']]

# Crear df_final con todas las columnas del original (excepto las excluidas)
df_final = df_crosses[cols_to_copy + ['league_anon', 'TeamName_anon', 'TeamRival_anon', 'jugador_anon']].copy()

print(f"   ✓ Copiando {len(cols_to_copy)} columnas del original")

# Agregar SOLO las variables numéricas sintetizadas (reemplazan los valores copiados)
# Usar .loc para garantizar alineación correcta por índice
for col in numeric_vars_to_synthesize:
    if col in df_synthetic.columns:
        df_final[col] = df_synthetic.loc[df_final.index, col].values

# Agregar SOLO las variables derivadas (recalculadas desde síntéticas)
# Usar .loc para garantizar alineación correcta por índice
for col in numeric_vars_derived:
    if col in df_synthetic.columns:
        df_final[col] = df_synthetic.loc[df_final.index, col].values

# xG, xGoT, y otras "originales" ya están copiadas desde df_crosses en el paso anterior
# NO necesitan ser sobrescritas
print(f"   ✓ Agregando {len(numeric_vars_to_synthesize)} variables sintetizadas")
print(f"   ✓ Agregando {len(numeric_vars_derived)} variables derivadas")

print(f"   ✓ Variables agregadas:")
print(f"     - Sintetizadas: {numeric_vars_to_synthesize}")
print(f"     - Originales (copiadas sin cambios): {numeric_vars_original}")
print(f"     - Derivadas: {numeric_vars_derived}")

# Preservar tipo_exito del dataset ORIGINAL usando merge por (eventId, matchId)
# Esta combinación es la clave exacta para cada freekick
df_final = df_final.merge(
    tipo_exito_map,
    on=['eventId', 'matchId'],
    how='left'
)

# Reclasificar tipo_exito: goles deben distinguirse de remates
# Si es remate Y primer_remate_gol=True, cambiar a 'gol_*'
def reclassify_tipo_exito(row):
    if pd.isna(row['tipo_exito']):
        return None
    if row['primer_remate_gol'] == True:
        # Es un gol
        if row['tipo_exito'] == 'remate_con_desmarque':
            return 'gol_con_desmarque'
        elif row['tipo_exito'] == 'remate_estatico':
            return 'gol_sin_desmarque'
    # En cualquier otro caso, mantener el valor original
    return row['tipo_exito']

df_final['tipo_exito'] = df_final.apply(reclassify_tipo_exito, axis=1)

print(f"   ✓ tipo_exito reclasificado (goles separados de remates)")

# Renombrar columnas de anonimización
df_final.rename(columns={
    'league_anon': 'league',
    'TeamName_anon': 'TeamName',
    'TeamRival_anon': 'TeamRival',
    'jugador_anon': 'jugador'
}, inplace=True)

# Remover columnas temporales si existen
df_final = df_final.drop(columns=[], errors='ignore')

print(f"   ✓ Dataset final: {df_final.shape}")
print(f"   ✓ tipo_exito preservado del dataset original:")
print(f"     {df_final['tipo_exito'].value_counts().to_dict()}")

# ============================================================================
# 8. VALIDACIÓN ESTADÍSTICA
# ============================================================================
print(f"\n8️⃣ VALIDACIÓN ESTADÍSTICA (SOLO {len(numeric_vars_to_synthesize)} VARIABLES SINTETIZADAS)...")

validation_results = []

for col in numeric_vars_to_synthesize:
    if col not in df_final.columns or col not in df_numeric.columns:
        continue
    
    original = df_numeric[col].dropna().values
    synthetic = df_final[col].dropna().values
    
    if len(original) < 2 or len(synthetic) < 2:
        continue
    
    # KS Test
    ks_stat, ks_pval = ks_2samp(original, synthetic)
    
    # Wasserstein Distance
    wd = wasserstein_distance(original, synthetic)
    
    # Estadísticas descriptivas
    orig_mean, orig_std = original.mean(), original.std()
    synth_mean, synth_std = synthetic.mean(), synthetic.std()
    
    validation_results.append({
        'variable': col,
        'ks_stat': ks_stat,
        'ks_pval': ks_pval,
        'wasserstein': wd,
        'original_mean': orig_mean,
        'synthetic_mean': synth_mean,
        'mean_diff_%': abs(synth_mean - orig_mean) / orig_mean * 100 if orig_mean != 0 else 0,
        'original_std': orig_std,
        'synthetic_std': synth_std
    })

df_validation = pd.DataFrame(validation_results)

print(f"\n📊 RESULTADOS DE VALIDACIÓN ({len(numeric_vars_to_synthesize)} variables sintetizadas):")
print("-" * 100)
print(df_validation[['variable', 'ks_pval', 'wasserstein', 'mean_diff_%']].to_string(index=False))
print("-" * 100)

# Contar p-values > 0.05 (similitud)
similar_count = (df_validation['ks_pval'] > 0.05).sum()
print(f"\n✅ Variables estadísticamente similares (KS test p > 0.05): {similar_count}/{len(df_validation)}")
print(f"   Wasserstein Distance promedio: {df_validation['wasserstein'].mean():.6f}")
print(f"   Diferencia media de medias: {df_validation['mean_diff_%'].mean():.2f}%")

# ============================================================================
# 9. GUARDAR DATASET SINTÉTICO
# ============================================================================
print("\n9️⃣ GUARDANDO DATASET...")

output_path = 'Outputs/freekicks_dataset_synthetic.csv'
df_final.to_csv(output_path, index=False)
print(f"   ✓ Dataset guardado en: {output_path}")

# Guardar reporte de validación
validation_path = 'Outputs/synthetic_validation_report.csv'
df_validation.to_csv(validation_path, index=False)
print(f"   ✓ Reporte de validación guardado en: {validation_path}")

# Guardar mapeos de anonimización
mapping_info = {
    'league_map': league_map,
    'team_map': {str(k): v for k, v in team_map.items()},
    'player_map_count': len(player_map)
}

with open('Outputs/anonimization_mapping.json', 'w') as f:
    json.dump(mapping_info, f, indent=2)
print(f"   ✓ Mapeos de anonimización guardados")

# ============================================================================
# 10. RESUMEN FINAL
# ============================================================================
print("\n" + "="*80)
print("✅ DATASET SINTÉTICO GENERADO EXITOSAMENTE")
print("="*80)
print(f"\n📊 RESUMEN:")
print(f"   • Dataset original (Crosses): {len(df_crosses):,} filas")
print(f"   • Dataset sintético: {len(df_final):,} filas")
print(f"   • Variables sintetizadas con Copula: {len(numeric_vars_to_synthesize)}")
print(f"     {numeric_vars_to_synthesize}")
print(f"   • Variables copiadas del original: {len(numeric_vars_original)}")
print(f"     {numeric_vars_original}")
print(f"   • Variables derivadas (recalculadas): {len(numeric_vars_derived)}")
print(f"   • Ruido espacial aplicado: ±5% con clipping [0-100]")
print(f"   • Ligas anonimizadas: {len(league_map)}")
print(f"   • Equipos anonimizados: {len(team_map)}")
print(f"   • Jugadores anonimizados: {len(player_map)}")
print(f"\n📈 VALIDACIÓN (solo {len(numeric_vars_to_synthesize)} variables sintetizadas):")
print(f"   • Test KS (similitud estadística): {similar_count}/{len(df_validation)} variables válidas")
print(f"   • Wasserstein Distance promedio: {df_validation['wasserstein'].mean():.6f}")
print(f"   • Diferencia media de medias: {df_validation['mean_diff_%'].mean():.2f}%")
print("\n" + "="*80)
