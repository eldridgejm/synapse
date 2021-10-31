from setuptools import setup, find_packages


setup(
    name="synapse",
    version="0.0.0",
    packages=find_packages(),
    install_requires=["pyyaml"],
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "synapse = synapse.cli:main",
        ]
    },
)
