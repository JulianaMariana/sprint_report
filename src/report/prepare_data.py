from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from unidecode import unidecode


class PrepareProjectData:
    def __init__(self, sprint_name, start_sprint, end_sprint, df_limite_hours, limit_hour_report=9) -> None:
        self.sprint_name = sprint_name
        self.start_sprint = start_sprint
        self.end_sprint = end_sprint

        self.limit_hour_report = limit_hour_report
        self.df_limite_hours = df_limite_hours

    def filter_sprint(self, data):
        df = data.copy()

        columns_sprints = [column for column in df.columns.to_list() if "Sprint" in column]
        df["Sprints"] = df[columns_sprints].apply(lambda x: "".join(str(x)), axis=1)
        df = df.loc[df["Sprints"].apply(lambda x: True if self.sprint_name in x else False)]

        return df

    def add_original_sprint_column(self, data):
        def get_original_sprint(x):
            x = x.split("\n")[0].split(" ")[-3:]
            return " ".join(x)

        df = data.copy()
        df["Original Sprint"] = df["Sprints"].apply(get_original_sprint)

        return df

    def convert_times2hours(self, data, columns_times=["Original estimate", "Time Spent"]):
        df = data.copy()
        df[columns_times] = df[columns_times].apply(lambda x: x / 3600)

        return df

    def get_log_works(self, data):
        data = data.copy()

        data = self.filter_sprint(data)
        coluns_filter = ["Assignee", "Issue key"]
        coluns_filter.extend([column for column in data.columns.to_list() if "Log Work" in column])
        data = data.loc[:, coluns_filter]

        columns_log_work = [column for column in data.columns.to_list() if "Log Work" in column]
        logs_work = data.loc[:, columns_log_work]
        logs_work.fillna(0, inplace=True)
        for column in columns_log_work:
            logs = logs_work[column][logs_work[column] != 0]

            for index, log in zip(logs.index, logs):
                time, __, work_log = log.split(";")[1:]
                time = datetime.strptime(time, "%d/%m/%Y %H:%M")
                limit_hour = datetime.strptime(self.limit_hour_report, "%H:%M")
                time < time.replace(hour=limit_hour.hour, minute=limit_hour.minute)
                date = time.strftime("%d/%m/%Y %H:%M")
                data[column][index] = str(date) + " - " + str(float(work_log) / 3600) + "hs"
        return data

    def add_date_worklog(self, data):
        df = data.copy()

        dates_sprint = pd.date_range(start=self.start_sprint, end=self.end_sprint).to_pydatetime().tolist()
        dates_str = [date.strftime("%d/%m/%Y") for date in dates_sprint]
        df_dates = pd.DataFrame(0, index=np.arange(len(df.index)), columns=dates_str)

        columns_log_work = [column for column in df.columns.to_list() if "Log Work" in column]
        logs_work = df.loc[:, columns_log_work]
        logs_work.fillna(0, inplace=True)
        for column in columns_log_work:
            logs = logs_work[column][logs_work[column] != 0]

            for index, log in zip(logs.index, logs):
                time, __, work_log = log.split(";")[1:]
                time = datetime.strptime(time, "%d/%m/%Y %H:%M")

                assignee_name = df["Assignee"][index]
                date = time.strftime("%d/%m/%Y")

                limite_hour = self.df_limite_hours[self.df_limite_hours["Date"] == date][assignee_name].to_list()
                limite_hour = self.limit_hour_report if limite_hour == [] else limite_hour[0]
                limite_hour = datetime.strptime(date + " " + str(limite_hour), "%d/%m/%Y %H:%M")

                date = (
                    time.strftime("%d/%m/%Y")
                    if time > time.replace(hour=limite_hour.hour, minute=limite_hour.minute)
                    else (time - timedelta(days=1)).strftime("%d/%m/%Y")
                )

                if date in dates_str:
                    df_dates.at[index, date] = df_dates.at[index, date] + (float(work_log) / 3600)

        return pd.concat([df, df_dates], axis=1)

    def get_init_spent_date(self, data):
        df = data.copy()
        df = self.get_log_works(df)
        columns_logwork = [column for column in df.columns.to_list() if "Log Work" in column]

        df["Init Spend Date"] = ""
        # print(df)
        for col in columns_logwork:
            try:
                log_col = df[df[col].notnull()][col]
                for index, log_line in zip(log_col.index, log_col):
                    if df.iloc[index]["Init Spend Date"] == "" and log_line != "":
                        df.at[index, "Init Spend Date"] = log_line.split()[0]
            except Exception as e:
                print("############# Exception get_init_spent_date #############")
                print("df indexs", df.index)
                print("index", index)
                print("log_line", log_line, "\n")
                print("dataframe", df)
                print(e)
                print("#########################################################")

        return df["Init Spend Date"]

    def get_project_dataframe(self, data):
        df = data.copy()
        df = self.filter_sprint(df)
        df = df.reset_index(drop=True)
        df["Init Spent Date"] = self.get_init_spent_date(df)
        df = self.add_original_sprint_column(df)

        columns_filter = [
            "Assignee",
            "Summary",
            "Issue key",
            "Issue Type",
            "Status",
            "Original estimate",
            "Time Spent",
            "Init Spent Date",
            "Original Sprint",
        ]

        columns_logwork = [column for column in df.columns.to_list() if "Log Work" in column]
        columns_filter.extend(columns_logwork)
        df = df.loc[:, columns_filter].reset_index(drop=True)
        df["Assignee"] = df["Assignee"].fillna("Time")
        df.fillna(0, inplace=True)

        df = self.convert_times2hours(df)
        df = self.add_date_worklog(df)
        df = df.drop(columns_logwork, axis=1)

        # Convert assignee names to without accentuation
        df["Assignee"] = df["Assignee"].apply(lambda x: unidecode(x))

        # Compute task time by sprint
        dates_sprint = pd.date_range(start=self.start_sprint, end=self.end_sprint).to_pydatetime().tolist()
        dates_str = [date.strftime("%d/%m/%Y") for date in dates_sprint]

        df["Time Spent Sprint"] = df[dates_str].sum(axis=1)
        df.rename(columns={"Time Spent": "Total Time Spent"}, inplace=True)

        return df.reset_index(drop=True)
