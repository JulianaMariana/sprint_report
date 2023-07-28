import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.report import assignee_report


def plot_num_status_percentage(df, graph_name):
    list_status = ["Done", "In Progress", "Review", "To Do"]
    list_status.sort()

    n_status = []
    for status in list_status:
        n_status.append(len(df[df["Status"] == status].index))

    sprint_name = graph_name + " - N° tasks"
    sunburst = pd.DataFrame(data={"labels": [], "parents": [], "values": []})
    sunburst.loc[len(sunburst)] = [sprint_name, "", sum(n_status)]
    sunburst.loc[len(sunburst)] = ["Done", sprint_name, n_status[0]]
    sunburst.loc[len(sunburst)] = ["Not Done", sprint_name, sum(n_status[1:])]
    for status, value in zip(list_status[1:], n_status[1:]):
        sunburst.loc[len(sunburst)] = [status, "Not Done", value]

    fig = go.Figure(
        go.Sunburst(
            labels=sunburst["labels"].to_list(),
            parents=sunburst["parents"].to_list(),
            values=sunburst["values"].to_list(),
            textinfo="label+percent parent+value",
            branchvalues="total",
        )
    )

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return fig


def plot_histogram_hours(project_data, option="All"):
    work_log = assignee_report.get_worklogs_by_assignee(project_data)
    work_log["Assignee"] = work_log.index

    if option != "All":
        work_log = work_log[work_log["Assignee"] == option]

    work_log = work_log.melt(id_vars=["Assignee"], var_name="Date", value_name="Value")
    fig = px.histogram(work_log, x="Date", y="Value", color="Assignee", barmode="group", height=400)
    return fig


