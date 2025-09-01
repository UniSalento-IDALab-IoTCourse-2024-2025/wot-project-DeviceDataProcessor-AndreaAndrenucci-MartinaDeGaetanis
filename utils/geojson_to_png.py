import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os


INPUT_DIR = './out/'
OUTPUT_DIR = './output_geojson_png/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

alpha_value = 0.8

for filename in os.listdir(INPUT_DIR):
    if not filename.endswith('.geojson'):
        continue

    filepath = os.path.join(INPUT_DIR, filename)
    print(f"Elaborazione: {filename}")

    gdf = gpd.read_file(filepath)
    gdf = gdf.set_crs(epsg=4326).to_crs(epsg=3857)

    pred_cols = [col for col in gdf.columns if col.endswith('_predicted')]

    if not pred_cols:
        print(f"⚠️ Nessuna colonna '_predicted' trovata in {filename}, salto il file.")
        continue

    for pollutant in pred_cols:
        print(f"↳ Genero mappa per: {pollutant}")

        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(
            ax=ax,
            column=pollutant,
            cmap="inferno",
            legend=True,
            legend_kwds={"label": pollutant},
            alpha=alpha_value,
            edgecolor='none'
        )
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, alpha=1)
        ax.axis("off")

        basename = os.path.splitext(filename)[0]
        out_filename = f"{basename}_{pollutant}.png"
        out_path = os.path.join(OUTPUT_DIR, out_filename)
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"✅ Mappa salvata in '{out_path}'")
