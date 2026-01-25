import pytest
from unittest.mock import MagicMock
import pandas as pd
from great_expectations.validator.metrics_calculator import MetricsCalculator

def test_head_with_pyspark_style_dataframe_no_reset_index():
    """
    이슈 #11617 재발 방지 테스트: 
    reset_index가 없는 객체(예: PySpark DataFrame)가 들어와도 에러가 나지 않아야 함.
    """
    # 1. Setup: MetricsCalculator와 가짜 객체 생성
    mock_engine = MagicMock()
    calculator = MetricsCalculator(execution_engine=mock_engine)
    
    # reset_index가 없는 가짜 객체 (PySpark 스타일)
    class FakeSparkDataFrame:
        def __repr__(self): return "<Fake Spark DataFrame>"
        
    fake_df = FakeSparkDataFrame()
    calculator.get_metric = MagicMock(return_value=fake_df)
    
    # 2. Execution: 에러 없이 실행되는지 확인
    try:
        result = calculator.head(n_rows=5)
    except AttributeError as e:
        pytest.fail(f"AttributeError raised: {e}. PySpark compatibility issue is not fixed.")

    # 3. Assertion: 결과값이 잘 반환되었는지 확인
    assert result == fake_df