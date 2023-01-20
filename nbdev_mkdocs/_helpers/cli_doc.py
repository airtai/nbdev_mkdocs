# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/CLI_Doc_Helper.ipynb.

# %% auto 0
__all__ = ['generate_cli_doc']

# %% ../../nbs/CLI_Doc_Helper.ipynb 1
from typing import *
import importlib
import importlib.util
import sys
from pathlib import Path

import click
import click.core
from click import Command, Group  # , Option
import typer
from typer.testing import CliRunner

# %% ../../nbs/CLI_Doc_Helper.ipynb 3
_default_app_names = ("app", "cli", "main")
_default_func_names = ("main", "cli", "app")


class _State:
    """A class to represent a state.

    Attributes:
        app : the app
        func : the func
        file : the file
        module : the module

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    def __init__(self) -> None:
        """Initialize the class

        Args:
            app: The app name
            func: The function name
            file: The file name
            module: The module name

        Returns:
            None

        !!! note

            The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
        """
        self.app: Optional[str] = None
        self.func: Optional[str] = None
        self.file: Optional[Path] = None
        self.module: Optional[str] = None


_state = _State()


def _get_typer_from_module(module: Any) -> Optional[typer.Typer]:
    # Try to get defined app
    """Get a Typer object from a module.

    Args:
        module: The module to get the Typer object from.

    Returns:
        A Typer object.

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """
    if _state.app:
        obj: Optional[typer.Typer] = getattr(module, _state.app, None)
        if not isinstance(obj, typer.Typer):
            typer.echo(f"Not a Typer object: --app {_state.app}", err=True)
            sys.exit(1)
        return obj
    # Try to get defined function
    if _state.func:
        func_obj = getattr(module, _state.func, None)
        if not callable(func_obj):
            typer.echo(f"Not a function: --func {_state.func}", err=True)
            sys.exit(1)
        sub_app = typer.Typer()
        sub_app.command()(func_obj)
        return sub_app
    # Iterate and get a default object to use as CLI
    local_names = dir(module)
    local_names_set = set(local_names)
    # Try to get a default Typer app
    for name in _default_app_names:
        if name in local_names_set:
            obj = getattr(module, name, None)
            if isinstance(obj, typer.Typer):
                return obj
    # Try to get any Typer app
    for name in local_names_set - set(_default_app_names):
        obj = getattr(module, name)
        if isinstance(obj, typer.Typer):
            return obj
    # Try to get a default function
    for func_name in _default_func_names:
        func_obj = getattr(module, func_name, None)
        if callable(func_obj):
            sub_app = typer.Typer()
            sub_app.command()(func_obj)
            return sub_app
    # Try to get any func app
    for func_name in local_names_set - set(_default_func_names):
        func_obj = getattr(module, func_name)
        if callable(func_obj):
            sub_app = typer.Typer()
            sub_app.command()(func_obj)
            return sub_app
    return None


def _get_typer_from_state() -> Optional[typer.Typer]:
    """Get a Typer object from a module.

    Returns:
        The Typer object.

    Raises:
        ValueError: If the module does not contain a Typer object.

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """
    spec = None
    if _state.file:
        module_name = _state.file.name
        spec = importlib.util.spec_from_file_location(module_name, str(_state.file))
    elif _state.module:
        spec = importlib.util.find_spec(_state.module)

    if spec is None:
        if _state.file:
            typer.echo(f"Could not import as Python file: {_state.file}", err=True)
        else:
            typer.echo(f"Could not import as Python module: {_state.module}", err=True)
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    obj = _get_typer_from_module(module)
    return obj


def _get_docs_for_click(
    *,
    obj: Command,
    ctx: typer.Context,
    indent: int = 0,
    name: str = "",
    call_prefix: str = "",
) -> str:
    """Generate documentation for a click command.

    Args:
        obj: The click command to document.
        ctx: The click context.
        indent: The indentation level.
        name: The name of the command.
        call_prefix: The prefix to use when calling the command.

    Returns:
        The generated documentation.

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """
    docs = "#" * (1 + indent)
    command_name = name or obj.name
    if call_prefix:
        command_name = f"{call_prefix} {command_name}"
    title = f"`{command_name}`" if command_name else "CLI"
    docs += f" {title}\n\n"
    if obj.help:
        docs += f"{obj.help}\n\n"
    usage_pieces = obj.collect_usage_pieces(ctx)
    if usage_pieces:
        docs += "**Usage**:\n\n"
        docs += "```console\n"
        docs += "$ "
        if command_name:
            docs += f"{command_name} "
        docs += f"{' '.join(usage_pieces)}\n"
        docs += "```\n\n"
    args = []
    opts = []
    for param in obj.get_params(ctx):
        rv = param.get_help_record(ctx)
        if rv is not None:
            if param.param_type_name == "argument":
                args.append(rv)
            elif param.param_type_name == "option":
                opts.append(rv)
    if args:
        docs += f"**Arguments**:\n\n"
        for arg_name, arg_help in args:
            docs += f"* `{arg_name}`"
            if arg_help:
                docs += f": {arg_help}"
            docs += "\n"
        docs += "\n"
    if opts:
        docs += f"**Options**:\n\n"
        for opt_name, opt_help in opts:
            docs += f"* `{opt_name}`"
            if opt_help:
                docs += f": {opt_help}"
            docs += "\n"
        docs += "\n"
    if obj.epilog:
        docs += f"{obj.epilog}\n\n"
    if isinstance(obj, Group):
        group: Group = cast(Group, obj)
        commands = group.list_commands(ctx)
        if commands:
            docs += f"**Commands**:\n\n"
            for command in commands:
                command_obj = group.get_command(ctx, command)
                docs += f"* `{command_obj.name}`"  # type: ignore
                command_help = command_obj.get_short_help_str()  # type: ignore
                if command_help:
                    docs += f": {command_help}"
                docs += "\n"
            docs += "\n"
        for command in commands:
            command_obj = group.get_command(ctx, command)
            use_prefix = ""
            if command_name:
                use_prefix += f"{command_name}"
            docs += _get_docs_for_click(
                obj=command_obj, ctx=ctx, indent=indent + 1, call_prefix=use_prefix  # type: ignore
            )
    return docs

# %% ../../nbs/CLI_Doc_Helper.ipynb 4
def generate_cli_doc(module_name: str, app_name: str) -> str:
    def _generate_cli_doc(
        ctx: typer.Context,
        module_name: str,
        app_name: str,
    ) -> None:
        """Generate Markdown docs for a Typer app."""
        _state.module = f"{module_name}"
        typer_obj = _get_typer_from_state()

        if not typer_obj:
            typer.echo(f"No Typer app found", err=True)
            raise typer.Abort()
        click_obj = typer.main.get_command(typer_obj)
        docs = _get_docs_for_click(obj=click_obj, ctx=ctx, name=app_name)
        clean_docs = f"{docs.strip()}\n"
        typer.echo(clean_docs)

    app = typer.Typer()
    app.command()(_generate_cli_doc)
    runner = CliRunner()
    result = runner.invoke(app, [module_name, app_name])
    return result.stdout
