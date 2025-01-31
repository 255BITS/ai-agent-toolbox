#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="ai_agent_toolbox",
    version='0.1.11',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    extras_require={
        'dev': ['pytest']
    },
    python_requires=">=3.7",
    license="MIT",
    description="An easy to use framework for adding tool use to AI agents.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="255labs.xyz",
    author_email="martyn@255bits.com",
    url="https://github.com/255BITS/ai-agent-toolbox",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
