import re
from typing import Tuple


def remove_quotations(sql_query: str) -> Tuple[str, bool]:
    """
    Remove quotations from the SQL query.

    :param sql_query: SQL query to process.
    :return: Tuple containing (processed SQL query, changed flag).
    """

    changed = False

    # Regex pattern to extract content between ```sql, ```code, or similar delimiters
    patterns = [
        r"```(?:sql|code)?\s*(.*?)\s*```",  # ```sql ... ```
        r"``(?:sql|code)?\s*(.*?)\s*``",  # ``sql ... ``
        r"`(?:sql|code)?\s*(.*?)\s*``",  # ``sql ... ``
    ]

    for pattern in patterns:
        match = re.search(pattern, sql_query, re.DOTALL | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if extracted:
                sql_query = extracted
                changed = True
                break

    return sql_query, changed
