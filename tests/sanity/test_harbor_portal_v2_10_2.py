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


IMAGE_NAME = "harbor-portal"
IMAGE_TAG = "v2.10.2"
ORIGINAL_IMAGE = f"docker.io/goharbor/{IMAGE_NAME}:{IMAGE_TAG}"


@pytest.mark.abort_on_fail
def test_check_rock_contains_files(rock_test_env):
    """Test ROCK contains expected files"""

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, IMAGE_TAG, "amd64")
    rock_image = rock_meta.image

    image_files_to_check = [
        # Nginx-related dirs:
        "/home/nginx",
        "/var/log/nginx",
    ]
    docker_util.ensure_image_contains_paths(
        rock_image, image_files_to_check)

@pytest.mark.abort_on_fail
def test_compare_rock_files_to_original(rock_test_env):
    """Test ROCK contains same fileset as original image."""

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, IMAGE_TAG, "amd64")
    rock_image = rock_meta.image

    dir_to_check = "/usr/share/nginx/html"

    original_image_files = docker_util.list_files_under_container_image_dir(
        ORIGINAL_IMAGE, root_dir=dir_to_check)
    rock_image_files = docker_util.list_files_under_container_image_dir(
        rock_image, root_dir=dir_to_check)

    rock_fileset = set(rock_image_files)
    original_fileset = set(original_image_files)

    original_extra_files = original_fileset - rock_fileset
    if original_extra_files:
        pytest.fail(
            f"Missing some files from the original image: "
            f"{original_extra_files}")

    rock_extra_files = rock_fileset - original_fileset
    if rock_extra_files:
        pytest.fail(
            f"Rock has extra files not present in original image: "
            f"{rock_extra_files}")

    # Nginx-related dirs:
    image_files_to_check = [
        "/home/nginx",
        "/var/log/nginx",
    ]
    docker_util.ensure_image_contains_paths(
        rock_image, image_files_to_check)
