import sys

sys.path.insert(0, "..")

import os

import pandas as pd

from src.report import prepare_data, project_report


def limite_hours(dataframe, start_sprint, end_sprint, limit_hour_report="12:00"):
    # Limite hours
    dates_sprint = pd.date_range(start=start_sprint, end=end_sprint).to_pydatetime().tolist()
    dates_str = [date.strftime("%d/%m/%Y") for date in dates_sprint]

    df_limite_hours = pd.DataFrame()
    df_limite_hours["Date"] = dates_str
    for name in dataframe["Assignee"].unique().tolist():
        df_limite_hours[name] = limit_hour_report

    return limit_hour_report, df_limite_hours


def get_project_data(sprint_name, date, start_sprint, end_sprint):
    path_csv_file = os.path.join("../csv_files", sprint_name, "Jira_" + date + ".csv")
    dataframe = pd.read_csv(path_csv_file, delimiter=",")

    limit_hour_report, df_limite_hours = limite_hours(dataframe, start_sprint, end_sprint)

    # Prepare data
    p_data = prepare_data.PrepareProjectData(
        sprint_name=sprint_name,
        start_sprint=start_sprint,
        end_sprint=end_sprint,
        df_limite_hours=df_limite_hours,
        limit_hour_report=limit_hour_report,
    )
    project_data = p_data.get_project_dataframe(dataframe)

    return p_data, project_data


def get_report_data(sprint_name, file_date):
    path_xlsx_file = os.path.join("../csv_files", sprint_name, sprint_name + ".xlsx")
    p_data_excel = project_report.PrepareDatafromExcel(path_xlsx_file)
    start_sprint, end_sprint = p_data_excel.get_sprint_dates()

    # Get Jira data
    path_csv_file = os.path.join("../csv_files", sprint_name, "Jira_" + file_date + ".csv")
    dataframe = pd.read_csv(path_csv_file, delimiter=",")

    limit_hour_report, df_limite_hours = limite_hours(dataframe, start_sprint, end_sprint)
    p_data = prepare_data.PrepareProjectData(
        sprint_name=sprint_name,
        start_sprint=start_sprint,
        end_sprint=end_sprint,
        df_limite_hours=df_limite_hours,
        limit_hour_report=limit_hour_report,
    )
    project_data = p_data.get_project_dataframe(dataframe)

    # Get orderly data
    weeks_time = p_data_excel.get_week_time()
    ordered_data = p_data_excel.get_task_times_by_project_order(project_data)

    return p_data, project_data, p_data_excel, ordered_data, weeks_time


def get_sprint_options():
    return next(os.walk("../csv_files"))[1]


def get_last_file(sprint_name):
    res = []
    dir_path = os.path.join("../csv_files", sprint_name)
    for path in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, path)):
            if ".csv" in path and "Jira" in path:
                path = path.strip("Jira_").strip(".csv")
                res.append(path)

    res.sort()
    return res[-1]
