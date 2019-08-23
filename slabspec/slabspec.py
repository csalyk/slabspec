import numpy as np
from astropy.io import fits
from astropy.constants import c,h, k_B, G, M_sun, au, pc, u
import pickle as pickle
from scipy.interpolate import interp1d
from slabspec.utils.helpers import fwhm_to_sigma, sigma_to_fwhm, markgauss, extract_hitran_data, get_molecule_identifier, compute_thermal_velocity
import pdb as pdb
from astropy.table import Table

def spec_convol(wave, flux, dv):
    '''
    Convolve a spectrum, given wavelength in microns and flux density, by a given FWHM in velocity 

    Parameters
    ---------
    wave : numpy array
        wavelength values, in microns
    flux : numpy array
        flux density values, in units of Energy/area/time/Hz
    dv : float
        FWHM of convolution kernel, in km/s

    Returns
    --------
    newflux : numpy array
        Convolved spectrum flux density values, in same units as input

    '''

#Program assumes units of dv are km/s, and dv=FWHM                                                                        

    dv=fwhm_to_sigma(dv)
    n=round(4.*dv/(c.value*1e-3)*np.median(wave)/(wave[1]-wave[0]))
    if (n < 10):
        n=10.

#Pad arrays to deal with edges                                                                                            
    dwave=wave[1]-wave[0]
    wave_low=np.arange(wave[0]-dwave*n, wave[0]-dwave, dwave)
    wave_high=np.arange(np.max(wave)+dwave, np.max(wave)+dwave*(n-1.), dwave)
    nlow=np.size(wave_low)
    nhigh=np.size(wave_high)
    flux_low=np.zeros(nlow)
    flux_high=np.zeros(nhigh)
    mask_low=np.zeros(nlow)
    mask_high=np.zeros(nhigh)
    mask_middle=np.ones(np.size(wave))
    wave=np.concatenate([wave_low, wave, wave_high])
    flux=np.concatenate([flux_low, flux, flux_high])
    mask=np.concatenate([mask_low, mask_middle, mask_high])

    newflux=np.copy(flux)

    if( n > (np.size(wave)-n)):
        print("Your wavelength range is too small for your kernel")
        print("Program will return an empty array")

    for i in np.arange(n, np.size(wave)-n+1):
        lwave=wave[np.int(i-n):np.int(i+n+1)]
        lflux=flux[np.int(i-n):np.int(i+n+1)]
        lvel=(lwave-wave[np.int(i)])/wave[np.int(i)]*c.value*1e-3
        nvel=(np.max(lvel)-np.min(lvel))/(dv*.2) +3
        vel=np.arange(nvel)
        vel=.2*dv*(vel-np.median(vel))
        kernel=markgauss(vel,mean=0,sigma=dv,area=1.)
        f = interp1d(vel,kernel, bounds_error=False)
        wkernel=f(lvel)
        wkernel=wkernel/np.nansum(wkernel)
        newflux[np.int(i)]=np.nansum(lflux*wkernel)/np.nansum(wkernel[np.isfinite(lflux)])
        #Note: denominator is necessary to correctly account for NaN'd regions                                            

#Remove NaN'd regions                                                                                                     
    nanbool=np.invert(np.isfinite(flux))   #Places where flux is not finite                                               
    newflux[nanbool]='NaN'

#Now remove padding                                                                                                       
    newflux=newflux[mask==1]

    return newflux

#------------------------------------------------------------------------------------                                     
def make_spec(molecule_name, n_col, temp, area, wmax=40, wmin=1, res=1e-4, deltav=None, isotopologue_number=1, d_pc=1,
              aupmin=None, convol_fwhm=None, eupmax=None, vup=None):

    '''
    Create an IR spectrum for a slab model with given temperature, area, and column density

    Parameters
    ---------
    molecule_name : string
        String identifier for molecule, for example, 'CO', or 'H2O'             
    n_col : float
        Column density, in m^-2
    temp : float
        Temperature of slab model, in K
    area : float
        Area of slab model, in m^2
    wmin : float, optional
        Minimum wavelength of output spectrum, in microns. Defaults to 1 micron.
    wmax : float, optional
        Maximum wavelength of output spectrum, in microns.  Defaults to 40 microns.
    deltav : float, optional
        FWHM of local velocity distribution, in m/s.  Note this is NOT the global velocity distribution.
        Defaults to thermal speed of molecule given input temperature.
    isotopologue_number : float, optional
        Number representing isotopologue (1=most common, 2=next most common, etc.)
    d_pc : float, optional
        Distance to slab, in units of pc, for computing observed flux density.  Defaults to 1 pc.
    aupmin : float, optional
        Minimum Einstein-A coefficient for transitions
    convol_fwhm : float, optional
        FWHM of convolution kernel, in km/s.
    res : float, optional
        max resolution of spectrum, in microns.  Must be significantly higher than observed spectrum for correct calculation.
        Defaults to 1e-4.
    eupmax : float, optional
        Maximum energy of transitions to consider, in K
    vup : float, optional
        Optional parameter to restrict output to certain upper level vibrational states

    Returns
    --------
    slabdict : dictionary
        Dictionary includes two astropy tables: 
          lineparams : line parameters and fluxes
          spectrum : wavelength, flux, convolflux, tau
        and a dictionary
          modelparams : model parameters: Area, column density, temperature, local velocity, convolution fwhm
    '''

    isot=isotopologue_number
    si2jy=1e26   #SI to Jy flux conversion factor

