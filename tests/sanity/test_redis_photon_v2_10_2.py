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


IMAGE_NAME = "redis-photon"
IMAGE_TAG = "v2.10.2"
ORIGINAL_IMAGE = f"docker.io/goharbor/{IMAGE_NAME}:{IMAGE_TAG}"


@pytest.mark.abort_on_fail
def test_rock_contains_files(rock_test_env):
    """Test ROCK contains same fileset as original image."""

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, IMAGE_TAG, "amd64")
    rock_image = rock_meta.image

    paths_to_check = [
        "/usr/bin/docker-healthcheck",
        "/etc/redis.conf",
        "/var/lib/redis",
    ]
    docker_util.ensure_image_contains_paths(
        rock_image, paths_to_check)

