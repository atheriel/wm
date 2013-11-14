import AppKit
import signal
import logging

from wm.manager import *

# Allow quitting with CTRL-C
signal.signal(signal.SIGINT, signal.SIG_DFL)

logging.basicConfig(
    filename="/tmp/wm.log",
    filemode="w",
    level=logging.DEBUG,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    datefmt='%y-%m-%d %H:%M:%S')

console = logging.StreamHandler()
console.setFormatter(logging.Formatter(
    fmt="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"))
logging.getLogger().addHandler(console)
console.setLevel(logging.DEBUG)

# New window manager & notification observer
wm = WindowManager()
observer = ObserverHelper.new()
observer.window_manager = wm

wm.reflow()

# Run app loop
AppKit.NSRunLoop.currentRunLoop().run()
