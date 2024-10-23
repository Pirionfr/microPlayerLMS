"""Initial documentation of MicroPlayer."""
import logging
import os

assets = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')


def get_asset_path(filename):
    return os.path.join(assets, filename)
