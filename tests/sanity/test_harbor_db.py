#
# Copyright 2024 Canonical, Ltd.
#

import logging
import sys

import pytest
from k8s_test_harness.util import docker_util, env_util, platform_util

LOG: logging.Logger = logging.getLogger(__name__)

LOG.addHandler(logging.FileHandler(f"{__name__}.log"))
LOG.addHandler(logging.StreamHandler(sys.stdout))


IMAGE_NAME = "harbor-db"
IMAGE_VERSIONS = ["v2.6.3", "v2.9.3", "v2.10.2"]


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_check_rock_contains_files(image_version):
    """Test ROCK contains same fileset as original image."""

    architecture = platform_util.get_current_rockcraft_platform_architecture()

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, image_version, architecture
    )
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
    docker_util.ensure_image_contains_paths(rock_image, image_files_to_check)
