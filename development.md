# Development

## Linux

### Coverage 

Make sure pip package `coverage` is installed:

    (venv)[naev-pm]$ pip install coverage
    (venv)[naev-pm]$ coverage run --data-file temp/.coverage --source naevpm -m unittest discover -s tests/
    (venv)[naev-pm]$ coverage report -m --data-file temp/.coverage 
    (venv)[naev-pm]$ coverage html -d temp/htmlcov --data-file temp/.coverage 

Open temp/htmlcov/index.html in a browser

### Tests

    (venv)[naev-pm]$ python -m unittest discover -s tests/

### PyInstaller


Take note that site-packages path depends on python version.

    (venv)[naev-pm]$ pip install pyinstaller
    (venv)[naev-pm]$ cd src
    (venv)[src]$ pyinstaller --distpath ../temp/dist --workpath ../temp/build --onefile --windowed --hidden-import "PIL._tkinter_finder" --paths=venv/lib/python3.11/site-packages --add-data naevpm/gui/resources/icon2.png:naevpm/gui/resources/  --icon naevpm/gui/resources/icon2.png --name naevpm naevpm/gui/start.py && mv naevpm.spec ../temp/

## Windows

### PyInstaller

Given venv is in src folder:

    (venv)[naev-pm]$ cd src
    (venv)[src]$ pyinstaller --onefile --windowed --paths=venv\Lib\site-packages --add-data naevpm\gui\resources\icon2.png:naevpm\gui\resources\  --icon naevpm\gui\resources\icon2.png --name naevpm naevpm\gui\start.py

