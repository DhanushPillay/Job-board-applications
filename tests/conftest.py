from __future__ import annotations

import pytest

import analysis


@pytest.fixture(scope="session")
def cleaned():
    return analysis.clean_data()


@pytest.fixture(scope="session")
def data_path():
    return analysis.DATA_PATH
