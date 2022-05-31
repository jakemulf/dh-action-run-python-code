"""
deephaven_io_code.py

This script is used to validate the code in regards to the special rules for the deephaven.io repo.

The markdown files in the repo are split based on the `docker-config` tags in the code snippets.
If no `docker-config` is found, then default is assumed. These are then written to files used to
supply the `run_path` parameter to the code runner.
"""
from run_code import run_code_main

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

def deephaven_io_code_main(deephaven_io_path: str, reset_between_files: int):
    """
    Main method for the deephaven_io_code.py file. Reads all the markdown files in the directory, organizes them
    by `docker-config` tags, and runs the `run_code` main method against each set of markdown files.

    Parameters:
        deephaven_io_path (str): The path to the markdown files to run in the deephaven.io project.
            This should be something like deephaven.io/core/docs for community docs
        reset_between_files (int): Code snippet count for resetting the docker instance. Set to 0
            to reset between every code snippet, None to not reset, or any number to reset
            after that number of code snippet runs
    """
    docker_configs_to_run = {
        "default_python": set(),
        "default_groovy": set()
    }

    for file_path in os.popen(f"find {deephaven_io_path} -type f -name \"*.md\" | sort").read().split("\n"):
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

    failed = False
    for docker_config in docker_configs_to_run.keys():
        os.system(f"curl -O {DOCKER_CONFIG_TAG_TO_IMAGE[docker_config]}")
        console_type = "groovy" if "groovy" in docker_config else "python"
        (success_files, skipped_files, error_files) = run_code_main("localhost", "10000", console_type, docker_configs_to_run[docker_config], max_retries=20,
                docker_compose="docker-compose", reset_between_files=reset_between_files)

        if len(skipped_files) > 0:
            print(f"Skipped {len(skipped_files)} files")
        if len(success_files) > 0:
            print(f"{len(success_files)} files ran without errors")
        if len(error_files) > 0:
            error_files_print = "\n".join(error_files)
            print(f"Errors were found in the following files:\n{error_files_print}")
            failed = True

    os.system("rm docker-compose.yml")
    if failed:
        sys.exit("At least 1 file failed to run. Check the logs for information on what failed")

usage = """
usage: python deephaven_io_code.py <deephaven_io_path> <reset_between_files>
"""

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 3:
        sys.exit(usage)

    try:
        deephaven_io_path = sys.argv[1]
        reset_between_files = int(sys.argv[2])
    except:
        sys.exit(usage)

    deephaven_io_code_main(deephaven_io_path, reset_between_files)
