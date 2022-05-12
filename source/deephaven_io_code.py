"""
deephaven_io_code.py

This script is used to validate the code in regards to the special rules for the deephaven.io repo.

The markdown files in the repo are split based on the `docker-config` tags in the code snippets.
If no `docker-config` is found, then default is assumed. These are then written to files used to
supply the `run_path` parameter to the code runner.
"""
import os
import re

DOCKER_DEFAULT_PYTHON = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples/base/docker-compose.yml"
DOCKER_DEFAULT_GROOVY = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/groovy-examples/docker-compose.yml"
DOCKER_NLTK = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples/NLTK/docker-compose.yml"
DOCKER_PYTORCH = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples/PyTorch/docker-compose.yml"
DOCKER_SCIKIT_LEARN = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples/SciKit-Learn/docker-compose.yml"
DOCKER_TENSORFLOW = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples/TensorFlow/docker-compose.yml"
DOCKER_KAFKA = "https://raw.githubusercontent.com/deephaven/deephaven-core/main/containers/python-examples-redpanda/docker-compose.yml"

DOCKER_CONFIG_TAG_TO_IMAGE = {
    "kafka": DOCKER_KAFKA,
    "pytorch": DOCKER_PYTORCH,
    "tensorflow": DOCKER_TENSORFLOW,
    "scikit_learn": DOCKER_SCIKIT_LEARN,
    "default_python": DOCKER_DEFAULT_PYTHON,
    "default_groovy": DOCKER_DEFAULT_GROOVY
}

docker_configs_to_run = {
    "default_python": set(),
    "default_groovy": set()
}

for file_path in os.popen(f"find ~/deephaven/deephaven.io/core/docs -type f | sort").read().split("\n"):
    if len(file_path) > 0 and file_path.endswith(".md"):
        with open(file_path) as f:
            file_contents = f.read()
            if "docker-config" in file_contents:
                docker_config = re.findall(r'docker-config=(\S+)', file_contents)[0]
                if not docker_config in docker_configs_to_run.keys():
                    docker_configs_to_run[docker_config] = set()
                docker_configs_to_run[docker_config].add(file_path)
            else:
                docker_configs_to_run["default_python"].add(file_path)
                docker_configs_to_run["default_groovy"].add(file_path)

from run_code import main

"""
for docker_config in docker_configs_to_run.keys():
    os.system(f"curl -O {DOCKER_CONFIG_TAG_TO_IMAGE[docker_config]}")
    console_type = "groovy" if "groovy" in docker_config else "python"
    main("localhost", "10000", console_type, docker_configs_to_run[docker_config], max_retries=10,
            docker_compose="docker-compose", reset_between_files=0)
"""
docker_config = "kafka"
os.system(f"curl -O {DOCKER_CONFIG_TAG_TO_IMAGE[docker_config]}")
console_type = "groovy" if "groovy" in docker_config else "python"
main("localhost", "10000", console_type, docker_configs_to_run[docker_config], max_retries=10,
        docker_compose="docker-compose", reset_between_files=0)
