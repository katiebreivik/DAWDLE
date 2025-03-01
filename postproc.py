import utils as dutil

import numpy as np
import pandas as pd
import astropy.units as u
from astropy.time import Time
import astropy.constants as const
import astropy.coordinates as coords
from astropy.coordinates import SkyCoord
from scipy.interpolate import interp1d, UnivariateSpline
from scipy.optimize import curve_fit
import tqdm
from schwimmbad import MultiPool


from legwork import psd, strain, utils
import legwork.source as source

pd.options.mode.chained_assignment = None


# Specific to Thiele et al. (2021), here are the used metallicity
# array, the associated binary fractions for each Z value, and the ratios 
# of mass in singles to mass in binaries of the Lband with each specific 
# binary fraction as found using COSMIC's independent samplers
# (See Binary_Fraction_Modeling.ipynb for Tutorials). All values were
# rounded to 4 significant digits except metallicity which used 8:

met_arr = np.logspace(np.log10(1e-4), np.log10(0.03), 15)
met_arr = np.round(met_arr, 8)
met_arr = np.append(0.0, met_arr)

binfracs = np.array([0.4847, 0.4732, 0.4618, 0.4503, 0.4388, 
                     0.4274, 0.4159, 0.4044, 0.3776, 0.3426, 
                     0.3076, 0.2726, 0.2376, 0.2027, 0.1677])

ratios = np.array([0.68, 0.71, 0.74, 0.78, 0.82, 
                   0.86, 0.9, 0.94, 1.05, 1.22, 
                   1.44, 1.7 , 2.05, 2.51, 3.17])

ratio_05 = 0.64

# LEGWORK uses astropy units so we do also for consistency
G = const.G.value
c = const.c.value  # speed of light in m s^-1
M_sol = const.M_sun.value  # sun's mass in kg
R_sol = const.R_sun.value  # sun's radius in metres
sec_Myr = u.Myr.to('s')  # seconds in a million years
m_kpc = u.kpc.to('m')  # metres in a kiloparsec
Z_sun = 0.02  # solar metallicity
sun = coords.get_sun(Time("2021-04-23T00:00:00", scale='utc'))
sun_g = sun.transform_to(coords.Galactocentric)
sun_yGx = sun_g.galcen_distance.to('kpc').value
sun_zGx = sun_g.z.to('kpc').value
M_astro = 7070  # FIRE star particle mass in solar masses



#===================================================================================
# Lband and Evolution Functions:
#===================================================================================

def beta_(pop):
    '''
    Beta constant from page 8 of Peters(1964) used in the evolution 
    of DWDs due to gravitational waves.
    
    Parameters
    ----------
    pop : `pandas dataframe`
        DF of population which includes component masses in solar
        masses
    Returns
    -------
    beta : `array`
        array of beta values
    '''
    m1 = pop.mass_1 * M_sol
    m2 = pop.mass_2 * M_sol
    beta = 64 / 5 * G ** 3 * m1 * m2 * (m1 + m2) / c ** 5
    return beta


def a_of_t(pop, t):
    '''
    Uses Peters(1964) equation (5.9) for circular binaries to find separation.
    as a function of time.

    Input: the population dataframe from COSMIC. Time t must be in Myr.

    Returns: array of separation at time t in solar radii.
    '''
    t = t * sec_Myr
    beta = beta_(pop)
    a_i = pop.sep * R_sol
    a = (a_i ** 4 - 4 * beta * t) ** (1/4)
    return a / R_sol


def porb_of_a(pop, a):
    '''
    Converts semi-major axis "a" to orbital period using Kepler's equations.

    Input the population dataframe from COSMIC. "a" must be in solar radii and
    an array of the same length as the dateframe pop.

    Returns orbital period in days.
    '''
    a = a * R_sol
    m1 = pop.mass_1 * M_sol
    m2 = pop.mass_2 * M_sol
    P_sqrd = 4 * np.pi ** 2 * a ** 3 / G / (m1 + m2)
    P = np.sqrt(P_sqrd)
    P = P / 3600 / 24  # converts from seconds to days
    return P


def t_of_a(pop, a):
    '''
    Finds time from SRF at which a binary would have a given separation after
    evolving due to gw radiation. (Re-arrangement of a_of_t(pop, t)).

    "a" must be in solar radii.

    Returns time in Myr.
    '''
    beta = beta_(pop)
    a_i = pop.sep * R_sol
    a = a * R_sol
    t = (a_i ** 4 - a ** 4) / 4 / beta
    t = t / sec_Myr
    return t


