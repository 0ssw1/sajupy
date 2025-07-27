"""Setup configuration for sajupy package."""

from setuptools import setup, find_packages
from pathlib import Path

# 현재 디렉토리 경로
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# 버전 정보 읽기
version = {}
with open(this_directory / "src/sajupy/__init__.py", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="sajupy",
    version=version.get("__version__", "0.1.0"),
    author="Suh Seungwan",
    author_email="suh@yumeta.kr",
    description="사주팔자 만세력 계산 라이브러리",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0ssw1/sajupy",
    project_urls={
        "Bug Tracker": "https://github.com/0ssw1/sajupy/issues",
        "Documentation": "https://github.com/0ssw1/sajupy/wiki",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Other/Nonlisted Topic",
        "Natural Language :: Korean",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "geopy>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.990",
            "sphinx>=4.0.0",
        ],
    },
    package_data={
        "sajupy": ["calendar_data.csv"],
    },
    include_package_data=True,
    keywords="saju korean-calendar lunar-calendar 사주팔자 사주 음력 양력 만세력 bazi",
) 