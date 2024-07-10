# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import random
import pytest
import string
import subprocess
import sys

from charmed_kubeflow_chisme.rock import CheckRock

logger: logging.Logger = logging.getLogger(__name__)

logger.addHandler(logging.FileHandler(f"{__name__}.log"))
logger.addHandler(logging.StreamHandler(sys.stdout))


ORIGINAL_IMAGE = "docker.io/goharbor/harbor-core"

@pytest.fixture()
def rock_test_env(tmpdir):
    """Yields a temporary directory and random docker container name, then cleans them up after."""
    container_name = "".join(
        [str(i) for i in random.choices(string.ascii_lowercase, k=8)]
    )
    yield tmpdir, container_name

    try:
        subprocess.run(["docker", "rm", container_name])
    except Exception:
        pass
    # tmpdir fixture we use here should clean up the other files for us


def _list_files_in_image_dir(
        image: str, container_name: str, root_dir: str="/") -> list[str]:
    """Lists all regular file paths under the given dir in the given image."""
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        image,
        "find",
        root_dir,
        "-type",
        "f"
    ]

    proc = subprocess.run(cmd, capture_output=True)
    return [l.decode('utf8').strip() for l in proc.stdout.splitlines()]


@pytest.mark.abort_on_fail
def test_rock(rock_test_env):
    """Test rock."""
    _, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"
    ORIGINAL_ROCK_IMAGE = f"{ORIGINAL_IMAGE}:{rock_version}"

    dir_to_check = "/harbor"

    original_image_files = _list_files_in_image_dir(
        ORIGINAL_ROCK_IMAGE, f"{container_name}-original",
        root_dir=dir_to_check)
    local_rock_files = _list_files_in_image_dir(
        LOCAL_ROCK_IMAGE, container_name, root_dir=dir_to_check)

    rock_fileset = set(local_rock_files)
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
