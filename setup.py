import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flux_calculator",
    version="0.0.1",
    author="Colette Salyk",
    author_email="cosalyk@vassar.edu",
    description="A package to perform line fits for IR spectroscopic data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)    
