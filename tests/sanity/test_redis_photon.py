# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import pytest
import sys

from k8s_test_harness.util import docker_util
from k8s_test_harness.util import env_util
from k8s_test_harness.util import platform_util


LOG: logging.Logger = logging.getLogger(__name__)

LOG.addHandler(logging.FileHandler(f"{__name__}.log"))
LOG.addHandler(logging.StreamHandler(sys.stdout))


IMAGE_NAME = "redis-photon"
IMAGE_VERSIONS = ["v2.6.3", "v2.9.3", "v2.10.2"]


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_rock_contains_files(image_version):
    """Test ROCK contains same fileset as original image."""

    architecture = platform_util.get_current_rockcraft_platform_architecture()

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, image_version, architecture)
    rock_image = rock_meta.image

    paths_to_check = [
        "/usr/bin/docker-healthcheck",
        "/etc/redis.conf",
        "/var/lib/redis",
    ]
    docker_util.ensure_image_contains_paths(
        rock_image, paths_to_check)

