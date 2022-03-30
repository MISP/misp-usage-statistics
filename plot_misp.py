#!/usr/bin/env python3

from calendar import day_name
import json
from collections import defaultdict
import datetime

import pandas as pd
from math import pi

from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum, jitter
from bokeh.models import FactorRange, HoverTool, LinearAxis, ColumnDataSource, LinearColorMapper, Tabs, Panel, Div
from bokeh.models import ColorBar, BasicTicker, PrintfTickFormatter
from bokeh.models.formatters import FuncTickFormatter
from bokeh.models.ranges import Range1d
from bokeh.layouts import column
import bokeh.palettes as all_palettes
from bokeh.embed import file_html

from bokeh.resources import CDN, JSResources, CSSResources
from jinja2 import Template

from config import misp as misp_conf
from config import all as all_config

DIRDATA = misp_conf['DIR']
DIRHTML = misp_conf['DIR_HTML']
MISPBASEURL = misp_conf['baseurl']

TEXT_HEADING = 'MISP Usage Statistics'
TEXT_DOWNDLOAD = '<a href="{}" download id="download">{}</a>'.format(all_config['stat_download_location'], 'Download MISP statistics')
TEXT_FOOTING = '<i>Generated {}</i>'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

assignedColors = {}


def getColorForCountry(cc):
    combinedColorPalettes = all_palettes.Category20[20] + all_palettes.Category20b[20]
    if cc in assignedColors:
        return assignedColors[cc]
    else:
        assignedColors[cc] = combinedColorPalettes[len(assignedColors)]
        return assignedColors[cc]

def getColorPaletteForCountries(dic):
    return tuple([getColorForCountry(cc) for cc in dic.keys()])


def plotOvertime(x, y, y_year=False, title="", y_label = '', y_year_label = ''):
    tools = ["wheel_zoom,box_zoom,reset,save"]

    factors = []
    for d in x:
        year, month = d.split('-')
        factors.append((year, month))

    p = figure(x_range=FactorRange(*factors), width=940, height=350, tools=tools, title=title)

    r1 = p.vbar(x=factors, top=y, width=0.9, alpha=0.5, legend_label=y_label)
    p.add_tools(HoverTool(
        renderers=[r1],
        tooltips=[("Date", '@x'), ("Amount", "@top")],
        formatters={
            '@{x close}'        : 'printf',
            '@{amount close}' : 'numeral',
        }))

    if y_year is not False:
        sortedYears = list(y_year.keys())
        sortedYears.sort()
        amountPerYear = [y_year[y] for y in sortedYears]
        p.y_range = Range1d(0, max(y)*1.05)
        p.extra_y_ranges = {"NumPerYear": Range1d(start=0, end=max(amountPerYear)*1.05)}
        p.add_layout(LinearAxis(y_range_name="NumPerYear"), 'right')
        r2 = p.line(x=sortedYears, y=amountPerYear, color="red", line_width=2, y_range_name='NumPerYear', legend_label=y_year_label)
        p.add_tools(HoverTool(
            renderers=[r2],
            tooltips=[("Date", '@x'), ("Amount", "@y")],
            formatters={
                '@{x close}'      : 'printf',
                '@{amount close}' : 'numeral',
            }))

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xaxis.major_label_orientation = 1
    p.axis[0].major_label_text_font_size = '9px'
    p.yaxis[0].axis_label = y_label
    if y_year is not False:
        p.yaxis[1].axis_label = y_year_label
    p.xaxis.formatter = FuncTickFormatter(code = '''
        return parseInt(tick) % 2 != 0 ? '' : tick
    ''')

    p.xgrid.grid_line_color = None
    p.title.text_font_size = "20px"
    p.legend.location = "top_left"
    p.legend.orientation = "vertical"
    p.legend.background_fill_alpha = 0.65

    return p

