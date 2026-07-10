from __future__ import annotations

import warnings

from great_expectations.compatibility.not_imported import NotImported

SPARK_NOT_IMPORTED = NotImported("pyspark is not installed, please 'pip install pyspark'")

with warnings.catch_warnings():
    # DeprecationWarning: typing.io is deprecated, import directly from typing instead. typing.io will be removed in Python 3.12.  # noqa: E501 # FIXME CoP
    warnings.simplefilter(action="ignore", category=DeprecationWarning)
    try:
        import pyspark
    except ImportError:
        pyspark = SPARK_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

try:
    from pyspark.sql import functions
except (ImportError, AttributeError):
    functions = SPARK_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

try:
    from pyspark.sql import types
except (ImportError, AttributeError):
    types = SPARK_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

try:
    from pyspark import SparkContext
except ImportError:
    SparkContext = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.ml.feature import Bucketizer
except (ImportError, AttributeError):
    Bucketizer = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql import Column
except (ImportError, AttributeError):
    Column = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql.connect.dataframe import DataFrame as ConnectDataFrame
except (ImportError, AttributeError):
    ConnectDataFrame = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql import DataFrame
except (ImportError, AttributeError):
    DataFrame = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql import Row
except (ImportError, AttributeError):
    Row = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql import SparkSession
except (ImportError, AttributeError):
    SparkSession = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql.connect.session import SparkSession as SparkConnectSession
except (ImportError, AttributeError):
    SparkConnectSession = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql import Window
except (ImportError, AttributeError):
    Window = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.sql.readwriter import DataFrameReader
except (ImportError, AttributeError):
    DataFrameReader = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    # pyspark >= 3.4; base class covering both classic and Spark Connect exception hierarchies
    from pyspark.errors import AnalysisException
except (ImportError, AttributeError):
    try:
        from pyspark.sql.utils import AnalysisException  # pyspark < 3.4
    except (ImportError, AttributeError):
        AnalysisException = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    from pyspark.errors import PySparkAttributeError
except (ImportError, AttributeError):
    PySparkAttributeError = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc] # FIXME CoP

try:
    # spark.conf.get() raises this typed error ([SQL_CONF_NOT_FOUND]) when a config key
    # is absent from SQLConf. It is importable from pyspark.errors on modern releases
    # (present since ~3.5); only much older pyspark lacks it and raises a generic
    # Py4JJavaError instead.
    from pyspark.errors import SparkNoSuchElementException
except (ImportError, AttributeError):
    # On those much older pyspark versions the typed error is unavailable. Use a private
    # Exception subclass so that `except SparkNoSuchElementException` remains a valid
    # clause while never matching a real runtime error (unlike the NotImported sentinel,
    # which is not a usable exception type).
    class SparkNoSuchElementException(Exception):  # type: ignore[no-redef] # FIXME CoP
        """Placeholder keeping `except SparkNoSuchElementException` valid on old pyspark."""
