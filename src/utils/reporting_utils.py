import os

import numpy as np
import pandas as pd
import tabulate


def performance_report(results_path: str, file_name_prefix: str) -> None:
    """
    Load all the CSV files in the results_path folder that start with the file_name_prefix.
    Calculate the performance of each model based on the number of rows, columns, time taken
    to execute the SQL query, and token costs.

    :param results_path: Path to the results folder.
    :param file_name_prefix: Prefix of the files to consolidate.
    :return: None
    """
    # Search for the generated files
    filtered_files = []

    for file in os.listdir(results_path):
        file_path = os.path.join(results_path, file)
        if os.path.isfile(file_path) and file.startswith(file_name_prefix) and file.endswith(".csv"):
            filtered_files.append(file_path)

    if not filtered_files:
        print("No files found with the specified prefix.")
        return

    # Read all files into dataframes
    dataframes = []
    for file in filtered_files:
        try:
            df = pd.read_csv(file, sep="\t", encoding="utf-8")
            dataframes.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if not dataframes:
        print("No files could be loaded correctly.")
        return

    # Concatenate all dataframes
    all_data = pd.concat(dataframes, ignore_index=True)

    # Normalize column names
    all_data.rename(
        columns={
            "Model": "model",
            "Question": "question",
            "Rows": "rows",
            "Columns": "columns",
            "SQL_time": "sql_time",
            "LLM_time": "llm_time",
            "Total_tokens": "total_tokens",
            "Prompt_tokens": "prompt_tokens",
            "Completion_tokens": "completion_tokens",
            "Percent_rows_equality": "percent_rows_equality",
            "Percent_columns_equality": "percent_columns_equality",
            "Percent_source_rows_equality": "percent_source_rows_equality",
            "Percent_llm_rows_equality": "percent_llm_rows_equality",
            "Cost_input_tokens_EUR": "cost_input_tokens_EUR",
            "Cost_output_tokens_EUR": "cost_output_tokens_EUR",
        },
        inplace=True,
    )

    # Validate that the required columns exist
    required_columns = [
        "model",
        "question",
        "rows",
        "columns",
        "sql_time",
        "llm_time",
        "total_tokens",
        "prompt_tokens",
        "completion_tokens",
        "percent_rows_equality",
        "percent_columns_equality",
        "percent_source_rows_equality",
        "percent_llm_rows_equality",
        "cost_input_tokens_EUR",
        "cost_output_tokens_EUR",
    ]

    missing_columns = [col for col in required_columns if col not in all_data.columns]
    if missing_columns:
        print(f"The following required columns are missing in the data: {missing_columns}")
        return

    # Calculate the total token cost
    all_data["total_cost_tokens_EUR"] = all_data["cost_input_tokens_EUR"] + all_data["cost_output_tokens_EUR"]

    # Generate performance reports
    _generate_model_performance_report(all_data)
    _generate_query_performance_report(all_data)
    _generate_ranking_reports(all_data)


def _generate_model_performance_report(all_data: pd.DataFrame) -> None:
    """Generate performance report aggregated by model."""
    agg = (
        all_data.groupby("model")
        .agg(
            queries_executed=("question", "count"),
            mean_sql_time=("sql_time", "mean"),
            mean_llm_time=("llm_time", "mean"),
            stdev_llm_time=("llm_time", "std"),
            mean_tokens=("total_tokens", "mean"),
            mean_source_rows_equality=("percent_source_rows_equality", "mean"),
            mean_llm_rows_equality=("percent_llm_rows_equality", "mean"),
            mean_cost_EUR=("total_cost_tokens_EUR", "mean"),
        )
        .reset_index()
    )

    # Round numeric columns
    cols_to_round = [
        "mean_sql_time",
        "mean_llm_time",
        "stdev_llm_time",
        "mean_tokens",
        "mean_source_rows_equality",
        "mean_llm_rows_equality",
    ]
    agg[cols_to_round] = agg[cols_to_round].round(2)
    agg["mean_cost_EUR"] = agg["mean_cost_EUR"].round(6)

    print("\nPerformance Report per model:\n")
    print(tabulate.tabulate(agg, headers="keys", tablefmt="pipe", showindex=False))


