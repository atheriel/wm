from distutils.core import setup, Extension
from platform import mac_ver


# Deal with the new location of headers in Mavericks
if mac_ver()[0].startswith('10.9'):
    header_dir = '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/HIServices.framework/Versions/A/Headers'  # noqa
else:
    header_dir = '/System/Library/Frameworks/ApplicationServices.framework/Frameworks/HIServices.framework/Headers'

shadows = Extension('wm._shadows',
    sources = ['wm/_shadows.c'],
    extra_link_args = ['-framework', 'Cocoa', '-v']
)

setup(
    name = 'wm',
    description = 'A window manager for OS X, written in Python.',
    version = '0.2.0',
    author_email = 'atheriel@gmail.com',
    url = 'https://github.com/atheriel/wm',
    license = 'ISCL',
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
    ext_modules = [shadows],
    scripts = ['scripts/wm'],
    package_data = {'wm': ['config/*.rc']},

    install_requires = [
        'docutils>=0.3',
        'docopt>=0.6.1',
        'accessibility>=0.3'
    ]
)
