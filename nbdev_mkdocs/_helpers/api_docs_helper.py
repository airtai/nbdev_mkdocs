# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/API_Docs_Helper.ipynb.

# %% auto 0
__all__ = ['get_formatted_docstring_for_symbol']

# %% ../../nbs/API_Docs_Helper.ipynb 1
from typing import *
import re
import types
from inspect import (
    Signature,
    getmembers,
    isclass,
    isfunction,
    signature,
    getsource,
    getsourcefile,
)
import textwrap

from griffe.dataclasses import Docstring
from griffe.docstrings.parsers import Parser, parse
from griffe.docstrings.dataclasses import (
    DocstringSectionAdmonition,
    DocstringSectionText,
    DocstringSectionParameters,
    DocstringSectionReturns,
    DocstringSectionRaises,
    DocstringSectionExamples,
    DocstringSectionYields,
    DocstringRaise,
    DocstringParameter,
)

from nbdev.config import get_config

# %% ../../nbs/API_Docs_Helper.ipynb 3
def _convert_union_to_optional(annotation_str: str) -> str:
    """Convert the 'Union[Type1, Type2, ..., NoneType]' to 'Optional[Type1, Type2, ...]' in the given annotation string

    Args:
        annotation_str: The type annotation string to convert.

    Returns:
        The converted type annotation string.
    """
    pattern = r"Union\[(.*)?,\s*NoneType\s*\]"
    match = re.search(pattern, annotation_str)
    if match:
        union_type = match.group(1)
        optional_type = f"Optional[{union_type}]"
        return re.sub(pattern, optional_type, annotation_str)
    else:
        return annotation_str

# %% ../../nbs/API_Docs_Helper.ipynb 5
def _get_arg_list_with_signature(
    _signature: Signature, return_as_list: bool = False
) -> Union[str, List[str]]:
    """Converts a function's signature into a string representation of its argument list.

    Args:
        _signature (signature): The signature object for the function to convert.

    Returns:
        str: A string representation of the function's argument list.
    """
    arg_list = []
    for param in _signature.parameters.values():
        arg_list.append(_convert_union_to_optional(str(param)))

    return arg_list if return_as_list else ", ".join(arg_list)

# %% ../../nbs/API_Docs_Helper.ipynb 9
def _get_return_annotation(sig: Signature, symbol_definition: str) -> str:
    if sig.return_annotation and "inspect._empty" not in str(sig.return_annotation):
        if isinstance(sig.return_annotation, type):
            symbol_definition = (
                symbol_definition + f" -> {sig.return_annotation.__name__}\n"
            )
        else:
            symbol_definition = symbol_definition + f" -> {sig.return_annotation}\n"
            symbol_definition = symbol_definition.replace("typing.", "")

    else:
        symbol_definition = symbol_definition + " -> None\n"
    return symbol_definition

# %% ../../nbs/API_Docs_Helper.ipynb 12
def _get_symbol_definition(symbol: Union[types.FunctionType, Type[Any]]) -> str:
    """Return the definition of a given symbol.

    Args:
        symbol: A function or method object to get the definition for.

    Returns:
        A string representing the function definition
    """
    _signature = signature(symbol)
    arg_list = _get_arg_list_with_signature(_signature)
    ret_val = ""

    if isfunction(symbol):
        ret_val = f"### `{symbol.__name__}`\n\n"
        ret_val = ret_val + f"`def {symbol.__name__}({arg_list})"
        ret_val = _get_return_annotation(_signature, ret_val) + "`"

    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 18
def _format_raises_section(
    section_dict: Dict[str, Union[str, List[DocstringRaise]]]
) -> str:
    ret_val = """| Type | Description |
| --- | --- |
"""

    ret_val += "\n".join(
        [
            f"| `{v.as_dict()['annotation']}` | {v.as_dict()['description']} |"  # type: ignore
            for v in section_dict["value"]
        ]
    )

    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 20
def _format_return_section(
    section_dict: Dict[str, Union[str, List[DocstringRaise]]],
    symbol: Union[types.FunctionType, Type[Any]],
) -> str:
    ret_val = """| Type | Description |
| --- | --- |
"""
    sig = signature(symbol)
    return_type = (
        "`"
        + _get_return_annotation(sig, "").replace("->", "").replace("\n", "").strip()
        + "`"
    )

    ret_val += "\n".join(
        [
            f"| {return_type} | {v.as_dict()['description']} |"  # type: ignore
            for v in section_dict["value"]
        ]
    )

    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 23
def _get_default_value(default_value: List[str], param_name: str) -> str:
    if param_name == "**kwargs":
        return "`{}`"
    return "`required`" if len(default_value) == 0 else f"`{default_value[0].strip()}`"


def _format_params_annotations(
    params_annotation_list: List[str],
) -> Dict[str, Dict[str, str]]:
    ret_val = {}
    for param in params_annotation_list:
        if param == "self":
            continue
        param_name, annotation_with_default_value = param.split(":")
        annotation, *default_value = annotation_with_default_value.split("=")
        ret_val[param_name.strip()] = {
            "annotation": f"`{annotation.strip()}`",
            "default": _get_default_value(default_value, param_name),
        }
    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 27
