"""
# Tutorial: Building data apps with Streamlit
Created by Natkamon Tovanich - version 2022-03-01
"""

import streamlit as st
import pandas as pd
import altair as alt
from altair import datum
from vega_datasets import data
from streamlit_vega_lite import vega_lite_component, altair_component
import time

st.write('# World Development Indicators')

st.write('## 1. Load data')
# Load Gapminder data
# @st.cache decorator skip reloading the code when the apps rerun.
@st.cache
def loadData():
    return pd.read_csv('WDIData.csv')

df = loadData()

# Use st.write() to render any objects on the web app
st.write('This is dataset table.')
st.write(df)

# Magic command: Streamlit automatically writes a variable 
# or a literal value to your app using st.write().
'List of columns in the table.'
df.columns.values

# Select year
year = 2012
source = df[df['Year'] == 2012]

# Create an Altair chart
st.write('#### This is the first chart we created.')

# Create the bubble chart with selection
@st.cache(allow_output_mutation=True)
def plotTheFirstChart(source):
    selected = alt.selection_multi(encodings=['x', 'y', 'size'])

    chart = alt.Chart(source).mark_circle(opacity=0.7, stroke='black', strokeWidth=1).encode(
        x=alt.X('GDP per capita (current LCU):Q', scale=alt.Scale(type='log', zero=False)),
        y=alt.Y('Life expectancy at birth, total (years):Q', scale=alt.Scale(zero=False)),
        size=alt.Size('Population, total:Q', scale=alt.Scale(range=(30, 3000), zero=False)),
        color=alt.condition(selected, alt.Color('Region:N'), alt.value('lightgray')),
        tooltip='Country'
    ).add_selection(selected).properties(width=800, height=500).interactive()

    return chart

# Showing Altair chait on the apps
st.altair_chart(plotTheFirstChart(source), use_container_width=False)

# Create the world map chart
@st.cache(allow_output_mutation=True)
def plotChoroplethMap(source):
    countries = alt.topo_feature(data.world_110m.url, 'countries')

    chart = alt.Chart(countries).mark_geoshape(
        stroke='white'
    ).encode(
        color='CO2 emissions (kt):Q'
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(source, 'id', ['CO2 emissions (kt)'])
    ).project('equirectangular').properties(
        width=800,
        height=500,
        title='CO2 emissions (kt)'
    )

    return chart

# Showing Altair chart on the apps
st.altair_chart(plotChoroplethMap(source), use_container_width=False)

st.write('## 3. Add user inputs and update the chart')

# What if we can select the variable to display in the chart
indicators = list(df.columns.values[2:16])

x_sel = st.sidebar.selectbox('X-axis', indicators, 5)
x_log = st.sidebar.checkbox('Log scale on x-axis', value=True)

y_sel = st.sidebar.selectbox('Y-axis', indicators, 9)
y_log = st.sidebar.checkbox('Log scale on y-axis')

# What if we can filter some countries to show on the chart
countries = set(df['Country'])
countries_sel = st.sidebar.multiselect('Countries', countries)

# Put those inputs on the sidebar

# What if we can see the statistics over the years
if 'year' not in st.session_state:
    year = st.slider('Year', 1960, 2020, 2015)
else:
    year = st.slider('Year', 1960, 2020, st.session_state.year)

# Select the data according to the user inputs
keys = dict()
keys['x'] = x_sel
keys['y'] = y_sel
keys['x_log'] = x_log
keys['y_log'] = y_log
keys['year'] = year
keys['countries'] = countries_sel

# Add text.markdown() to show the year displayed on the chart
text = st.empty()
text.markdown("Year: {}".format(year))

