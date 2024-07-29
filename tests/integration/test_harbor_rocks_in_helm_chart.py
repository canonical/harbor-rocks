#
# Copyright 2024 Canonical, Ltd.
#

import json
import logging
import sys

import pytest
from k8s_test_harness import harness
from k8s_test_harness.util import constants, env_util, k8s_util, platform_util

LOG: logging.Logger = logging.getLogger(__name__)

LOG.addHandler(logging.FileHandler(f"{__name__}.log"))
LOG.addHandler(logging.StreamHandler(sys.stdout))


IMAGE_VERSIONS = ["v2.6.3", "v2.9.3", "v2.10.2"]
CHART_RELEASE_URL = (
    "https://github.com/goharbor/harbor-helm/archive/refs/tags/v1.15.0.tar.gz"
)
INSTALL_NAME = "harbor"

# This mapping indicates which fields of the upstream Harbor Helm chart
# contain the 'image' fields which should be overriden with the ROCK
# image URLs and version during testing.
# https://github.com/goharbor/harbor-helm/blob/main/values.yaml
IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP = {
    "harbor-db": "database.internal",
    "harbor-core": "core",
    "harbor-jobservice": "jobservice",
    "harbor-registryctl": "registry.controller",
    "harbor-exporter": "exporter",
    "harbor-portal": "portal",
    "nginx-photon": "nginx",
    "redis-photon": "redis.internal",
    "registry-photon": "registry.registry",
    "trivy-adapter-photon": "trivy",
}


@pytest.mark.parametrize("image_version", IMAGE_VERSIONS)
def test_harbor_chart_deployment(
    function_instance: harness.Instance, image_version: str
):

    architecture = platform_util.get_current_rockcraft_platform_architecture()

    # Compose the Helm command line args for overriding the
    # image fields for each component:
    all_chart_value_overrides_args = []
    found_env_rocks_metadata = []
    all_rocks_meta_info = env_util.get_rocks_meta_info_from_env()

    # NOTE(aznashwan): GitHub actions UI sometimes truncates env values:
    LOG.info(
        f"All built rocks metadata from env was: "
        f"{json.dumps([rmi.__dict__ for rmi in all_rocks_meta_info])}"
    )

    for rmi in all_rocks_meta_info:
        if rmi.name in IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP and (
            rmi.version == image_version and rmi.arch == architecture
        ):
            chart_section = IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP[rmi.name]
            repo, tag = rmi.image.split(":")
            all_chart_value_overrides_args.extend(
                [
                    "--set",
                    f"{chart_section}.image.repository={repo}",
                    "--set",
                    f"{chart_section}.image.tag={tag}",
                ]
            )
            found_env_rocks_metadata.append(rmi.name)

    missing = [
        img
        for img in IMAGE_NAMES_TO_CHART_VALUES_OVERRIDES_MAP
        if img not in found_env_rocks_metadata
    ]
    if missing:
        pytest.fail(
            f"Failed to find built ROCK metadata for images {missing} "
            f"of version '{image_version}' and architecture '{architecture}'. "
            f"All built images metadata was: {all_rocks_meta_info}"
        )

    helm_command = [
        "sudo",
        "k8s",
        "helm",
        "install",
        INSTALL_NAME,
        CHART_RELEASE_URL,
    ]
    helm_command.extend(all_chart_value_overrides_args)

    function_instance.exec(helm_command)

    # NOTE(aznashwan): The harbor-jobservice depends on harbor-core which
    # depends on harbor-db which needs a PVC allocated for it and also has an
    # InitContainer to `chown -R` said PVC, so we add a generous retry period:
    retry_kwargs = {"retry_times": 30, "retry_delay_s": 10}

    # HACK(aznashwan): the `harbor-trivy` StatefulSet should be in this list
    # too, but it consistently fails to have its PVC provisioned on the GitHub
    # amd64 runners despite it seemingly working consistently in local testing.
    stateful_sets = ["harbor-database", "harbor-redis"]
    for stateful_set in stateful_sets:
        k8s_util.wait_for_statefulset(
            function_instance,
            stateful_set,
            **retry_kwargs,
        )

    deployments = [
        "harbor-core",
        "harbor-jobservice",
        "harbor-portal",
        "harbor-registry",
    ]
    for deployment in deployments:
        k8s_util.wait_for_deployment(
            function_instance,
            deployment,
            condition=constants.K8S_CONDITION_AVAILABLE,
            **retry_kwargs,
        )
