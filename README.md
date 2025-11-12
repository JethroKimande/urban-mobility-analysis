<!-- Urban Mobility Analysis README -->

# Urban Mobility Analysis

Weekly analytics for Transport for London (TfL) road disruptions, including:

- Automated data ingestion from the TfL API (with cached fallbacks)
- Static report generation (`index.html`) featuring dashboard embeds, map, plots, and dark mode toggle
- Spatial visualization using Folium and Plotly
- Archival snapshots stored under `data/YYYY-MM-DD/` with an `archives.html` index
- Automated GitHub Pages deployment through GitHub Actions

See the live site: [Urban Mobility Blog](https://jethrokimande.github.io/urban-mobility-analysis/)  
(Updates occur after each workflow run.)

---

## Contents

- [`main.py`](main.py) — Fetches disruptions, produces CSV/XLSX/JSON, updates visualizations, and writes `index.html`, `map.html`, `archives.html`.
- [`dash_app2.py`](dash_app2.py) — Plotly Dash dashboard (optional local UI).
- `data/` — Time-stamped archives (`data/YYYY-MM-DD/`) plus `data/index.json`.
- GitHub Actions workflow — `.github/workflows/pages_deploy.yml`.

Generated artifacts:
- `index.html` / `map.html`
- `time_series_plot.png`
- `disruptions.csv`, `disruptions.xlsx`, `disruptions.json`

---

## Getting Started (Local)

1. **Clone**:
   ```bash
   git clone https://github.com/JethroKimande/urban-mobility-analysis.git
   cd urban-mobility-analysis
   ```

2. **Install dependencies** (Python 3.10+ recommended):
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Set environment variables** (optional but recommended):
   ```powershell
   $env:TFL_APP_ID="your-app-id"
   $env:TFL_APP_KEY="your-app-key"
   ```
   Without keys, the script uses cached CSV/XLSX/JSON if available.

4. **Run the pipeline**:
   ```bash
   python main.py
   ```
   Outputs refresh and archives are created under `data/YYYY-MM-DD/`.

5. **Launch the dashboard (optional)**:
   ```bash
   python dash_app2.py
   ```
   Visit http://127.0.0.1:8050/ (the `index.html` iframe points to this URL).

---

## GitHub Pages Deployment

The workflow in `.github/workflows/pages_deploy.yml`:

- Triggers on push to `main`, manual dispatch, or every Monday at 00:00 UTC.
- Installs dependencies and runs `python main.py`.
- Uploads the repository contents as a Pages artifact.
- Deploys to the `gh-pages` branch via `actions/deploy-pages`.

### One-Time Setup

1. **Enable GitHub Pages**:  
   Repository Settings → Pages → Build and Deployment → Source: *GitHub Actions*.

2. **Authorize Actions (first run only)**:  
   If GitHub prompts for “Approve workflow” or “Enable Actions for this repo,” approve it in the Actions tab.

3. **Configure secrets (optional)**:  
   Repository Settings → Secrets → Actions → add `TFL_APP_ID` and `TFL_APP_KEY` for live API data.

Once configured, any push to `main` (or the weekly timer) regenerates the site and publishes to <https://jethrokimande.github.io/urban-mobility-analysis/>.

---

## Manual Publish (Fallback)

If CI is unavailable:

1. Run `python main.py`.
2. Commit all generated artifacts (`index.html`, `archives.html`, `data/`, etc.).
3. Push to a branch configured for GitHub Pages (e.g., `gh-pages`).

---

## Architecture & Data Flow

```text
TfL API ──► fetch_tfl_disruptions() ──► DataFrame ──► CSV/XLSX/JSON
                                              │
                                              ├─► Matplotlib Histogram ──► time_series_plot.png
                                              ├─► Folium Map ──► map.html
                                              ├─► HTML report ──► index.html
                                              └─► Archive copy ──► data/YYYY-MM-DD/
```

Dash app (`dash_app2.py`) consumes `fetch_tfl_disruptions()` for interactive views.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| GitHub Pages shows outdated content | Ensure the Pages workflow succeeded; approve any pending workflow runs. |
| Missing API keys | Script will fall back to cached files; check console output for warnings. |
| iframe dashboard blank in `index.html` | Confirm `dash_app2.py` is running on http://127.0.0.1:8050/ or adjust the iframe source. |

---

## License

[MIT](LICENSE)

---

## Legacy Readme

Older notes remain in [`READMEfile.md`](READMEfile.md); new updates should target this `README.md`.

