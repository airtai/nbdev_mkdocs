# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/API_Docs_Helper.ipynb.

# %% auto 0
__all__ = ['get_formatted_docstring_for_symbol']

# %% ../../nbs/API_Docs_Helper.ipynb 1
from typing import *
import types
import os
from pathlib import Path
from inspect import (
    isfunction,
    isclass,
    getmembers,
    getsourcefile,
    isroutine,
    ismethod,
    isclass,
)

import griffe
import yaml
from nbdev.config import get_config

from .utils import raise_error_and_exit

# %% ../../nbs/API_Docs_Helper.ipynb 3
def _get_symbol_filepath(symbol: Union[types.FunctionType, Type[Any]]) -> Path:
    config = get_config()
    filepath = getsourcefile(symbol)
    return Path(filepath).relative_to(  # type: ignore
        filepath.split(f'{config["lib_path"].name}/')[0]  # type: ignore
    )

# %% ../../nbs/API_Docs_Helper.ipynb 6
def _generate_autodoc(
    symbol: Union[types.FunctionType, Type[Any]], symbol_path: Path
) -> str:
    return f"\n\n::: {os.path.splitext(str(symbol_path).replace('/', '.'))[0]}.{symbol.__name__}\n"

# %% ../../nbs/API_Docs_Helper.ipynb 8
def _add_mkdocstring_header_config(
    autodoc: str, heading_level: int, show_category_heading: bool, is_root_object: bool
) -> str:
    """Adds the mkdocstring header configuration to the autodoc string.

    Args:
        autodoc: The autodoc string to modify.
        heading_level: The base heading level set in the mkdocs config file.
        show_category_heading: The value of the show_category_heading flag set in the mkdocs config file.
        is_root_object: A flag indicating whether the object is the root object.

    Returns:
        The modified autodoc string with the heading level and options.

    """
    if not is_root_object:
        autodoc_header_level = (
            heading_level + 2 if show_category_heading else heading_level + 1
        )
        autodoc += f"    options:\n      heading_level: {autodoc_header_level}\n      show_root_full_path: false\n"
    return autodoc

# %% ../../nbs/API_Docs_Helper.ipynb 12
def _generate_autodoc_string(
    symbol: Union[types.FunctionType, Type[Any]],
    *,
    heading_level: int,
    show_category_heading: bool,
    is_root_object: bool = True,
) -> str:
    """Generate the autodoc string for the given symbol.

    Args:
        symbol: The symbol to generate the autodoc string for.
        heading_level: The base heading level set in the mkdocs config file.
        show_category_heading: The value of the show_category_heading flag set in the mkdocs config file.
        is_root_object: A flag indicating whether the object is the root object.

    Returns:
        The generated autodoc string with the appropriate heading level and options.

    """
    if isinstance(symbol, property):
        symbol = symbol.fget
    try:
        module = f"{symbol.__module__}.{symbol.__qualname__}"
        parsed_module = griffe.load(module)
        if "raise NotImplementedError()" in parsed_module.source:
            raise KeyError
        autodoc = f"\n\n::: {module}\n"
    except KeyError as e:
        patched_symbol_path = _get_symbol_filepath(symbol)
        autodoc = _generate_autodoc(symbol, patched_symbol_path)

    return _add_mkdocstring_header_config(
        autodoc, heading_level, show_category_heading, is_root_object
    )

# %% ../../nbs/API_Docs_Helper.ipynb 14
def _is_method(symbol: Union[types.FunctionType, Type[Any]]) -> bool:
    """Check if the given symbol is a method or a property.

    Args:
        symbol: A function or method object to check.

    Returns:
        A boolean indicating whether the symbol is a method.
    """
    return ismethod(symbol) or isfunction(symbol) or isinstance(symbol, property)

