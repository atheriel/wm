#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import wm
except ImportError:
    print 'wm has not been installed properly.'
    exit(1)

__doc__ = """wm: %(desc)s

Usage:
  wm [-V N --config FILE]
  wm (start | stop) [-V N --config FILE]
  wm copy-config
  wm toggle-shadows
  wm -h | --help | --version

Commands:
  start, stop         start or stop the window manager as a daemon
  copy-config         copy the default configuration files to ~/.config/wm/
                      and exit
  toggle-shadows      toggle OS X shadows on or off and exit

Options:
  -V, --log-level N   the level of info logged to the console, which can be
                      one of INFO, DEBUG, or WARNING [default: INFO]
      --config FILE   load the configuration in FILE
  -v, --version       show program's version number and exit
  -h, --help          show this help message and exit

Licensed under the %(license)s.
""" % {'desc': wm.__doc__, 'license': wm.__license__}

try:
    import accessibility
    if not accessibility.is_enabled():
        print 'Accessibility must be enabled before this program can run.'
        exit(1)
except ImportError:
    print 'wm depends on the Accessibility module, which does not seem to be installed.'
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
    from docopt import docopt

    args = docopt(__doc__, version = 'wm version: %s' % wm.__version__)

    if args['toggle-shadows']:
        toggle_shadows()
        exit(0)

    if args['copy-config']:
        copy_config()
        exit(0)

    import logging
    import wm.manager

    logging.basicConfig(
        filename = "/tmp/wm.log",
        filemode = "w",
        level = getattr(logging, args['--log-level'].upper()),
        format = '[%(asctime)s][%(levelname)s] %(message)s',
        datefmt = '%y-%m-%d %H:%M:%S')

    daemon = wm.manager.WindowManager('/tmp/wm-daemon.pid')

    if args['start']:
        logging.info('Starting daemon...')
        daemon.start()

    elif args['stop']:
        logging.info('Stopping daemon...')
        daemon.stop()

    else:
        # Logs to console as well
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            fmt="[%(asctime)s][%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"))
        logging.getLogger().addHandler(console)
        console.setLevel(getattr(logging, args['--log-level'].upper()))

        daemon.run()

if __name__ == "__main__":
    main()
