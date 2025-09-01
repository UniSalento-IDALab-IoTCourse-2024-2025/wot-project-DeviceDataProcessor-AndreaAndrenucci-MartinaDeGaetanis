def filter_by_municipality(measurements, city):
    """Filtra le stazioni per municipio."""
    try:
        return [
            m for m in measurements
            if getattr(m, "municipality", "").lower() == city.lower()
        ]
    except Exception as e:
        print(f"[filter_by_municipality] Errore: {e}")
        return []