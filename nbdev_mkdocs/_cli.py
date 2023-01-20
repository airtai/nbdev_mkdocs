# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/CLI.ipynb.

# %% auto 0
__all__ = ['new', 'prepare', 'preview', 'docs', 'generate_social_image']

# %% ../nbs/CLI.ipynb 1
from typing import *
from pathlib import Path
from asyncio import run as aiorun

import typer

import nbdev_mkdocs
import nbdev_mkdocs.mkdocs
from docstring_gen.docstring_generator import add_docstring_to_source

# %% ../nbs/CLI.ipynb 3
_app = typer.Typer(help="")


@_app.command(
    help="Creates files in **mkdocs** subdirectory needed for other **nbdev_mkdocs** subcommands",
)
def new(root_path: str = typer.Option(".", help="")):
    """CLI command for creating files for nbdev_mkdocs command"""
    try:
        nbdev_mkdocs.mkdocs.new(root_path=root_path)
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)


@_app.command(
    help="Runs tests and prepares files in **mkdocs/docs** and then runs **mkdocs build** command on them ",
)
def prepare(root_path: str = typer.Option(".", help="")):
    """CLI command for running tests and creating files for nbdev_mkdocs command"""
    try:
        nbdev_mkdocs.mkdocs.prepare(root_path=root_path)
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)


@_app.command(
    help="Prepares files in **mkdocs/docs** and then runs **mkdocs serve** command on them ",
)
def preview(
    root_path: str = typer.Option(
        ".", help="path under which mkdocs directory will be created"
    ),
    port: int = typer.Option(4000, help="port to use"),
):
    """CLI command for creating files for nbdev_mkdocs command"""
    try:
        nbdev_mkdocs.mkdocs.preview(root_path=root_path, port=port)
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)


@_app.command(
    help="Prepares files in **mkdocs/docs** and then runs **mkdocs build** command on them ",
)
def docs(root_path: str = typer.Option(".", help="Project's root path.")):
    """CLI command for creating files for nbdev_mkdocs command"""
    try:
        nbdev_mkdocs.mkdocs.nbdev_mkdocs_docs(
            root_path=root_path, refresh_quarto_settings=True
        )
    except Exception as e:
        typer.secho(f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1)


@_app.command(
    help="Generate a custom social share image",
)
def generate_social_image(
    root_path: str = typer.Option(".", help="Project's root path."),
    generator: nbdev_mkdocs.social_image_generator._IMG_Generator = typer.Option(
        "file",
        help="Generator to use to create the social image. Valid options are: 'file' and 'dall_e'. Choose 'file' if you want to use an existing image from your local machine in the social share image.",
    ),
    prompt: Optional[str] = typer.Option(
        "Cute animal wearing hoodie sitting in high chair in purple room, browsing computer, 3d render",
        help="The prompt to use for generating the image.",
    ),
    image_path: Optional[str] = typer.Option(
        None,
        help="Image file path to use in the social share image. Use images with a 1:1 aspect ratio and at least 512x512 pixels for the best results. If None, then the default image will be used.",
    ),
):
    """CLI command for generating a custom social share image"""

    async def _generate_social_image(root_path, generator, prompt, image_path):
        """Generate a social image.

        Args:
            root_path: The root path of the project.
            generator: The generator to use.
            prompt: The prompt to use.
            image_path: The path to save the image to.

        Raises:
            typer.Exit: If an unexpected internal error occurs.

        !!! note

            The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
        """
        try:
            await nbdev_mkdocs.social_image_generator.generate_social_image(
                root_path=root_path,
                generator=generator,
                prompt=prompt,
                image_path=image_path,
            )
        except Exception as e:
            typer.secho(
                f"Unexpected internal error: {e}", err=True, fg=typer.colors.RED
            )
            raise typer.Exit(1)

    aiorun(_generate_social_image(root_path, generator, prompt, image_path))

# %% ../nbs/CLI.ipynb 5
def _create_docstring_gen_sub_cmd(_app: typer.Typer = _app) -> None:

    _docstring_gen_app = typer.Typer(
        help="Command for adding docstrings to classes and methods that don't have one using docstring-gen library."
    )

    @_docstring_gen_app.command(
        help="Add docstring to classes and methods that don't have one using docstring-gen library.",
    )
    def generate(
        path: str = typer.Argument(
            ".",
            help="The path to the Jupyter notebook or Python file, or a directory containing these files",
        ),
        include_auto_gen_txt: bool = typer.Option(
            True,
            help="If set to True, a note indicating that the docstring was autogenerated by docstring-gen library will be added to the end.",
        ),
        recreate_auto_gen_docs: bool = typer.Option(
            False,
            "--force-recreate-auto-generated",
            "-f",
            help="If set to True, the autogenerated docstrings from the previous runs will be replaced with the new one.",
        ),
        model: str = typer.Option(
            "code-davinci-002",
            help="The name of the Codex model that will be used to generate docstrings.",
        ),
        temperature: float = typer.Option(
            0.2,
            help="Setting the temperature close to zero produces better results, whereas higher temperatures produce more complex, and sometimes irrelevant docstrings.",
            min=0.0,
            max=1.0,
        ),
        max_tokens: int = typer.Option(
            250,
            help="The maximum number of tokens to be used when generating a docstring for a function or class. Please note that a higher number will deplete your token quota faster.",
        ),
        top_p: float = typer.Option(
            1.0,
            help="You can also specify a top-P value from 0-1 to achieve similar results to changing the temperature. According to the Open AI documentation, it is generally recommended to change either this or the temperature but not both.",
            min=0.0,
            max=1.0,
        ),
        n: int = typer.Option(
            3,
            help="The number of docstrings to be generated for each function or class, with the best one being added to the source code. Please note that a higher number will deplete your token quota faster.",
        ),
    ) -> None:

        """Add docstring to classes and methods that don't have one by using the 'docstring-gen' library

        Args:
            path: The path to the Jupyter notebook or Python file, or a directory containing these files.
            include_auto_gen_txt: If set to True, a note indicating that the docstring was autogenerated by 'docstring-gen' library will be added to the end.
            recreate_auto_gen_docs: If set to True, the autogenerated docstrings from the previous runs will be replaced with the new one.
            model: The name of the Codex model that will be used to generate docstrings.
            temperature: Setting the temperature close to zero produces better results, whereas higher temperatures produce more complex, and sometimes irrelevant docstrings.
            max_tokens: The maximum number of tokens to be used when generating a docstring for a function or class. Please note that a higher number will deplete your token quota faster.
            top_p: You can also specify a top-P value from 0-1 to achieve similar results to changing the temperature. According to the Open AI documentation, it is generally recommended to change either this or the temperature but not both.
            n: The number of docstrings to be generated for each function or class, with the best one being added to the source code. Please note that a higher number will deplete your token quota faster.

        Returns:
            None

        !!! note

            The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
        """
        try:
            add_docstring_to_source(
                path=path,
                include_auto_gen_txt=include_auto_gen_txt,
                recreate_auto_gen_docs=recreate_auto_gen_docs,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                n=n,
            )
        except Exception as e:
            typer.secho(e, err=True, fg=typer.colors.RED)
            raise typer.Exit(1)

    _app.add_typer(
        _docstring_gen_app,
        name="docstring",
    )


_create_docstring_gen_sub_cmd()
