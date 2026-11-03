import public_salaries
from public_salaries import portals


def test_package_imports():
    assert public_salaries.__version__ == "0.1.0"
    assert portals.__name__ == "public_salaries.portals"
