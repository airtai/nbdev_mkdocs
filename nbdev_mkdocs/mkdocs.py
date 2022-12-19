# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/Mkdocs.ipynb.

# %% auto 0
__all__ = ['new', 'new_cli', 'is_library_notebook', 'get_submodules', 'generate_api_doc_for_submodule',
           'generate_api_docs_for_module', 'generate_cli_doc_for_submodule', 'generate_cli_docs_for_module',
           'build_summary', 'copy_cname_if_needed', 'nbdev_mkdocs_docs', 'nbdev_mkdocs_docs_cli', 'prepare',
           'prepare_cli', 'preview', 'preview_cli']

# %% ../nbs/Mkdocs.ipynb 1
from typing import *

import os
import re
import collections
from pathlib import Path
import textwrap
import shutil
import types
import pkgutil
import importlib
import subprocess  # nosec: B404
import shlex
import sys
import multiprocessing
import datetime
from tempfile import TemporaryDirectory
import yaml

import typer
from typer.testing import CliRunner

from configupdater import ConfigUpdater, Section
from configupdater.option import Option

from configparser import ConfigParser
from fastcore.script import call_parse

import nbdev
from nbdev.serve import proc_nbs
from nbdev.process import NBProcessor
from nbdev.frontmatter import FrontmatterProc
from nbdev.quarto import prepare as nbdev_prepare
from nbdev.quarto import refresh_quarto_yml, nbdev_readme
from nbdev.doclinks import nbdev_export
from nbdev.frontmatter import _fm2dict
from fastcore.shutil import move

from ._package_data import get_root_data_path
from ._helpers.cli_doc import generate_cli_doc
from ._helpers.utils import set_cwd, get_value_from_config
from .social_image_generator import _update_social_image_in_mkdocs_yml

