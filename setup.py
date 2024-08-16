#!/usr/bin/env python3

from setuptools import setup, find_packages


def get_requirements():
    with open("requirements.txt", "r") as fp:
        requirements = fp.readlines()
    return requirements


def description():
    return "pyfyzz"


setup(
    name="pyfyzz",
    version="0.1",
    packages=find_packages(),
    entry_points={"console_scripts": ["pyfyzz = pyfyzz.main:main"]},
    install_requires=get_requirements(),
    description=description(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license=open("LICENSE").read(),
)