def plotStackedOvertime(x, orgsLocalOvertime, orgsKnownOvertime, title="", y_label = ''):
    tools = ["wheel_zoom,box_zoom,reset,save"]

    factors = []
    for d in x:
        year, month = d.split('-')
        factors.append((year, month))
    
    categ = ['Created Organisation', 'Imported Organisation']
    data = {
        'date': factors,
        'Created Organisation': orgsLocalOvertime,
        'Imported Organisation': orgsKnownOvertime,
    }
    source = ColumnDataSource(data=data)

    p = figure(x_range=FactorRange(*factors), width=940, height=350, tools=tools, title=title)
    r1 = p.vbar_stack(categ, x='date', width=0.9, source=source, alpha=0.5, legend_label=categ, color=all_palettes.Colorblind3[:2])

    p.add_tools(HoverTool(
        renderers=r1,
        tooltips=[("Type", '$name'), ("Date", '@date'), ("Amount", "@$name")],
        formatters={
            '@{Date close}'  : 'printf',
            '@{amount close}': 'numeral',
        }))

    p.x_range.range_padding = 0.1
    p.xaxis.major_label_orientation = 1
    p.axis[0].major_label_text_font_size = '9px'
    p.yaxis[0].axis_label = y_label
    p.xaxis.formatter = FuncTickFormatter(code = '''
        return parseInt(tick) % 2 != 0 ? '' : tick
    ''')

    p.xgrid.grid_line_color = None
    p.title.text_font_size = "20px"
    p.legend.location = "top_left"
    p.legend.orientation = "vertical"
    p.legend.background_fill_alpha = 0.65
    p.legend.click_policy = 'hide'

    return p


def bokehPlotHeatMapLoginPerMonth(dfLogin, title=""):

    dfLogin['Year'] = dfLogin['Year'].astype(str)
    dfLogin = dfLogin.set_index('Year')
    dfLogin.columns.name = 'Month'
    years = list(dfLogin.index)
    months = list(dfLogin.columns)

    # reshape to 1D array or rates with a month and year for each row.
    df = pd.DataFrame(dfLogin.stack(), columns=['login']).reset_index()

    cutoffValue = df['login'].max()
    # Trying to do some stupid manipulation to avoid outliers hiding other data
    # noOutliers = df[df['login']-df['login'].mean() <= (3*df['login'].std())]
    # cutoffValue = noOutliers['login'].max() - noOutliers['login'].std()*1
    mapper = LinearColorMapper(
        palette=all_palettes.Reds256[::-1],
        low=0,
        high=cutoffValue
    )

    tools = "hover,save"
    p = figure(title=title,
        x_range=years, y_range=list(reversed(months)),
        x_axis_location="above", width=940, height=500,
        tools=tools, toolbar_location='below',
        tooltips = [("Logins", "@login")])


    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.title.text_font_size = "20px"

    p.rect(x="Year", y="Month", width=0.95, height=0.95,
        source=df,
        fill_color={'field': 'login', 'transform': mapper},
        line_color=None)

    color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="10px",
                        ticker=BasicTicker(desired_num_ticks=10),
                        formatter=PrintfTickFormatter(format="%d"),
                        label_standoff=6, border_line_color=None)
    p.add_layout(color_bar, 'right')
    return p


def bokehPlotHeatMapLoginPerHour(dfLogin, title=""):
    dfLogin['Hour'] = dfLogin['Hour'].astype(str)
    dfLogin = dfLogin.set_index('Hour')
    dfLogin.columns.name = 'Days'
    hours = list(dfLogin.index)
    days = list(dfLogin.columns)

    # reshape to 1D array or rates with a month and year for each row.
    df = pd.DataFrame(dfLogin.stack(), columns=['login']).reset_index()

    cutoffValue = df['login'].max()
    # Trying to do some stupid manipulation to avoid outliers hiding other data
    # noOutliers = df[df['login']-df['login'].mean() <= (3*df['login'].std())]
    # cutoffValue = noOutliers['login'].max() - noOutliers['login'].std()*1
    mapper = LinearColorMapper(
        palette=all_palettes.Reds256[::-1],
        low=0,
        high=cutoffValue
    )

    tools = "hover,save"
    p = figure(title=title,
        x_range=hours, y_range=list(reversed(days)),
        x_axis_location="above", width=940, height=500,
        tools=tools, toolbar_location='below',
        tooltips = [("Logins", "@login")])


    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.title.text_font_size = "20px"

    p.rect(x="Hour", y="Days", width=0.95, height=0.95,
        source=df,
        fill_color={'field': 'login', 'transform': mapper},
        line_color=None)

    color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="10px",
                        ticker=BasicTicker(desired_num_ticks=10),
                        formatter=PrintfTickFormatter(format="%d"),
                        label_standoff=6, border_line_color=None)
    p.add_layout(color_bar, 'right')
    return p