def t_merge(pop):
    '''
    Uses Peters(1964) equation (5.10) to determine the merger time of a circular
    DWD binary from time of SRF.

    Returns time in Myr.
    '''
    a_0 = pop.sep * R_sol
    beta = beta_(pop)
    T = a_0 ** 4 / 4 / beta
    T / sec_Myr
    return T


def a_of_RLOF(set):
    '''
    Finds separation when secondary overflows its
    Roche Lobe. Returns "a" in solar radii.
    
    Taken from Eq. 23 in "Binary evolution in a nutshell" 
    by Marc van der Sluys, which is an approximation of a fit
    done of Roche-lobe radius by Eggleton (1983).
    '''
    m1 = set.mass_1
    m2 = set.mass_2
    R2 = set.rad_2
    q = m2 / m1
    num = 0.49 * q ** (2/3)
    denom = 0.6 * q ** (2/3) + np.log(1 + q ** (1/3))
    a = denom * R2 / num
    return a


def random_sphere(R, num):
    '''
    Generates "num" number of random points within a
    sphere of radius R. It picks random x, y, z values
    within a cube and discards it if it's outside the
    sphere.

    Inputs: Radius in kpc, num is an integer

    Outputs: X, Y, Z arrays of length num
    '''
    X = []
    Y = []
    Z = []
    while len(X) < num:
        x = np.random.uniform(-R, R)
        y = np.random.uniform(-R, R)
        z = np.random.uniform(-R, R)
        r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        if r > R:
            continue
        if r <= R:
            X.append(x)
            Y.append(y)
            Z.append(z)
    X = np.array(X)
    Y = np.array(Y)
    Z = np.array(Z)
    return X, Y, Z


def rad_WD(M):
    '''
    Calculates the radius of a WD as a function of mass M in solar masses.
    Taken from Eq. 91 in Hurley et al. (2000), from Eq. 17 in Tout et al. (1997)
    
    Input an array M of mass in solar masses
    
    Outputs the radius of the WD in solar radii
    '''
    M_ch = 1.44
    R_NS = 1.4e-5*np.ones(len(M))
    A = 0.0115 * np.sqrt((M_ch/M)**(2/3) - (M/M_ch)**(2/3))
    rad = np.max(np.array([R_NS, A]), axis=0)
    return rad 

def evolve(pop_init):
    '''
    Evolve an initial population of binary WD's using
    GW radiation.
    '''
    t_evol = pop_init.age * 1000 - pop_init.tphys
    sep_f = a_of_t(pop_init, t_evol)
    porb_f = porb_of_a(pop_init, sep_f)
    f_gw = 2 / (porb_f * 24 * 3600)
    pop_init['t_evol'] = t_evol
    pop_init['sep_f'] = sep_f
    pop_init['porb_f'] = porb_f
    pop_init['f_gw'] = f_gw
    return pop_init


def position(pop_init):
    '''
    Assigning random microchanges to positions to
    give each system a unique position for identical
    FIRE star particles
    '''
    R_list = pop_init.kern_len.values
    xGx = pop_init.xGx.values.copy()
    yGx = pop_init.yGx.values.copy()
    zGx = pop_init.zGx.values.copy()
    x, y, z = random_sphere(1.0, len(R_list))
    X = xGx + (x * R_list)
    Y = yGx + (y * R_list)
    Z = zGx + (z * R_list)
    pop_init['X'] = X
    pop_init['Y'] = Y
    pop_init['Z'] = Z
    pop_init['dist_sun'] = (X ** 2 + (Y - sun_yGx) ** 2 + (Z - sun_zGx) ** 2) ** (1/2)   
    return pop_init
  
    
def merging_pop(pop_init):
    t_m = t_merge(pop_init)
    pop_init['t_delay'] = t_m + pop_init.tphys.values
    pop_merge = pop_init.loc[pop_init.t_delay <= pop_init.age * 1000]
    pop_init = pop_init.loc[pop_init.t_delay >= pop_init.age * 1000]
    return pop_init, pop_merge


def RLOF_pop(pop_init):
    a_RLOF = a_of_RLOF(pop_init)
    t_RLOF = t_of_a(pop_init, a_RLOF)
    pop_init['t_RLOF'] = t_RLOF
    pop_RLOF = pop_init.loc[t_RLOF + pop_init.tphys <= pop_init.age * 1000]
    pop_init = pop_init.loc[t_RLOF + pop_init.tphys >= pop_init.age * 1000]
    return pop_init, pop_RLOF


