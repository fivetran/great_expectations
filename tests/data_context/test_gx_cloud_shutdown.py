"""Tests pinning the GX Cloud shutdown behavior.

GX Cloud has been shut down. The backend the cloud surface relied on no longer
exists, so the two cloud construction entry points now raise immediately:

* constructing ``CloudDataContext(...)`` directly, and
* calling ``gx.get_context(...)`` in a way that resolves to the cloud branch
  (``mode="cloud"``, ``cloud_mode=True``, a complete set of ``cloud_*`` kwargs,
  or recognized ``GX_CLOUD_*`` environment configuration).

Both entry points raise ``GreatExpectationsError`` with a fixed message and emit
no warning. Calls that do not resolve to the cloud branch -- including a non-cloud
``get_context()`` and an incomplete lone ``cloud_*`` kwarg -- are unaffected and
still build a context. All of these paths are removed in great_expectations 2.0.
"""

from __future__ import annotations

import pathlib
import traceback
import warnings
from typing import Any

import pytest

import great_expectations as gx
from great_expectations.data_context import CloudDataContext, EphemeralDataContext
from great_expectations.data_context.cloud_constants import GXCloudEnvironmentVariable
from great_expectations.data_context.data_context.file_data_context import (
    FileDataContext,
)
from great_expectations.exceptions import GreatExpectationsError
from tests.test_utils import working_directory

# The exact, fixed shutdown message both cloud entry points raise.
SHUTDOWN_MESSAGE = (
    "GX Cloud has been shut down, so this no longer functions "
    "and will be removed in great_expectations 2.0."
)

# A complete set of cloud_* kwargs (sufficient for cloud resolution).
CLOUD_PARAMS_COMPLETE: dict[str, Any] = {
    "cloud_base_url": "localhost:7000",
    "cloud_organization_id": "bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
    "cloud_access_token": "i_am_a_token",
}


@pytest.fixture
def unset_cloud_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no ambient GX_CLOUD_* configuration leaks into a test."""
    for env_var in GXCloudEnvironmentVariable:
        monkeypatch.delenv(env_var, raising=False)


@pytest.fixture
def set_cloud_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a complete recognized GX_CLOUD_* environment configuration."""
    monkeypatch.setenv("GX_CLOUD_BASE_URL", "localhost:7000")
    monkeypatch.setenv("GX_CLOUD_ORGANIZATION_ID", "bd20fead-2c31-4392-bcd1-f1e87ad5a79c")
    monkeypatch.setenv("GX_CLOUD_ACCESS_TOKEN", "i_am_a_token")


def _assert_raising_frame_is_construction_site(exc_info: pytest.ExceptionInfo) -> None:
    """The shutdown error must surface at the cloud construction site.

    The deepest traceback frame should be the cloud construction entry point
    (``CloudDataContext.__init__`` or the ``get_context`` factory), proving the
    error is raised up front rather than terminating inside removed GX Cloud
    backend machinery.
    """
    last_frame = traceback.extract_tb(exc_info.tb)[-1]
    filename = pathlib.Path(last_frame.filename).name
    assert filename in {"cloud_data_context.py", "context_factory.py"}, (
        f"shutdown error surfaced from unexpected frame {last_frame.filename}:"
        f"{last_frame.lineno} ({last_frame.name})"
    )


# ---------------------------------------------------------------------------
# Direct construction (Req 1.1-1.4, 1.6 / 5.2)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cloud_data_context_construction_raises_shutdown_error():
    """Constructing CloudDataContext directly raises the GX Cloud shutdown error."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        CloudDataContext(
            cloud_base_url="localhost:7000",
            cloud_organization_id="bd20fead-2c31-4392-bcd1-f1e87ad5a79c",
            cloud_access_token="i_am_a_token",
        )
    assert str(exc_info.value) == SHUTDOWN_MESSAGE


@pytest.mark.unit
def test_cloud_data_context_construction_surfaces_caller_frame():
    """The direct-construction shutdown error surfaces at the construction site,
    not inside removed GX Cloud backend internals."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        CloudDataContext()
    _assert_raising_frame_is_construction_site(exc_info)


# ---------------------------------------------------------------------------
# get_context() cloud-resolution triggers (Req 2.1, 2.2, 2.5, 2.7 / 5.3)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_context_mode_cloud_raises_shutdown_error(unset_cloud_env_vars):
    """get_context(mode="cloud") raises the GX Cloud shutdown error before building."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        gx.get_context(mode="cloud")
    assert str(exc_info.value) == SHUTDOWN_MESSAGE
    _assert_raising_frame_is_construction_site(exc_info)


@pytest.mark.unit
def test_get_context_cloud_mode_true_raises_shutdown_error(unset_cloud_env_vars):
    """get_context(cloud_mode=True) raises the GX Cloud shutdown error."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        gx.get_context(cloud_mode=True)
    assert str(exc_info.value) == SHUTDOWN_MESSAGE


