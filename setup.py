import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# The requirements file
with open('requirements.txt') as f:
    required = f.read().splitlines()

# This call to setup() does all the work
setup(
    name="crdesc",
    version="0.1",
    description="crdesc is a python package that produces a textual description from a crmodel.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/jeremyk6/crdesc/",
    author="Jérémy Kalsron",
    author_email="jeremy.kalsron@gmail.com  ",
    license="AGPL-3.0",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=required,
    packages=["crdesc"],
    include_package_data=True,
)