def filter_population(dat):
    pop_init, i, label, ratio, binfrac, pathtosave, interfile = dat
    
    pop_init[['bin_num', 'FIRE_index']] = pop_init[['bin_num', 'FIRE_index']].astype('int64')
    if interfile == True:
        pop_init[['bin_num', 'FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label,
                                                                                     met_arr[i+1],
                                                                                     binfrac),
                                                   key='pop_init', format='t', append=True)    
    # Now that we've obtained an initial population, we make data cuts
    # of systems who wouldn't form in time for their FIRE age, or would
    # merge or overflow their Roche Lobe before present day.
    pop_init = pop_init.loc[pop_init.tphys <= pop_init.age * 1000]
    if interfile == True:
        pop_init[['bin_num', 'FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label, 
                                                                                     met_arr[i+1], 
                                                                                     binfrac), 
                                                    key='pop_age', format='t', append=True)
    
    pop_init, pop_merge = merging_pop(pop_init)
    if interfile == True:
        pop_merge[['bin_num', 'FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label,
                                                                                      met_arr[i+1], 
                                                                                      binfrac), 
                                                    key='pop_merge', format='t', append=True)    
    
        pop_init[['bin_num', 'FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label, 
                                                                                     met_arr[i+1], 
                                                                                     binfrac), 
                                key='pop_nm', format='t', append=True)
    
    pop_merge = pd.DataFrame()
    pop_init, pop_RLOF = RLOF_pop(pop_init)
    
    if interfile == True:
        pop_RLOF[['bin_num','FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label,
                                                                                           met_arr[i+1], 
                                                                                           binfrac), 
                                                  key='pop_RLOF', format='t', append=True)
    
        pop_init[['bin_num', 'FIRE_index']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label, 
                                                                                            met_arr[i+1], 
                                                                                            binfrac), 
                                key='pop_nRLOF', format='t', append=True)
    pop_RLOF = pd.DataFrame()
    
    # We now have a final population which we can evolve
    # using GW radiation
    pop_init = evolve(pop_init)
    
    # Assigning random microchanges to positions to
    # give each system a unique position for identical
    # FIRE star particles
    pop_init = position(pop_init)
    
    if interfile == True:
        pop_init[['bin_num', 'FIRE_index', 'X', 'Y', 'Z']].to_hdf(pathtosave + 'Lband_{}_{}_{}_inter.hdf'.format(label, 
                                                                                                    met_arr[i+1], 
                                                                                                    binfrac), 
                                                                  key='pop_f', format='t', append=True)    
    if binfrac == 0.5:
        binfrac_write = 0.5
    else:
        binfrac_write = 'variable'
    
    # Assigning weights to population to be used for histograms.
    # This creates an extra columns which states how many times
    # a given system was sampled from the cosmic-pop conv df.
    pop_init = pop_init.join(pop_init.groupby('bin_num')['bin_num'].size(), 
                             on='bin_num', rsuffix='_pw')
    
    # Systems detectable by LISA will be in the frequency band
    # between f_gw's 0.01mHz and 1Hz.
    LISA_band = pop_init.loc[(pop_init.f_gw >= 1e-4)]
    if len(LISA_band) == 0:
        print('No LISA sources for source {} and met {} and binfrac {}'.format(label, met_arr[i+1], binfrac))
        return []
    else:
        pop_init = pd.DataFrame()
        LISA_band = LISA_band.join(LISA_band.groupby('bin_num')['bin_num'].size(), 
                                   on='bin_num', rsuffix='_Lw')
        #if verbose:
        #    print('got LISA band and added weight column')

        # Output to hdf files
        #savefile = 'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], binfrac)
        #LISA_band.to_hdf(pathtosave + savefile, key='Lband', format='t', append=True)
        return LISA_band
    
#def sample_and_filter(dat):
#    params_list = ['bin_num', 'mass_1', 'mass_2', 'kstar_1', 'kstar_2', 'porb', 'sep', 
#            'met', 'age', 'tphys', 'rad_1', 'rad_2', 'kern_len', 'xGx', 'yGx', 'zGx', 
#                   'FIRE_index']#, 'CEsep', 'CEtime', 'RLOFsep', 'RLOFtime']
#    
#    conv, i, label, ratio, binfrac, pathtosave, interfile, N_sample_int = dat
#    sample_int = pd.DataFrame.sample(conv, N_sample_int, replace=True)
#    pop_init_int = pd.concat([sample_int.reset_index(), 
#                              FIRE_repeat.reset_index()], axis=1)
#    N = len(sample_int)
#    sample_int = pd.DataFrame()
#    FIRE_repeat = pd.DataFrame()
#    dat = [pop_init_int[params_list], i, label, ratio, binfrac, pathtosave, interfile]
#    filter_population()
    
