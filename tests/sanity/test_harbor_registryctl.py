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


IMAGE_NAME = "harbor-registryctl"
IMAGE_VERSIONS = ["v2.6.3", "v2.9.3", "v2.10.2"]


@pytest.mark.abort_on_fail
@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_compare_rock_files_to_original(image_version):
    """Test ROCK contains same fileset as original image."""

    original_image = f"docker.io/goharbor/{IMAGE_NAME}:{image_version}"
    architecture = platform_util.get_current_rockcraft_platform_architecture()

    rock_meta = env_util.get_build_meta_info_for_rock_version(
        IMAGE_NAME, image_version, architecture)
    rock_image = rock_meta.image

    dir_to_check = "/home/harbor"

    original_image_files = docker_util.list_files_under_container_image_dir(
        original_image, root_dir=dir_to_check)
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

    # NOTE(aznashwan): the registryctl image also embeds a `registry` binary:
    # https://github.com/goharbor/harbor/blob/v2.10.2/make/photon/registryctl/Dockerfile#L6
    docker_util.ensure_image_contains_paths(
        rock_image, ["/usr/bin/registry_DO_NOT_USE_GC"])
