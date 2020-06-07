#!/usr/bin/env python
from setuptools import setup, Extension
from os.path import join
import sys

MAJOR, MINOR = sys.version_info[:2]

SRC_BASE = 'regex_%i' % MAJOR

with open('README.md') as file:
    long_description = file.read()

setup(
    name='cpytraceafl-regex',
    version='0.1.1',  # based on mrab-regex 2020.5.14
    description='A modified version of mrab-regex with added cpytraceafl instrumentation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Robert Scott',
    author_email='code@humanleg.org.uk',
    url='https://github.com/risicle/cpytraceafl-regex',
    license='Python Software Foundation License',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: General',
    ],

    package_dir={'regex': SRC_BASE},
    py_modules=['regex.__init__', 'regex.regex', 'regex._regex_core',
     'regex.test_regex'],
    ext_modules=[Extension('regex._regex', [join(SRC_BASE, '_regex.c'),
      join(SRC_BASE, '_regex_unicode.c')])],

    setup_requires=["pytest-runner"],
    # apologies for exact version specifier, but there is a binary interface that must be
    # adhered to
    install_requires=["cpytraceafl==0.7.0"],
    tests_require=["pytest"],
)
