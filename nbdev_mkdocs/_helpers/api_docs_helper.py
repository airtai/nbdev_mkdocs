# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/API_Docs_Helper.ipynb.

# %% auto 0
__all__ = ['get_formatted_docstring_for_symbol']

# %% ../../nbs/API_Docs_Helper.ipynb 1
from typing import *
import types
from pathlib import Path
from inspect import isfunction, isclass, getmembers, getsourcefile, isroutine

import griffe
from nbdev.config import get_config

# %% ../../nbs/API_Docs_Helper.ipynb 3
def _get_symbol_filepath(symbol: Union[types.FunctionType, Type[Any]]) -> Path:
    config = get_config()
    filepath = getsourcefile(symbol)
    return Path(filepath).relative_to(  # type: ignore
        filepath.split(f'{config["lib_name"].replace("-", "_")}/')[0]  # type: ignore
    )

# %% ../../nbs/API_Docs_Helper.ipynb 5
def _get_annotated_symbol_definition(
    symbol: Union[types.FunctionType, Type[Any]]
) -> str:
    try:
        module = f"{symbol.__module__}.{symbol.__qualname__}"
        parsed_module = griffe.load(module)
        if "raise NotImplementedError()" in parsed_module.source:
            raise KeyError
        return f"\n\n::: {module}\n"
    except KeyError as e:
        patched_symbol_path = _get_symbol_filepath(symbol)
        return f"\n\n::: {str(patched_symbol_path.parent)}.{str(patched_symbol_path.stem)}.{symbol.__name__}\n"

# %% ../../nbs/API_Docs_Helper.ipynb 7
def _get_attributes_to_exclude_in_docstring(
    symbol: Union[types.FunctionType, Type[Any]]
) -> str:
    members_list = [
        f'"!^{a}$"'
        for a in dir(symbol)
        if callable(getattr(symbol, a)) and (not a.startswith("__") or a == "__init__")
    ]
    return f"""    options:
      filters: [{", ".join(members_list)}]"""

# %% ../../nbs/API_Docs_Helper.ipynb 9
def get_formatted_docstring_for_symbol(
    symbol: Union[types.FunctionType, Type[Any]]
) -> str:
    """Recursively parses and get formatted docstring of a symbol.

    Args:
        symbol: A Python class or function object to parse the docstring for.

    Returns:
        A formatted docstring of the symbol and its members.

    """

    def traverse(symbol: Union[types.FunctionType, Type[Any]], contents: str) -> str:
        """Recursively traverse the members of a symbol and append their docstrings to the provided contents string.

        Args:
            symbol: A Python class or function object to parse the docstring for.
            contents: The current formatted docstrings.

        Returns:
            The updated formatted docstrings.

        """
        for x, y in getmembers(symbol):
            if not x.startswith("_") or x == "__init__":
                if isfunction(y) and y.__doc__ is not None:
                    contents += f"{_get_annotated_symbol_definition(y)}\n\n"
                elif isclass(y) and not x.startswith("__") and y.__doc__ is not None:
                    contents += (
                        "\n" + _get_attributes_to_exclude_in_docstring(y) + "\n\n"
                    )
                    contents = traverse(y, contents)
        return contents

    if symbol.__doc__ is None:
        return ""

    contents = _get_annotated_symbol_definition(symbol)
    if isclass(symbol):
        contents += _get_attributes_to_exclude_in_docstring(symbol) + "\n\n"
        contents = traverse(symbol, contents)
    return contents
