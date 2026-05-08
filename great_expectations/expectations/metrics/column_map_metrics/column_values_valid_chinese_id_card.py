from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)


def validate_chinese_id_card(id_str: object) -> bool:
    """Return True if *id_str* is a valid 15- or 18-digit Chinese resident ID number."""
    if id_str is None:
        return False
    try:
        if pd.isna(id_str):
            return False
    except TypeError:
        pass
    if not isinstance(id_str, str):
        id_str = str(id_str).strip()

    id_str = id_str.strip()

    if len(id_str) not in (15, 18):
        return False

    if len(id_str) == 18:
        if not re.match(r"^\d{17}[\dXx]$", id_str):
            return False
    elif not re.match(r"^\d{15}$", id_str):
        return False

    if len(id_str) == 18:
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
        total = sum(int(id_str[i]) * weights[i] for i in range(17))
        if id_str[-1].upper() != check_codes[total % 11]:
            return False

    try:
        if len(id_str) == 18:
            birth_str = id_str[6:14]
        else:
            birth_str = "19" + id_str[6:12]

        if not re.match(r"^\d{8}$", birth_str):
            return False

        year = int(birth_str[:4])
        month = int(birth_str[4:6])
        day = int(birth_str[6:8])

        current_year = datetime.now().year
        if not (1900 <= year <= current_year) or not (1 <= month <= 12) or not (1 <= day <= 31):
            return False
    except Exception:
        return False

    return True


class ColumnValuesValidChineseIdCard(ColumnMapMetricProvider):
    condition_metric_name = "column_values.valid_chinese_id_card"
    filter_column_isnull = True

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return column.apply(validate_chinese_id_card)
