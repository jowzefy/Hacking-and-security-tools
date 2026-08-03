from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="god-web-master",
    version="5.0.0",
    author="God_Web_Master",
    description="Professional Web Scanner and Information Gatherer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "colorama>=0.4.6",
        "builtwith>=1.3.0",
        "requests>=2.31.0",
        "ipapi>=1.0.0",
        "pyyaml>=6.0.1",
        "cryptography>=41.0.7",
        "tldextract>=5.0.1",
        "aiohttp>=3.9.1",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "god-web-master=app.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)