from distutils.core import setup, Extension

accessibility = Extension(
	'wm._accessibility', 
	sources = ['wm/_accessibility.c'],
	include_dirs=['/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/Headers'],
	extra_link_args=['-framework', 'ApplicationServices', '-v']
)

shadows = Extension(
	'wm._shadows', 
	sources = ['wm/_shadows.c'],
	extra_link_args=['-framework', 'Cocoa', '-v']
)

setup(
    name = 'Window Manager',
    version = '0.1',
    packages = ['wm'],
    py_modules = ['wm.config', 'wm.elements', 'wm.errors', 'wm.manager', 'wm.utils'],
    ext_modules=[accessibility, shadows]
)