from setuptools import setup
import sys

setup(
    name='Lego_v0',
    version='0.0.1',
    url='https://github.com/sgauthamr2001/Lego_v0',
    description='Data tiling code generation compiler for the AHA CGRA',
    packages=[
        "./",
    ],
    install_requires=[
        "sam",
        "lark",
        "sparse"
    ],
    python_requires='>=3.6'
)
