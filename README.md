# TFM_Guillermo_Sierra
Ficheros sobre el TFM 'Análisis de desmarques en saques de falta y de porteria en el fútbol.' del máster en Ciencia de Datos por la UIMP

## Descripción

Este repositorio contiene los scripts, datasets y resultados empleados
en el desarrollo del Trabajo Fin de Máster, centrado en el análisis
de datos de fútbol mediante técnicas estadísticas y de aprendizaje
automático.

## Estructura del repositorio

El repositorio se organiza en dos carpetas principales, correspondientes a los análisis de **saques de meta (Goalkicks)** y **saques de esquina (Freekicks)**. Cada una contiene los scripts desarrollados para el procesamiento y análisis de los datos, así como los resultados generados.

```text
TFM-football-analytics/
│
├── Goalkicks/
│   │
│   └── Scripts/
│       ├── export_goalkicks.py
│       └── generate_porteros_final.py
│
├── Freekicks/
│   │
│   ├── Scripts/
│   │   ├── export_freekicks_dataset.py
│   │   ├── generate_synthetic_dataset.py
│   │   ├── generate_interactive_heatmap.py
│   │   ├── generate_interactive_heatmap2.py
│   │   ├── generate_interactive_heatmap_synt.py
│   │   └── generate_interactive_heatmap_synt2.py
│   │
│   └── Results/
│       ├── interactive_freekicks_heatmap_synt.html
│       └── interactive_freekicks_heatmap_synt2.html
```

### Goalkicks

La carpeta `Goalkicks` contiene los scripts empleados para el procesamiento y análisis de los datos correspondientes a los saques de meta. La subcarpeta `Scripts` incluye los programas desarrollados para la extracción y generación de los resultados del análisis.

### Freekicks

La carpeta `Freekicks` contiene los scripts y resultados asociados al análisis de los saques de esquina. La subcarpeta `Scripts` incluye los programas utilizados para la generación y transformación de los datasets, así como para la generación de las visualizaciones interactivas. La subcarpeta `Results` contiene los resultados finales en formato HTML de las visualizaciones interactivas generadas a partir de los datos sintéticos.
