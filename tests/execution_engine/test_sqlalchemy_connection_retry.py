from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)


try:
    import sqlalchemy as sa

    sqlalchemy_not_installed = False
except ImportError:
    sqlalchemy_not_installed = True


pytestmark = [
    pytest.mark.skipif(sqlalchemy_not_installed, reason="sqlalchemy not installed"),
    pytest.mark.unit,
]


class TestConnectionRetryParameters:
    def test_default_retry_count_is_zero(self):
        engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")
        assert engine._connection_retry_count == 0

    def test_default_backoff_factor(self):
        engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")
        assert engine._connection_retry_backoff_factor == 0.5

    def test_custom_retry_count(self):
        engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=3,
        )
        assert engine._connection_retry_count == 3

    def test_custom_backoff_factor(self):
        engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_backoff_factor=1.0,
        )
        assert engine._connection_retry_backoff_factor == 1.0


class TestConnectWithRetries:
    def test_successful_connection_no_retry(self):
        execution_engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")
        connection = execution_engine._connect_with_retries()
        assert connection is not None
        connection.close()

    def test_no_retry_on_operational_error_when_retry_count_zero(self):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=0,
        )

        mock_connect = MagicMock(
            side_effect=sa.exc.OperationalError("test", {}, Exception("connection refused")),
        )
        execution_engine.engine.connect = mock_connect

        with pytest.raises(sa.exc.OperationalError):
            execution_engine._connect_with_retries()

        assert mock_connect.call_count == 1

    @patch("great_expectations.execution_engine.sqlalchemy_execution_engine.time.sleep")
    def test_retry_succeeds_after_transient_failure(self, mock_sleep):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=2,
        )

        mock_connection = MagicMock()
        execution_engine.engine.connect = MagicMock(
            side_effect=[
                sa.exc.OperationalError("test", {}, Exception("connection refused")),
                mock_connection,
            ]
        )

        result = execution_engine._connect_with_retries()
        assert result is mock_connection
        assert execution_engine.engine.connect.call_count == 2
        mock_sleep.assert_called_once_with(0.5)

    @patch("great_expectations.execution_engine.sqlalchemy_execution_engine.time.sleep")
    def test_retry_exhausted_raises_last_error(self, mock_sleep):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=2,
            connection_retry_backoff_factor=0.5,
        )

        execution_engine.engine.connect = MagicMock(
            side_effect=sa.exc.OperationalError("test", {}, Exception("connection refused")),
        )

        with pytest.raises(sa.exc.OperationalError):
            execution_engine._connect_with_retries()

        assert execution_engine.engine.connect.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.5)
        mock_sleep.assert_any_call(1.0)

    @patch("great_expectations.execution_engine.sqlalchemy_execution_engine.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=3,
            connection_retry_backoff_factor=1.0,
        )

        mock_connection = MagicMock()
        execution_engine.engine.connect = MagicMock(
            side_effect=[
                sa.exc.OperationalError("test", {}, Exception("fail 1")),
                sa.exc.OperationalError("test", {}, Exception("fail 2")),
                sa.exc.OperationalError("test", {}, Exception("fail 3")),
                mock_connection,
            ]
        )

        result = execution_engine._connect_with_retries()
        assert result is mock_connection
        assert mock_sleep.call_count == 3
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)

    def test_non_operational_error_not_retried(self):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=3,
        )

        execution_engine.engine.connect = MagicMock(
            side_effect=ValueError("bad config"),
        )

        with pytest.raises(ValueError, match="bad config"):
            execution_engine._connect_with_retries()

        assert execution_engine.engine.connect.call_count == 1


class TestGetConnectionWithRetries:
    def test_get_connection_uses_retry_logic(self):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=1,
        )

        with execution_engine.get_connection() as connection:
            assert connection is not None

    @patch("great_expectations.execution_engine.sqlalchemy_execution_engine.time.sleep")
    def test_get_connection_retries_on_failure(self, mock_sleep):
        execution_engine = SqlAlchemyExecutionEngine(
            connection_string="sqlite://",
            connection_retry_count=1,
        )

        mock_connection = MagicMock()
        mock_connection.close = MagicMock()
        with patch.object(
            execution_engine.engine,
            "connect",
            side_effect=[
                sa.exc.OperationalError("test", {}, Exception("connection refused")),
                mock_connection,
            ],
        ):
            with execution_engine.get_connection() as connection:
                assert connection is mock_connection
