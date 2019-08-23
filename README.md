# slabspec
slabspec is a set of python codes to produce LTE slab model spectra using the HITRAN database

## Functions
makespec produces a spectrum with the desired attributes
utils.helpers.extract_hitran_data extracts relevant data from HITRAN database
## Usage

```python
from slabspec.utils.helpers import extract_hitran_data
extract_hitran_data('CO',4,5,isotopologue_number=1, eupmax=9000., aupmin=10.)

from slabspec.slabspec.slabspec import make_spec
out=make_spec('CO',1.e20,600.,(1*1.5e11)**2., wmin=4.5, wmax=5, d_pc=140.,
              res=1.e-6,vup=1)

out=make_spec('H2O',1.e20,600.,(1*1.5e11)**2., wmin=15, wmax=17, d_pc=140.,
              res=1.e-6)
```

## License
[MIT](https://choosealicense.com/licenses/mit/)

