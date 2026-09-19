"""Compatibility facade for the SEMIROH semantic reference model.

The implementation is decomposed into the semiroh package.
This module preserves the previous import and execution entry point.
"""

from semiroh import *


def run_all_tests() -> None:
    from test_identity_model import run_all_tests as run_tests

    run_tests()


if __name__ == "__main__":
    run_all_tests()
    print("All identity/version/reference tests passed.")
