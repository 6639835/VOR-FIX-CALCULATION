"""
Setup configuration for VOR FIX Coordinate Calculator
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="vor-fix-calculator",
    version="2.0.0",
    author="VOR FIX Calculator Team",
    description="A professional aviation coordinate calculation application for determining waypoint and FIX coordinates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/6639835/VOR-FIX-CALCULATION",
    packages=find_packages(exclude=["tests", "tests.*", "legacy", "legacy.*", "scripts", "scripts.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Other Audience",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vor-fix-calculator=src.main:main",
        ],
        "gui_scripts": [
            "vor-fix-calculator-gui=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="aviation navigation vor dme ndb waypoint fix coordinates geodesic",
    project_urls={
        "Bug Reports": "https://github.com/6639835/VOR-FIX-CALCULATION/issues",
        "Source": "https://github.com/6639835/VOR-FIX-CALCULATION",
    },
)