# %% ../nbs/Mkdocs.ipynb 5
def _add_requirements_to_settings(root_path: str):
    """Adds requirments needed for mkdocs to settings.ini

    Args:
        root_path: path to where the settings.ini file is located

    """
    _requirements_path = get_root_data_path() / "requirements.txt"
    with open(_requirements_path, "r") as f:
        _new_req_to_add = f.read()
        lines = _new_req_to_add.split("\n")
        lines = [s.strip() for s in lines]
        lines = [s for s in lines if s != ""]
        _new_req_to_add = " \\\n".join(lines)

    setting_path = Path(root_path) / "settings.ini"
    if not setting_path.exists():
        typer.secho(
            f"Path '{setting_path.resolve()}' does not exists! Please use --root_path option to set path to setting.ini file.",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    try:

        updater = ConfigUpdater()
        updater.read(setting_path)
    except Exception as e:
        typer.secho(
            f"Error while reading '{setting_path.resolve()}': {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=2)

    try:
        _user = updater["DEFAULT"]["user"].value
        _repo = updater["DEFAULT"]["repo"].value
        option_name = (
            "requirements"
            if (f"{_user}/{_repo}") == "airtai/nbdev-mkdocs"
            else "dev_requirements"
        )
        if option_name not in updater["DEFAULT"]:
            updater["DEFAULT"].last_block.add_after.space(2).comment(f"### {option_name.title()} ###").option(option_name, "")  # type: ignore

        old_req: str = updater["DEFAULT"][option_name].value  # type: ignore

        def remove_leading_spaces(s: str) -> str:
            return "\n".join([x.lstrip() for x in s.split("\n")])

        old_req = remove_leading_spaces(old_req)
        new_req = remove_leading_spaces(_new_req_to_add)
        if new_req in old_req:
            typer.secho(f"Requirements already added to '{setting_path.resolve()}'.")
            return

        req = old_req + " \\\n" + new_req
        req = textwrap.indent(req, " " * 4)

        req_option = Option(key=option_name, value=req)
        updater["DEFAULT"][option_name] = req_option
    except Exception as e:
        typer.secho(
            f"Error while updating requiremets in '{setting_path.resolve()}': {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=3)

    updater.update_file()

    typer.secho(f"Requirements added to '{setting_path.resolve()}'.")

    return

# %% ../nbs/Mkdocs.ipynb 9
def _create_mkdocs_dir(root_path: str):
    mkdocs_template_path = get_root_data_path() / "mkdocs_template"
    if not mkdocs_template_path.exists():
        typer.secho(
            f"Unexpected error: path {mkdocs_template_path.resolve()} does not exists!",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=4)
    dst_path = Path(root_path) / "mkdocs"
    if dst_path.exists():
        typer.secho(
            f"Directory {dst_path.resolve()} already exist, skipping its creation.",
        )
    else:
        shutil.copytree(mkdocs_template_path, dst_path)
        #         shutil.move(dst_path.parent / "mkdocs_template", dst_path)
        typer.secho(
            f"Directory {dst_path.resolve()} created.",
        )

# %% ../nbs/Mkdocs.ipynb 12
_mkdocs_template_path = get_root_data_path() / "mkdocs_template.yml"

# %% ../nbs/Mkdocs.ipynb 14
with open(_mkdocs_template_path, "r") as f:
    _mkdocs_template = f.read()

# %% ../nbs/Mkdocs.ipynb 16
def _get_kwargs_from_settings(
    settings_path: Path, mkdocs_template: Optional[str] = None
) -> Dict[str, str]:
    config = ConfigParser()
    config.read(settings_path)
    if not mkdocs_template:
        mkdocs_template = _mkdocs_template
    keys = [s[1:-1] for s in re.findall("\{.*?\}", _mkdocs_template)]
    kwargs = {k: config["DEFAULT"][k] for k in keys}
    return kwargs

# %% ../nbs/Mkdocs.ipynb 18
def _create_mkdocs_yaml(root_path: str):
    try:
        # create mkdocs folder if necessary
        mkdocs_path = Path(root_path) / "mkdocs" / "mkdocs.yml"
        mkdocs_path.parent.mkdir(exist_ok=True)
        # mkdocs.yml already exists, just return
        if mkdocs_path.exists():
            typer.secho(
                f"Path '{mkdocs_path.resolve()}' exists, skipping generation of it."
            )
            return

        # get default values from settings.ini
        settings_path = Path(root_path) / "settings.ini"
        kwargs = _get_kwargs_from_settings(settings_path)
        mkdocs_yaml_str = _mkdocs_template.format(**kwargs)
        with open(mkdocs_path, "w") as f:
            f.write(mkdocs_yaml_str)
            typer.secho(f"File '{mkdocs_path.resolve()}' generated.")
            return
    except Exception as e:
        typer.secho(
            f"Unexpected Error while creating '{mkdocs_path.resolve()}': {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=3)

# %% ../nbs/Mkdocs.ipynb 21
_summary_template = """{sidebar}
{api}
{cli}
{changelog}
"""


def _create_summary_template(root_path: str):
    try:
        # create mkdocs folder if necessary
        summary_template_path = Path(root_path) / "mkdocs" / "summary_template.txt"
        summary_template_path.parent.mkdir(exist_ok=True)
        # summary_template_path.yml already exists, just return
        if summary_template_path.exists():
            typer.secho(
                f"Path '{summary_template_path.resolve()}' exists, skipping generation of it."
            )
            return

        # generated a new summary_template_path.yml file
        with open(summary_template_path, "w") as f:
            f.write(_summary_template)
            typer.secho(f"File '{summary_template_path.resolve()}' generated.")
            return
    except Exception as e:
        typer.secho(
            f"Unexpected Error while creating '{summary_template_path.resolve()}': {e}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=3)

# %% ../nbs/Mkdocs.ipynb 23
def _replace_ghp_deploy_action(root_path: str):
    """Replace the default gh-pages deploy action file with the custom action template file

    Args:
        root_path: Project's root path
    """

    src_path = get_root_data_path() / "ghp_deploy_action_template.yml"
    if not src_path.exists():
        typer.secho(
            f"Unexpected error: path {src_path.resolve()} does not exists!",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=4)

    workflows_path = Path(root_path) / ".github" / "workflows"
    workflows_path.mkdir(exist_ok=True, parents=True)

    dst_path = Path(workflows_path) / "deploy.yaml"
    shutil.copyfile(src_path, dst_path)

# %% ../nbs/Mkdocs.ipynb 26
def _update_gitignore_file(root_path: str):
    """Update the .gitignore file to include the autogenerated mkdocs directories

    Args:
        root_path: Project's root path
    """

    _mkdocs_gitignore_path = get_root_data_path() / "gitignore.txt"
    with open(_mkdocs_gitignore_path, "r") as f:
        _new_paths_to_ignore = f.read()
        _new_paths_to_ignore = "\n\n" + _new_paths_to_ignore

    gitignore_path = Path(root_path) / ".gitignore"
    if not gitignore_path.exists():
        typer.secho(
            f"Unexpected error: path {gitignore_path.resolve()} does not exists!",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    with open(gitignore_path, "a") as f:
        f.write(_new_paths_to_ignore)

# %% ../nbs/Mkdocs.ipynb 28
def _generate_default_social_image_link(root_path: str):
    """Generating default social sharing image link and add it to the mkdocs yaml file

    Args:
        root_path: Project's root path
    """

    with set_cwd(root_path):
        repo = get_value_from_config(root_path, "repo")
        user = get_value_from_config(root_path, "user")

        timestamp = datetime.datetime.now().timestamp()
        img_url = f"https://opengraph.githubassets.com/{timestamp}/{user}/{repo}"

        _update_social_image_in_mkdocs_yml(root_path, img_url)

# %% ../nbs/Mkdocs.ipynb 31
def new(root_path: str):
    """Initialize mkdocs project files

    Creates **mkdocs** directory in the **root_path** directory and populates
    it with initial values. You should edit mkdocs.yml file to customize it if
    needed.

    Args:
        root_path: path under which mkdocs directory will be created
    """
    _add_requirements_to_settings(root_path)
    _create_mkdocs_dir(root_path)
    _create_mkdocs_yaml(root_path)
    _create_summary_template(root_path)
    _replace_ghp_deploy_action(root_path)
    _update_gitignore_file(root_path)
    _generate_default_social_image_link(root_path)


@call_parse
def new_cli(root_path: str = "."):
    """Initialize mkdocs project files

    Creates **mkdocs** directory in the **root_path** directory and populates
    it with initial values. You should edit mkdocs.yml file to customize it if
    needed.
    """
    new(root_path)

# %% ../nbs/Mkdocs.ipynb 35
def is_library_notebook(fname: Path) -> bool:
    """Check if a notebook is exported as part of the library

    Args:
        fname: The path to the notebook to check.

    Returns:
        `True` if the notebook is exported as part of the library, `False` otherwise.
    """
    if fname.suffix == ".qmd":
        return False

    nb = NBProcessor(fname)
    for cell in nb.nb.cells:
        if cell["cell_type"] == "code":
            if "default_exp" in cell["directives_"]:
                return True
    return False


def _get_files_to_convert_to_markdown(root_path: str) -> List[Path]:
    """Gets a list of notebooks and qmd files that need to be converted to markdown.

    Args:
        cache: Project's root path

    Returns:
        A list of files that need to be converted to markdown
    """
    with TemporaryDirectory() as d:
        nbs_directory = get_value_from_config(root_path, "nbs_path")
        src_nbs_path = Path(root_path) / nbs_directory

        dst_nbs_path = Path(d) / f"{nbs_directory}"
        shutil.copytree(src_nbs_path, dst_nbs_path)

        exts = [".ipynb", ".qmd"]
        files = [
            f
            for f in dst_nbs_path.rglob("*")
            if f.suffix in exts
            and not str(f.name).startswith("_")
            and not any(p.startswith(".") for p in f.parts)
            and not is_library_notebook(f)
        ]
        files = [f.relative_to(dst_nbs_path) for f in files]

        return files

# %% ../nbs/Mkdocs.ipynb 37
def _sprun(cmd):
    try:
        # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
        subprocess.check_output(
            cmd, shell=True  # nosec: B602:subprocess_popen_with_shell_equals_true
        )

    except subprocess.CalledProcessError as e:
        sys.exit(
            f"CMD Failed: e={e}\n e.returncode={e.returncode}\n e.output={e.output}\n e.stderr={e.stderr}\n cmd={cmd}"
        )

# %% ../nbs/Mkdocs.ipynb 38
def _generate_markdown_from_files(root_path: str):

    doc_path = Path(root_path) / "mkdocs" / "docs"
    doc_path.mkdir(exist_ok=True, parents=True)

    with set_cwd(root_path):
        files = _get_files_to_convert_to_markdown(root_path)
        cache = proc_nbs()

        for f in files:
            dir_prefix = str(Path(f).parent)
            dst_md = doc_path / f"{dir_prefix}" / f"{f.stem}.md"
            dst_md.parent.mkdir(parents=True, exist_ok=True)

            cmd = f'cd "{cache}" && quarto render "{cache / f}" -o "{f.stem}.md" -t gfm --no-execute'
            _sprun(cmd)

            src_md = cache / "_docs" / f"{f.stem}.md"
            shutil.move(src_md, dst_md)

# %% ../nbs/Mkdocs.ipynb 40
def _replace_all(text: str, dir_prefix: str) -> str:
    """Replace the images relative path in the markdown text

    Args:
        text: String to replace
        dir_prefix: Sub directory prefix to append to the image's relative path

    Returns:
        The text with the updated images relative path
    """
    _replace = {}
    _pattern = re.compile(r"!\[[^\]]*\]\(([^https?:\/\/].*?)\s*(\"(?:.*[^\"])\")?\s*\)")
    _matches = [match.groups()[0] for match in _pattern.finditer(text)]

    if len(_matches) > 0:
        for m in _matches:
            _replace[m] = (
                os.path.normpath(Path("../images/nbs/").joinpath(f"{dir_prefix}/{m}"))
                if len(dir_prefix) > 0
                else f"images/nbs/{m}"
            )

        for k, v in _replace.items():
            text = text.replace(k, v)

    return text

# %% ../nbs/Mkdocs.ipynb 42
def _update_path_in_markdown(root_path: str, doc_path: Path):
    """Update guide images relative path in the markdown files

    Args:
        root_path: Project's root directory
        doc_path: Path to the mkdocs/docs directory
    """
    files = _get_files_to_convert_to_markdown(root_path)

    for file in files:
        dir_prefix = str(file.parent)
        md = doc_path / f"{dir_prefix}" / f"{file.stem}.md"

        with open(Path(md), "r") as f:
            _new_text = f.read()
            _new_text = _replace_all(_new_text, dir_prefix)
        with open(Path(md), "w") as f:
            f.write(_new_text)


def _copy_images_to_docs_dir(root_path: str):
    """Copy guide images to the docs directory

    Args:
        root_path: Project's root directory
    """
    # Reference: https://github.com/quarto-dev/quarto-cli/blob/main/src/core/image.ts#L38
    image_extensions = [
        ".apng",
        ".avif",
        ".gif",
        ".jpg",
        ".jpeg",
        ".jfif",
        ".pjpeg",
        ".pjp",
        ".png",
        ".svg",
        ".webp",
    ]

    cache = proc_nbs()
    nbs_images_path = [
        p for p in Path(cache).glob(r"**/*") if p.suffix in image_extensions
    ]

    if len(nbs_images_path) > 0:
        doc_path = Path(root_path) / "mkdocs" / "docs"
        img_path = Path(doc_path) / "images" / "nbs"
        for src_path in nbs_images_path:
            dir_prefix = str(src_path.parent)[len(str(cache)) + 1 :]
            dst_path = Path(img_path) / f"{dir_prefix}"
            dst_path.mkdir(exist_ok=True, parents=True)
            shutil.copy(src_path, dst_path)

        _update_path_in_markdown(root_path, doc_path)

# %% ../nbs/Mkdocs.ipynb 47
def _get_title_from_notebook(file_path: Path) -> str:
    cache = proc_nbs()
    _file_path = Path(cache) / file_path

    if not _file_path.exists():
        typer.secho(
            f"Unexpected error: path {_file_path.resolve()} does not exists!",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    if _file_path.suffix == ".ipynb":
        nbp = NBProcessor(_file_path, procs=FrontmatterProc)
        nbp.process()
        title = nbp.nb.frontmatter_["title"]

    else:
        with open(_file_path) as f:
            contents = f.read()
        metadata = _fm2dict(contents, nb=False)
        metadata = {k.lower(): v for k, v in metadata.items()}
        title = metadata["title"]

    return title

# %% ../nbs/Mkdocs.ipynb 49
def _get_sidebar_from_config(file_path: Path) -> List[Union[str, Any]]:

    with open(file_path) as f:
        config = yaml.safe_load(f)

    try:
        sidebar = config["website"]["sidebar"]["contents"]
    except KeyError as e:
        typer.secho(
            f"Key Error: Contents of the sidebar are not defined in the files sidebar.yml or _quarto.yml.",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    return sidebar


def _read_sidebar_from_yml(root_path: str) -> List[Union[str, Any]]:

    # can you read it from _proc
    nbs_path = get_value_from_config(root_path, "nbs_path")
    sidebar_yml_path = Path(root_path) / f"{nbs_path}" / "sidebar.yml"
    _quarto_yml_path = Path(root_path) / f"{nbs_path}" / "_quarto.yml"

    custom_sidebar = get_value_from_config(root_path, "custom_sidebar")
    if custom_sidebar == "False":
        cmd = f'cd "{root_path}" && nbdev_docs'
        _sprun(cmd)

    return (
        _get_sidebar_from_config(sidebar_yml_path)
        if sidebar_yml_path.exists()
        else _get_sidebar_from_config(_quarto_yml_path)
    )

# %% ../nbs/Mkdocs.ipynb 52
def _flattern_sidebar_items(items: List[Union[str, Any]]) -> List[Union[str, Any]]:
    return [i for item in items if isinstance(item, list) for i in item] + [
        item for item in items if not isinstance(item, list)
    ]


def _expand_sidebar_if_needed(
    root_path: str, sidebar: List[Union[str, Any]]
) -> List[Union[str, Any]]:
    """ """
    _proc_dir = Path(root_path) / "_proc"
    exts = [".ipynb", ".qmd"]

    for index, item in enumerate(sidebar):
        if "auto" in item:
            files = list(_proc_dir.glob("".join(item["auto"].split("/")[1:])))  # type: ignore
            files = sorted([str(f.relative_to(_proc_dir)) for f in files if f.suffix in exts])  # type: ignore
            sidebar[index] = files

        if isinstance(item, dict) and "contents" in item:
            _contents = item["contents"]
            if isinstance(_contents, str) and bool(re.search(r"[*?\[\]]", _contents)):
                files = list(_proc_dir.glob(item["contents"]))
                files = sorted([str(f.relative_to(_proc_dir)) for f in files if f.suffix in exts])  # type: ignore
                item["contents"] = files

    flat_sidebar = _flattern_sidebar_items(sidebar)
    return flat_sidebar

# %% ../nbs/Mkdocs.ipynb 54
def _filter_sidebar(
    root_path: str,
    sidebar: List[Union[str, Any]],
    nbs_to_include: List[Path],
) -> List[Union[str, Any]]:
    nbs_to_include_set = set(map(str, nbs_to_include))
    _sidebar = _expand_sidebar_if_needed(root_path, sidebar)

    def should_include_item(item):
        if isinstance(item, str):
            return item in nbs_to_include_set
        elif isinstance(item, dict):
            return any(map(should_include_item, item["contents"]))

    return [item for item in _sidebar if should_include_item(item)]

# %% ../nbs/Mkdocs.ipynb 56
def _generate_nav_from_sidebar(sidebar_items, level=0):
    output = ""
    links = [
        "{}- [{}]({}.md)\n".format(
            "    " * level,
            _get_title_from_notebook(Path(item)),
            Path(item).with_suffix(""),
        )
        if isinstance(item, str)
        else "{}- {}\n".format("    " * level, item["section"])
        + _generate_nav_from_sidebar(item["contents"], level + 1)
        for item in sidebar_items
    ]
    output += "".join(links)
    return output

# %% ../nbs/Mkdocs.ipynb 58
def _generate_summary_for_sidebar(
    root_path: str,
) -> str:
    with set_cwd(root_path):
        sidebar = _read_sidebar_from_yml(root_path)
        nbs_to_include = _get_files_to_convert_to_markdown(root_path)

        filtered_sidebar = _filter_sidebar(root_path, sidebar, nbs_to_include)
        sidebar_nav = _generate_nav_from_sidebar(filtered_sidebar)

        return sidebar_nav

# %% ../nbs/Mkdocs.ipynb 61
def get_submodules(package_name: str) -> List[str]:
    # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
    m = importlib.import_module(package_name)
    submodules = [
        info.name
        for info in pkgutil.walk_packages(m.__path__, prefix=f"{package_name}.")
    ]
    submodules = [
        x
        for x in submodules
        if not any([name.startswith("_") for name in x.split(".")])
    ]
    return submodules

# %% ../nbs/Mkdocs.ipynb 63
def generate_api_doc_for_submodule(root_path: str, submodule: str) -> str:
    subpath = "API/" + submodule.replace(".", "/") + ".md"
    path = Path(root_path) / "mkdocs" / "docs" / subpath
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, "w") as f:
        f.write(f"::: {submodule}")
    subnames = submodule.split(".")
    if len(subnames) > 2:
        return " " * 4 * (len(subnames) - 2) + f"- [{subnames[-1]}]({subpath})"
    else:
        return f"- [{submodule}]({subpath})"


def generate_api_docs_for_module(root_path: str, module_name: str) -> str:
    submodules = get_submodules(module_name)
    shutil.rmtree(Path(root_path) / "mkdocs" / "docs" / "API", ignore_errors=True)

    if not len(submodules):
        return ""

    submodule_summary = "\n".join(
        [
            generate_api_doc_for_submodule(root_path=root_path, submodule=x)
            for x in submodules
        ]
    )

    return "- API\n" + textwrap.indent(submodule_summary, prefix=" " * 4)

# %% ../nbs/Mkdocs.ipynb 65
def _restrict_line_length(s: str, width: int = 80) -> str:
    """Restrict the line length of the given string.

    Args:
        s: Docstring to fix the width
        width: The maximum allowed line length

    Returns:
        A new string in which each line is less than the specified width.
    """
    _s = ""

    for blocks in s.split("\n\n"):
        sub_block = blocks.split("\n  ")
        for line in sub_block:
            line = line.replace("\n", " ")
            line = "\n".join(textwrap.wrap(line, width=width, replace_whitespace=False))
            if len(sub_block) == 1:
                _s += line + "\n\n"
            else:
                _s += "\n" + line + "\n" if line.endswith(":") else " " + line + "\n"
    return _s

# %% ../nbs/Mkdocs.ipynb 67
def generate_cli_doc_for_submodule(root_path: str, cmd: str) -> str:

    cli_app_name = cmd.split("=")[0]
    module_name = cmd.split("=")[1].split(":")[0]
    method_name = cmd.split("=")[1].split(":")[1]

    subpath = f"CLI/{cli_app_name}.md"
    path = Path(root_path) / "mkdocs" / "docs" / subpath
    path.parent.mkdir(exist_ok=True, parents=True)

    # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
    m = importlib.import_module(module_name)
    if isinstance(getattr(m, method_name), typer.Typer):
        app = typer.Typer()
        app.command()(generate_cli_doc)
        runner = CliRunner()
        result = runner.invoke(app, [module_name, cli_app_name])
        cli_doc = str(result.stdout)
    else:
        cmd = f"{cli_app_name} --help"

        # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
        cli_doc = subprocess.run(  # nosec: B602:subprocess_popen_with_shell_equals_true
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).stdout.decode("utf-8")

        cli_doc = _restrict_line_length(cli_doc)
        cli_doc = "\n```\n" + cli_doc + "\n```\n"

    with open(path, "w") as f:
        f.write(cli_doc)

    return f"- [{cli_app_name}]({subpath})"


def generate_cli_docs_for_module(root_path: str, module_name: str) -> str:
    shutil.rmtree(Path(root_path) / "mkdocs" / "docs" / "CLI", ignore_errors=True)
    console_scripts = get_value_from_config(root_path, "console_scripts")

    if not console_scripts:
        return ""

    submodule_summary = "\n".join(
        [
            generate_cli_doc_for_submodule(root_path=root_path, cmd=cmd)
            for cmd in console_scripts.split("\n")
        ]
    )

    return "- CLI\n" + textwrap.indent(submodule_summary, prefix=" " * 4)

# %% ../nbs/Mkdocs.ipynb 69
def _copy_change_log_if_exists(
    root_path: Union[Path, str], docs_path: Union[Path, str]
) -> str:
    changelog = ""
    source_change_log_path = Path(root_path) / "CHANGELOG.md"
    dst_change_log_path = Path(docs_path) / "CHANGELOG.md"
    if source_change_log_path.exists():
        shutil.copy(source_change_log_path, dst_change_log_path)
        changelog = "- [Releases](CHANGELOG.md)"
    return changelog

# %% ../nbs/Mkdocs.ipynb 72
def build_summary(
    root_path: str,
    module: str,
):
    # create docs_path if needed
    docs_path = Path(root_path) / "mkdocs" / "docs"
    docs_path.mkdir(exist_ok=True)

    # copy README.md as index.md
    shutil.copy(Path(root_path) / "README.md", docs_path / "index.md")

    # generate markdown files
    _generate_markdown_from_files(root_path)

    # copy images to docs dir and update path in generated markdown files
    _copy_images_to_docs_dir(root_path)

    # generates sidebar navigation
    sidebar = _generate_summary_for_sidebar(root_path)

    # generate API
    api = generate_api_docs_for_module(root_path, module)

    # generate CLI
    cli = generate_cli_docs_for_module(root_path, module)

    # copy CHANGELOG.md as CHANGELOG.md is exists
    changelog = _copy_change_log_if_exists(root_path, docs_path)

    # read summary template from file
    with open(Path(root_path) / "mkdocs" / "summary_template.txt") as f:
        summary_template = f.read()

    summary = summary_template.format(
        sidebar=sidebar, api=api, cli=cli, changelog=changelog
    )
    summary = "\n".join(
        [l for l in [l.rstrip() for l in summary.split("\n")] if l != ""]
    )

    with open(docs_path / "SUMMARY.md", mode="w") as f:
        f.write(summary)

# %% ../nbs/Mkdocs.ipynb 75
def copy_cname_if_needed(root_path: str):
    cname_path = Path(root_path) / "CNAME"
    dst_path = Path(root_path) / "mkdocs" / "docs" / "CNAME"
    if cname_path.exists():
        dst_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(cname_path, dst_path)
        typer.secho(
            f"File '{cname_path.resolve()}' copied to '{dst_path.resolve()}'.",
        )
    else:
        typer.secho(
            f"File '{cname_path.resolve()}' not found, skipping copying..",
        )

# %% ../nbs/Mkdocs.ipynb 77
def _copy_docs_overrides(root_path: str):
    """Copy lib assets inside mkodcs/docs directory

    Args:
        root_path: Project's root path.
    """
    src_path = Path(root_path) / "mkdocs" / "docs_overrides"
    dst_path = Path(root_path) / "mkdocs" / "docs" / "overrides"

    if not src_path.exists():
        typer.secho(
            f"Unexpected error: path {src_path.resolve()} does not exists!",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    shutil.rmtree(dst_path, ignore_errors=True)
    shutil.copytree(src_path, dst_path)

# %% ../nbs/Mkdocs.ipynb 79
def nbdev_mkdocs_docs(root_path: str, refresh_quarto_settings: bool = False):
    """Prepares mkdocs documentation

    Args:
        root_path: Project's root path.
        refresh_quarto_settings: Flag to refresh quarto yml file. This flag should be set to `True`
            if this function is called directly without calling prepare.
    """

    with set_cwd(root_path):

        if refresh_quarto_settings:
            refresh_quarto_yml()

        copy_cname_if_needed(root_path)

        _copy_docs_overrides(root_path)

        lib_name = get_value_from_config(root_path, "lib_name")
        lib_path = get_value_from_config(root_path, "lib_path")

        build_summary(root_path, lib_path)
        #         _generate_default_social_image_link(root_path)

        cmd = f"mkdocs build -f \"{(Path(root_path) / 'mkdocs' / 'mkdocs.yml').resolve()}\""
        _sprun(cmd)


@call_parse
def nbdev_mkdocs_docs_cli(root_path: str = "."):
    """Prepares mkdocs documentation"""
    nbdev_mkdocs_docs(root_path, refresh_quarto_settings=True)


def prepare(root_path: str, no_test: bool = False):
    """Prepares mkdocs for serving

    Args:
        root_path: path under which mkdocs directory will be created
    """
    with set_cwd(root_path):

        if no_test:
            nbdev_export.__wrapped__()
            refresh_quarto_yml()
            nbdev_readme.__wrapped__(chk_time=True)
        else:
            cmd = "nbdev_prepare"
            _sprun(cmd)

    nbdev_mkdocs_docs(root_path)


@call_parse
def prepare_cli(root_path: str = "."):
    """Prepares mkdocs for serving"""
    prepare(root_path)

# %% ../nbs/Mkdocs.ipynb 82
def preview(root_path: str, port: Optional[int] = None):
    """Previes mkdocs documentation

    Args:
        root_path: path under which mkdocs directory will be created
        port: port to use
    """
    with set_cwd(root_path):
        prepare(root_path=root_path, no_test=True)

        cmd = f"mkdocs serve -f {root_path}/mkdocs/mkdocs.yml -a 0.0.0.0"
        if port:
            cmd = cmd + f":{port}"

        with subprocess.Popen(  # nosec B603:subprocess_without_shell_equals_true
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            bufsize=1,
            text=True,
            universal_newlines=True,
        ) as p:
            for line in p.stdout:  # type: ignore
                print(line, end="")

        if p.returncode != 0:
            typer.secho(
                f"Command cmd='{cmd}' failed!",
                err=True,
                fg=typer.colors.RED,
            )
            raise typer.Exit(6)


@call_parse
def preview_cli(root_path: str = ".", port: Optional[int] = None):
    """Previes mkdocs documentation"""
    preview(root_path, port)
