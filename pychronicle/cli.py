import click
import os
from pychronicle.tui import PyChronicleApp

@click.group()
def main():
    """PyChronicle: AST-Powered Time-Travel Debugger."""
    pass

@main.command()
@click.argument('script_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def run(script_path):
    """Run PyChronicle debugger on the target Python script."""
    PyChronicleApp(os.path.abspath(script_path)).run()

if __name__ == "__main__":
    main()
