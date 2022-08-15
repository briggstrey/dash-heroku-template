import os
ON_HEROKU = os.environ.get('ON_HEROKU')

if ON_HEROKU:
    # get the heroku port
    port = int(os.environ.get('PORT', 17995))  # as per OP comments default is 17995
else:
    port = 3000
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import dash
from dash import dcc
#import dash_core_components as dcc
from dash import html
#import dash_html_components as html
from dash.dependencies import Input, Output
import requests
import json
from dash import dash_table

gss = pd.read_csv("https://github.com/jkropko/DS-6001/raw/master/localdata/gss2018.csv",
                 encoding='cp1252', na_values=['IAP','IAP,DK,NA,uncodeable', 'NOT SURE',
                                               'DK', 'IAP, DK, NA, uncodeable', '.a', "CAN'T CHOOSE"])

mycols = ['id', 'wtss', 'sex', 'educ', 'region', 'age', 'coninc',
          'prestg10', 'mapres10', 'papres10', 'sei10', 'satjob',
          'fechld', 'fefam', 'fepol', 'fepresch', 'meovrwrk'] 
gss_clean = gss[mycols]
gss_clean = gss_clean.rename({'wtss':'weight', 
                              'educ':'education', 
                              'coninc':'income', 
                              'prestg10':'job_prestige',
                              'mapres10':'mother_job_prestige', 
                              'papres10':'father_job_prestige', 
                              'sei10':'socioeconomic_index', 
                              'fechld':'relationship', 
                              'fefam':'male_breadwinner', 
                              'fehire':'hire_women', 
                              'fejobaff':'preference_hire_women', 
                              'fepol':'men_bettersuited', 
                              'fepresch':'child_suffer',
                              'meovrwrk':'men_overwork'},axis=1)
gss_clean.age = gss_clean.age.replace({'89 or older':'89'})
gss_clean.age = gss_clean.age.astype('float')\

gss_bar = gss_clean.groupby('sex').agg({'income':'mean',
                                        'job_prestige':'mean',
                                        'socioeconomic_index':'mean',
                                        'education':'mean'})

markdown_text = '''The gender wage gap has been a hotly debated topic since the women's rights movement back in the \
1960s. According the the US Census Bureau women earned 60% of what men were earning for similar jobs. Today, \
people argue that there is no wage gap while others argue that it does still exist. Even worse than this, some \
people manipulate data to advance their agenda instead of trying to uncover the truth. \
https://www.investopedia.com/history-gender-wage-gap-america-5074898#:~:text=According%20to%20the%20U.S.%20Census,\
signing%20the%20Equal%20Pay%20Act.&text=Source%3A%20U.S.%20Census%20Bureau%2C%20Current,\
Annual%20Social%20and%20Economic%20Supplements.  

The General Social Survey is a national survey that conducts data collection in America to try to quantify how people \
are feeling about certain topics. It collects demographics, opinions, and personality data on indicuals in the US and \
is a key source for social analysis.  

https://www.gss.norc.org/About-The-GSS
'''


gss_bar.income = round(gss_bar.income,2)
gss_bar.job_prestige = round(gss_bar.job_prestige,2)
gss_bar.socioeconomic_index = round(gss_bar.socioeconomic_index,2)
gss_bar.education = round(gss_bar.education,2)
table = gss_bar.rename({'income':'Income',
                'job_prestige':'Occupational Prestige',
                'socioeconomic_index':'Socioeconomic Status', 
                'education':'Years of Formal Education'},axis=1).reset_index()

table2 = ff.create_table(table)
cat_cols = ['satjob', 'relationship', 'male_breadwinner', 'men_bettersuited', 'child_suffer', 'men_overwork']
group_cols = ['sex', 'region', 'education']
group = 'sex'
x = 'male_breadwinner'
fig_scatter = px.scatter(
    gss_clean,
    x='job_prestige',
    y='income',
    color='sex',
    labels={'income':'Annual Income', 
            'job_prestige':'Occupational Prestige'},
    trendline='ols',
    hover_data=['education','socioeconomic_index'],
    height=700,
    opacity = .25)