def _format_param(
    param: DocstringParameter, param_annotations_dict: Dict[str, Dict[str, str]]
) -> str:
    param_dict = param.as_dict()
    nl = "\n"
    if param_dict["name"] in param_annotations_dict:
        ret_val = f"| `{param_dict['name']}` | {param_annotations_dict[param_dict['name']]['annotation']} | {param_dict['description'].replace(nl, ' ')} | {param_annotations_dict[param_dict['name']]['default']} |"
    else:
        ret_val = f"| `{param_dict['name']}` |  | {param_dict['description'].replace(nl, ' ')} |  |"

    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 30
def _format_parameters_section(
    section_dict: Dict[str, Union[str, List[DocstringParameter]]],
    symbol: Union[types.FunctionType, Type[Any]],
) -> str:
    ret_val = """| Name | Type | Description | Default |
| --- | --- | --- | --- |
"""
    sig = signature(symbol)
    param_annotations_list = _get_arg_list_with_signature(sig, True)
    formatted_param_annotations_dict = _format_params_annotations(
        param_annotations_list  # type: ignore
    )
    ret_val += "\n".join(
        [
            _format_param(v, formatted_param_annotations_dict)  # type: ignore
            for v in section_dict["value"]
        ]
    )

    return ret_val

# %% ../../nbs/API_Docs_Helper.ipynb 34
def _get_source_relative_filename(
    source_filename: Optional[str] = None,
) -> Optional[str]:
    if source_filename is None:
        return None
    cfg = get_config()
    lib_name = cfg["lib_name"].replace("-", "_")
    return f"{lib_name}{source_filename.split(lib_name)[1]}"

# %% ../../nbs/API_Docs_Helper.ipynb 36
def _docstring_to_markdown(symbol: Union[types.FunctionType, Type[Any]]) -> str:
    """Converts a docstring to a markdown-formatted string.

    Args:
        docstring: The docstring to convert.

    Returns:
        The markdown-formatted docstring.
    """
    docstring = Docstring(symbol.__doc__)  # type: ignore
    parsed_docstring_sections = parse(docstring, Parser.google)
    formatted_docstring = ""
    for section in parsed_docstring_sections:
        section_dict = section.as_dict()
        if section_dict["kind"] == "text":
            formatted_docstring += f"{section.value}\n\n"

        elif section_dict["kind"] == "examples":
            section_header = f"**{section_dict['kind'].capitalize()}**:\n\n"
            formatted_docstring += f"{section_header}" + "".join(
                [f"{v[1]}\n\n" for v in section_dict["value"]]
            )

        elif section_dict["kind"] == "returns" or section_dict["kind"] == "yields":
            section_header = f"**{section_dict['kind'].capitalize()}**:\n\n"
            formatted_docstring += (
                f"{section_header}"
                + _format_return_section(section_dict, symbol)
                + "\n\n"
            )

        elif section_dict["kind"] == "raises":
            section_header = f"**{section_dict['kind'].capitalize()}**:\n\n"
            formatted_docstring += (
                f"{section_header}" + _format_raises_section(section_dict) + "\n\n"
            )
        elif section_dict["kind"] == "parameters":
            section_header = f"**{section_dict['kind'].capitalize()}**:\n\n"
            formatted_docstring += (
                f"{section_header}"
                + _format_parameters_section(section_dict, symbol)
                + "\n\n"
            )
        elif section_dict["kind"] == "admonition":
            value = section_dict["value"]
            annotation = value["annotation"]
            description = value["description"]
            formatted_docstring += (
                f"??? {annotation}"
                + "\n\n"
                + f"{textwrap.indent(description, '    ')}\n\n"
            )

    source_relative_filename = _get_source_relative_filename(getsourcefile(symbol))
    if source_relative_filename is not None:
        formatted_docstring += (
            f'??? quote "Source code in `{source_relative_filename}`"\n\n'
            + f"    ```python\n{textwrap.indent(getsource(symbol), '    ')}    ```\n\n"
        )

    return formatted_docstring

# %% ../../nbs/API_Docs_Helper.ipynb 40
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
                    contents += (
                        f"{_get_symbol_definition(y)}\n\n{_docstring_to_markdown(y)}"
                    )
                elif isclass(y) and not x.startswith("__") and y.__doc__ is not None:
                    contents += (
                        f"{_get_symbol_definition(y)}\n\n{_docstring_to_markdown(y)}"
                    )
                    contents = traverse(y, contents)
        return contents

    contents = (
        f"{_get_symbol_definition(symbol)}\n\n{_docstring_to_markdown(symbol)}"
        if symbol.__doc__ is not None
        else ""
    )
    if isclass(symbol):
        contents = traverse(symbol, contents)
    return contents
