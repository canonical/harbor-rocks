#
# Copyright 2024 Canonical, Ltd.
#

import logging
import re
import sys

import pytest
from k8s_test_harness.util import docker_util, env_util, platform_util

LOG: logging.Logger = logging.getLogger(__name__)

LOG.addHandler(logging.FileHandler(f"{__name__}.log"))
LOG.addHandler(logging.StreamHandler(sys.stdout))


IMAGE_NAME = "harbor-portal"
IMAGE_VERSIONS = ["v2.6.3", "v2.9.3", "v2.10.2"]


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_check_rock_contains_files(image_version):
    """Test ROCK contains expected files"""

    architecture = platform_util.get_current_rockcraft_platform_architecture()

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, image_version, architecture
    )
    rock_image = rock_meta.image

    image_files_to_check = [
        # Nginx-related dirs:
        "/home/nginx",
        "/var/log/nginx",
    ]
    docker_util.ensure_image_contains_paths(rock_image, image_files_to_check)


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_compare_rock_files_to_original(image_version):
    """Test ROCK contains same fileset as original image."""

    original_image = f"docker.io/goharbor/{IMAGE_NAME}:{image_version}"
    architecture = platform_util.get_current_rockcraft_platform_architecture()

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, image_version, architecture
    )
    rock_image = rock_meta.image

    dir_to_check = "/usr/share/nginx/html"

    original_image_files = docker_util.list_files_under_container_image_dir(
        original_image, root_dir=dir_to_check
    )
    rock_image_files = docker_util.list_files_under_container_image_dir(
        rock_image, root_dir=dir_to_check
    )

    # NOTE(aznashwan): the names of main.js have randomized tags:
    main_js_re = re.compile("(/usr/share/nginx/html/main\\..*\\.js)")
    original_image_main = [f for f in original_image_files if main_js_re.match(f)]
    rock_image_main = [f for f in rock_image_files if main_js_re.match(f)]
    if original_image_main and not rock_image_main:
        pytest.fail(
            f"ROCK image seems to be missing a main.*.js file. "
            f"Original image's main: {original_image_main}. All "
            f"ROCK files under {dir_to_check}: {rock_image_files}"
        )

    rock_fileset = set(rock_image_files) - set(rock_image_main)
    original_fileset = set(original_image_files) - set(original_image_main)

    original_extra_files = original_fileset - rock_fileset
    if original_extra_files:
        pytest.fail(
            f"Missing some files from the original image: " f"{original_extra_files}"
        )

    rock_extra_files = rock_fileset - original_fileset
    if rock_extra_files:
        pytest.fail(
            f"Rock has extra files not present in original image: "
            f"{rock_extra_files}"
        )

    # Nginx-related dirs:
    image_files_to_check = [
        "/home/nginx",
        "/var/log/nginx",
    ]
    docker_util.ensure_image_contains_paths(rock_image, image_files_to_check)
