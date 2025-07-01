from pathlib import Path

from setuptools import setup

if __name__ == "__main__":
    requirements_path = Path(__file__).parent / "requirements.txt"
    requirements_lines = requirements_path.read_text().strip().splitlines()

    readme_path = Path(__file__).parent / "README.md"
    long_description = readme_path.read_text()

    version_path = Path(__file__).parent / "pydra" / "version.txt"
    version = version_path.read_text().strip()

    setup(
        name="pydra-config",
        version=version,
        packages=["pydra"],
        author="Jordan Juravsky",
        url="https://github.com/jordan-benjamin/pydra",
        description="A flexible configuration library in pure Python",
        install_requires=requirements_lines,
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires=">=3.10",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3.10",
        ],
        license="Apache License 2.0",
        include_package_data=True,
    )
