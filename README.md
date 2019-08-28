# slabspec
slabspec is a set of python codes to produce LTE slab model spectra using the HITRAN database.  Code
is created with infrared medium/high-resolution spectroscopy in mind.  

Users are requested to let the developer know if they are using the code.  Code has been
tested for only a few use cases, and users utilize at their own risk.

# Requirements
Requires internet access to utilize astroquery.hitran and access HITRAN partition function files

Requires the molmass and astropy packages

## Functions
extract_hitran_data extracts relevant data from HITRAN database

compute_partition_function compute a partition function given a molecule, isotopologue, and temperature

spec_convol performs convolution of a spectrum given a spectrum and convolution FWHM 

make_spec produces a model spectrum with the desired attributes

make_rotation_diagram computes abscissa and ordinate values for a rotation diagram, given make_spec lineparams output

## Usage

```python
from slabspec import extract_hitran_data
hitran_table=extract_hitran_data('CO',4,5,isotopologue_number=1, eupmax=9000., aupmin=10.)

from slabspec import compute_partition_function
q=compute_partition_function('CO', 800., isotopologue_number=1)

from slabspec import spec_convol
convolflux=spec_convol(wave, flux, 12.5)

from slabspec import make_spec
out=make_spec('CO',1.e20,600.,(1*1.5e11)**2., wmin=4.5, wmax=5, d_pc=140.,
              res=1.e-6,vup=1)

out=make_spec('H2O',1.e20,600.,(1*1.5e11)**2., wmin=15, wmax=17, d_pc=140.,
              res=1.e-6)

from slabspec import make_rotation_diagram
rot=make_rotation_diagram(out['lineparams'])

```

## License
[MIT](https://choosealicense.com/licenses/mit/)

