# dh-action-run-python-code

This action runs Python code against Deephaven. It works with both .py files and .md files. For .md files, code between the Python ticks is extracted.

## Parameters

| Parameter | Description | Required |
|--|--|--|
| directory | The path to the directory to run the code | Yes |
| host | The host name or IP address of the Deephaven instance | Yes |
| port | The port to access on the host | Yes |
| max-retries | The maximum attempts to retry connecting to Deephaven | No |

## Example

- name: Run PR check
uses: jakemulf/dh-action-run-python-code
with:
  directory: ./test
  host: localhost
  port: 10000
