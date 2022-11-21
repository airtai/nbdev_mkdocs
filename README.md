Getting Started
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

**nbdev_mkdocs** is a nbdev extension that allows you to use [Material
for MkDocs](https://squidfunk.github.io/mkdocs-material/) to generate
documentation for nbdev projects.

## Workflow

A typical development workflow for making changes to an existing nbdev
project looks like:

1.  Developer makes changes and then run `nbdev_prepare`.
2.  Runs `nbdev_preview` to see a local preview of the documentation.
3.  Reviews the changes, then git add, git commit, and git push.

| nbdev workflow:                       |
|---------------------------------------|
| **nbdev_prepare** → **nbdev_preview** |

For nbdev projects configured with nbdev_mkdocs, the same workflow would
look like:

1.  Runs `nbdev_mkdocs new` (only once during setup) to bootstrap
    Material for MkDocs documentation.
2.  Developer makes changes and then run `nbdev_prepare`.
3.  Runs `nbdev_mkdocs prepare` to prepare the Material for MkDocs
    documentation.
4.  Runs `nbdev_mkdocs preview` to see a local preview of the Material
    for MkDocs documentation.
5.  Reviews the changes, then git add, git commit, and git push.

| nbdev with nbdev_mkdocs workflow:                                                                                  |
|--------------------------------------------------------------------------------------------------------------------|
| **nbdev_mkdocs new** (once during setup) → **nbdev_prepare** → **nbdev_mkdocs prepare** → **nbdev_mkdocs preview** |

## Quick start

The following quick start guide will walk you through installing and
configuring nbdev_mkdocs for an existing nbdev project. It also assumes
you’ve already initialized your project with nbdev and installed all of
the required libraries.

For detailed installation instructions, configuration options, and an
End-To-End Walkthrough, please see the
[documentation](https://nbdev-mkdocs.airt.ai/guides/Guide_01_End_To_End_Walkthrough/).

nbdev_mkdocs is published as a Python package and can be installed with
pip:

``` shell
pip install nbdev_mkdocs
```

Note that `nbdev_mkdocs` must be installed into the same Python
environment that you used to install nbdev.

If the installation was successful, you should now have the
**nbdev_mkdocs** installed on your system. Run the below command from
the terminal to see the full list of available commands:

``` shell
nbdev_mkdocs --help
```

                                                                                    
     Usage: nbdev_mkdocs [OPTIONS] COMMAND [ARGS]...                                
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --install-completion          Install completion for the current shell.      │
    │ --show-completion             Show completion for the current shell, to copy │
    │                               it or customize the installation.              │
    │ --help                        Show this message and exit.                    │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ new      Creates files in **mkdocs** subdirectory needed for other           │
    │          **nbdev_mkdocs** subcommands                                        │
    │ prepare  Prepares files in **mkdocs/docs** and then runs **mkdocs build**    │
    │          command on them                                                     │
    │ preview  Prepares files in **mkdocs/docs** and then runs **mkdocs serve**    │
    │          command on them                                                     │
    ╰──────────────────────────────────────────────────────────────────────────────╯

### Setup

After installing nbdev_mkdocs, bootstrap your project documentation by
executing the following command from the project’s root directory:

``` shell
nbdev_mkdocs new
```

Using information from the project’s settings.ini file, the above
command creates files and directories required to build the
documentation and saves it in the **mkdocs** subdirectory.

Note: You should only run the **nbdev_mkdocs new** command once for the
project to initialise the files required for building Material for
MkDocs documentation.

### Prepare

Execute the following command to build the Python modules, run tests,
and clean the Jupyter notebooks:

``` shell
nbdev_prepare
```

Then execute the following command to generate the Material for MkDocs
documentation.

``` shell
nbdev_mkdocs prepare
```

Running the above command will:

- Generate the markdown files from the notebooks and saves them to the
  **mkdocs/docs/** directory.
- Builds the documentation from the generated markdown files and saves
  the resulting files to the **mkdocs/site** directory.

### Preview

After the documentation has been successfully built, execute the
following command to start a local server and preview the documentation.

``` python
nbdev_mkdocs preview
```

## Copyright

Copyright © 2022 onwards airt.ai, Inc. Licensed under the Apache
License, Version 2.0.
