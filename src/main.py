import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from utils import filter_by

app = dash.Dash(__name__)

# Количество строк, которые берем из таблицы
LIMIT = 1000

# Читаем CSV файл
df = pd.read_csv('src/hr.csv')
filtered_active = df[df['Status'] == 'Active'].head(LIMIT)

departments = df['Department'].unique()
data_by_dept = {}

for dep in departments:
    data_by_dept[dep] = filter_by(
        'Department', dep, filtered_active).sort_values(by='Performance_Rating', ascending=False).head(100)

# df = pd.DataFrame({
#     'Employers': filtered_active["Full_Name"],
#     'KPI': filtered_active["Performance_Rating"].unique()
# })
# person = {"name": "John", "age": 30, "city": "New York"}


app.layout = html.Div([
    html.Div([
        html.H1("Анализ KPI и расчета вознаграждения для сотрудников компании"),

        # dcc.Dropdown(id='dropdown-id',
        #              options=['Option 1', 'Option 2', 'Option 3'], value='Option 1'),

        html.Div([
            # Таблица с отображением данных
            html.H3("Таблица с начальными данными"),
            dash_table.DataTable(
                columns=[
                    {"name": i, "id": i, "selectable": True}
                    for i in filtered_active.columns
                ],
                data=filtered_active.head(5).to_dict('records'),
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': '#636efa'
                },
                style_data={
                    'backgroundColor': '#f9f9f9'
                }
            )
        ], className='table'),

        # Цикл по отделам
        html.Div([
            html.H3("KPI сотрудников по департаментам"),
            *[html.Div([
                # График продаж по данному отделу
                dcc.Graph(
                    figure=px.bar(
                        data_by_dept[dept],
                        x='Full_Name',
                        y='Performance_Rating',
                        title=f'Показатель KPI по сотрудникам отдела "{dept}"'
                    )
                )
            ], className="department-block")

                for dept in departments
            ]
        ], className='diagrams-by-department')

    ], className='page')
], className='root')

if __name__ == '__main__':
    app.run(debug=True)
