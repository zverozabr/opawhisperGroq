"""Pytest configuration for the test suite."""

import pytest


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Configure Playwright to use system Chrome installation."""
    return {
        **browser_type_launch_args,
        "channel": "chrome",  # Use system Google Chrome
    }