class PlotAssigneeTimeline:
    def __init__(
        self,
        df_assignee: pd.DataFrame,
        df_project_plan: pd.DataFrame,
        weeks_time: list,
        height: float = 0.5,
        type_plot: str = "assignee",
    ):
        if type_plot.lower() not in ["assignee", "all"]:
            raise ValueError("The type_plot should be 'assignee' or 'all'.")

        self.type_plot = type_plot.lower()

        self.df = df_assignee.copy()
        self.df_plan = df_project_plan.copy()
        self.weeks_time = weeks_time.copy()
        self.height = height

        self.col_init_estimate, self.col_duration_estimate = ("Init Estimate", "Duration estimate")
        self.col_init_spent, self.col_duration_spent = ("Init Spent", "Duration Spent")

    def _add_init_duration_columns(self, data, init_name, duration_name):
        # Generate datas init
        data[init_name] = 0
        for index in data.index.to_list():
            if index > 0:
                data.at[index, init_name] = data[init_name][index - 1] + data[duration_name][index - 1]

        return data

    def _add_task_situation(self, df_assignee, df_project_plan):
        df_assignee_plan = df_project_plan.copy()
        df_assignee_plan = df_assignee_plan.loc[df_assignee_plan["Assignee"] == df_assignee["Assignee"][0].split()[0]]
        df_assignee_plan = df_assignee_plan.reset_index(names=["order"], drop=True)

        df_assignee["Situation"] = "Original"
        df_assignee.loc[~df_assignee["Issue key"].isin(df_project_plan["Issue key"]), "Situation"] = "Added"

        if self.type_plot == "assignee":
            df_assignee.loc[
                df_assignee["Issue key"].isin(df_project_plan["Issue key"])
                & ~df_assignee["Issue key"].isin(df_assignee_plan["Issue key"]),
                "Situation",
            ] = "Relocated"

        return df_assignee

    def prepare_spent_data(self, df_assignee):
        a_spent = df_assignee.copy()

        a_spent.loc[a_spent["Init Spent Date"] == "", "Init Spent Date"] = np.nan
        a_spent["Init Spent Date"] = pd.to_datetime(a_spent["Init Spent Date"], format="%d/%m/%Y")
        a_spent = a_spent.sort_values(by=["Init Spent Date"], na_position="last")
        a_spent.rename(columns={"Time Spent Sprint": self.col_duration_spent}, inplace=True)
        a_spent = a_spent.reset_index(drop=True)
        a_spent = self._add_init_duration_columns(a_spent, self.col_init_spent, self.col_duration_spent)

        return a_spent

    def prepare_estimate_data(self, df_assignee, df_project_plan):
        a_est = df_assignee.copy()

        d_filter = df_project_plan.loc[~df_project_plan["Issue key"].isin(df_assignee["Issue key"])]
        d_filter = d_filter.loc[d_filter["Assignee"] == df_assignee["Assignee"][0].split()[0]]
        d_filter["Situation"] = "Relocated"
        d_filter["Time Spent Sprint"] = 0
        a_est = pd.concat([a_est, d_filter])
        a_est = a_est.reset_index(drop=True)
        a_est.loc[a_est["Issue key"] == "Review", "Situation"] = "Original"

        a_est.rename(columns={"Sprint estimation": "Duration estimate"}, inplace=True)
        a_est = self._add_init_duration_columns(a_est, self.col_init_estimate, self.col_duration_estimate)

        index_add = len(a_est.index)
        a_est.at[index_add, self.col_init_estimate] = 0
        a_est.at[index_add, self.col_duration_estimate] = self.weeks_time[2]
        a_est.at[index_add, "Issue key"] = "Total"

        return a_est

    def _add_bar_plot(self, da, situation: str, col_init, col_duration, color_bar, bar_type="Estimate"):
        d_orig = da.loc[da["Situation"] == situation]

        index_plot = (
            d_orig["Issue key"].tolist()
            if bar_type == "Estimate"
            else [("S_" + i) for i in d_orig["Issue key"].tolist()]
        )
        init, duration = (d_orig[col_init].tolist(), d_orig[col_duration].tolist())

        if index_plot != []:
            plt.barh(index_plot, init, height=self.height, visible=False)
            plt.barh(
                index_plot, duration, left=init, color=color_bar, height=self.height, label=bar_type + " - " + situation
            )

    def prepare_data_plot(self):
        df_assignee = self._add_task_situation(self.df, self.df_plan)

        estimate_data = self.prepare_estimate_data(df_assignee, self.df_plan)
        spent_data = self.prepare_spent_data(df_assignee)

        # Revert list order
        estimate_data = estimate_data.reindex(index=estimate_data.index[::-1])
        spent_data = spent_data.reindex(index=spent_data.index[::-1])

        return estimate_data, spent_data

    def plot_timeline(self):
        estimate_data, spent_data = self.prepare_data_plot()

        fig = plt.figure(figsize=(12, 5))
        if self.type_plot == "assignee":
            plt.title(self.df["Assignee"][0])

        # Total bar
        total = estimate_data.loc[estimate_data["Issue key"] == "Total"]
        index_plot, init, duration = (
            total["Issue key"].tolist(),
            total[self.col_init_estimate].tolist(),
            total[self.col_duration_estimate].tolist(),
        )
        plt.barh(index_plot, duration, left=init, color="lightsteelblue", height=self.height, label="Total Time")

        # Spent data
        self._add_bar_plot(spent_data, "Added", self.col_init_spent, self.col_duration_spent, "lightskyblue", "Spent")
        self._add_bar_plot(spent_data, "Relocated", self.col_init_spent, self.col_duration_spent, "royalblue", "Spent")
        self._add_bar_plot(spent_data, "Original", self.col_init_spent, self.col_duration_spent, "darkblue", "Spent")

        # Estimated data
        self._add_bar_plot(estimate_data, "Added", self.col_init_estimate, self.col_duration_estimate, "lime")
        self._add_bar_plot(estimate_data, "Relocated", self.col_init_estimate, self.col_duration_estimate, "limegreen")
        self._add_bar_plot(estimate_data, "Original", self.col_init_estimate, self.col_duration_estimate, "darkgreen")

        # Weeks deadlines
        plt.axvline(x=self.weeks_time[0], label="1° Semana End", color="coral")
        plt.axvline(x=self.weeks_time[1], label="2° Semana End", color="tomato")
        plt.axvline(x=self.weeks_time[2], label="3° Semana End", color="salmon")

        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        plt.grid(color="gray", linestyle="-", linewidth=0.2)

        return fig

    def _add_bar_plotly(self, fig, da, situation: str, col_init, col_duration, color_bar, bar_type="Estimate"):
        d_orig = da.loc[da["Situation"] == situation]

        index_plot = (
            d_orig["Issue key"].tolist()
            if bar_type == "Estimate"
            else [("S_" + i) for i in d_orig["Issue key"].tolist()]
        )
        init, duration = (d_orig[col_init].tolist(), d_orig[col_duration].tolist())

        if index_plot != []:
            fig.add_trace(
                go.Bar(
                    y=index_plot, x=init, orientation="h", opacity=0.0, marker=dict(color=color_bar), showlegend=False
                )
            )

            fig.add_trace(
                go.Bar(
                    y=index_plot,
                    x=duration,
                    name=bar_type + " - " + situation,
                    orientation="h",
                    marker=dict(color=color_bar),
                )
            )

            fig.update_layout(barmode="stack")
        return fig

    def plotly_timeline(self):
        estimate_data, spent_data = self.prepare_data_plot()
        fig = go.Figure()

        # Total bar
        total = estimate_data.loc[estimate_data["Issue key"] == "Total"]
        index_plot, init, duration = (
            total["Issue key"].tolist(),
            total[self.col_init_estimate].tolist(),
            total[self.col_duration_estimate].tolist(),
        )
        fig.add_trace(
            go.Bar(y=index_plot, x=duration, name="Total Time", orientation="h", marker=dict(color="lightsteelblue"))
        )

        # Spent data
        fig = self._add_bar_plotly(
            fig,
            spent_data,
            "Added",
            self.col_init_spent,
            self.col_duration_spent,
            "lightskyblue",
            "Spent",
        )
        fig = self._add_bar_plotly(
            fig,
            spent_data,
            "Relocated",
            self.col_init_spent,
            self.col_duration_spent,
            "royalblue",
            "Spent",
        )
        fig = self._add_bar_plotly(
            fig,
            spent_data,
            "Original",
            self.col_init_spent,
            self.col_duration_spent,
            "darkblue",
            "Spent",
        )

        # Estimated data
        fig = self._add_bar_plotly(
            fig, estimate_data, "Added", self.col_init_estimate, self.col_duration_estimate, "lime"
        )
        fig = self._add_bar_plotly(
            fig, estimate_data, "Relocated", self.col_init_estimate, self.col_duration_estimate, "limegreen"
        )
        fig = self._add_bar_plotly(
            fig, estimate_data, "Original", self.col_init_estimate, self.col_duration_estimate, "#01870F"
        )

        # Weeks deadlines
        fig.add_vline(
            x=self.weeks_time[0],
            line_width=2,
            line_color="#F55D01",
            label=dict(text="1 week", textposition="start", font=dict(size=12, color="#F55D01")),
        )
        fig.add_vline(
            x=self.weeks_time[1],
            line_width=2,
            line_color="#F55D01",
            label=dict(text="2 week", textposition="start", font=dict(size=12, color="#F55D01")),
        )
        fig.add_vline(
            x=self.weeks_time[2],
            line_width=2,
            line_color="#F55D01",
            label=dict(text="3 week", textposition="start", font=dict(size=12, color="#F55D01")),
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        if self.type_plot == "all":
            fig.update_layout(
                autosize=False,
                width=1200,
                height=600,
            )

        return fig
