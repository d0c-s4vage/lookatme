"""
Setup for lookatme
"""


from setuptools import setup, find_packages
import os


req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
with open(req_path, "r") as f:
    required = f.read().splitlines()


readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r") as f:
    readme = f.read().splitlines()


setup(
    name='lookatme',
    version='{{VERSION}}',
    description='An interactive, command-line presentation tool',
    author='James Johnson',
    author_email='d0c.s4vage@gmail.com',
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["docs", ".gitignore", "README.md"]),
    install_requires=required,
    entry_points={
        "console_scripts": [
            "lookatme = lookatme.__main__:main",
            "lam = lookatme.__main__:main",
            "witnessme = lookatme.__main__:main",
        ]
    },
)