@pytest.mark.unit
def test_get_context_complete_cloud_kwargs_raises_shutdown_error(unset_cloud_env_vars):
    """get_context() with a complete set of cloud_* kwargs raises the shutdown error."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        gx.get_context(**CLOUD_PARAMS_COMPLETE)
    assert str(exc_info.value) == SHUTDOWN_MESSAGE


# ---------------------------------------------------------------------------
# get_context() env-var path (Req 2.1, 2.4 / 5.3)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_context_cloud_env_config_raises_shutdown_error(set_cloud_env_vars):
    """A recognized GX_CLOUD_* environment configuration alone raises the shutdown
    error, proving the gate reuses the factory's cloud-resolution predicate."""
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        gx.get_context()
    assert str(exc_info.value) == SHUTDOWN_MESSAGE


# ---------------------------------------------------------------------------
# Narrow-gate negatives (Req 2.3, 4.5 / 5.4)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_non_cloud_get_context_returns_usable_context(unset_cloud_env_vars):
    """A non-cloud get_context() call does not raise and returns a usable context."""
    context = gx.get_context()
    assert isinstance(context, EphemeralDataContext)
    # The returned context is usable: its stores are configured.
    assert context.config.stores


@pytest.mark.filesystem
def test_non_cloud_get_context_file_mode_returns_file_context(
    tmp_path: pathlib.Path, unset_cloud_env_vars
):
    """A non-cloud file-mode get_context() does not raise and returns a FileDataContext."""
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)


@pytest.mark.unit
def test_incomplete_lone_cloud_kwarg_resolves_to_non_cloud_context(unset_cloud_env_vars):
    """An incomplete lone cloud_* kwarg (no token/org) does not resolve to the cloud
    branch: it does not raise and yields a non-cloud context."""
    context = gx.get_context(cloud_base_url="localhost:7000")
    assert isinstance(context, EphemeralDataContext)


# ---------------------------------------------------------------------------
# No warning emitted alongside the error (Req 1.5, 6.1)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_direct_construction_emits_no_warning(unset_cloud_env_vars):
    """Direct construction raises the shutdown error without emitting any warning."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE):
            CloudDataContext()
    assert [str(w.message) for w in recorded] == []


@pytest.mark.unit
def test_get_context_cloud_branch_emits_no_warning(unset_cloud_env_vars):
    """The get_context() cloud branch raises the shutdown error without emitting any
    warning (in particular, no DeprecationWarning)."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE):
            gx.get_context(mode="cloud")
    assert [str(w.message) for w in recorded] == []
    assert not any(issubclass(w.category, DeprecationWarning) for w in recorded)


# ---------------------------------------------------------------------------
# mode / cloud_mode precedence and cloud-env interaction (Req 2.1, 2.3, 2.5)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_get_context_mode_cloud_raises_even_with_cloud_mode_false(unset_cloud_env_vars):
    """mode="cloud" always resolves to the cloud branch (cloud_mode is ignored when an
    explicit mode is given), so it raises the shutdown error from the get_context()
    frame even when cloud_mode=False -- the error is not deferred to deeper construction.
    """
    with pytest.raises(GreatExpectationsError, match=SHUTDOWN_MESSAGE) as exc_info:
        gx.get_context(mode="cloud", cloud_mode=False)
    assert str(exc_info.value) == SHUTDOWN_MESSAGE
    _assert_raising_frame_is_construction_site(exc_info)


@pytest.mark.filesystem
def test_get_context_file_mode_does_not_raise_with_cloud_env(
    tmp_path: pathlib.Path, set_cloud_env_vars
):
    """An explicit mode="file" builds a FileDataContext and does not raise, even when a
    complete GX_CLOUD_* configuration is present -- explicit non-cloud modes never
    resolve to the cloud branch."""
    with working_directory(tmp_path):
        context = gx.get_context(mode="file")
    assert isinstance(context, FileDataContext)


@pytest.mark.unit
def test_get_context_ephemeral_mode_does_not_raise_with_cloud_env(set_cloud_env_vars):
    """An explicit mode="ephemeral" builds an EphemeralDataContext and does not raise,
    even when a complete GX_CLOUD_* configuration is present."""
    context = gx.get_context(mode="ephemeral")
    assert isinstance(context, EphemeralDataContext)


@pytest.mark.unit
def test_get_context_cloud_mode_false_opts_out_of_cloud_env(set_cloud_env_vars):
    """With cloud_mode=False and no explicit mode, cloud auto-detection is suppressed:
    get_context() does not raise and resolves to a non-cloud context even when a
    complete GX_CLOUD_* configuration is present."""
    context = gx.get_context(cloud_mode=False)
    assert isinstance(context, EphemeralDataContext)
