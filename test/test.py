import AppKit
import signal
from wm.manager import *

# Allow quitting with CTRL-C
signal.signal(signal.SIGINT, signal.SIG_DFL)

# New window manager & notification observer
wm = WindowManager(debug = False)
observer = ObserverHelper.new()
observer.window_manager = wm

# wm.reflow()

# Run app loop
AppKit.NSRunLoop.currentRunLoop().run()