def make_galaxy(dat, verbose=False):
    pathtodat, fire_path, pathtosave, filename, i, label, ratio, binfrac, interfile, nproc = dat
    FIRE = pd.read_hdf(fire_path+'FIRE.h5').sort_values('met')

    rand_seed = np.random.randint(0, 100, 1)
    np.random.seed(rand_seed)
    
    rand_seed = pd.DataFrame(rand_seed)
    rand_seed.to_hdf(pathtosave+'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], binfrac), 
                     key='rand_seed')

    # Choose metallicity bin
    met_start = met_arr[i] / Z_sun
    met_end = met_arr[i+1] / Z_sun
    
    # Calculating the formation time of each component:
    conv = pd.read_hdf(pathtodat+filename, key='conv')
    
    # Re-writing the radii of each component since the conv df 
    # doesn't log the WD radius properly
    conv['rad_1'] = rad_WD(conv.mass_1.values)
    conv['rad_2'] = rad_WD(conv.mass_2.values)    
    
    # Use ratio to scale to astrophysical pop w/ specific binary frac.
    try:
        mass_binaries = pd.read_hdf(pathtodat+filename, key='mass_stars').iloc[-1]
    except:
        print('m_binaries key')
        mass_binaries = pd.read_hdf(pathtodat+filename, key='mass_binaries').iloc[-1]
    mass_total = (1 + ratio) * mass_binaries
    
    mass_total.to_hdf(pathtosave+'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], 
                                                  binfrac), key='mass_total')
    DWD_per_mass = len(conv) / mass_total
    N_astro = DWD_per_mass * M_astro  # num of binaries per star particle
    
    # Choose FIRE bin based on metallicity
    FIRE['FIRE_index'] = FIRE.index
    if met_end * Z_sun == met_arr[-1]:
        FIRE_bin = FIRE.loc[FIRE.met >= met_start]
    else:
        FIRE_bin = FIRE.loc[(FIRE.met >= met_start)&(FIRE.met <= met_end)]
    FIRE = []
    
    # We sample by the integer number of systems per star particle,
    # as well as a probabilistic approach for the fractional component
    # of N_astro:
    N_astro_dec = N_astro % 1
    p_DWD = np.random.rand(len(FIRE_bin))
    N_sample_dec = np.zeros(len(FIRE_bin))
    N_sample_dec[p_DWD <= N_astro_dec.values] = 1.0
    num_sample_dec = int(N_sample_dec.sum())
    if verbose:
        print('we will sample {} stars from the decimal portion'.format(num_sample_dec))
    sample_dec = pd.DataFrame.sample(conv, num_sample_dec, replace=True)
    FIRE_bin2 = FIRE_bin.loc[N_sample_dec == 1.0]
    
    params_list = ['bin_num', 'mass_1', 'mass_2', 'kstar_1', 'kstar_2', 'porb', 'sep', 
            'met', 'age', 'tphys', 'rad_1', 'rad_2', 'kern_len', 'xGx', 'yGx', 'zGx', 
                   'FIRE_index']#, 'CEsep', 'CEtime', 'RLOFsep', 'RLOFtime']
    
    pop_init = pd.concat([sample_dec.reset_index(), FIRE_bin2.reset_index()], axis=1)
    sample_dec = pd.DataFrame()
    FIRE_bin2 = pd.DataFrame()
    dat = [pop_init[params_list], i, label, ratio, binfrac, pathtosave, interfile]
    LISA_band = filter_population(dat)

    if len(LISA_band) > 0:
        savefile = 'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], binfrac)
        LISA_band.to_hdf(pathtosave + savefile, key='Lband', format='t', append=True)
    
    N_sample_int = int(N_astro) * len(FIRE_bin)
    if verbose:
        print('we will sample {} stars from the integer portion'.format(N_sample_int))

    if verbose:
        print('getting FIRE bin')
    FIRE_repeat = pd.DataFrame(np.repeat(FIRE_bin.values, int(N_astro), axis=0))
    FIRE_repeat.columns = FIRE_bin.columns
    FIRE_bin = pd.DataFrame()
    
    Nsamp_split = 5e6
    if N_sample_int < Nsamp_split:
        sample_int = pd.DataFrame.sample(conv, N_sample_int, replace=True)
        pop_init_int = pd.concat([sample_int.reset_index(), 
                                  FIRE_repeat.reset_index()], axis=1)
        N = len(sample_int)
        sample_int = pd.DataFrame()
        FIRE_repeat = pd.DataFrame()
        dat = [pop_init_int[params_list], i, label, ratio, binfrac, pathtosave, interfile]
        LISA_band = filter_population(dat)
        
        if len(LISA_band) > 0:
            savefile = 'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], binfrac)
            LISA_band.to_hdf(pathtosave + savefile, key='Lband', format='t', append=True)
    

    elif N_sample_int > Nsamp_split:
        if verbose:
            print('looping the integer population')
        N = 0
        j = 0
        jlast = int(Nsamp_split)
        dat_filter = []
        while j < N_sample_int:
            if verbose:
                print('j: ', j)
                print('jlast: ', jlast)
                print('sampling {} systems'.format(int(jlast - j)))
            sample_int = pd.DataFrame.sample(conv, int(jlast-j), replace=True)
            N += len(sample_int)
            pop_init_int = pd.concat([sample_int.reset_index(), 
                                      FIRE_repeat.iloc[j:jlast].reset_index()], axis=1)
            dat_filter.append([pop_init_int[params_list], i, label, ratio, binfrac, pathtosave, interfile])
            j += Nsamp_split
            j = int(j)
            jlast += Nsamp_split
            jlast = int(jlast)
            if jlast > N_sample_int:
                jlast = N_sample_int
        with MultiPool(processes=nproc) as pool:
            LISA_band_list = list(pool.map(filter_population, dat_filter))
        
        for LISA_band in LISA_band_list:
            savefile = 'Lband_{}_{}_{}.hdf'.format(label, met_arr[i+1], binfrac)
            LISA_band.to_hdf(pathtosave + savefile, key='Lband', format='t', append=True)
    
       
    if N != N_sample_int:
        print('loop is incorrect')

    FIRE_repeat = pd.DataFrame()
    sample_int = pd.DataFrame()
    
    return