fig_box = px.box(gss_clean,
             y='income',
             color='sex',
             hover_data=['sex'],
             labels={'income':'Annual Income'})
fig_box.update_layout(showlegend=False)

fig_box2 = px.box(gss_clean,
             y='job_prestige',
             color='sex',
             #color_discrete_map = {'male':'lightblue', 'female':'moccasin'},
             hover_data=['sex'],
             labels={'job_prestige':'Occupational Prestige'})
fig_box2.update_layout(
    showlegend=False,
    # plot_bgcolor='white'
)

gss_grid = gss_clean[['income','sex','job_prestige']]
gss_grid['job_prestige_cat'] = pd.cut(gss_grid.job_prestige, 6)
gss_grid = gss_grid.dropna()

fig_grid = px.box(gss_grid, y='income',color='sex',
             facet_col='job_prestige_cat',facet_col_wrap=3,
             color_discrete_map = {'male':'blue', 'female':'red'})
fig_grid.update(layout=dict(title=dict(x=0.5)))
fig_grid.update_layout(showlegend=True)
fig_grid.for_each_annotation(lambda a: a.update(text=a.text.replace("job_prestige_cat=","")))

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1('Gender Wage Gap Analysis'),
    html.Div([
        html.Div([dcc.Graph(id='graph')], 
             #style={'width': '70%', 'float': 'right'}
                ),
        dcc.Dropdown(id='x',
                     options=[{'label': i, 'value': i} for i in cat_cols],
                     value = 'male_breadwinner'),
        dcc.Dropdown(id='group', 
                     options=[{'label': i, 'value': i} for i in group_cols],
                     value='sex'),
             ], 
        #style = {'width': '25%', 'float': 'left'}
    ),
    html.H2("Comparing Men and Women"),
    dcc.Markdown(children=markdown_text),
    html.Div([
            html.H2("Informational Table"),
            dcc.Graph(figure=table2)
        ]),
    dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
        dcc.Tab(label='Income and Occupational Prestige Distributions', value='tab-1'),
        dcc.Tab(label='Occupational Prestige vs Income', value='tab-2'),
        dcc.Tab(label='Prestige Brackets', value='tab-3')
    ]),
    html.Div(id='tabs-content-example-graph')
])

@app.callback(Output(component_id="graph",component_property="figure"),
              [Input(component_id='x',component_property="value"),
              Input(component_id='group',component_property="value")])
def make_figure(x, group):
    gss_groupbar = gss_clean.groupby([group,x]).size().reset_index().rename({0:'count'},axis=1)
    #gss_groupbar.x = gss_groupbar.x.astype('category').cat.reorder_categories(['strongly agree', 'agree', 'disagree','strongly disagree'])
    fig_bar = px.bar(gss_groupbar, x=x, y='count', color=group,
                     #labels={f'{x}':'Men Should be the Breadwinner','count':'Number in Category'},
                     barmode='group',
                     #color_discrete_map = {'male':'blue', 'female':'red'},
                     #category_orders ={'male_breadwinner':['strongly agree', 'agree', 'disagree','strongly disagree']})
                    )
    fig_bar.update_layout(showlegend=True)
    fig_bar.update(layout=dict(title=dict(x=0.5)))
    return fig_bar

@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.H2("Income Distributions for Men and Women"),
            dcc.Graph(figure=fig_box)
        ], style={'width': '48%', 'float': 'left'}),\
    html.Div([
            html.H2("Occupation Prestige Distributions for Men and Women"),
            dcc.Graph(figure=fig_box2)
        ], style={'width': '48%', 'float': 'right'}),

    elif tab == 'tab-2':
        return html.Div([
            html.H2("Income vs Occupational Prestige"),
            dcc.Graph(figure=fig_scatter)
        ])
    
    elif tab == 'tab-3':
        return html.Div([
            html.H2("Prestige Brackets"),
            dcc.Graph(figure=fig_grid)
        ])
    
if __name__ == '__main__':
    app.run_server(debug=True,port=port)
