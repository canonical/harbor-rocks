# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import pytest
import sys

from k8s_test_harness.util import docker_util
from k8s_test_harness.util import env_util


LOG: logging.Logger = logging.getLogger(__name__)

LOG.addHandler(logging.FileHandler(f"{__name__}.log"))
LOG.addHandler(logging.StreamHandler(sys.stdout))


IMAGE_NAME = "harbor-db"
IMAGE_TAG = "v2.10.2"
ORIGINAL_IMAGE = f"docker.io/goharbor/{IMAGE_NAME}:{IMAGE_TAG}"


@pytest.mark.abort_on_fail
def test_check_rock_contains_files():
    """Test ROCK contains same fileset as original image."""

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, IMAGE_TAG, "amd64")
    rock_image = rock_meta.image

    image_files_to_check = [
        "/var/lib/postgresql/data",
        "/run/postgresql",
        "/docker-entrypoint.sh",
        "/initdb.sh",
        "/upgrade.sh",
        "/docker-healthcheck.sh",
        "/docker-entrypoint-initdb.d/initial-registry.sql",
    ]
    docker_util.ensure_image_contains_paths(
        rock_image, image_files_to_check)
