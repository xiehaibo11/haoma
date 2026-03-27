#!/usr/bin/env python3
"""
Setup script for LiveStream Phone Extractor
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "LiveStream Phone Extractor - Extract phone numbers from live stream comments"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "playwright>=1.40.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
    ]

setup(
    name="livestream-phone-extractor",
    version="1.0.0",
    author="LiveStream Scraper Team",
    author_email="contact@example.com",
    description="Extract phone numbers from live stream comments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/livestream-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "livestream-scraper=src.scraper:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.txt", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/livestream-scraper/issues",
        "Source": "https://github.com/yourusername/livestream-scraper",
        "Documentation": "https://github.com/yourusername/livestream-scraper/tree/main/docs",
    },
    keywords="scraper phone extractor livestream comments automation playwright",
    license="MIT",
    zip_safe=False,
)
