from distutils.core import setup, Extension

import wm

accessibility = Extension('wm._accessibility',
    sources = ['wm/_accessibility.c'],
    include_dirs = ['/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/Headers'],
    # Uncomment the next line to include debug symbols while compiling
    # extra_compile_args = ['-g'],
    extra_link_args = ['-framework', 'ApplicationServices', '-v']
)

shadows = Extension('wm._shadows',
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
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Environment :: Console',
        'Environment :: MacOS X :: Cocoa',
        'Operating System :: MacOS :: MacOS X',
        'Natural Language :: English',
        'Topic :: Desktop Environment :: Window Managers',
    ],

    packages = ['wm'],
    py_modules = ['wm.config', 'wm.daemon', 'wm.elements', 'wm.errors', 'wm.manager', 'wm.utils'],
    ext_modules = [accessibility, shadows],
    scripts = ['scripts/wm'],
    package_data = {'wm': ['config/*.rc']},

    install_requires = [
        'docutils>=0.3',
        'docopt>=0.6.1',
    ]
)
