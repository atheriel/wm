#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	import wm
except ImportError:
	print 'wm has not been installed properly.'
	exit(1)

if not wm.accessibility_check():
	print 'Accessibility must be enabled on this system before this program can run:'
	print '    System Preferences -> Accessibility -> Enable access for assistive devices.'
	exit(1)

import signal
# Allow quitting with CTRL-C
signal.signal(signal.SIGINT, signal.SIG_DFL)

def toggle_shadows():
	import wm._shadows
	wm._shadows.toggle_shadows()

def copy_config():
	import wm.config
	wm.config.copy_config()

def main():
	import wm
	from argparse import ArgumentParser
	from wm.utils import WellSpacedHelpFormatter

	parser = ArgumentParser(description = wm.__doc__, 
		add_help = False,
		usage = '%s [options]' % 'wm',
		formatter_class = lambda prog: WellSpacedHelpFormatter(prog, max_help_position = 30),
		epilog = "Licensed under the %s." % 'ISC')

	options = parser.add_argument_group('Options')

	options.add_argument('--config', metavar = 'FILE', type = file, nargs = 1,
		help = 'load the configuration in FILE')
	options.add_argument('-V', '--log-level', metavar='N', default = 'INFO', choices = ['DEBUG', 'INFO', 'WARNING'], nargs = 1, type = str,
		help = 'the level of info logged to the console, which can be one of INFO, DEBUG, or WARNING (default: %(default)s)')
	options.add_argument('-q', '--quiet', action = 'store_true', help = 'suppress output')

	other = parser.add_argument_group('Other')

	other.add_argument('--copy-config', action = 'store_true',
		help = 'copy the default configuration files to ~/.config/wm/ and exit')
	other.add_argument('--shadows', action = 'store_true',
		help = 'toggle OS X shadows on or off and exit')
	other.add_argument('-v', '--version', action = 'version',
		version = '%s version: %s' % ('wm', wm.__version__))
	other.add_argument('-h', '--help', action = 'help',
		help = 'show this help message and exit')

	args = parser.parse_args()

	if args.shadows:
		toggle_shadows()
		exit(0)

	if args.copy_config:
		copy_config()
		exit(0)

	if isinstance(args.log_level, list): # silly argparse...
		args.log_level = args.log_level[0]
	
	import logging

	logging.basicConfig(
	    filename = "/tmp/wm.log",
	    filemode = "w",
	    level = getattr(logging, args.log_level),
	    format = '[%(asctime)s][%(levelname)s] %(message)s',
	    datefmt = '%y-%m-%d %H:%M:%S')

	console = logging.StreamHandler()
	console.setFormatter(logging.Formatter(
	    fmt="[%(asctime)s][%(levelname)s] %(message)s",
	    datefmt="%H:%M:%S"))
	logging.getLogger().addHandler(console)
	console.setLevel(getattr(logging, args.log_level.upper()))

	import wm.config
	import wm.manager
	from Quartz import CFRunLoopRun, NSEvent

	# New window manager & notification observer
	WM = wm.manager.WindowManager()
	observer = wm.manager.ObserverHelper.new()
	observer.window_manager = WM

	WM.reflow()

	# Allows calling arbitrary methods of WindowManager with hotkeys
	def hotkey_handler(proxy, type, event, refcon):
		keyEvent = NSEvent.eventWithCGEvent_(event)
		flags = keyEvent.modifierFlags()
		
		if flags != 0: # any key event we want deals with mod keys
			code = keyEvent.keyCode()
			
			# Cycle through registered hotkeys
			for name, value in wm.config.HOTKEYS.items():
				if (value[0] & flags) and value[1] == code:
					# call the name of the hotkey as a function
					getattr(WM, name)()
					logging.debug('Called method \'%s\' in response to hotkey.', name)
					continue

	wm.manager._add_hotkey_callback(hotkey_handler)

	# Run app loop
	CFRunLoopRun()

if __name__ == "__main__":
	main()
