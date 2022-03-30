# MISP Usage statistics

# Installation
```bash
cp config.py.sample config.py
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
Update the geo location data base:
- Download the database [here](https://data.public.lu/fr/datasets/geo-open-ip-address-geolocation-per-country-in-mmdb-format/)
- save it in the `geolocation` folder
    - Don't forget to update `config.py`

# Usage
0. Activate environment `source venv/bin/activate`
1. Review `config.py` and adapt paths accordingly
2. Generate the statistics with the `generate_misp.py` script
3. Generate the charts via the `plot_misp.py` script
4. `package_data.sh` creates an archive containing the JSON files

**TL;DR**: The whole procedure can be done by calling the `RUN-ME.sh` script:
```bash
bash RUN-ME.sh
```

## Result of running the command above:
- A JSON containing the aggregated data is written in `data/misp/data-misp.json`
- An HTML file containing the chart is written in `html/misp/plot-bokeh-misp.html`
- An archive containing the aggregated data is written in `exposed/data.tar.gz`
