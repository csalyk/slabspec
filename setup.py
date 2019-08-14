import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="slabspec",
    version="0.0.1",
    author="Colette Salyk",
    author_email="cosalyk@vassar.edu",
    description="A package to create infrared spectra using the HITRAN database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)    