# Plot the bubble chart again as a function with st.cache decorator
@st.cache(allow_output_mutation=True)
def plotBubbleChart(df, keys, global_max=False):
    # Filter countries, if they are selected in the input
    if len(keys['countries']) > 0:
        df = df[df['Country'].isin(keys['countries'])]

    # Set the scale based on whether the value needs to be transform to log scale or not
    if global_max:
        x_scale = alt.Scale(domain=[df[keys['x']].min(), df[keys['x']].max()], type='log', zero=False) if keys['x_log'] else alt.Scale(domain=[df[keys['x']].min(), df[keys['x']].max()], zero=False)
        y_scale = alt.Scale(domain=[df[keys['y']].min(), df[keys['y']].max()], type='log', zero=False) if keys['y_log'] else alt.Scale(domain=[df[keys['y']].min(), df[keys['y']].max()], zero=False)
        size_scale = alt.Scale(domain=[df['Population, total'].min(), df['Population, total'].max()], range=(30, 3000), zero=False)
    else:
        x_scale = alt.Scale(type='log', zero=False) if keys['x_log'] else alt.Scale(zero=False)
        y_scale = alt.Scale(type='log', zero=False) if keys['y_log'] else alt.Scale(zero=False)
        size_scale = alt.Scale(range=(30, 3000), zero=False)

    source = df[df['Year'] == keys['year']]
    source = source[(~source[keys['x']].isna()) & (~source[keys['y']].isna())]

    selected = alt.selection_multi(encodings=['x', 'y', 'size'])

    chart = alt.Chart(source).mark_circle(opacity=0.7, stroke='black', strokeWidth=1).encode(
        x=alt.X('{}:Q'.format(keys['x']), scale=x_scale),
        y=alt.Y('{}:Q'.format(keys['y']), scale=y_scale),
        size=alt.Size('Population, total:Q', scale=size_scale),
        color=alt.condition(selected, alt.Color('Region:N'), alt.value('lightgray')),
        tooltip='Country'
    ).add_selection(selected).properties(width=800, height=500).interactive()

    return chart

new_chart = st.altair_chart(plotBubbleChart(df, keys), use_container_width=False)

# What if we can animate the chart to see statistics over the years

# Find the minimum and maximum year for the selected variables
@st.cache()
def minmaxYear(df, x, y):
    temp_x = df[['Year', x]].dropna()
    temp_y = df[['Year', y]].dropna()

    first = max(temp_x['Year'].min(), temp_y['Year'].min())
    last = min(temp_x['Year'].max(), temp_y['Year'].max())
    return (first, last)

# Add start and stop button and animate the chart over the years
col1, col2 = st.columns(2)

with col1:
    start = st.button("Start")
with col2:
    stop = st.button("Stop")

first, last = minmaxYear(df, keys['x'], keys['y'])
if start:
    for y in range(first, last+1):
        text.markdown("Year: {}".format(y))
        st.session_state['year'] = y
        keys['year'] = y
        new_chart.altair_chart(plotBubbleChart(df, keys, True))
        time.sleep(0.2)

if stop and 'year' in st.session_state:
    keys['year'] = st.session_state.year
    new_chart.altair_chart(plotBubbleChart(df, keys, True))

# Relate the data between charts
st.write('## 4. Interacting with other Altair charts')

# Plot the connected scatterplot
def plotConnectedScatterplot(df, keys, countries):
    source = df[df['Country'].isin(countries)]

    x_scale = alt.Scale(type='log', zero=False) if keys['x_log'] else alt.Scale(zero=False)
    y_scale = alt.Scale(type='log', zero=False) if keys['y_log'] else alt.Scale(zero=False)

    chart = alt.Chart(source).mark_line(point=True).encode(
        x=alt.X('{}:Q'.format(keys['x']), scale=x_scale),
        y=alt.Y('{}:Q'.format(keys['y']), scale=y_scale),
        color='Country:N',
        order='Year',
        tooltip=['Country', 'Year']
    ).properties(width=800, height=500)

    return chart


# Create another chart to related to the bubble chart
selection = altair_component(altair_chart=plotBubbleChart(df, keys))

# Add the selection to relate bubble chart with the connected scatter plot
if selection.get("vlMulti"):
    # What is the selection variable?
    st.success("Match found!")
    #st.write(selection)
    
    # Convert selection to data frame
    s = pd.DataFrame(selection['vlMulti']['or'])
    #st.dataframe(s)
    
    # Find countries that match the selection
    c = df.loc[(df['Year'] == keys['year']) & (df[keys['x']].isin(s[keys['x']])), 'Country']
    st.dataframe(c)

    # Plot the connected scatterplot chart
    st.altair_chart(plotConnectedScatterplot(df, keys, c))