# %% ../../nbs/API_Docs_Helper.ipynb 16
def _filter_attributes_in_autodoc(symbol: Union[types.FunctionType, Type[Any]]) -> str:
    """Add symbol attributes to exclude in the autodoc string.

    Args:
        symbol: The symbol for which the filters to be added.

    Returns:
        The autodoc string along with the filters.

    """
    members_list = [
        f'"!^{x}$"'
        for x, y in getmembers(symbol)
        # do not add __init__ to filters else Functions sections will not render in sidenav
        if _is_method(y) and x != "__init__"
    ]
    return f"""    options:
      filters: [{", ".join(members_list)}]"""

# %% ../../nbs/API_Docs_Helper.ipynb 18
def _get_mkdocstring_config(mkdocs_path: Path) -> Tuple[int, bool]:
    """Get the mkdocstring configuration from the mkdocs.yml file.

    Args:
        mkdocs_path: The path to the mkdocs directory.

    Returns:
        A tuple containing the heading level and show category heading settings.

    Raises:
        RuntimeError: If the mkdocstrings settings cannot be read from the mkdocs.yml file.

    """
    with open((mkdocs_path / "mkdocs.yml"), "r", encoding="utf-8") as file:
        # nosemgrep: python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load
        data = yaml.load(file, Loader=yaml.Loader)  # nosec: yaml_load
        mkdocstrings_config = [
            i for i in data["plugins"] if isinstance(i, dict) and "mkdocstrings" in i
        ]
        if len(mkdocstrings_config) == 0:
            raise_error_and_exit(
                f"Unexpected error: cannot read mkdocstrings settings from {mkdocs_path}/mkdocs.yml file"
            )

        mkdocstrings_options = mkdocstrings_config[0]["mkdocstrings"]["handlers"][
            "python"
        ]["options"]
        heading_level = mkdocstrings_options.get("heading_level", 2)
        show_category_heading = mkdocstrings_options.get("show_category_heading", False)

    return heading_level, show_category_heading

# %% ../../nbs/API_Docs_Helper.ipynb 22
def get_formatted_docstring_for_symbol(
    symbol: Union[types.FunctionType, Type[Any]], mkdocs_path: Path
) -> str:
    """Recursively parses and get formatted docstring of a symbol.

    Args:
        symbol: A Python class or function object to parse the docstring for.
        mkdocs_path: The path to the mkdocs folder.

    Returns:
        A formatted docstring of the symbol and its members.

    """

    def traverse(
        symbol: Union[types.FunctionType, Type[Any]],
        contents: str,
        heading_level: int,
        show_category_heading: bool,
    ) -> str:
        """Recursively traverse the members of a symbol and append their docstrings to the provided contents string.

        Args:
            symbol: A Python class or function object to parse the docstring for.
            contents: The current formatted docstrings.
            heading_level: The base heading level set in the mkdocs config file.
            show_category_heading: The value of the show_category_heading flag set in the mkdocs config file.

        Returns:
            The updated formatted docstrings.

        """
        for x, y in getmembers(symbol):
            if not x.startswith("_"):
                if _is_method(y) and y.__doc__ is not None:
                    contents += f"{_generate_autodoc_string(y, heading_level=heading_level, show_category_heading=show_category_heading, is_root_object=False)}\n\n"
        #                 elif isclass(y) and not x.startswith("_") and y.__doc__ is not None:
        #                     contents += "\n" + _filter_attributes_in_autodoc(y) + "\n\n"
        #                     contents = traverse(
        #                         y, contents, heading_level, show_category_heading
        #                     )
        return contents

    if symbol.__doc__ is None:
        return ""

    heading_level, show_category_heading = _get_mkdocstring_config(mkdocs_path)
    contents = _generate_autodoc_string(
        symbol, heading_level=heading_level, show_category_heading=show_category_heading
    )
    if isclass(symbol):
        contents += _filter_attributes_in_autodoc(symbol) + "\n\n"
        contents = traverse(symbol, contents, heading_level, show_category_heading)
    return contents
