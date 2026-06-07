import pytest_asyncio  # noqa: F401

# Configure pytest-asyncio mode
def pytest_collection_modifyitems(config, items):
    pass


# pytest-asyncio mode
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: async test")
