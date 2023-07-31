import sys

sys.path.insert(0, "..")

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, dash_table, dcc, html

from src.report import (
    assignee_report,
    prepare_data,
    project_report,
    read_files,
    report_plots,
)


def status_table():
    table = dash_table.DataTable(
        # ordered_data.to_dict("records"),
        id="task-status-table",
        columns=[{"name": i, "id": i} for i in ordered_data.columns],
        style_table={"overflowX": "auto"},
        style_data={
            "text-align": "center",
        },
        style_cell={"fontSize": 12, "font-family": "sans-serif"},
        style_cell_conditional=[
            {
                "if": {"column_id": "Summary"},
                "maxWidth": "300px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
        ],
        style_header={
            "backgroundColor": "royalblue",
            "fontWeight": "bold",
            "color": "white",
            "minWidth": "80px",
            "width": "80px",
            "maxWidth": "80px",
            "whiteSpace": "pre-line",
            "textAlign": "left",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#EEEEEE"},
            {
                "if": {"column_id": "Summary"},
                "textAlign": "left",
            },
            {
                "if": {"filter_query": '{Status} eq "Done"', "column_id": "Status"},
                "backgroundColor": "#7EF39B",
                "color": "green",
            },
            {
                "if": {"filter_query": '{Status} eq "Review"', "column_id": "Status"},
                "backgroundColor": "#90EBF9",
                "color": "blue",
            },
            {
                "if": {"filter_query": '{Status} eq "In Progress"', "column_id": "Status"},
                "backgroundColor": "#669FFD",
                "color": "blue",
            },
        ],
    )
    return table


sprint_name = ""
start_sprint = "2023-07-03"
end_sprint = "2023-07-21"

file_date = "13-07-23"

p_data, project_data = read_files.get_project_data(sprint_name, file_date, start_sprint, end_sprint)
p_data_excel, ordered_data, weeks_time = read_files.get_prepare_data(sprint_name, project_data)
original_plan = p_data_excel.get_excel_plan()


# Sprint dropdown options
sprints_options = read_files.get_sprint_options()

# Assignee dropdown options
assignee_names = ordered_data["Assignee"].unique().tolist()
if "Time" in assignee_names:
    assignee_names.remove("Time")

assignee_names = [
    str(name.split()[0] + " " + name.split()[1]) if len(name.split()) > 1 else name for name in assignee_names
]

assignee_names.sort()
options = ["All"]
options.extend(assignee_names)

################################### Dashboard

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

sidebar = html.Div(
    [
        html.H1("Project"),
        html.H2(" ".join(sprint_name.split(" ")[1:])),
        html.Br(),
        html.P("Select Sprint:"),
        html.P(
            dcc.Dropdown(id="sprint", options=sprints_options, value=sprints_options[-1], clearable=False),
            style={
                "height": "60px",
                "width": "240px",
                "margin-bottom": "25px",
            },
        ),
        html.P("Select Assignee:"),
        html.P(
            dcc.Dropdown(id="assignee", options=options, value="All", clearable=False),
            style={
                "height": "60px",
                "width": "240px",
                "margin-bottom": "25px",
            },
        ),
    ]
)


content = html.Div(
    [
        dbc.Col(status_table(), md=12),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="percentage-status-graphs"), md=2),
                dbc.Col(dcc.Graph(id="plotly-status-table"), md=10),
            ]
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id="histogram-hours-graphs")),
            align="left",
        ),
    ]
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [dbc.Col(sidebar, width=2, className="bg-light"), dbc.Col(content, width=10)], style={"height": "100vh"}
        ),
    ],
    fluid=True,
)


@app.callback(Output("task-status-table", "data"), Input("assignee", "value"))
def task_status_table(option):
    if option == "All":
        data = ordered_data
    else:
        assignee_name = option.split()[0]
        data = assignee_report.get_assignee_table(ordered_data, assignee_name=assignee_name)

    data["Assignee"] = [
        str(name.split()[0] + " " + name.split()[1][0] + ".") if len(name.split()) > 1 else name
        for name in data["Assignee"].to_list()
    ]
    return data.to_dict("records")


@app.callback(Output("plotly-status-table", "figure"), Input("assignee", "value"))
def plotly_status_table(option):
    if option == "All":
        plot_assignee = report_plots.PlotAssigneeTimeline(
            ordered_data, original_plan, weeks_time[option].to_list(), type_plot=option
        )
    else:
        assignee_name = option.split()[0]
        data = assignee_report.get_assignee_table(ordered_data, assignee_name=assignee_name)

        plot_assignee = report_plots.PlotAssigneeTimeline(data, original_plan, weeks_time[assignee_name].to_list())

    fig = plot_assignee.plotly_timeline()
    return fig


@app.callback(Output("percentage-status-graphs", "figure"), Input("assignee", "value"))
def percentage_status_graphs(option):
    if option == "All":
        fig = report_plots.plot_num_status_percentage(ordered_data, sprint_name)
    else:
        assignee_name = option.split()[0]
        assignee_data = assignee_report.get_assignee_table(ordered_data, assignee_name=assignee_name)
        fig = report_plots.plot_num_status_percentage(assignee_data, assignee_name)

    return fig


@app.callback(Output("histogram-hours-graphs", "figure"), Input("assignee", "value"))
def histogram_hours_graphs(option):
    fig = report_plots.plot_histogram_hours(project_data, option=option)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=1234)