def save_full_galaxy(DWD_list, pathtodat, fire_path, pathtoLband, interfile, nproc):
    # Generate array of metallicities:
    
    met_arr = np.logspace(np.log10(1e-4), np.log10(0.03), 15)
    met_arr = np.round(met_arr, 8)
    met_arr = np.append(0.0, met_arr)
    
    # Corresponding binaryy fractions and single-to-binaries mass ratios:
    # (These can be generated by get_binfrac_of_Z(Z) and get_ratios(binfracs)
    # functions)
    binfracs = np.array([0.4847, 0.4732, 0.4618, 0.4503, 0.4388, 
                         0.4274, 0.4159, 0.4044, 0.3776, 0.3426, 
                         0.3076, 0.2726, 0.2376, 0.2027, 0.1677])
    
    ratios = np.array([0.68, 0.71, 0.74, 0.78, 0.82, 
                       0.86, 0.9, 0.94, 1.05, 1.22, 
                       1.44, 1.7, 2.05, 2.51, 3.17])
    
    ratio_05 = 0.64

    
    # Run Code:
    # Run through all metallicities for metallicity-dependent
    # binary fraction and binary fraction of 0.5
    
    dat = []
    
    for DWD in DWD_list:
        if DWD == 'He_He':
            kstar1 = '10'
            kstar2 = '10'    
        elif DWD == 'CO_He':
            kstar1 = '11'
            kstar2 = '10'
        elif DWD == 'CO_CO':
            kstar1 = '11'
            kstar2 = '11'
        elif DWD == 'ONe_X':
            kstar1 = '12'
            kstar2 = '10_12'
            
        fnames, label = dutil.getfiles(kstar1=kstar1, kstar2=kstar2)
        i = 0
        for f, ratio, binfrac in zip(fnames, ratios, binfracs):
            dat.append([pathtodat, fire_path, pathtoLband, f, i, label, ratio, binfrac, interfile, nproc])
            i += 1
        i = 0
        for f, ratio, binfrac in zip(fnames, ratios, binfracs):
            dat.append([pathtodat, fire_path, pathtoLband, f, i, label, ratio_05, 0.5, interfile, nproc])
            i += 1
    for d in dat:
        make_galaxy(d)
          
    return


