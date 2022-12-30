"""
Setup for lookatme
"""


from setuptools import setup, find_namespace_packages
import os


req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
with open(req_path, "r") as f:
    required = f.read().splitlines()


readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r") as f:
    readme = f.read()


setup(
    name="lookatme",
    version="3.0.0rc1",
    description="An interactive, command-line presentation tool",
    author="James Johnson",
    author_email="d0c.s4vage@gmail.com",
    url="https://github.com/d0c-s4vage/lookatme",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=["docs", ".gitignore", "README.md", "tests"]),
    install_requires=required,
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
            "lam = lookatme.__main__:main",
            "witnessme = lookatme.__main__:main",
        ]
    },
)
