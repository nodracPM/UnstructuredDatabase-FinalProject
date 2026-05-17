# Documentation

## Filter Fixes

This update fixes the behavior of the sidebar filters used by the `Clientes prioritarios` and `Investigacion de caso` tabs.

### Grupos sospechosos

Previously, the app queried the global Top N clients first and only then filtered the resulting dataframe by `community_id`. That meant a selected suspicious group could disappear whenever none of its clients were already present in the global Top N result.

The `community_id` filter is now applied inside `Q_TOP_N` before sorting and before `LIMIT $top_n`:

```cypher
AND ($comunidades IS NULL OR size($comunidades) = 0 OR p.community_id IN $comunidades)
```

The selected groups are passed directly to Neo4j through the `comunidades` parameter. The later pandas filtering step was removed because it was filtering too late.

### Metrica principal del ranking

Previously, `Q_TOP_N` always ordered clients by `risk_score`, even when the user selected another ranking metric such as `risk_tel`, `risk_device`, `risk_ip`, or `risk_dom`. The chart could re-sort the already-limited dataframe, but relevant clients may already have been excluded by the database query.

The selected metric is now passed as the `metrica` parameter and used in the Cypher query before `LIMIT $top_n`. The query uses a `CASE` expression to choose the correct property safely:

```cypher
CASE $metrica
  WHEN 'risk_tel' THEN coalesce(p.risk_tel, 0)
  WHEN 'risk_device' THEN coalesce(p.risk_device, 0)
  WHEN 'risk_ip' THEN coalesce(p.risk_ip, 0)
  WHEN 'risk_dom' THEN coalesce(p.risk_dom, 0)
  ELSE coalesce(p.risk_score, 0)
END AS ranking_metrica
```

The selected metric is ordered descending, with `risk_score` as a secondary tie-breaker.

### Factor summary

`Q_FACTORES` now receives the selected suspicious groups too, so the factor summary reflects the active `Nivel de riesgo` and `Grupos sospechosos` filters. Empty averages are coalesced to `0` to keep the visualizations stable when a filter combination has no matching clients.

## Sidebar Styling Fix

The sidebar uses a dark background and previously forced every nested element to white text:

```css
section[data-testid="stSidebar"] * { color: white !important; }
```

That made labels and markdown readable, but it also affected the selected value inside `st.selectbox`. Since selectbox inputs have a light background, the selected values for `Nivel de riesgo` and `Metrica principal del ranking` became white text on a light field.

The fix keeps the existing sidebar color behavior, then adds a more specific override for only the selectbox input/value area:

```css
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] *,
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] input,
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] input {
    color: #1D3557 !important;
}
```

This keeps sidebar headings and labels readable on the dark background while making selectbox selected values visible on their light input background. The multiselect chips for `Grupos sospechosos` were left unchanged because they were already readable.

## Verification

After the change, the app was checked with Python bytecode compilation:

```bash
python3 -m py_compile app.py
```
