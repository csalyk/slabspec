import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="slabspec",
    version="1.0",
    author="Colette Salyk",
    author_email="cosalyk@vassar.edu",
    description="A package to calculate molecular slab models for IR spectroscopic data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['slabspec'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