def get_formeff(pathtodat, pathtoLband, pathtosave, getfrom='Lband'):
    def formeff(datfiles, Lbandfiles, pathtodat, pathtoLband, label, model, getfrom):
        lenconv = []
        masslist = []
        for i in range(15):
            if model == 'F50':
                binfrac = 0.5
                ratio = ratio_05
            elif model == 'FZ':
                binfrac = binfracs[i]
                ratio = ratios[i]
            if getfrom == 'Lband':
                mass = pd.read_hdf(pathtoLband + Lbandfiles[i], key='mass_total')
                conv = pd.read_hdf(pathtodat + datfiles[i], key='conv')
            elif getfrom == 'dat':
                try:
                    mass_binaries = pd.read_hdf(pathtodat + datfiles[i], key='mass_stars').iloc[-1]
                except:
                    print('m_binaries key')
                    mass_binaries = pd.read_hdf(pathtodat + datfiles[i], key='mass_binaries').iloc[-1]
                mass = (1 + ratio) * mass_binaries
                conv = pd.read_hdf(pathtodat + datfiles[i], key='conv')
                            
            masslist.append(mass)
            lenconv.append(len(conv))

        lenconv = np.array(lenconv)
        masslist = np.concatenate(np.array(masslist))
        eff = lenconv / masslist
        return eff

    kstar1_list = ['10', '11', '11', '12']
    kstar2_list = ['10', '10', '11', '10_12']
    labels = ['10_10', '11_10', '11_11', '12']
    
    eff_var = []
    eff_05 = []
    for kstar1, kstar2, label in tqdm.tqdm(zip(kstar1_list, kstar2_list, labels)):
        files, lab = dutil.getfiles(kstar1=kstar1, kstar2=kstar2)
        Lbandfiles = dutil.Lband_files(kstar1='10', kstar2='10', var=True)
        eff_var.append(formeff(files, Lbandfiles, pathtodat, pathtoLband, label, 'FZ', getfrom))
        Lbandfiles = dutil.Lband_files(kstar1='10', kstar2='10', var=False)
        eff_05.append(formeff(files, Lbandfiles, pathtodat, pathtoLband, label, 'F50', getfrom))
        print('finished {}'.format(label))

    DWDeff = pd.DataFrame(np.array(eff_var).T, columns=['He', 'COHe', 'CO', 'ONe'])
    DWDeff.to_hdf(pathtosave + 'DWDeff_FZ.hdf', key='data')

    DWDeff05 = pd.DataFrame(np.array(eff_05).T, columns=['He', 'COHe', 'CO', 'ONe'])
    DWDeff05.to_hdf(pathtosave + 'DWDeff_F50.hdf', key='data')
    
    return


def get_interactionsep(pathtodat, pathtoLband, pathtosave, verbose=False):
    def intersep(pathtodat, datfile, pathtoLband, fsave, i, label, binfrac, verbose=verbose):
        data = pd.DataFrame() 
        columns=['bin_num', 'FIRE_index', 'met', 'rad_1', 'rad_2', 'CEsep', 'CEtime', 'RLOFsep', 'RLOFtime'] 
        data.to_hdf(fsave, key='data', format='t', append=True) 

        if verbose:
            print('\n{}'.format(i))

        Z = met_arr[i+1] 

        if verbose:
            print('Z: ', Z) 
            print('binfrac: ', binfrac) 

        Lbandfile = pathtoLband + 'Lband_{}_{}_{}.hdf'.format(label, Z, binfrac)
        if verbose:
            print('Lbandfile: ' + Lbandfile)
        try:
            Lband = pd.read_hdf(Lbandfile, key='Lband').sort_values('bin_num') 
            data = Lband[['bin_num', 'FIRE_index', 'met', 'rad_1', 'rad_2']] 
    
            if verbose:
                print('dat file: ' + datfile)
            dat = pd.read_hdf(pathtodat+datfile, key='bpp') 
            dat = dat[['tphys', 'evol_type', 'sep', 'bin_num']]
    
            RLOFsep = dat.loc[dat.evol_type==3].groupby('bin_num', as_index=False).first()
            RLOFsep = RLOFsep.loc[RLOFsep.bin_num.isin(data.bin_num)]
            data_RLOF = data.loc[data.bin_num.isin(RLOFsep.bin_num)]
            RLOFsep['weights'] = data_RLOF.bin_num.value_counts().sort_index().values
            
            CEsep = dat.loc[dat.evol_type==7].groupby('bin_num', as_index=False).first()
            CEsep = CEsep.loc[CEsep.bin_num.isin(data.bin_num)]
            data_CE = data.loc[data.bin_num.isin(CEsep.bin_num)]
            CEsep['weights'] = data_CE.bin_num.value_counts().sort_index().values
    
            dat = []
            data_RLOF = []
            data_CE = []
    
            data['CEsep'] = np.repeat(CEsep['sep'], CEsep['weights']).values
            data['CEtime'] = np.repeat(CEsep['tphys'], CEsep['weights']).values
            data['RLOFsep'] = np.repeat(RLOFsep['sep'], RLOFsep['weights']).values
            data['RLOFtime'] = np.repeat(RLOFsep['tphys'], RLOFsep['weights']).values
    
            Ntot = len(data) 
            
            if verbose:
                print('Ntot: ', Ntot) 
            N = 0 
            j = 0 
            jlast = int(1e5) 
            while j < Ntot: 
                if verbose:
                    print('j: ', j) 
                    print('jlast: ', jlast) 
                data[j:jlast].to_hdf(fsave, key='data', format='t', append=True) 
                N += len(data[j:jlast]) 
                j += 1e5 
                j = int(j) 
                jlast += 1e5 
                if jlast > Ntot: 
                    jlast = Ntot 
                jlast = int(jlast) 
            if verbose:
                if N != Ntot: 
                    print('loop is wrong') 
                else: 
                    print('wrote to hdf successfully') 
    
            return
        except:
            return


    # FZ:
    kstar1_list = ['10', '11', '11', '12']
    kstar2_list = ['10', '10', '11', '10_12']
    for kstar1, kstar2 in zip(kstar1_list, kstar2_list):
        files, label = dutil.getfiles(kstar1, kstar2)
        for f, i in tqdm.tqdm(zip(files, range(len(files))), total=len(files)):
            if verbose:
                print('i = {}'.format(i))
            binfrac = binfracs[i]
            met = met_arr[i+1]
            fsave = pathtosave+'{}_intersep_FZ.hdf'.format(label)
            intersep(pathtodat, f, pathtoLband, fsave, i, label, binfrac, verbose)
            
            if verbose:
                print('i = {}'.format(i))
            binfrac = 0.5
            met = met_arr[i+1]
            fsave = pathtosave+'{}_intersep_F50.hdf'.format(label)
            intersep(pathtodat, f, pathtoLband, fsave, i, label, binfrac, verbose)
        
    return


