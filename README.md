# NAEV PLUGIN MANAGER

> **Warning**
> **This is a proof of concept.** naev-pm is extreme alpha and not production ready at all.

Plugin manager for Naev. This is not official Naev-related software.

Links to resources:
- What is a Naev plugin? https://github.com/naev/naev/blob/main/docs/manual/sec/plugins.md
- Official plugin registry: https://github.com/naev/naev-plugins
- Naev the game: https://github.com/naev/naev

## Usage

### Linux

Setup python venv:

    [naev-pm]$ python -m venv temp/venv
    [naev-pm]$ . temp/venv/bin/activate
    (venv)[naev-pm]$ pip install -r requirements.txt

For GUI run

    (venv)[naev-pm]$ cd src
    (venv)[src]$ python -m naevpm.gui.start

for CLI tool run

    (venv)[src]$ python -m naevpm.cli

or install it as a package.

    (venv)[src]$ cd ..
    (venv)[naev-pm]$ pip install .

It creates the CLI commands 'naevpm' and 'naevpm-gui'.   

    (venv)[naev-pm]$  naevpm registry --help
    Usage: naevpm registry [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      add
      fetch
      fetch-all
      list
      remove

    (venv)[naev-pm]$  naevpm plugin --help
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

### Windows

There is an experimental prerelease build for Windows. It is an exe which opens the GUI.
Release page: https://github.com/BlackFrame42/naev-pm/releases/tag/0.2.1

## Example screenshots
![GUI Screen Shots](Screenshot%20from%202024-01-13%2022-18-32.png "GUI Screen Shots")
![GUI Screen Shots](Screenshot%20from%202024-01-13%2022-18-37.png "GUI Screen Shots")

## Development

Read [development.md](development.md) for more details.
