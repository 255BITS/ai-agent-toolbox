#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="ai_agent_toolbox",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    license="MIT",
    description="A toolbox for building AI agent systems with parseable communications",
    author="Your Company",
    author_email="dev@example.com",
    url="https://example.com/ai_agent_toolbox",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