def bokehPlotPie(
        x={},
        title="Ticket Classification",
        legendTitle='',
    ):

    topAmount = 12
    filteredX = [(k, v) for k, v in x.items() if v > 0 and k != 'null']
    filteredX.sort(key=lambda x: x[1], reverse=True)
    topX = {k: v for k, v in filteredX[:topAmount]}
    topX['Others'] = sum([t[1] for t in filteredX[topAmount:]])

    data = pd.Series(topX).reset_index(name='value').rename(columns={'index': 'type'})
    data['angle'] = data['value']/data['value'].sum() * 2*pi
    data['color'] = getColorPaletteForCountries(topX)

    p = figure(
        height=400, width=940,
        title=title,
        toolbar_location=None,
        tools="hover",
        tooltips="@type: @value",
        x_range=(-0.5, 1.0)
    )
    
    p.wedge(x=0, y=1, radius=0.25,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='type', source=data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    p.legend.title = legendTitle
    p.title.text_font_size = "20px"
    
    return p


def bokehSegment(x, yName, title=''):
    if len(x) == 0:
        return Div(text=f'{title}: 0', style={'font-size': '1.0em', 'font-weight': 'bold'})

    tools = ["wheel_zoom,box_zoom,reset,save"]
    factors = []
    uniqueX = list(set([d for d in x]))
    uniqueX.sort()
    for d in x:
        year, month = d.split('-')
        factors.append((year, month))

    y = [yName] * len(x)

    allFactors = []
    today = datetime.date.today()
    minYear = int(uniqueX[0][:4])
    for year in range(minYear-1, today.year+1):
        for month in range(1, 13):
            if year == today.year and month == today.month+1:
                break
            allFactors.append((str(year), str(month).zfill(2)))

    p = figure(
        x_range=FactorRange(*allFactors),
        y_range=[yName],
        width=940, height=250,
        tools=tools, title=title
    )
    source = ColumnDataSource(data={
        'x': factors,
        'y': y
    })

    if len(y) > 5:
        yForCircle = jitter('y', width=0.20, range=p.y_range)
    else:
        yForCircle = 'y'

    r1 = p.circle(x='x', y=yForCircle, size=9, fill_color="#1f77b4", line_color="#424242", alpha=0.6, line_width=1, legend_label=title, source=source)
    p.add_tools(HoverTool(
        renderers=[r1],
        tooltips=[("Date", '@x'),],
        formatters={
            '@{x close}'        : 'printf',
        }))

    p.x_range.range_padding = 0.1
    p.xaxis.major_label_orientation = 1
    p.axis[0].major_label_text_font_size = '9px'
    p.xaxis.formatter = FuncTickFormatter(code = '''
        return parseInt(tick) % 2 != 0 ? '' : tick
    ''')
    p.xgrid.grid_line_color = None
    p.title.text_font_size = "20px"
    p.legend.title = 'Total number {}'.format(len(x))
    p.legend.location = "top_left"
    p.legend.orientation = "vertical"
    p.legend.background_fill_alpha = 0.65

    return p


def collect_data():
    filename = 'data-misp.json'
    path = DIRDATA + filename
    parsed = {}
    with open(path) as f:
        parsed = json.load(f)
    return parsed

def generateHtml(models, renderJS=True):
    template_name = 'basic.j2'
    with open(template_name, 'r') as template_f:
        template_content = template_f.read()
    the_template = Template(template_content)
    js_resources = JSResources(mode="inline", minified=True, components=["bokeh"])
    css_resources = CSSResources(mode="inline", minified=True, components=["bokeh"])
    html = file_html(
        models,
        (js_resources, css_resources),
        template=the_template,
        template_variables={
            'js_data': js_resources.render_js() if renderJS else '',
            'text_heading': TEXT_HEADING,
            'text_download': TEXT_DOWNDLOAD,
            'text_footing': TEXT_FOOTING,
        }
    )
    return html


def writeHtml(html):
    path = DIRHTML + 'plot-bokeh-misp.html'
    with open(path, 'w') as f:
        f.write(html)
    return path


def plot():
    data = collect_data()
    dates = list(data['users'].keys())
    dates.sort()
    today = datetime.date.today()
    usersOvertime = []
    usersCumuOvertime = []
    orgsLocalOvertime = []
    orgsKnownOvertime = []
    orgsAllOvertime = []
    orgsAllCumuOvertime = []
    counterUsersCumuOvertime = 0
    counterOrgsAllOvertime = 0
    for d in dates:
        usersOvertime.append(data['users'][d])
        usersCumuOvertime.append(counterUsersCumuOvertime)
        orgsLocalOvertime.append(data['orgs_local'][d])
        orgsKnownOvertime.append(data['orgs_known'][d])
        orgsAllOvertime.append(data['orgs_all'][d])
        orgsAllCumuOvertime.append(counterOrgsAllOvertime)
        counterUsersCumuOvertime += data['users'][d]
        counterOrgsAllOvertime += data['orgs_all'][d]

    orgsAllPerYear = defaultdict(int)
    for date, amount in data['orgs_all'].items():
        year, _ = date.split('-')
        orgsAllPerYear[year] += amount

    userPerYear = defaultdict(int)
    usersCumuPerYear = defaultdict(int)
    for date, amount in data['users'].items():
        year, _ = date.split('-')
        userPerYear[year] += amount
        usersCumuPerYear[year] += amount

    startYear = int(dates[0][:4])
    allYears = [y for y in range(startYear, today.year+1)]

    userPerYear = dict(userPerYear)
    orgsAllPerYear = dict(orgsAllPerYear)

    user_overtime = plotOvertime(dates, usersOvertime, y_year=userPerYear, title=f"New User on MISP ({MISPBASEURL}) over time", y_label='New User', y_year_label='New User per Year')
    user_cumulative_overtime = plotOvertime(dates, usersCumuOvertime, y_year=False, title=f"Cumulative Users on MISP ({MISPBASEURL}) over time", y_label='Cumulative New User')
    org_overtime = plotStackedOvertime(dates, orgsLocalOvertime, orgsKnownOvertime, title=f"New Organisations on MISP ({MISPBASEURL}) over time", y_label='New Organisation')
    org_cumulative_overtime = plotOvertime(dates, orgsAllCumuOvertime, y_year=False, title=f"Cumulative Organisations on MISP ({MISPBASEURL}) over time", y_label='Cumulative New Organisation')

    allMonthNames = [datetime.date(2022, m, 1).strftime('%b') for m in range(1, 13)]
    allNames = ['Year'].append(allMonthNames)
    dataHeatmap = {
        'Year': allYears,
    }
    for month in allMonthNames:
        dataHeatmap[month] = [0 for _ in range(len(dataHeatmap['Year']))]
    for date, amount in data['login_month'].items():
        year = int(date[:4])
        month = int(date[5:7])
        monthName = datetime.date(2022, month, 1).strftime('%b')
        yearIndex = year - startYear
        dataHeatmap[monthName][yearIndex] = amount
    dfLogin = pd.DataFrame.from_dict(dataHeatmap, columns=allNames)
    login_overtime = bokehPlotHeatMapLoginPerMonth(dfLogin, title=f"Heatmap of manual unique logins on MISP ({MISPBASEURL})")

    dataLoginPerHourOverYear = {
        year: {
            'Hour': list(range(24)),
        } for year in allYears
    }

    for year, dicDays in data['login_hour'].items():
        year = int(year)
        for dayName, dicHours in dicDays.items():
            dataLoginPerHourOverYear[year][dayName] = [dicHours[str(hour)] for hour in range(24)]

    allNames = ['Hours'].append(len(range(24)))
    charts_login_per_hour = []
    for year in allYears:
        hasLoginForThatYear = len([l for l in [dataLoginPerHourOverYear[year][d] for d in day_name] if sum(l) > 0]) > 0
        if hasLoginForThatYear:
            dfLogin = pd.DataFrame.from_dict(dataLoginPerHourOverYear[year], columns=allNames)
            login_per_hour = bokehPlotHeatMapLoginPerHour(dfLogin, title=f"Heatmap of manual unique logins on MISP ({MISPBASEURL})")
            panel = Panel(child=login_per_hour, title=str(year))
            charts_login_per_hour.append(panel)
    tabs_login_per_hour = Tabs(tabs=charts_login_per_hour[::-1])

    charts_loging_country_per_year = []
    for year in allYears:
        yearlyData = data['login_country'].get(str(year), {})
        total = sum(yearlyData.values())
        if total > 0:
            login_country = bokehPlotPie(yearlyData, title=f"Manual unique logins per country on MISP ({MISPBASEURL})", legendTitle=f"Total number of unique login {total}")
            panel = Panel(child=login_country, title=str(year))
            charts_loging_country_per_year.append(panel)
    tabs_login_country = Tabs(tabs=charts_loging_country_per_year[::-1])

    columns = column(user_overtime, user_cumulative_overtime, org_overtime, org_cumulative_overtime, login_overtime, tabs_login_per_hour, tabs_login_country, spacing=42)
    return columns


def main():
    chart = plot()
    html = generateHtml(chart)
    path = writeHtml(html)
    print(path)


if __name__ == '__main__':
    main()
