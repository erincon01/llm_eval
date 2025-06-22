from typing import Tuple

import numpy as np
import pandas as pd


def normalize_numeric_columns(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Normalizes numeric columns in both DataFrames to the smallest shared decimal precision.

    :param df1: First DataFrame.
    :param df2: Second DataFrame.
    :return: Tuple containing (normalized df1, normalized df2).
    """
    # Identify numeric columns in both DataFrames
    numeric_columns = df1.select_dtypes(include=[np.number]).columns.intersection(
        df2.select_dtypes(include=[np.number]).columns
    )

    for col in numeric_columns:
        # Determine the smallest decimal precision for the column in both DataFrames
        df1_precisions = df1[col].dropna().apply(lambda x: len(str(x).split(".")[1]) if "." in str(x) else 0)
        df2_precisions = df2[col].dropna().apply(lambda x: len(str(x).split(".")[1]) if "." in str(x) else 0)

        min_precision = min(df1_precisions.min(), df2_precisions.min())

        # Round both DataFrames to the smallest shared precision
        df1[col] = df1[col].round(min_precision)
        df2[col] = df2[col].round(min_precision)

    return df1, df2


def align_columns_by_first_row(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aligns the columns of df2 to match the order of df1 based on the first row's values.

    :param df1: Reference DataFrame (baseline).
    :param df2: DataFrame to reorder (LLM generated).
    :return: Tuple containing (df1, df2 with reordered columns).
    """
    if df1.empty or df2.empty:
        return df1, df2

    # Get the first row of both DataFrames
    df1_first_row = df1.iloc[0].tolist()
    df2_first_row = df2.iloc[0].tolist()

    # Create a mapping of df1 column names to their values in the first row
    df1_mapping = {col: val for col, val in zip(df1.columns, df1_first_row)}

    # Create a mapping of df2 column names to their values in the first row
    df2_mapping = {col: val for col, val in zip(df2.columns, df2_first_row)}

    # Determine the order of df2 columns based on matching values in df1
    ordered_columns = []
    for df1_col, df1_val in df1_mapping.items():
        for df2_col, df2_val in df2_mapping.items():
            if df1_val == df2_val:
                ordered_columns.append(df2_col)
                break

    # Reorder df2 columns to match the determined order
    df2 = df2[ordered_columns]

    return df1, df2