def _generate_query_performance_report(all_data: pd.DataFrame) -> None:
    """Generate performance report aggregated by query."""
    agg_queries = (
        all_data.groupby(["question"])
        .agg(
            mean_llm_time=("llm_time", "mean"),
            stdev_llm_time=("llm_time", "std"),
            mean_source_rows_equality=("percent_source_rows_equality", "mean"),
            mean_llm_rows_equality=("percent_llm_rows_equality", "mean"),
            mean_rows_equality=("percent_rows_equality", "mean"),
            mean_columns_equality=("percent_columns_equality", "mean"),
        )
        .reset_index()
    )

    cols_to_round = [
        "mean_llm_time",
        "stdev_llm_time",
        "mean_source_rows_equality",
        "mean_llm_rows_equality",
        "mean_rows_equality",
        "mean_columns_equality",
    ]
    agg_queries[cols_to_round] = agg_queries[cols_to_round].round(2)

    print("\nPerformance Report per query:\n")
    print(tabulate.tabulate(agg_queries, headers="keys", tablefmt="pipe", showindex=False))


def _generate_ranking_reports(all_data: pd.DataFrame) -> None:
    """Generate ranking reports for different metrics."""
    agg = (
        all_data.groupby("model")
        .agg(
            mean_llm_time=("llm_time", "mean"),
            mean_cost_EUR=("total_cost_tokens_EUR", "mean"),
            mean_source_rows_equality=("percent_source_rows_equality", "mean"),
        )
        .reset_index()
    )

    # Round values
    agg["mean_llm_time"] = agg["mean_llm_time"].round(2)
    agg["mean_cost_EUR"] = agg["mean_cost_EUR"].round(6)
    agg["mean_source_rows_equality"] = agg["mean_source_rows_equality"].round(2)

    # Best models by LLM time
    best_models = agg.sort_values(by="mean_llm_time")
    print("\nBest models based on average LLM time:\n")
    print(
        tabulate.tabulate(
            best_models[["model", "mean_llm_time"]],
            headers="keys",
            tablefmt="pipe",
            showindex=False,
        )
    )

    # Best models by cost
    best_cost_models = agg.sort_values(by="mean_cost_EUR")
    print("\nBest models based on mean token cost:\n")
    print(
        tabulate.tabulate(
            best_cost_models[["model", "mean_cost_EUR"]],
            headers="keys",
            tablefmt="pipe",
            showindex=False,
        )
    )

    # Best models by data quality
    best_data_rows_equality = agg.sort_values(by="mean_source_rows_equality", ascending=False)
    print("\nBest models based on average data rows equality:\n")
    print(
        tabulate.tabulate(
            best_data_rows_equality[["model", "mean_source_rows_equality"]],
            headers="keys",
            tablefmt="pipe",
            showindex=False,
        )
    )

    # Generate combined ranking
    _generate_combined_ranking(agg)


def _generate_combined_ranking(agg: pd.DataFrame) -> None:
    """Generate combined ranking based on quality, time, and price."""
    # Create rankings
    agg["rank_quality"] = agg["mean_source_rows_equality"].rank(method="min", ascending=False).astype(int)
    agg["rank_price"] = agg["mean_cost_EUR"].rank(method="min", ascending=True).astype(int)
    agg["rank_time"] = agg["mean_llm_time"].rank(method="min", ascending=True).astype(int)

    cols_rank = ["rank_quality", "rank_time", "rank_price"]

    # Convert rankings greater than 8 to empty string
    for col in cols_rank:
        agg[col] = agg[col].apply(lambda x: str(x) if x <= 8 and x > 0 else "")

    # Add values in parentheses for non-empty rankings
    agg["rank_quality"] = agg.apply(
        lambda row: (
            f"{row['rank_quality']} ({row['mean_source_rows_equality']})" if row["rank_quality"] != "" else ""
        ),
        axis=1,
    )
    agg["rank_time"] = agg.apply(
        lambda row: (f"{row['rank_time']} ({row['mean_llm_time']})" if row["rank_time"] != "" else ""),
        axis=1,
    )
    agg["rank_price"] = agg.apply(
        lambda row: (f"{row['rank_price']} ({row['mean_cost_EUR']})" if row["rank_price"] != "" else ""),
        axis=1,
    )

    # Create auxiliary columns for sorting
    for col in cols_rank:
        agg[f"_sort_{col}"] = agg[col].apply(lambda x: int(str(x).split()[0]) if x != "" else np.inf)

    # Sort using auxiliary columns
    agg = agg.sort_values(by=[f"_sort_{col}" for col in cols_rank], ascending=True).reset_index(drop=True)

    # Remove auxiliary columns
    agg.drop(columns=[f"_sort_{col}" for col in cols_rank], inplace=True)

    print("\n\nRanking of the models based on the total cost, LLM time and source rows equality:\n")
    print(
        tabulate.tabulate(
            agg[["model", "rank_quality", "rank_time", "rank_price"]],
            headers="keys",
            tablefmt="pipe",
            showindex=False,
        )
    )

    print("\n\n")
