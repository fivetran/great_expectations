from great_expectations.expectations.expectation import ColumnMapExpectation
import re

class ExpectColumnValuesToBeValidChineseIdCard(ColumnMapExpectation):
    """验证中国身份证号（15位/18位）"""
    map_metric = "column_values.valid_chinese_id_card"
    success_keys = ("mostly",)

    def validate_id(self, id_str: str) -> bool:
        if not isinstance(id_str, str):
            return False
        id_str = id_str.strip()
        if len(id_str) not in (15, 18):
            return False
        if len(id_str) == 18:
            if not re.match(r"^\d{17}[\dXx]$", id_str):
                return False
        else:
            if not re.match(r"^\d{15}$", id_str):
                return False
        return True