from datetime import datetime

import pandas as pd


def get_worklogs_by_assignee(data: pd.DataFrame) -> pd.DataFrame:
    """Get the daily worklogs listed by assignees.

    Args:
        data (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """

    df = data.copy()

    dates_col = ["Assignee"]
    dates_col.extend(
        [column for column in df.columns if not pd.isnull(pd.to_datetime(column, errors="coerce", dayfirst=True))]
    )

    df = df.loc[:, dates_col]

    return df.groupby("Assignee").sum()


def get_worklogs_by_assignee_col_dates(data: pd.DataFrame) -> pd.DataFrame:
    df_work_log = get_worklogs_by_assignee(data)

    df_work_log = df_work_log.T
    df_work_log["Date"] = df_work_log.index
    df_work_log = df_work_log.reset_index(drop=True)
    df_work_log["Week Day"] = [
        datetime.strptime(date, "%d/%m/%Y").strftime("%A") for date in df_work_log["Date"].to_list()
    ]

    cols = df_work_log.columns.to_list()
    cols = cols[-2:] + cols[:-2]
    df_work_log = df_work_log[cols]
    return df_work_log


def get_assignee_full_name(df, assignee_name):
    assignees = df["Assignee"].unique().tolist()
    assignees.sort()
    full_name = [name for name in assignees if assignee_name in name][0]

    return full_name


def get_assignee_table(data, assignee_name):
    ## data must be first filter with get_project_dataframe_by_task or get_task_times_by_project_order

    df = data.copy()
    full_name = get_assignee_full_name(df, assignee_name)
    df = df.loc[df["Assignee"].apply(lambda x: True if full_name in x else False)]
    df = df.reset_index(names=["order"], drop=True)

    return df


def get_assignee_available_week_time(data):
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

    return df_times
