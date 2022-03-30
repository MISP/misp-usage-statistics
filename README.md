# MISP Usage statistics

MISP Usage statistic is a Python software to generate static pages using [Bokeh](https://github.com/bokeh/bokeh) from a [MISP](https://www.misp-project.org/) instance.

![image](https://user-images.githubusercontent.com/6977223/160841628-5f695415-6ac7-4c36-bbd8-2e0dc0919f1d.png)

You can see the result in the [operational statistics of CIRCL](https://circl.lu/opendata/statistics/#usage-of-misp-offered-as-a-service-by-circl-misppriv-circl-lu).

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

# Requirements

- Python >=3.8
- [Bokeh library](https://github.com/bokeh/bokeh)
- [MMDB GeoOpen database](https://data.public.lu/fr/datasets/geo-open-ip-address-geolocation-per-country-in-mmdb-format/)

# Usage

- Activate environment `source venv/bin/activate`
- Review `config.py` and adapt paths accordingly
- Generate the statistics with the `generate_misp.py` script
- Generate the charts via the `plot_misp.py` script
- `package_data.sh` creates an archive containing the JSON files

**TL;DR**: The whole procedure can be done by calling the `RUN-ME.sh` script:

```bash
bash RUN-ME.sh
```

## Result of running the command above:

- A JSON containing the aggregated data is written in `data/misp/data-misp.json`
- An HTML file containing the chart is written in `html/misp/plot-bokeh-misp.html`
- An archive containing the aggregated data is written in `exposed/data.tar.gz`

## License

This software is an open source software [released under a 2-Clause BSD license](./LICENSE.md).

