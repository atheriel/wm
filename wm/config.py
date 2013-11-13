from ConfigParser import RawConfigParser
import ast

IGNORED_BUNDLES = []
MIN_SIZES = dict()

def read_config(filename):
	global IGNORED_BUNDLES
	global MIN_SIZES
	
	config = RawConfigParser()
	config.read(filename)
	
	IGNORED_BUNDLES = ast.literal_eval(config.get('General', 'ignored_bundles'))
	
	for name, value in config.items('Minimum Sizes'):
		MIN_SIZES[name] = ast.literal_eval(value)
