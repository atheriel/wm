from distutils.core import setup, Extension

import wm

accessibility = Extension(
	'wm._accessibility', 
	sources = ['wm/_accessibility.c'],
	include_dirs = ['/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/Headers'],
	extra_link_args = ['-framework', 'ApplicationServices', '-v']
)

shadows = Extension(
	'wm._shadows', 
	sources = ['wm/_shadows.c'],
	extra_link_args = ['-framework', 'Cocoa', '-v']
)

setup(
    name = 'wm',
    description = wm.__doc__,
    version = wm.__version__,
    author_email = 'atheriel@gmail.com',
    url = 'https://github.com/atheriel/wm',
    license = wm.__license__,
    platforms = ['MacOS X'],

    packages = ['wm'],
    py_modules = ['wm.config', 'wm.elements', 'wm.errors', 'wm.manager', 'wm.utils'],
    ext_modules = [accessibility, shadows],
    scripts = ['scripts/wm'],
    package_data = {'wm': ['config/*.rc']},

    install_requires = ['docutils>=0.3']
)
