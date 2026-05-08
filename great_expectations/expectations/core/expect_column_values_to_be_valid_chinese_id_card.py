from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.render import RenderedStringTemplateContent
from great_expectations.render.util import num_to_str, substitute_none_for_missing


class ExpectColumnValuesToBeValidChineseIdCard(ColumnMapExpectation):
    """
    验证列中的值为有效的中国居民身份证号
    - 支持15位（旧版）和18位（新版）身份证
    - 18位身份证会自动验证校验位
    - 简单验证出生日期格式
    """

    examples = [
        {
            "data": {
                "valid_ids": ["110105199003077753", "110105900307775"],
                "invalid_ids": ["123456", "110105199003077759", "abcdefg"],
            },
            "tests": [
                {
                    "title": "测试有效身份证",
                    "exact_match_out": False,
                    "in": {"column": "valid_ids"},
                    "out": {"success": True},
                },
                {
                    "title": "测试无效身份证",
                    "exact_match_out": False,
                    "in": {"column": "invalid_ids"},
                    "out": {"success": False},
                },
            ],
        }
    ]

    map_metric = "column_values.valid_chinese_id_card"
    success_keys = ("mostly",)

    @classmethod
    def _prescriptive_renderer(
        cls,
        configuration=None,
        runtime_configuration=None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        params = substitute_none_for_missing(
            configuration.kwargs,
            ["column", "mostly", "row_condition", "condition_parser"],
        )

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params["mostly_pct"] = num_to_str(params["mostly"] * 100, precision=4, no_scientific=True)
            template_str = "值必须为有效的中国身份证号，至少 $mostly_pct % 的时间满足。"
        else:
            template_str = "值必须为有效的中国身份证号。"

        if include_column_name:
            template_str = "$column " + template_str

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                    },
                }
            )
        ]