#If local velocity field is not given, assume sigma given by thermal velocity
    if(deltav is None):
        deltav=compute_thermal_velocity(molecule_name, temp)

#Read HITRAN data
    hitran_data=extract_hitran_data(molecule_name,wmin,wmax,isotopologue_number=isotopologue_number, eupmax=eupmax, aupmin=aupmin)

#Select for desired vup
#Probably want to add error catching here, since this code will only work if Vp is an integer
    if(vup is not None):
        vupbool = [(int(myvp)==1) for myvp in hitran_data['Vp']]
        hitran_data=hitran_data[vupbool]

    wn0=hitran_data['wn']*1e2 # now m-1
    aup=hitran_data['a']
    eup=(hitran_data['elower']+hitran_data['wn'])*1e2 #now m-1                                                             
    gup=hitran_data['gp']

#Compute partition function
    q=compute_partition_function(molecule_name,temp,isot)

#Begin calculations                                                                                                       
    afactor=((aup*gup*n_col)/(q*8.*np.pi*(wn0)**3.)) #mks                                                                 
    efactor=h.value*c.value*eup/(k_B.value*temp)
    wnfactor=h.value*c.value*wn0/(k_B.value*temp)
    phia=1./(deltav*np.sqrt(2.0*np.pi))
    tau0=afactor*np.exp(-1.*efactor)*(np.exp(wnfactor)-1.0)*phia
    w0=1.e6/wn0
    dvel=1.0e0    #km/s                                                                                                   
    nvel=101
    vel=(dvel*(np.arange(0,nvel)-50.0))*1.e3     #now in m/s                                                              
    omega=area/(d_pc*pc.value)**2.
    fthin=aup*gup*n_col*h.value*c.value*wn0/(q*4.*np.pi)*np.exp(-efactor)*omega # Energy/area/time, mks                   

#Now loop over transitions and velocities to calculate flux                                                               
    nlines=np.size(tau0)
    tau=np.zeros([nlines,nvel])
    wave=np.zeros([nlines,nvel])
    for ha,mytau in enumerate(tau0):
        for ka, myvel in enumerate(vel):
            tau[ha,ka]=tau0[ha]*np.exp(-vel[ka]**2./(2.*deltav**2.))
            wave[ha,ka]=1.e6/wn0[ha]*(1+vel[ka]/c.value)

#Now interpolate over wavelength space so that all lines can be added together                                            
    w_arr=wave            #nlines x nvel                                                                                  
    f_arr=w_arr-w_arr     #nlines x nvel                                                                                  
    nbins=(wmax-wmin)/res
    totalwave=np.arange(nbins)*(wmax-wmin)/nbins+wmin
    totaltau=np.zeros(np.size(totalwave))
    lineflux=np.zeros(nlines)
    for i in range(nlines):
        w=np.where((totalwave > np.min(wave[i,:])) & (totalwave < np.max(wave[i,:])))
        if(np.size(w) > 0):
            f = interp1d(wave[i,:], tau[i,:],bounds_error=False)
            newtau=f(totalwave[w])
            totaltau[w]+=newtau
            f_arr[i,:]=2*h.value*c.value*wn0[i]**3./(np.exp(wnfactor[i])-1.0e0)*(1-np.exp(-tau[i,:]))*si2jy*omega
            lineflux_jykms=np.sum(f_arr[i,:])*dvel
            lineflux[i]=lineflux_jykms*1e-23*1.*1e5*(1./(w0[i]*1e-4))

    wave_arr=wave
    wn=1.e6/totalwave                                         #m^{-1}                                                     
    wnfactor=h.value*c.value*wn/(k_B.value*temp)
    flux=2*h.value*c.value*wn**3./(np.exp(wnfactor)-1.0e0)*(1-np.exp(-totaltau))*si2jy*omega

    wave=totalwave

