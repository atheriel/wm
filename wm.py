#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
	import wm
except ImportError:
	print 'wm has not been installed properly.'
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
	options.add_argument('-V', '--log-level', metavar='N', default = 'INFO', choices = ['DEBUG', 'INFO', 'WARNING'], nargs = 1, 
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

	import logging

	logging.basicConfig(
	    filename = "/tmp/wm.log",
	    filemode = "w",
	    level = getattr(logging, args.log_level.upper()),
	    format = '[%(asctime)s][%(levelname)s] %(message)s',
	    datefmt = '%y-%m-%d %H:%M:%S')

	console = logging.StreamHandler()
	console.setFormatter(logging.Formatter(
	    fmt="[%(asctime)s][%(levelname)s] %(message)s",
	    datefmt="%H:%M:%S"))
	logging.getLogger().addHandler(console)
	console.setLevel(getattr(logging, args.log_level.upper()))

	from AppKit import NSRunLoop
	from wm.manager import WindowManager, ObserverHelper

	# New window manager & notification observer
	wm = WindowManager()
	observer = ObserverHelper.new()
	observer.window_manager = wm

	wm.reflow()

	# Run app loop
	NSRunLoop.currentRunLoop().run()

if __name__ == "__main__":
	main()