def get_numLISA(pathtoLband, pathtosave, Lbandfile, FIREmin=0.00015, FIREmax=13.346, Z_sun=0.02):
    num = 30
    met_bins = np.logspace(np.log10(FIREmin), np.log10(FIREmax), num)*Z_sun
    
    for var, model in zip([False, True], ['F50', 'FZ']):
        
        He = pd.DataFrame()
        for f in dutil.Lband_files(kstar1='10', kstar2='10', var=var):
            try:
                He = He.append(pd.read_hdf(pathtoLband + f, key='Lband')[['met']])
            except:
                print('no LISA sources for {}'.format(f))
                continue
        print('finished He + He')
        if len(He) > 0:
            Henums, bins = np.histogram(He.met*Z_sun, bins=met_bins)
        else:
            Henums = np.zeros(len(met_bins)-1)
        He = []
        
        COHe = pd.DataFrame()
        for f in dutil.Lband_files(kstar1='11', kstar2='10', var=var):
            try:
                COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband')[['met']])
            except:
                print('no LISA sources for {}'.format(f))
        print('finished CO + He')
        if len(COHe) > 0:
            COHenums, bins = np.histogram(COHe.met*Z_sun, bins=met_bins)
        else:
            COHenums = np.zeros(len(met_bins)-1)
        COHe = []
        
        
        CO = pd.DataFrame()
        for f in dutil.Lband_files(kstar1='11', kstar2='11', var=var):
            try:
                CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband')[['met']])
            except:
                print('no LISA sources for {}'.format(f))
        print('finished CO + CO')
        if len(CO) > 0:
            COnums, bins = np.histogram(CO.met*Z_sun, bins=met_bins)
        else:
            COnums = np.zeros(len(met_bins)-1)
        CO = []
        
        
        ONe = pd.DataFrame()
        for f in dutil.Lband_files(kstar1='12', kstar2='10', var=var):
            try:
                ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband')[['met']])
            except:
                print('no LISA sources for {}'.format(f))
        print('finished ONe + X')
        if len(ONe) > 0:
            ONenums, bins = np.histogram(ONe.met*Z_sun, bins=met_bins)
        else:
            ONenums = np.zeros(len(met_bins)-1)
        ONe = []
    
        numLISA_30bins = pd.DataFrame(np.array([Henums, COHenums, COnums, ONenums]).T, 
                                         columns=['He', 'COHe', 'CO', 'ONe'])
    
        numLISA_30bins.to_hdf(pathtosave+'numLISA_30bins_{}.hdf'.format(model), key='data')
    
    return


