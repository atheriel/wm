import os, os.path, shutil, ast, logging
from ConfigParser import RawConfigParser

__config_dir__ = 'wm'
__config_file__ = 'wm.rc'
__default_dir__ = os.path.join(os.path.dirname(__file__), 'config')

IGNORED_BUNDLES = []
MIN_SIZES = dict()

def get_config_dir():
	"""
	Gets the path of the configuration file directory.
	"""
	xdg_dir = os.getenv('XDG_CONFIG_HOME', os.environ['HOME'] + '/.config')
	return os.path.join(os.path.expanduser(xdg_dir), __config_dir__)

def copy_config(internal = False):
	"""
	Copies the default config file to XDG_CONFIG_HOME/wm/wm.rc. If the file
	already exists, prompt the user to confirm.

	If the internal parameter is set to ``True``, then prompting and output are
	respectively suppressed and redirected to logging.
	"""
	default_config_file = os.path.abspath(os.path.join(__default_dir__, __config_file__))
	config_dir = get_config_dir()
	config_file = os.path.join(config_dir, __config_file__)

	if os.path.exists(config_file) and not internal:
		print 'A configuration file already exist at this location. Overwrite? [y/n]',
		choice = raw_input()
		while choice != 'y' and choice != 'n':
			print 'Input error, try again:',
			choice = raw_input()

		if choice == 'n':
			return None

	if not os.path.exists(config_dir):
		os.mkdir(config_dir)
	shutil.copy(default_config_file, config_dir)
	
	if not internal:
		print 'Default configuration copied to %s.' % config_file
	else:
		logging.debug('Default configuration copied to %s.', config_file)

def read_config(filename = None):
	"""
	Reads the config file at filename (or at the default location if filename
	is ``None``).
	"""
	global IGNORED_BUNDLES
	global MIN_SIZES

	if filename == None:
		filename = os.path.join(get_config_dir(), __config_file__)
		if not os.path.exists(filename):
			copy_config(internal = True)
	
	config = RawConfigParser()
	config.read(filename)
	
	IGNORED_BUNDLES = ast.literal_eval(config.get('General', 'ignored_bundles'))
	
	for name, value in config.items('Minimum Sizes'):
		MIN_SIZES[name] = ast.literal_eval(value)
