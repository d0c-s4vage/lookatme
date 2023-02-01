"""
Setup for lookatme
"""


import glob
import os
from setuptools import setup, find_namespace_packages
from typing import Dict, List


def load_requirements(file: str) -> List[str]:
    req_path = os.path.join(os.path.dirname(__file__), file)
    with open(req_path, "r") as f:
        required = f.read().splitlines()
    return required


def extra_requirements() -> Dict:
    res = {
        # user-facing "all" (excluding test deps)
        "all": [],
        # dev-facing "all" (including test deps)
        "dev": [],
    }
    reqs = glob.glob(os.path.join(os.path.dirname(__file__), "requirements", "*.txt"))

    for req_file in reqs:
        extra_name = os.path.basename(req_file).replace(".txt", "")
        with open(req_file, "r") as f:
            reqs = f.read().splitlines()
        res[extra_name] = reqs

        if extra_name != "test":
            res["all"] += reqs
        res["dev"] += reqs

    return res


req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
with open(req_path, "r") as f:
    required = f.read().splitlines()


readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r") as f:
    readme = f.read()


setup(
    name="lookatme",
    version="3.0.0rc4",
    description="An interactive, command-line presentation tool",
    author="James Johnson",
    author_email="d0c.s4vage@gmail.com",
    url="https://github.com/d0c-s4vage/lookatme",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=["docs", ".gitignore", "README.md", "tests"]),
    install_requires=load_requirements("requirements.txt"),
    include_package_data=True,
    classifiers=[
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Multimedia :: Graphics :: Presentation",
        "Topic :: Software Development :: Documentation",
    ],
    entry_points={
        "console_scripts": [
            "lookatme = lookatme.__main__:main",
        ]
    },
    extras_require=extra_requirements(),
)