def get_resolvedDWDs(pathtoLband, pathtosave, var, window=1000):
    
    def func(x, a, b, c, d, e):
        return a + b*x + c*x**2 + d*x**3 + e*x**4
    
    def cosmic_confusion(f, L, t_obs=4 * u.yr, approximate_R=True, include_confusion_noise=False):
        lisa_psd_no_conf = psd.power_spectral_density(f, include_confusion_noise=False, t_obs=4 * u.yr)
        conf = 10**func(x=np.log10(f.value), 
                        a=popt[0], b=popt[1], 
                        c=popt[2], d=popt[3], e=popt[4]) * t_obs.to(u.s)
    
        psd_plus_conf = conf + lisa_psd_no_conf
        return psd_plus_conf.to(u.Hz**(-1))

    kstar1_list = ['10', '11', '11', '12']
    kstar2_list = ['10', '10', '11', '10_12']
    lisa_bins = np.arange(1e-9, 1e-1, 1/(4 * 3.155e7))
    Tobs = 4 * u.yr
    
    # load the data
    dat = pd.DataFrame()
    for kstar1, kstar2 in zip(kstar1_list, kstar2_list):
        for f in dutil.Lband_files(kstar1=kstar1, kstar2=kstar2, var=var):
            try:
                dat = dat.append(pd.read_hdf(pathtoLband + f, key='Lband'))
            except:
                continue            
            
    sources = source.Source(m_1=dat.mass_1.values * u.Msun, 
                            m_2=dat.mass_2.values * u.Msun,  
                            ecc=np.zeros(len(dat.mass_1)), 
                            dist=dat.dist_sun.values * u.kpc, 
                            f_orb=dat.f_gw.values/2 * u.Hz,
                            
                            interpolate_g=True, 
                            interpolate_sc=True, 
                            sc_params={"instrument": "LISA",
                                       "t_obs": Tobs,
                                       "L": 2.5e9,
                                       "approximate_R": True,
                                       "include_confusion_noise": False})
    
    strains = sources.get_h_0_n(harmonics=[2])
    dat['h_0'] = strains
    dat['power'] = strains**2
    dat['digits'] = np.digitize(dat.f_gw, lisa_bins)
            
    power = dat.groupby('digits').power.sum()
    power_foreground = np.zeros(len(lisa_bins))
    power_foreground[np.array(power.index.astype(int))] = power
    
    power_dat = pd.DataFrame(np.vstack([lisa_bins, power_foreground]).T, 
                             columns=['f_gw', 'strain_2'])
    
    power_dat_median = power_dat.rolling(window).median()
    power_dat_median = power_dat_median[window:]
    
    power_dat_median_fit = power_dat_median.loc[(power_dat_median.strain_2 > 0) & (power_dat_median.f_gw <= 1.2e-3)]

    popt, pcov = curve_fit(func, 
                           xdata=np.log10(power_dat_median_fit.f_gw.values),
                           ydata=np.log10(power_dat_median_fit.strain_2.values))

    
    psd_conf = psd.power_spectral_density(f=np.linspace(1e-4, 1e-1, 1000000) * u.Hz, 
                                          instrument="custom", 
                                          custom_function=cosmic_confusion, 
                                          t_obs=4 * u.yr, 
                                          L=None, 
                                          approximate_R=True, 
                                          include_confusion_noise=False)
    
    sources_conf = source.Source(m_1=dat.mass_1.values * u.Msun, 
                                 m_2=dat.mass_2.values * u.Msun,  
                                 ecc=np.zeros(len(dat.mass_1)), 
                                 dist=dat.dist_sun.values * u.kpc, 
                                 f_orb=dat.f_gw.values/2 * u.Hz,
                                 stat_tol = 1/(Tobs.to(u.s).value),
                                 interpolate_g=True, 
                                 interpolate_sc=True, 
                                 sc_params={"instrument": "custom",
                                            "custom_function":cosmic_confusion,
                                            "t_obs": Tobs,
                                            "L": 2.5e9,
                                            "approximate_R": True,
                                            "include_confusion_noise": True})

    
    dat['snr'] = sources_conf.get_snr(t_obs=Tobs, verbose=False)
    dat['chirp'] = utils.fn_dot(sources_conf.m_c, sources_conf.f_orb, sources_conf.ecc, n=2)

    dat = dat.loc[dat.snr > 7]
    dat['resolved_chirp'] = np.zeros(len(dat))
    dat.loc[dat.chirp > 1/((Tobs.to(u.s))**2), 'resolved_chirp'] = 1.0
    
    if var:
        fname = 'resolved_DWDs_FZ.hdf'
    else:
        fname = 'resolved_DWDs_F50.hdf'
    dat.to_hdf(pathtosave+fname, key='resolved')
    power_dat.to_hdf(pathtosave+fname, key='total_power')
    
    pd.DataFrame(popt).to_hdf(pathtosave+fname, key='conf_fit')
    
    return
    
