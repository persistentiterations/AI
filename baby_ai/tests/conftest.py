"""Shared fixtures: deterministic activation IDs per test + artifact dir."""

import pytest

from baby_ai._env import PACKAGE


@pytest.fixture()
def artifacts_dir(tmp_path):
    return tmp_path


@pytest.fixture()
def seed_item():
    return "flux_alpha"


@pytest.fixture()
def related_item():
    return "flux_beta"


@pytest.fixture()
def provenance_loaded():
    import baby_ai._env as env

    env.bootstrap()
    return env.organ_provenance()