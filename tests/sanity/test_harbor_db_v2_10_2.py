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


 def _check_file_present_in_image(image: str, path_to_check: str):
     """Checks whether a file with the given path is present within an image."""
     subprocess.run(
         [
             "docker",
             "run",
             image,
             "exec",
             "ls",
             "-la",
             path_to_check,
         ],
         check=True,
     )


@pytest.mark.abort_on_fail
def test_rock(rock_test_env):
    """Test rock."""
    _, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_name()
    rock_version = check_rock.get_version()
    LOCAL_ROCK_IMAGE = f"{rock_image}:{rock_version}"

    image_files_to_check = [
        "/var/lib/postgresql/data",
        "/run/postgresq",
        "/docker-entrypoint.sh",
        "/initdb.sh",
        "/upgrade.sh",
        "/docker-healthcheck.sh",
        "/docker-entrypoint-initdb.d/initial-registry.sql",
    ]

    for file in image_files_to_check:
        _check_file_present_in_image(LOCAL_ROCK_IMAGE, file)
