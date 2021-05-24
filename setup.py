import sys

from setuptools import setup

if sys.version_info < (3, 5):
    print('rets requires Python 3.5 or later')
    sys.exit(1)


long_desc = 'Python 3 client for the Real Estate Transaction Standard (RETS) Version 1.7.2'

install_requires = [
    'requests>=2.12.3',
    'requests-toolbelt>=0.7.0,!=0.9.0',
    'udatetime==0.0.16',
    'docopts',
    'lxml>=4.3.0',
]

setup_requires = [
    'pytest-runner',
]

tests_requires = [
    'flake8',
    'pytest',
]

packages = [
    'rets',
    'rets.client',
    'rets.http',
    'rets.http.parsers',
]

setup(
    name='rets-python',
    version='0.4.6',
    description='rets-python',
    long_description=long_desc,
    author='Martin Liu',
    author_email='martin@opendoor.com',
    url='https://github.com/opendoor-labs/rets',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
    ],
    license='MIT License',
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_requires,
    packages=packages,
)
