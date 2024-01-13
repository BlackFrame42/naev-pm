import logging

logger = logging.getLogger(__name__)

try:
    import tkinter
except ImportError as e:
    logger.critical("Could not load 'tkinter'. Make sure it is installed. Exception: " + str(e))
    # tkinter is usually bundled with python. On Linux systems, you might need to install it with the
    # distribution's package manager.
    import platform

    if platform.system() == 'Linux':
        logger.info("You run Linux. Try to install tkinter with your distribution's package manager.")
        import shutil

        if shutil.which('pacman'):
            logger.info("Your Linux distribution supports 'pacman'. Try to run 'sudo pacman -S tk' and "
                        "restart this application.")
        elif shutil.which('apt'):
            logger.info("Your Linux distribution supports 'apt'. try to run 'sudo apt install python3-tk' and "
                        "restart this application.")
    exit(1)

# Check version
tkinter_version = tkinter.Tcl().eval('info patchlevel')
logger.info(f"tkinter version '{tkinter_version}'")

# Check "Thread-enabled Operations" support
if tkinter.Tcl().eval('set tcl_platform(threaded)') != '1':
    logger.critical("Loaded tkinter version does not support 'Thread-enabled Operations'. "
                    "This application uses multiple threads for background tasks and depends on a tkinter version "
                    ">8.6 that is safe to use with multiple threads. Link: https://www.tcl.tk/software/tcltk/8.6.html")
    exit(2)
