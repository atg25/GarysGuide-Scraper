from garys_nyc_events import __version__


def test_package_version_exposed():
    assert isinstance(__version__, str)
    assert __version__
