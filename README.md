# NAEV PLUGIN MANAGER
> **Warning**
> **This is a proof of concept.** naev-pm is extreme alpha and not production ready at all.

Plugin registry manager for Naev. This is not official Naev-related software.

Links to resources:
- https://github.com/naev/naev/blob/main/docs/manual/sec/plugins.md

## Usage

Change directory into src/ and run

    python -m naevpm.gui.start

or run the cli tool with 

    python -m naevpm.cli

or change to main directory above src/ and install it as a package (creating venv advised).

    python -m venv venv
    . venv\bin\activate
    pip install .

It creates the cli commands 'naevpm' and 'naevpm-gui'.   

    $ naevpm registry --help
    Usage: naevpm registry [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      add
      fetch
      fetch-all
      list
      remove

    $ naevpm plugin --help
    Usage: naevpm plugin [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      check-all-for-update
      check-for-update
      delete
      fetch
      install
      list
      remove
      uninstall
      update

## Example screenshots

![GUI Screen Shots](Screenshot%20from%202024-01-07%2000-22-56.png "GUI Screen Shots")
![GUI Screen Shots](Screenshot%20from%202024-01-07%2000-23-03.png "GUI Screen Shots")

## Tests

    (venv)[naev-pm]$ python -m unittest discover -s tests/

## Coverage

    (venv)[naev-pm]$ coverage run -m unittest discover -s tests/
    (venv)[naev-pm]$ coverage report -m 
    (venv)[naev-pm]$ coverage html
