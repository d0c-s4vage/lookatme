"""
Setup for lookatme.contrib.calender example
"""


from setuptools import setup, find_namespace_packages
import os


setup(
    name="lookatme.contrib.calendar",
    version="0.0.0",
    description="Adds a calendar code block type",
    author="James Johnson",
    author_email="d0c.s4vage@gmail.com",
    python_requires=">=3.5",
    packages=find_namespace_packages(include=["lookatme.*"]),
)
