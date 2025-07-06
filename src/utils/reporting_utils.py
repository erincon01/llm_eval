import os

import numpy as np
import pandas as pd
import tabulate


def _print_and_log(message: str, log_file_path: str) -> None:
    """Print message to console and append to log file."""
    print(message)
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def performance_report(results_path: str, file_name_prefix: str, data_source: str = None) -> None:
    """
    Load all the CSV files in the results_path folder that start with the file_name_prefix.
    Calculate the performance of each model based on the number of rows, columns, time taken
    to execute the SQL query, and token costs.

    :param results_path: Path to the results folder.
    :param file_name_prefix: Prefix of the files to consolidate.
    :param data_source: Optional filter to include only files that contain this string in the filename.
    :return: None
    """
    # Search for the generated files
    filtered_files = []

    for file in os.listdir(results_path):
        file_path = os.path.join(results_path, file)
        if (os.path.isfile(file_path) and
                file.startswith(file_name_prefix) and
                file.endswith(".csv")):
            
            # Apply data_source filter if provided
            if data_source is None or data_source in file:
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
            "Rows_equality": "rows_equality",
            "Columns_equality": "columns_equality",
            "Datasets_equality": "datasets_equality",
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
        "rows_equality",
        "columns_equality",
        "datasets_equality",
        "cost_input_tokens_EUR",
        "cost_output_tokens_EUR",
    ]

    missing_columns = [col for col in required_columns if col not in all_data.columns]
    if missing_columns:
        print(f"The following required columns are missing in the data: {missing_columns}")
        return

    # Calculate the total token cost
    all_data["total_cost_tokens_EUR"] = all_data["cost_input_tokens_EUR"] + all_data["cost_output_tokens_EUR"]

    # Create log file path
    log_file_name = f"performance_report_{data_source}.txt" if data_source else "performance_report.txt"
    log_file_path = os.path.join(results_path, log_file_name)
    
    # Remove existing log file if it exists
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    if data_source:
        _print_and_log(f"Data source: {data_source}", log_file_path)

    # Generate performance reports
    _generate_model_performance_report(all_data, log_file_path)
    _generate_query_performance_report(all_data, log_file_path)
    _generate_ranking_reports(all_data, log_file_path)
    
    print(f"\nPerformance report saved to: {log_file_path}")


def _generate_model_performance_report(all_data: pd.DataFrame, log_file_path: str) -> None:
    """Generate performance report aggregated by model."""
    agg = (
        all_data.groupby("model")
        .agg(
            queries_executed=("question", "count"),
            mean_sql_time=("sql_time", "mean"),
            mean_llm_time=("llm_time", "mean"),
            stdev_llm_time=("llm_time", "std"),
            mean_tokens=("total_tokens", "mean"),
            mean_datasets_equality=("datasets_equality", "mean"),
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
        "mean_datasets_equality",
    ]
    agg[cols_to_round] = agg[cols_to_round].round(2)
    agg["mean_cost_EUR"] = agg["mean_cost_EUR"].round(6)

    _print_and_log("\nPerformance Report per model:\n", log_file_path)
    table_output = tabulate.tabulate(agg, headers="keys", tablefmt="pipe", showindex=False)
    _print_and_log(table_output, log_file_path)


def _generate_query_performance_report(all_data: pd.DataFrame, log_file_path: str) -> None:
    """Generate performance report aggregated by query."""
    agg_queries = (
        all_data.groupby(["question"])
        .agg(
            mean_llm_time=("llm_time", "mean"),
            stdev_llm_time=("llm_time", "std"),
            mean_rows_equality=("rows_equality", "mean"),
            mean_columns_equality=("columns_equality", "mean"),
            mean_datasets_equality=("datasets_equality", "mean"),
        )
        .reset_index()
    )

    cols_to_round = [
        "mean_llm_time",
        "stdev_llm_time",
        "mean_rows_equality",
        "mean_columns_equality",
        "mean_datasets_equality",
    ]
    agg_queries[cols_to_round] = agg_queries[cols_to_round].round(2)

    _print_and_log("\nPerformance Report per query:\n", log_file_path)
    table_output = tabulate.tabulate(agg_queries, headers="keys", tablefmt="pipe", showindex=False)
    _print_and_log(table_output, log_file_path)


def _generate_ranking_reports(all_data: pd.DataFrame, log_file_path: str) -> None:
    """Generate ranking reports for different metrics."""
    agg = (
        all_data.groupby("model")
        .agg(
            mean_llm_time=("llm_time", "mean"),
            mean_cost_EUR=("total_cost_tokens_EUR", "mean"),
            mean_datasets_equality=("datasets_equality", "mean"),
        )
        .reset_index()
    )

    # Round values
    agg["mean_llm_time"] = agg["mean_llm_time"].round(2)
    agg["mean_cost_EUR"] = agg["mean_cost_EUR"].round(6)
    agg["mean_datasets_equality"] = agg["mean_datasets_equality"].round(2)

    # Best models by LLM time
    best_models = agg.sort_values(by="mean_llm_time")
    _print_and_log("\nBest models based on average LLM time:\n", log_file_path)
    table_output = tabulate.tabulate(
        best_models[["model", "mean_llm_time"]],
        headers="keys",
        tablefmt="pipe",
        showindex=False,
    )
    _print_and_log(table_output, log_file_path)

    # Best models by cost
    best_cost_models = agg.sort_values(by="mean_cost_EUR")
    _print_and_log("\nBest models based on mean token cost:\n", log_file_path)
    table_output = tabulate.tabulate(
        best_cost_models[["model", "mean_cost_EUR"]],
        headers="keys",
        tablefmt="pipe",
        showindex=False,
    )
    _print_and_log(table_output, log_file_path)

    # Best models by data quality
    best_data_rows_equality = agg.sort_values(by="mean_datasets_equality", ascending=False)
    _print_and_log("\nBest models based on average datasets equality:\n", log_file_path)
    table_output = tabulate.tabulate(
        best_data_rows_equality[["model", "mean_datasets_equality"]],
        headers="keys",
        tablefmt="pipe",
        showindex=False,
    )
    _print_and_log(table_output, log_file_path)

    # Generate combined ranking
    _generate_combined_ranking(agg, log_file_path)


def _generate_combined_ranking(agg: pd.DataFrame, log_file_path: str) -> None:
    """Generate combined ranking based on quality, time, and price."""
    # Create rankings
    agg["rank_quality"] = agg["mean_datasets_equality"].rank(method="min", ascending=False).astype(int)
    agg["rank_price"] = agg["mean_cost_EUR"].rank(method="min", ascending=True).astype(int)
    agg["rank_time"] = agg["mean_llm_time"].rank(method="min", ascending=True).astype(int)

    cols_rank = ["rank_quality", "rank_time", "rank_price"]

    # Convert rankings greater than 8 to empty string
    for col in cols_rank:
        agg[col] = agg[col].apply(lambda x: str(x) if x <= 8 and x > 0 else "")

    # Add values in parentheses for non-empty rankings
    agg["rank_quality"] = agg.apply(
        lambda row: (
            f"{row['rank_quality']} ({row['mean_datasets_equality']})" if row["rank_quality"] != "" else ""
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

    _print_and_log("\n\nRanking of the models based on the total cost, LLM time and source rows equality:\n", log_file_path)
    table_output = tabulate.tabulate(
        agg[["model", "rank_quality", "rank_time", "rank_price"]],
        headers="keys",
        tablefmt="pipe",
        showindex=False,
    )
    _print_and_log(table_output, log_file_path)

    _print_and_log("\n\n", log_file_path)
