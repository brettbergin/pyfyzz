#!/usr/bin/env python3

from setuptools import setup, find_packages

VERSION = "0.0.1"
NAME = "pyfyzz"


def get_requirements():
    with open("requirements.txt", "r") as fp:
        requirements = fp.readlines()
    return requirements


def description():
    return f"{NAME}:v{VERSION} - an automated type fuzzer for python packages"


def license():
    with open("LICENSE", "r") as fp:
        content = fp.read()
    return content


def readme():
    with open("README.md", "r") as fp:
        content = fp.read()
    return content


def entry_points():
    return {"console_scripts": ["pyfyzz = pyfyzz.main:main"]}


setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    entry_points=entry_points(),
    install_requires=get_requirements(),
    description=description(),
    long_description=readme(),
    long_description_content_type="text/markdown",
    license=license(),
)
