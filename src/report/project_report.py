import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from unidecode import unidecode


############################# INIT DEPRECATED  ######################
def get_project_dataframe_by_task(data):
    df = data.copy()

    columns_filter = [
        "Assignee",
        "Summary",
        "Issue key",
        "Issue Type",
        "Status",
        "Original estimate",
        "Time Spent Sprint",
        "Total Time Spent",
        "Init Spent Date",
        "Original Sprint",
    ]
    df = df.loc[:, columns_filter]
    return df


def get_task_times_by_project_order(data, sorted_issues):
    df = get_project_dataframe_by_task(data)

    da = df.copy()

    col_issues = da["Issue key"]
    for i, issue in enumerate(sorted_issues):
        if issue in col_issues.to_list():
            index = col_issues[col_issues == issue].index[0]
            da.at[index, "order"] = i

    order_value = len(sorted_issues)
    for index in (da["order"][da["order"].isnull().values.tolist()]).index:
        da.at[index, "order"] = order_value
        order_value = order_value + 1

    da = da.sort_values(by=["order"])
    da = da.astype({"order": "int"})
    da = da.set_index("order")
    da = da.reset_index(names=["order"], drop=True)

    return da


############################# END DEPRECATED  ######################


class PrepareDatafromExcel:
    def __init__(self, path_xlsx_file) -> None:
        self.xls = pd.ExcelFile(path_xlsx_file)

    def get_assignee_available_week_time(self, data):
        assignee_times = data.copy()
        assignee_times = assignee_times.replace("-", 0)

        columns_names = assignee_times.columns.to_list()
        columns_names.remove("Dia Semana")
        columns_names.remove("Data")
        columns_names.sort()

        df_times = pd.DataFrame({"Week End": ["1°", "2°", "3°"]})
        for name in columns_names:
            assignee_times[name] = pd.to_numeric(assignee_times[name])
            first_week_time = assignee_times[0:6][name].sum()
            second_week_time = assignee_times[7:13][name].sum() + first_week_time
            third_week_time = assignee_times[14:18][name].sum() + second_week_time

            df_times[name] = [first_week_time, second_week_time, third_week_time]

        df_times["All"] = df_times[columns_names].sum(axis=1)

        return df_times

    def get_sprint_dates(self):
        week = self.get_week_plan()

        return week["Data"][0].strftime("%Y-%m-%d"), week["Data"][len(week.index) - 1].strftime("%Y-%m-%d")

    def get_week_plan(self):
        assignee_times = pd.read_excel(self.xls, "Assignee Sprint Time")
        return assignee_times

    def get_week_time(self):
        assignee_times = pd.read_excel(self.xls, "Assignee Sprint Time")
        weeks_time = self.get_assignee_available_week_time(assignee_times)

        return weeks_time

    def get_excel_plan(self):
        original_plan = pd.read_excel(self.xls, "Original Plan")
        original_plan = original_plan.dropna().reset_index(drop=True)
        original_plan.rename(columns={"Task": "Issue key"}, inplace=True)

        return original_plan

    def add_column_sprint_estimation(self, data, get_excel_plan):
        df = data.copy()

        df["Sprint estimation"] = df["Original estimate"]
        for index in df.index:
            issue_key = df["Issue key"][index]
            line_orig_plan = get_excel_plan[get_excel_plan["Issue key"] == issue_key]
            if not line_orig_plan.empty:
                if df["Original estimate"][index] != line_orig_plan["Original estimate"].values[0]:
                    df.at[index, "Sprint estimation"] = line_orig_plan["Original estimate"].values[0]

        columns_filter = [
            "Assignee",
            "Summary",
            "Issue key",
            "Issue Type",
            "Status",
            "Original estimate",
            "Sprint estimation",
            "Time Spent Sprint",
            "Total Time Spent",
            "Init Spent Date",
            "Original Sprint",
        ]
        df = df.loc[:, columns_filter]

        return df

    def get_project_dataframe_by_task(self, data):
        df = data.copy()

        columns_filter = [
            "Assignee",
            "Summary",
            "Issue key",
            "Issue Type",
            "Status",
            "Original estimate",
            "Time Spent Sprint",
            "Total Time Spent",
            "Init Spent Date",
            "Original Sprint",
        ]
        df = df.loc[:, columns_filter]
        return df

    def get_task_times_by_project_order(self, prepare_data):
        # prepare_data data that come from PrepareProjectData

        da = self.get_project_dataframe_by_task(prepare_data)
        df_excel_plan = self.get_excel_plan()
        sorted_issues = df_excel_plan["Issue key"].to_list()

        col_issues = da["Issue key"]
        for i, issue in enumerate(sorted_issues):
            if issue in col_issues.to_list():
                index = col_issues[col_issues == issue].index[0]
                da.at[index, "order"] = i

        order_value = len(sorted_issues)
        for index in (da["order"][da["order"].isnull().values.tolist()]).index:
            da.at[index, "order"] = order_value
            order_value = order_value + 1

        da = da.sort_values(by=["order"])
        da = da.astype({"order": "int"})
        da = da.set_index("order")
        da = da.reset_index(names=["order"], drop=True)

        da = self.add_column_sprint_estimation(da, df_excel_plan)

        return da
