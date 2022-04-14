# dh-action-run-python-code

This package runs code against Deephaven. It works with both code files (currently .py and .groovy) and .md files. For .md files, code between the Python/Groovy ticks is extracted.

## Usage

Run `python source/script.py -h` to display the usage of the package

## Overview

This package connects to Deephaven via the [pydeephaven](https://pypi.org/project/pydeephaven/) package, and then runs scripts in Deephaven. The `host`, `port`, and `session_type` parameters are used to connect to Deephaven, and the `run_path` parameter tells the package what files to run.

### `run_path` and `ignore_path`

`run_path` can be a path to either a file or a directory. If it's a file, the package is expecting the file to contain a line separated list of files and/or directories. For each file found, its code is ran in Deephaven, and for each directory found, all files in the directory and its sub directories are ran in Deephaven. If `run_path` points to a directory, all the files in the directory and its sub directories are ran in Deephaven.

The `ignore_path` parameter works just like `run_path`, except it tells the package what files to not run.

`run_path` and `ignore_path` work with both relative and absolute paths. Relative paths must start with `./`

### `docker_compose` and `reset_between_files`

This package can connect to any instance of Deephaven running anywhere. However, extra features are supported for local instances of Deephaven that are launched through Docker with the `docker_compose` and `reset_between_files` flags.

`docker_compose` simply defines the base `docker-compose` command to execute when launching the package. This will typically look like `VERSION=<deephaven_version> docker-compose -f <path/to/deephaven/docker-compose.yml>`.

If `reset_between_files` is defined, the package will reset the `docker_compose` instance after `reset_between_files` files have ran. This will run `"{docker_compose} stop"` and then `"{docker_compose} up -d"`.

## Examples

Examples of code files and config files can be found in the `./test` directory.

`./test/sample.sh` shows a few examples of various CLI commands to run the package.
