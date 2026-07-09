from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in swift_theme/__init__.py
from swift_theme import __version__ as version

setup(
    name="swift_theme",
    version=version,
    description="Swift Theme - Fast, multi-scheme theme for Frappe v16 (Desk, Portal, Login)",
    author="MuleRun",
    author_email="hello@mulerun.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
