from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages

long_desc = 'Python 3.5 client for the Real Estate Transaction Standard (RETS) Version 1.7.2'

install_requires = [str(req.req) for req in parse_requirements('requirements.txt',
                                                               session=PipSession())]

setup(
    name='rets',
    version='0.1.0',
    description='rets',
    long_description=long_desc,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Other Audience',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
    ],
    author='Opendoor',
    author_email='developers@opendoor.com',
    url='https://github.com/opendoor-labs/rets',
    install_requires=install_requires,
    packages=find_packages(),
)
