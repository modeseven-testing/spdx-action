<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# SPDX License Header Verification

Forked from: <https://github.com/enarx/spdx>

A Github Action that verifies whether project files include a SPDX license
header. If any files do not pass the ruleset for their file type, the test
will fail with some guidance about how to fix it.

## spdx-action

## Usage

Include the action as part of a workflow that performs a checkout. You'll also
need to provide input:

- `licenses`: The accepted SPDX License Identifiers.

Here's an example:

```yml
name: 'SPDX License Header Verification'

on:
  pull_request

jobs:
  check-spdx-headers:
    name: 'File Check'
    runs-on: 'ubuntu-latest'
    steps:
    - name: checkout
      uses: actions/checkout@v4
    - uses: modeseven-testing/spdx@main
      with:
        licenses: |-
          Apache-2.0
          MIT
```

## How it Works

This script basically performs two actions:

1. It identifies the source code language for each file.
2. It validates the SPDX header using the semantics for the language.

If the action cannot identify the language of a file, or when there are no SPDX
comment semantics supported by that file type, processing will move on without
error.

We identify the source code of a language using two strategies:

1. Map the extension to a known language
2. Check the shebang line, if present

## Adding Support for New Languages

Adding support for new languages should be trivial. See the examples for
[Ruby](https://github.com/enarx/spdx/commit/1d7f186e69e3d8d6e5e8837a1d2f0aac20b51942)
and [C/C++](https://github.com/enarx/spdx/commit/32f8b3d964c09dee5e4052336f1271624db29bfb).
