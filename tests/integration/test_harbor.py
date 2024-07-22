#
# Copyright 2024 Canonical, Ltd.
#
import logging
import os

pytest_plugins = ["k8s_test_harness.plugin"]

LOG = logging.getLogger(__name__)


def test_integration_place_holder():
    # TODO: remove this placeholder test
    # pytest fails if there is no test run
    pass
