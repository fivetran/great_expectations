"""Lazy compatibility wrapper for the optional Hugging Face Datasets package."""

from __future__ import annotations

from typing import Any

from great_expectations.compatibility.not_imported import NotImported

_NOT_IMPORTED = NotImported(
    "Hugging Face Datasets support requires the optional 'datasets' package. "
    "Install it with `pip install 'great-expectations[huggingface]'`."
)


def load_dataset(*args: Any, **kwargs: Any) -> Any:
    """Load a Hugging Face dataset, importing the optional dependency on demand."""
    try:
        from datasets import load_dataset as hf_load_dataset
    except ImportError:
        return _NOT_IMPORTED(*args, **kwargs)
    return hf_load_dataset(*args, **kwargs)


def get_download_config_class() -> Any:
    """Return the optional DownloadConfig class when installed."""
    try:
        from datasets import DownloadConfig
    except ImportError:
        return _NOT_IMPORTED
    return DownloadConfig


def get_datasets_module() -> Any:
    """Import and return the optional package on demand."""
    try:
        import datasets as hf_datasets
    except ImportError:
        return _NOT_IMPORTED
    return hf_datasets