#Make this its own function
#    yrot=np.log(lineflux/(hitran_data.linecenter*gup*aup))  #y values for rotation diagrams                               

    #convol should be set to FWHM of convolution kernel, in km/s                                                          
    convolflux=np.copy(flux)
    if(convol_fwhm is not None):
        convolflux=spec_convol(wave,flux,convol_fwhm)

    slabdict={}

#Line params
    slabdict['lineparams']=hitran_data
#lineflux, flux_arr, wave_arr, vel?, tau0, fthin

#Spectrum
    spectrum_table = Table([wave, flux, convolflux, totaltau], names=('wave', 'flux', 'convolflux','totaltau'),  dtype=('f8', 'f8', 'f8','f8'))
    spectrum_table['wave'].unit = 'micron'
    spectrum_table['flux'].unit = 'Jy'
    spectrum_table['convolflux'].unit = 'Jy'
    slabdict['spectrum']=spectrum_table

#Model params
    modelparams_table={'area':area,'temp':temp,'n_col':n_col, 'res':res, 'deltav':deltav, 'convol_fwhm':convol_fwhm, 'd_pc':d_pc,
                       'isotopologue_number':isot,'molecule_name':molecule_name}
    slabdict['modelparams']=modelparams_table

    return slabdict


def compute_partition_function(molecule_name,temp,isotopologue_number=1):
    '''                                                                                                                                       
    For a given input molecule name, isotope number, and temperature, return the partition function Q
                                                                                                                                              
    Parameters                                                                                                                                
    ----------                                                                                                                                
    molecule_name : string
        The molecule name string (e.g., 'CO', 'H2O')
    temp : float
        The temperature at which to compute the partition function
    isotopologue_number : float, optional
        Isotopologue number, with 1 being most common, etc. Defaults to 1.

    Returns                                                                                                                                   
    -------                                                                                                                                   
    q : float
      The partition function
    '''

    mol_code=get_molecule_identifier(molecule_name)
    mol_isot_code=str(mol_code)+str(isotopologue_number)
    print(mol_isot_code)

    switcher = {
              '11': qh2o(temp),                                                          #H2O
              '12': 175.11*(temp/296.)**1.5,
              '21': -3.5179e+02 + 2.7793*temp -3.6737e-03*(temp**2.)+4.0901e-06*(temp**3.),  #CO2      
              '51': 0.36288*temp*(1.+np.exp(-3083.7/temp)),                             #CO
              '52': 6.212e-1+temp*7.5758e-1-(temp**2.)*5.9194e-6+(temp**3.)*1.5232e-08,
              '261': 9.4384+temp*3.6148e-01+(temp**2.)*3.3278e-03-(temp**3.)*6.1666e-07, #C2H2 - not correct?!
              '231': 9.4384+temp*3.6148e-01+(temp**2.)*3.3278e-03-(temp**3.)*6.1666e-07, #HCN - not correct?!
              '131': qoh(temp),
              '61': 100.,  #CH4 - not correct - placeholder!!
              '111': 100.  #NH3 - not correct - placeholder!!
               }


    q=switcher.get(mol_isot_code,"This molecule/isotopologue combination not covered yet.")

    return q


def qh2o(temp):
    qrot=-4.9589+2.8147e-1*temp+1.2848e-3*temp**2.-5.8343e-7*temp**3.
    qvib=9.9842e-1+2.9713e-5*temp-1.7345e-7*(temp)**2.+3.2366e-10*(temp)**3.
    if(temp > 1000):
        qrot=-210. + 1.1911*temp #just a linear fit to qrot at high T to extend it to higher T                                        
    q=qvib*qrot     
    return q

def qoh(temp):
    qrot=7.7363+1.7152e-1*temp+3.4886e-4*temp**2.-3.3504e-7*temp**3.
    qvib=9.9999e-1+2.0075e-7*temp-9.3665e-10*temp**2.+1.3295e-12*temp**3.
    if(temp > 500):
        qrot=temp*.28129676-2.3   #extrapolated from 100-450 K trend                                                                  
    q=qvib*qrot
    return q
