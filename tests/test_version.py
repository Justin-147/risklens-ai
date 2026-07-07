from importlib.metadata import version

import risklens


def test_package_version_matches_project_metadata():
    assert risklens.__version__ == version("risklens-ai")
