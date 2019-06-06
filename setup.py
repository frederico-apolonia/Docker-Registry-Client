from setuptools import setup
from os import path
import re


def packagefile(*relpath):
    return path.join(path.dirname(__file__), *relpath)


def read(*relpath):
    with open(packagefile(*relpath)) as f:
        return f.read()


def get_version(*relpath):
    match = re.search(
        r'''^__version__ = ['"]([^'"]*)['"]''',
        read(*relpath),
        re.M
    )
    if not match:
        raise RuntimeError('Unable to find version string.')
    return match.group(1)


setup(
    name='docker-registry-admin',
    version=get_version('docker_registry_client.py'),
    description='A convenience script to list and delete registries from docker registry.',
    long_description=read('README.rst'),
    url='https://github.com/frederico-apolonia/Docker-Registry-Client',
    author='Frederico Apolonia',
    author_email='fredericojcapolo@gmail.com',
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='docker registry',
    install_requires=[
        'docopt',
        'requests',
    ],
    package_dir={'': '.'},
    py_modules=['docker_registry_client'],
    entry_points={
        'console_scripts': [
            'docker-registry=docker_registry_client:main',
        ],
    },
)
