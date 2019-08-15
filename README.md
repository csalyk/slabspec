# slabspec
slabspec is a set of python codes to produce LTE slab model spectra using the HITRAN database

## Functions
makespec produces a spectrum with the desired attributes
utils.helpers.extract_hitran_data extracts relevant data from HITRAN database
## Usage

```python
slabspec.utils.helpers.extract_hitran_data('CO',4,5,isotopologue_number=1, eupmax=9000., aupmin=10.)
```

## License
[MIT](https://choosealicense.com/licenses/mit/)

