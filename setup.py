from setuptools import setup, find_packages

setup(
    name="kwen-ext",
    version="1.0.0",
    description="Media extractor toolkit — pull video streams, download links & metadata from streaming sites",
    author="Kwen",
    url="https://github.com/kwen/kwen-ext",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.12.0",
        "cloudscraper>=1.2.71",
        "lxml>=4.9.0",
    ],
    entry_points={
        "console_scripts": [
            "kwen-ext=kwen_ext.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
