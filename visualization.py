from funcs_v1 import *
import matplotlib.pyplot as plt
import legwork.visualisation as vis
from matplotlib.colors import TwoSlopeNorm
from matplotlib import rcParams
from matplotlib.lines import Line2D
import matplotlib.colors as col

rcParams['font.family'] = 'serif'
rcParams['font.size'] = 14
rcParams['mathtext.default'] = 'regular'

obs_sec = 4 * u.yr.to('s')
obs_hz = 1 / obs_sec

def plot_FIRE_F_mass():
    fig, ax = plt.subplots()
    plt.grid(lw=0.25, which='both')
    bins = np.append(met_arr[1:-1]/Z_sun, FIRE.met.max())
    bins = np.append(FIRE.met.min(), bins)
    bins = np.log10(bins)
    ax2 = ax.twinx()
    h, bins, _ = ax2.hist(np.log10(FIRE.met), bins=bins, histtype='step', lw=2, 
                          color='xkcd:tomato red', label='Latte m12i')
    ax2.set_yscale('log')
    #plt.xscale('log')
    ax2.legend(loc='lower left', bbox_to_anchor= (0.6, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20)
    ax.scatter(np.log10(met_arr[1:]/Z_sun), get_binfrac_of_Z(met_arr[1:]), color='k', s=15, zorder=2, 
               label='COSMIC Z grid')
    met_plot = np.linspace(FIRE.met.min()*Z_sun, FIRE.met.max()*Z_sun, 10000)
    ax.plot(np.log10(met_plot/Z_sun), get_binfrac_of_Z(met_plot), color='k', label='FZ')
    ax.set_xlim(bins[1]-0.17693008, bins[-2] + 2 * 0.17693008)
    ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=3)
    ax.set_zorder(ax2.get_zorder()+1)
    ax.patch.set_visible(False)
    ax.set_xlabel('Log$_{10}$(Z/Z$_\odot$)')
    #ax.set_ylabel('Binary Fraction f$_b$(Z)')
    ax.set_ylabel('Binary Fraction')
    ax2.set_ylabel(r'M$_{\rm{stars}}$ per Z bin (M$_\odot$)')
    #plt.savefig('PaperPlots/FIREfb.png')
    ax2.set_yticks([1e4, 1e5, 1e6, 1e7]);
    ax2.set_yticklabels(['7e7', '7e8', '7e9', '7e10']);
    plt.show(block=False)
    
    return


def plot_FIRE_F_NSP():
    fig, ax = plt.subplots()
    plt.grid(lw=0.25, which='both')
    bins = np.append(met_arr[1:-1]/Z_sun, FIRE.met.max())
    bins = np.append(FIRE.met.min(), bins)
    bins = np.log10(bins)
    ax2 = ax.twinx()
    h, bins, _ = ax2.hist(np.log10(FIRE.met), bins=bins, histtype='step', lw=2, 
                          color='xkcd:tomato red', label='Latte m12i')
    ax2.set_yscale('log')
    #plt.xscale('log')
    ax2.legend(loc='lower left', bbox_to_anchor= (0.6, 1.01), ncol=4, borderaxespad=0,
               frameon=False, fontsize=20)
    ax.scatter(np.log10(met_arr[1:]/Z_sun), get_binfrac_of_Z(met_arr[1:]), color='k', s=15, 
               zorder=2, label='COSMIC Z grid')
    met_plot = np.linspace(FIRE.met.min()*Z_sun, FIRE.met.max()*Z_sun, 10000)
    ax.plot(np.log10(met_plot/Z_sun), get_binfrac_of_Z(met_plot), color='k', label='FZ')
    ax.set_xlim(bins[1]-0.17693008, bins[-2] + 2 * 0.17693008)
    ax.legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=3)
    ax.set_zorder(ax2.get_zorder()+1)
    ax.patch.set_visible(False)
    ax.set_xlabel('Log$_{10}$(Z/Z$_\odot$)')
    ax.set_ylabel('Binary Fraction')
    ax2.set_ylabel(r'N$_{\rm{SP}}$ per Z bin')
    plt.show(block=False)

    return

def plot_FIREpos():
    X = FIRE.xGx
    Y = FIRE.yGx
    Z = FIRE.zGx
    fig, ax = plt.subplots(figsize=(10, 8))
    plt.hist2d(X, Y, norm=col.LogNorm(), bins=500);
    plt.scatter(0, sun_yGx, edgecolor='xkcd:light pink', facecolor='xkcd:bright pink', s=90, label='Sun')
    cb = plt.colorbar()
    cb.ax.set_ylabel('LogNormed Density')
    plt.legend(fontsize=20, markerscale=2)
    plt.xlabel('X (kpc)')
    plt.ylabel('Y (kpc)')
    plt.show(block=False)
    
    return


def get_formeff(pathtodat, pathtoeff, pathtoLband, getfrom):
    def formeff(datfiles, Lbandfiles, pathtoLband, label, model, getfrom):
        lenconv = []
        masslist = []
        for i in range(15):
            if model == 'F50':
                binfrac = 0.5
                ratio = ratio_05
            elif model == 'FZ':
                binfrac = binfracs[i]
                ratio = ratios[i]
            bpp = pd.read_hdf(datfiles[i], key='bpp')
            if getfrom == 'Lband':
                mass = pd.read_hdf(pathtoLband + Lbandfiles[i], key='mass_total')
                conv = pd.read_hdf(datfiles[i], key='conv')
            elif getfrom == 'dat':
                try:
                    mass_binaries = pd.read_hdf(datfiles[i], key='mass_stars').iloc[-1]
                except:
                    print('m_binaries key')
                    mass_binaries = pd.read_hdf(datfiles[i], key='mass_binaries').iloc[-1]
                mass = (1 + ratio) * mass_binaries
                if label == '10_10' or label == '11_10':
                    conv = pd.read_hdf(datfiles[i], key='conv')
                elif label == '11_11':
                    conv = bpp.loc[(bpp.kstar_1==11)&(bpp.kstar_2==11)].groupby('bin_num').first()  
                elif label == '12':
                     conv = bpp.loc[(bpp.kstar_1==12)&(bpp.kstar_2.isin([10,11,12]))].groupby('bin_num').first()                 
            masslist.append(mass)
            lenconv.append(len(conv))

        lenconv = np.array(lenconv)
        masslist = np.concatenate(np.array(masslist))
        eff = lenconv / masslist
        return eff

    files, label = getfiles_He_He(pathtodat)
    Lbandfiles = Lband_files_10_10_var()
    effHe = formeff(files, Lbandfiles, pathtoLband, label, 'FZ', getfrom)
    Lbandfiles = Lband_files_10_10_05()
    effHe05 = formeff(files, Lbandfiles, pathtoLband, label, 'F50', getfrom)
    print('finished He + He')

    files, label = getfiles_CO_He(pathtodat)
    Lbandfiles = Lband_files_11_10_var()
    effCOHe = formeff(files, Lbandfiles, pathtoLband, label, 'FZ', getfrom)
    Lbandfiles = Lband_files_11_10_05()
    effCOHe05 = formeff(files, Lbandfiles, pathtoLband, label, 'F50', getfrom)
    print('finished CO + He')

    files, label = getfiles_CO_CO(pathtodat)
    Lbandfiles = Lband_files_11_11_var()
    effCO = formeff(files, Lbandfiles, pathtoLband, label, 'FZ', getfrom)
    Lbandfiles = Lband_files_11_11_05()
    effCO05 = formeff(files, Lbandfiles, pathtoLband, label, 'F50', getfrom)
    print('finished CO + CO')

    files, label = getfiles_ONe(pathtodat)
    Lbandfiles = Lband_files_12_var()
    effONe = formeff(files, Lbandfiles, pathtoLband, label, 'FZ', getfrom)
    Lbandfiles = Lband_files_12_05()
    effONe05 = formeff(files, Lbandfiles, pathtoLband, label, 'F50', getfrom)
    print('finished ONe + XX')

    DWDeff = pd.DataFrame(np.array([effHe, effCOHe, effCO, effONe]).T, columns=['He', 'COHe', 'CO', 'ONe'])
    DWDeff.to_hdf(pathtoeff + 'DWDeff_FZ.hdf', key='data')

    DWDeff05 = pd.DataFrame(np.array([effHe05, effCOHe05, effCO05, effONe05]).T, columns=['He', 'COHe', 'CO', 'ONe'])
    DWDeff05.to_hdf(pathtoeff + 'DWDeff_F50.hdf', key='data')
    
    return

def plot_formeff(effHe, effHe05, effCOHe, effCOHe05, effCO, effCO05, effONe, effONe05):
    fig, ax = plt.subplots(1, 4, figsize=(30, 8))
    ax[0].plot(np.log10(met_arr[1:]/Z_sun), effHe*1e3, color='xkcd:tomato red',
                 drawstyle='steps-mid', lw=4, label='FZ')
    ax[0].plot(np.log10(met_arr[1:]/Z_sun), effHe05*1e3, color='xkcd:tomato red',
               ls='--', drawstyle='steps-mid', lw=4, label='F50')

    ax[1].plot(np.log10(met_arr[1:]/Z_sun), effCOHe*1e3, color='xkcd:blurple', 
               drawstyle='steps-mid', lw=4, label='FZ')
    ax[1].plot(np.log10(met_arr[1:]/Z_sun), effCOHe05*1e3, color='xkcd:blurple', 
               ls='--', drawstyle='steps-mid', lw=4, label='F50')

    ax[2].plot(np.log10(met_arr[1:]/Z_sun), effCO*1e3, color='xkcd:pink', 
               drawstyle='steps-mid', lw=4, label='FZ')
    ax[2].plot(np.log10(met_arr[1:]/Z_sun), effCO05*1e3, color='xkcd:pink', ls='--', 
               drawstyle='steps-mid', lw=4, label='F50')

    ax[3].plot(np.log10(met_arr[1:]/Z_sun), effONe*1e3, color='xkcd:light blue', 
               drawstyle='steps-mid', lw=4, label='FZ')
    ax[3].plot(np.log10(met_arr[1:]/Z_sun), effONe05*1e3, color='xkcd:light blue', ls='--', 
               drawstyle='steps-mid', lw=4, label='F50')

    #ax[0].set_ylabel('DWD Formation\nEfficiency (10$^{-3}$ M$_\odot^{-1}$)', fontsize=27)
    ax[0].set_ylabel(r'$\eta_{\rm{FORM, DWD}}$ (10$^{-3}$ M$_\odot^{-1}$)', fontsize=27)
    ax[1].set_ylim(top=3.75)
    ax[2].set_ylim(top=16)
    ax[0].set_ylim(top=2.25)
    ax[3].set_ylim(top=1.4)
    ax[0].set_yticks([0.25, 0.75, 1.25, 1.75, 2.25])
    ax[1].set_yticks([0.75, 1.5, 2.25, 3., 3.75])
    plt.subplots_adjust(wspace=0.18)
    labels = ['He + He', "CO + He", 'CO + CO', "ONe + X"]
    for i in range(4):
        #ax[i].set_yscale('log')
        ax[i].set_xticks([-2, -1.5, -1, -0.5, 0.])
        ax[i].tick_params(labelsize=22)
        ax[i].text(0.05, 0.05, labels[i], fontsize=25, transform=ax[i].transAxes)
        ax[i].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=3, borderaxespad=0, 
                   frameon=False, fontsize=26)
        ax[i].set_xlabel('Log$_{10}$(Z/Z$_\odot$)', fontsize=27)
    plt.show(block=False)
    
    return()

def make_numLISAplot(numsFZ, numsF50):
    num = 30
    met_bins = np.logspace(np.log10(FIRE.met.min()), np.log10(FIRE.met.max()), num)*Z_sun
    met_bins

    nums = pd.read_hdf('numLISA_30bins.hdf', key='data')
    nums05 = pd.read_hdf('numLISA_30bins_05.hdf', key='data')

    Henums = numsFZ.He.values
    COHenums = numsFZ.COHe.values
    COnums = numsFZ.CO.values
    ONenums = numsFZ.ONe.values

    Henums05 = numsF50.He.values
    COHenums05 = numsF50.COHe.values
    COnums05 = numsF50.CO.values
    ONenums05 = numsF50.ONe.values

    fig, ax = plt.subplots(1, 4, figsize=(24, 6))

    ax[0].plot(np.log10(met_bins[1:]/Z_sun), Henums/1e5, drawstyle='steps-mid', 
               color='xkcd:tomato red', lw=3, label='f$_b$(Z)')
    ax[0].plot(np.log10(met_bins[1:]/Z_sun), Henums05/1e5, 
               drawstyle='steps-mid', color='xkcd:tomato red', ls='--', lw=3, label='f$_b$=0.5')
    ax[0].text(0.05, 0.9, 'He + He', fontsize=20, transform=ax[0].transAxes)

    ax[1].plot(np.log10(met_bins[1:]/Z_sun), COHenums/1e5, drawstyle='steps-mid', 
               color='xkcd:blurple', lw=3, label='f$_b$(Z)')
    ax[1].plot(np.log10(met_bins[1:]/Z_sun), COHenums05/1e5, drawstyle='steps-mid', 
               color='xkcd:blurple', ls='--', lw=3, label='f$_b$=0.5')
    ax[1].text(0.05, 0.9, 'CO + He', fontsize=20, transform=ax[1].transAxes)

    ax[2].plot(np.log10(met_bins[1:]/Z_sun), COnums/1e5, drawstyle='steps-mid', 
               color='xkcd:pink', lw=3, label='f$_b$(Z)')
    ax[2].plot(np.log10(met_bins[1:]/Z_sun), COnums05/1e5, drawstyle='steps-mid', 
               color='xkcd:pink', ls='--', lw=3, label='f$_b$=0.5')
    ax[2].text(0.05, 0.9, 'CO + CO', fontsize=20, transform=ax[2].transAxes)

    ax[3].plot(np.log10(met_bins[1:]/Z_sun), ONenums/1e5, drawstyle='steps-mid', 
               color='xkcd:light blue', lw=3, label='f$_b$(Z)')
    ax[3].plot(np.log10(met_bins[1:]/Z_sun), ONenums05/1e5, drawstyle='steps-mid',
               color='xkcd:light blue', ls='--', lw=3, label='f$_b$=0.5')
    ax[3].text(0.05, 0.9, 'ONe + X', fontsize=20, transform=ax[3].transAxes)

    for i in range(4):
        #ax[i].set_yscale('log')
        #ax[i].set_ylim(10, 2.5e6)
        #ax[i].grid(which='both', zorder=0, alpha=0.2)
        ax[i].set_xlabel('Log$_{10}$(Z/Z$_\odot$)')
        ax[i].set_xticks([-3, -2, -1, 0, 1.])
        ax[i].legend(loc='lower left', bbox_to_anchor= (-0.02, 1.01), ncol=2, 
                     borderaxespad=0, frameon=False, fontsize=21)

    plt.subplots_adjust(wspace=0.2)   
    ax[0].set_ylabel(r'N$_{\rm{DWD}}$(f$_{\rm{GW}} \geq 10^{-4} \rm{HZ}$) (10$^5$)')
    ax[0].set_yticks(np.arange(0, 2.5, 0.5));
    ax[2].set_yticks(np.arange(0, 3.5, 0.5));
    plt.show(block=False)
    
    return 

def make_Mc_fgw_plot(pathtoLband, model):
    if model == 'FZold':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        CO = pd.DataFrame()
        for f in galaxy_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        ONe = pd.DataFrame()
        for f in galaxy_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
            
    elif model == 'FZnew':
        He = pd.DataFrame()
        for f in Lband_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        CO = pd.DataFrame()
        for f in Lband_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        COHe = pd.DataFrame()
        for f in Lband_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        ONe = pd.DataFrame()
        for f in Lband_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
            
    if model == 'F50old':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        CO = pd.DataFrame()
        for f in galaxy_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        ONe = pd.DataFrame()
        for f in galaxy_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
            
    elif model == 'F50new':
        He = pd.DataFrame()
        for f in Lband_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        CO = pd.DataFrame()
        for f in Lband_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        COHe = pd.DataFrame()
        for f in Lband_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))

        ONe = pd.DataFrame()
        for f in Lband_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))

    Heplot = He.loc[(He.fdot>=obs_hz**2)&(He.snr>7)] #[::100]
    COHeplot = COHe.loc[(COHe.fdot>=obs_hz**2)&(COHe.snr>7)] #[::1000]
    COplot = CO.loc[(CO.fdot>=obs_hz**2)&(CO.snr>7)] #[::100]
    ONeplot = ONe.loc[(ONe.fdot>=obs_hz**2)&(ONe.snr>7)] #[::100]
    print(len(Heplot), len(COHeplot), len(COplot), len(ONeplot))

    fig, ax = plt.subplots(4, 3, figsize=(20,16))
    levels = [0.01, 0.1, 0.3, 0.6, 0.9]
    colors = ['#80afd6', '#2b5d87', '#4288c2', '#17334a']

    ax[0,0].scatter(y=utils.chirp_mass(Heplot.mass_1.values*u.M_sun, 
                                  Heplot.mass_2.values*u.M_sun),
               x=np.log10(Heplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(Heplot.loc[Heplot.met*Z_sun<=met_arr[1]].mass_1.values*u.M_sun, 
                                  Heplot.loc[Heplot.met*Z_sun<=met_arr[1]].mass_2.values*u.M_sun),
               x=np.log10(Heplot.loc[Heplot.met*Z_sun<=met_arr[1]].f_gw.values), levels=levels,fill=False, 
               ax=ax[0,0], color=colors[0], zorder=3, linewidths=2.5)

    ax[0,1].scatter(y=utils.chirp_mass(Heplot.mass_1.values*u.M_sun, 
                                  Heplot.mass_2.values*u.M_sun),
               x=np.log10(Heplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(Heplot.loc[(Heplot.met*Z_sun>=met_arr[7])&(Heplot.met*Z_sun<=met_arr[8])].mass_1.values*u.M_sun, 
                                  Heplot.loc[(Heplot.met*Z_sun>=met_arr[7])&(Heplot.met*Z_sun<=met_arr[8])].mass_2.values*u.M_sun),
               x=np.log10(Heplot.loc[(Heplot.met*Z_sun>=met_arr[7])&(Heplot.met*Z_sun<=met_arr[8])].f_gw.values), levels=levels,fill=False, 
               ax=ax[0,1], color=colors[1], zorder=3, linewidths=2.5)

    ax[0,2].scatter(y=utils.chirp_mass(Heplot.mass_1.values*u.M_sun, 
                                  Heplot.mass_2.values*u.M_sun),
               x=np.log10(Heplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(Heplot.loc[(Heplot.met*Z_sun>=met_arr[-2])].mass_1.values*u.M_sun, 
                                  Heplot.loc[(Heplot.met*Z_sun>=met_arr[-2])].mass_2.values*u.M_sun),
               x=np.log10(Heplot.loc[(Heplot.met*Z_sun>=met_arr[-2])].f_gw.values), levels=levels,fill=False, 
               ax=ax[0,2], color=colors[3], zorder=3, linewidths=2.5)

    ax[1,0].scatter(y=utils.chirp_mass(COHeplot.mass_1.values*u.M_sun, 
                                  COHeplot.mass_2.values*u.M_sun),
               x=np.log10(COHeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COHeplot.loc[COHeplot.met*Z_sun<=met_arr[1]].mass_1.values*u.M_sun, 
                                  COHeplot.loc[COHeplot.met*Z_sun<=met_arr[1]].mass_2.values*u.M_sun),
               x=np.log10(COHeplot.loc[COHeplot.met*Z_sun<=met_arr[1]].f_gw.values), levels=levels,fill=False, 
               ax=ax[1,0], color=colors[0], zorder=3, linewidths=2.5)

    ax[1,1].scatter(y=utils.chirp_mass(COHeplot.mass_1.values*u.M_sun, 
                                  COHeplot.mass_2.values*u.M_sun),
               x=np.log10(COHeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[7])&(COHeplot.met*Z_sun<=met_arr[8])].mass_1.values*u.M_sun, 
                                  COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[7])&(COHeplot.met*Z_sun<=met_arr[8])].mass_2.values*u.M_sun),
               x=np.log10(COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[7])&(COHeplot.met*Z_sun<=met_arr[8])].f_gw.values), 
               levels=levels,fill=False, ax=ax[1,1], color=colors[1], zorder=3, linewidths=2.5)

    ax[1,2].scatter(y=utils.chirp_mass(COHeplot.mass_1.values*u.M_sun, 
                                  COHeplot.mass_2.values*u.M_sun),
               x=np.log10(COHeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[-2])].mass_1.values*u.M_sun, 
                                  COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[-2])].mass_2.values*u.M_sun),
               x=np.log10(COHeplot.loc[(COHeplot.met*Z_sun>=met_arr[-2])].f_gw.values), levels=levels,fill=False, 
               ax=ax[1,2], color=colors[3], zorder=3, linewidths=2.5)

    ax[2,0].scatter(y=utils.chirp_mass(COplot.mass_1.values*u.M_sun, 
                                  COplot.mass_2.values*u.M_sun),
               x=np.log10(COplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COplot.loc[COplot.met*Z_sun<=met_arr[1]].mass_1.values*u.M_sun, 
                                  COplot.loc[COplot.met*Z_sun<=met_arr[1]].mass_2.values*u.M_sun),
               x=np.log10(COplot.loc[COplot.met*Z_sun<=met_arr[1]].f_gw.values), levels=levels,fill=False, 
               ax=ax[2,0], color=colors[0], zorder=3, linewidths=2.5)

    ax[2,1].scatter(y=utils.chirp_mass(COplot.mass_1.values*u.M_sun, 
                                  COplot.mass_2.values*u.M_sun),
               x=np.log10(COplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COplot.loc[(COplot.met*Z_sun>=met_arr[7])&(COplot.met*Z_sun<=met_arr[8])].mass_1.values*u.M_sun, 
                                  COplot.loc[(COplot.met*Z_sun>=met_arr[7])&(COplot.met*Z_sun<=met_arr[8])].mass_2.values*u.M_sun),
               x=np.log10(COplot.loc[(COplot.met*Z_sun>=met_arr[7])&(COplot.met*Z_sun<=met_arr[8])].f_gw.values), levels=levels,fill=False, 
               ax=ax[2,1], color=colors[1], zorder=3, linewidths=2.5)

    ax[2,2].scatter(y=utils.chirp_mass(COplot.mass_1.values*u.M_sun, 
                                  COplot.mass_2.values*u.M_sun),
               x=np.log10(COplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(COplot.loc[(COplot.met*Z_sun>=met_arr[-2])].mass_1.values*u.M_sun, 
                                  COplot.loc[(COplot.met*Z_sun>=met_arr[-2])].mass_2.values*u.M_sun),
               x=np.log10(COplot.loc[(COplot.met*Z_sun>=met_arr[-2])].f_gw.values), levels=levels,fill=False, 
               ax=ax[2,2], color=colors[3], zorder=3, linewidths=2.5)


    ax[3,0].scatter(y=utils.chirp_mass(ONeplot.mass_1.values*u.M_sun, 
                                  ONeplot.mass_2.values*u.M_sun),
               x=np.log10(ONeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(ONeplot.loc[ONeplot.met*Z_sun<=met_arr[1]].mass_1.values*u.M_sun, 
                                  ONeplot.loc[ONeplot.met*Z_sun<=met_arr[1]].mass_2.values*u.M_sun),
               x=np.log10(ONeplot.loc[ONeplot.met*Z_sun<=met_arr[1]].f_gw.values), levels=levels,fill=False, 
               ax=ax[3,0], color=colors[0], zorder=3, linewidths=2.5)


    ax[3,1].scatter(y=utils.chirp_mass(ONeplot.mass_1.values*u.M_sun, 
                                  ONeplot.mass_2.values*u.M_sun),
               x=np.log10(ONeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[7])&(ONeplot.met*Z_sun<=met_arr[8])].mass_1.values*u.M_sun, 
                                  ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[7])&(ONeplot.met*Z_sun<=met_arr[8])].mass_2.values*u.M_sun),
               x=np.log10(ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[7])&(ONeplot.met*Z_sun<=met_arr[8])].f_gw.values), levels=levels,fill=False, 
               ax=ax[3,1], color=colors[1], zorder=3, linewidths=2.5)

    ax[3,2].scatter(y=utils.chirp_mass(ONeplot.mass_1.values*u.M_sun, 
                                  ONeplot.mass_2.values*u.M_sun),
               x=np.log10(ONeplot.f_gw.values), color='xkcd:light grey', zorder=0.)

    sb.kdeplot(y=utils.chirp_mass(ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[-2])].mass_1.values*u.M_sun, 
                                  ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[-2])].mass_2.values*u.M_sun),
               x=np.log10(ONeplot.loc[(ONeplot.met*Z_sun>=met_arr[-2])].f_gw.values), levels=levels,fill=False, 
               ax=ax[3,2], color=colors[3], zorder=3, linewidths=2.5)

    from matplotlib.lines import Line2D
    custom_lines = [Line2D([0], [0], color='xkcd:light grey', lw=4),
                    Line2D([0], [0], color=colors[0], lw=4),
                    Line2D([0], [0], color=colors[1], lw=4),
                    Line2D([0], [0], color=colors[2], lw=4)]

    ax[0,0].legend([custom_lines[0], custom_lines[1]], ['All Z', 'Z=0.0001'], loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=18)

    ax[0,1].legend([custom_lines[0], custom_lines[3]], ['All Z', 'Z={}'.format(met_arr[8])], loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=18)

    ax[0,2].legend([custom_lines[0], custom_lines[2]], ['All Z', 'Z=03'], loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=18)

    for i in range(4):
        ax[i,0].set_ylabel('Chirp Mass (M$_\odot$)', fontsize=20)
        ax[i,1].set_yticklabels('')
        ax[i,2].set_yticklabels('')

    for i in range(3):
        ax[3,i].set_xlabel(r'Log$_{10}$(f$_{\rm{GW}}$/Hz)', fontsize=20)
        ax[i,0].set_xticklabels('')
        ax[i,1].set_xticklabels('')
        ax[i,2].set_xticklabels('')
        #ax[3,i].set_xticks([-4.25, -3.75, -3.25, -2.75])
        #ax[3,i].set_xticklabels(['-4.25', '-3.75', '-3.25', '-2.75'])
        #ax[0,i].set_ylim(0.175, 0.375)
        #ax[2,i].set_ylim(0.3, 1.05)
        #ax[1,i].set_ylim(0.2, 0.6)
        #ax[3,i].set_ylim(0.3, 1.1)
        ax[0,i].text(0.85, 0.85, 'He + He', fontsize=18, horizontalalignment='center', 
                     transform=ax[0,i].transAxes)
        ax[1,i].text(0.85, 0.85, 'CO + He', fontsize=18, horizontalalignment='center', 
                     transform=ax[1,i].transAxes)
        ax[2,i].text(0.85, 0.85, 'CO + CO', fontsize=18, horizontalalignment='center', 
                     transform=ax[2,i].transAxes)
        ax[3,i].text(0.85, 0.85, 'ONe + X', fontsize=18, horizontalalignment='center', 
                     transform=ax[3,i].transAxes)

    for i in range(4):
        for j in range(3):
            ax[i,j].set_xlim(-3.5, -1.25)
            ax[i,j].axvline(-4.0, color='xkcd:grey', ls='--', lw=2., zorder=1.)

    plt.subplots_adjust(hspace=0.06, wspace=0.03)

    plt.show(block=False)
    
    return

def plot_intersep(Heinter, COHeinter, COinter, ONeinter, whichsep):
    '''
    whichsep must be either "CEsep" or "RLOFsep"
    '''
    num = 30
    met_bins = np.logspace(np.log10(FIRE.met.min()), np.log10(FIRE.met.max()), num)#*Z_sun
    met_mids = (met_bins[1:] + met_bins[:-1]) / 2


    Heavgs = []
    Hecovs = []
    COHeavgs = []
    COHecovs = []
    COavgs = []
    COcovs = []
    ONeavgs = []
    ONecovs = []
    for i in range(num-1):
        meti = met_bins[i]
        metf = met_bins[i+1]

        Hebin = Heinter.loc[(Heinter.met>=meti)&(Heinter.met<=metf)]
        if len(Hebin) != 0:
            Heavgs.append(np.mean(Hebin[whichsep].values))
            Hecovs.append(np.std(Hebin[whichsep].values))
        else:
            Heavgs.append(0.)
            Hecovs.append(0.)

        COHebin = COHeinter.loc[(COHeinter.met>=meti)&(COHeinter.met<=metf)]
        if len(COHebin) != 0:
            COHeavgs.append(np.mean(COHebin[whichsep].values))
            COHecovs.append(np.std(COHebin[whichsep].values))
        else:
            COHeavgs.append(0.)
            COHecovs.append(0.)

        CObin = COinter.loc[(COinter.met>=meti)&(COinter.met<=metf)]
        if len(CObin) != 0:
            COavgs.append(np.mean(CObin[whichsep].values))
            COcovs.append(np.std(CObin[whichsep].values))
        else:
            COavgs.append(0.)
            COcovs.append(0.)

        ONebin = ONeinter.loc[(ONeinter.met>=meti)&(ONeinter.met<=metf)]
        if len(ONebin) != 0:
            ONeavgs.append(np.mean(ONebin[whichsep].values))
            ONecovs.append(np.std(ONebin[whichsep].values))
        else:
            ONeavgs.append(0.)
            ONecovs.append(0.)
            
    Heavgs = np.array(Heavgs)
    Hecovs = np.array(Hecovs)
    COHeavgs = np.array(COHeavgs)
    COHecovs = np.array(COHecovs)
    COavgs = np.array(COavgs)
    COcovs = np.array(COcovs)
    ONeavgs = np.array(ONeavgs)
    ONecovs = np.array(ONecovs)
    
    fig, ax = plt.subplots(1, 4, figsize=(16, 4))
    ax[0].plot(np.log10(met_mids[Heavgs>0]), Heavgs[Heavgs>0]/1e3, color='xkcd:tomato red', lw=3, ls='-', label='He + He', 
             drawstyle='steps-mid')
    ax[0].fill_between(np.log10(met_mids[Heavgs>0]), (Heavgs[Heavgs>0]-Hecovs[Heavgs>0])/1e3, 
                     (Heavgs[Heavgs>0]+Hecovs[Heavgs>0])/1e3, alpha=0.3, color='xkcd:tomato red',
                       zorder=0, step='mid', label='$\sigma$')

    ax[2].plot(np.log10(met_mids[COavgs>0]), COavgs[COavgs>0]/1e3, color='xkcd:pink', lw=3, ls='-', 
             label='CO + CO', drawstyle='steps-mid')
    ax[2].fill_between(np.log10(met_mids[COavgs>0]), (COavgs[COavgs>0]-COcovs[COavgs>0])/1e3, 
                     (COavgs[COavgs>0]+COcovs[COavgs>0])/1e3, alpha=0.3, color='xkcd:pink', 
                       zorder=0, step='mid', label='$\sigma$')

    ax[1].plot(np.log10(met_mids), COHeavgs/1e3, color='xkcd:blurple', lw=3, ls='-', label='CO + He', 
             drawstyle='steps-mid')
    ax[1].fill_between(np.log10(met_mids[COHeavgs>0]), (COHeavgs[COHeavgs>0]-COHecovs[COHeavgs>0])/1e3, 
                     (COHeavgs[COHeavgs>0]+COHecovs[COHeavgs>0])/1e3, alpha=0.3, color='xkcd:blurple',
                       zorder=0, step='mid', label='$\sigma$')

    ax[3].plot(np.log10(met_mids[ONeavgs>0]), ONeavgs[ONeavgs>0]/1e3, color='xkcd:light blue', lw=3, 
             label='ONe + X', drawstyle='steps-mid')
    ax[3].fill_between(np.log10(met_mids[ONeavgs>0]), (ONeavgs[ONeavgs>0]-ONecovs[ONeavgs>0])/1e3,
                     (ONeavgs[ONeavgs>0]+ONecovs[ONeavgs>0])/1e3, alpha=0.3, color='xkcd:light blue', 
                       zorder=0, step='mid', label='$\sigma$')

    for i in range(4):
        #ax[i].set_xscale('log')
        ax[i].set_xticks([-3., -2., -1., 0., 1.])
        ax[i].set_xlim(np.log10(met_mids[0]), np.log10(met_mids[-1]))
        ax[i].set_xlabel('Log$_{10}$(Z/Z$_\odot$)', fontsize=18)
        ax[i].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=2, borderaxespad=0, frameon=False, 
              fontsize=15, markerscale=0.5)
    #ax[0].set_ylabel('Avg. Interaction\nSeparation (10$^3$ R$_\odot$)', fontsize=18)
    ax[0].set_ylabel(r'$\langle a_{\rm{RLOF}}\rangle$   (10$^3$ R$_\odot$)', fontsize=18)

    plt.show(block=False)
    
    return

def plot_LISAcurves(modelfile):
    if Lbandfile == 'FZold':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))  
        print('finished He + He')
        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + He')
        CO = pd.DataFrame()
        for f in galaxy_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + CO')
        ONe = pd.DataFrame()
        for f in galaxy_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished ONe + X')
    
    elif Lbandfile == 'FZnew':
        He = pd.DataFrame()
        for f in Lband_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished He + He')
        CO = pd.DataFrame()
        for f in Lband_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + He')
        COHe = pd.DataFrame()
        for f in Lband_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + CO')
        ONe = pd.DataFrame()
        for f in Lband_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished ONe + X')

    elif Lbandfile == 'F50old':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished He + He, F50')
        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + He, F50')
        CO = pd.DataFrame()
        for f in galaxy_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + CO, F50')
        ONe = pd.DataFrame()
        for f in galaxy_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished ONe + X, F50') 

    elif Lbandfile == 'F50new':
        He = pd.DataFrame()
        for f in Lband_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished He + He, F50')
        COHe = pd.DataFrame()
        for f in Lband_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + He, F50')
        CO = pd.DataFrame()
        for f in Lband_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished CO + CO, F50')
        ONe = pd.DataFrame()
        for f in Lband_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        print('finished ONe + X, F50')
        
    from legwork.visualisation import plot_sensitivity_curve
    t_obs = 4 * u.yr
    Heasd = ((1/4 * t_obs)**(1/2) * He.h_0[He.snr>7].values).to(u.Hz**(-1/2))
    COasd = ((1/4 * t_obs)**(1/2) * CO.h_0[CO.snr>7].values).to(u.Hz**(-1/2))
    COHeasd = ((1/4 * t_obs)**(1/2) * COHe.h_0[COHe.snr>7].values).to(u.Hz**(-1/2))
    ONeasd = ((1/4 * t_obs)**(1/2) * ONe.h_0[ONe.snr>7].values).to(u.Hz**(-1/2))

    fig, ax = plt.subplots(1, 4, figsize=(25, 5))
    plot_sensitivity_curve(fig=fig, ax=ax[0], show=False, t_obs=t_obs)
    ax[0].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:tomato red', label='He + He')
    ax[0].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[0].text(0.75, 0.8, 'SNR > 7: {}\nf$_b$=f$_b$(Z)'.format(len(Heasd)), fontsize=20, transform=ax[0].transAxes,
              horizontalalignment='center')
    ax[0].set_xlim(4e-5, 5e-1)
    ax[0].set_ylim(top=1e-15)
    ax[0].tick_params(labelsize=20)

    plot_sensitivity_curve(fig=fig, ax=ax[2], show=False, t_obs=t_obs)
    ax[2].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:pink', label='CO + CO')
    ax[2].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[2].text(0.75, 0.8, 'SNR > 7: {}\nf$_b$=f$_b$(Z)'.format(len(COasd)), fontsize=20, 
               transform=ax[2].transAxes, horizontalalignment='center')
    ax[2].set_xlim(4e-5, 5e-1)
    ax[2].set_ylim(top=1e-15)
    ax[2].tick_params(labelsize=20)
    ax[2].set_ylabel('')
    ax[2].set_yticks([])

    plot_sensitivity_curve(fig=fig, ax=ax[1], show=False, t_obs=t_obs)
    ax[1].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:blurple', label='CO + He')
    ax[1].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[1].text(0.75, 0.8, 'SNR > 7: {}\nf$_b$=f$_b$(Z)'.format(len(COHeasd)), fontsize=20, transform=ax[1].transAxes,
              horizontalalignment='center')
    ax[1].set_xlim(4e-5, 5e-1)
    ax[1].set_ylim(top=1e-15)
    ax[1].tick_params(labelsize=20)
    ax[1].set_ylabel('')
    ax[1].set_yticks([])

    plot_sensitivity_curve(fig=fig, ax=ax[3], show=False, t_obs=t_obs)
    ax[3].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light blue', label='ONe + X')
    ax[3].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[3].text(0.75, 0.8, 'SNR > 7: {}\nf$_b$=f$_b$(Z)'.format(len(ONeasd)), fontsize=20, 
               transform=ax[3].transAxes, horizontalalignment='center')
    ax[3].set_xlim(4e-5, 5e-1)
    ax[3].set_ylim(top=1e-15)
    ax[3].tick_params(labelsize=20)
    ax[3].set_ylabel('')
    ax[3].set_yticks([])

    plt.subplots_adjust(wspace=0.01)
    for i in range(4):
        ax[i].set_xticks([])
        ax[i].set_xticklabels('')
        ax[i].set_xlabel('')
    plt.show()
    return

def plot_LISAcurves(pathtoLband, modelfile):
    if modelfile == 'FZold':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))  
        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        CO = pd.DataFrame()
        for f in galaxy_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        ONe = pd.DataFrame()
        for f in galaxy_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        model = 'FZ'
    
    elif modelfile == 'FZnew':
        He = pd.DataFrame()
        for f in Lband_files_10_10_var():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        CO = pd.DataFrame()
        for f in Lband_files_11_11_var():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        COHe = pd.DataFrame()
        for f in Lband_files_11_10_var():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        ONe = pd.DataFrame()
        for f in Lband_files_12_var():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        model = 'FZ'

    elif modelfile == 'F50old':
        He = pd.DataFrame()
        for f in galaxy_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        COHe = pd.DataFrame()
        for f in galaxy_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        CO = pd.DataFrame()
        for f in galaxy_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        ONe = pd.DataFrame()
        for f in galaxy_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        model = 'F50'

    elif modelfile == 'F50new':
        He = pd.DataFrame()
        for f in Lband_files_10_10_05():
            He = He.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        COHe = pd.DataFrame()
        for f in Lband_files_11_10_05():
            COHe = COHe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        CO = pd.DataFrame()
        for f in Lband_files_11_11_05():
            CO = CO.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        ONe = pd.DataFrame()
        for f in Lband_files_12_05():
            ONe = ONe.append(pd.read_hdf(pathtoLband + f, key='Lband'))
        model = 'F50'
        
    from legwork.visualisation import plot_sensitivity_curve
    t_obs = 4 * u.yr
    Heasd = ((1/4 * t_obs)**(1/2) * He.h_0[He.snr>7].values).to(u.Hz**(-1/2))
    COasd = ((1/4 * t_obs)**(1/2) * CO.h_0[CO.snr>7].values).to(u.Hz**(-1/2))
    COHeasd = ((1/4 * t_obs)**(1/2) * COHe.h_0[COHe.snr>7].values).to(u.Hz**(-1/2))
    ONeasd = ((1/4 * t_obs)**(1/2) * ONe.h_0[ONe.snr>7].values).to(u.Hz**(-1/2))

    fig, ax = plt.subplots(1, 4, figsize=(25, 5))
    plot_sensitivity_curve(fig=fig, ax=ax[0], show=False, t_obs=t_obs)
    ax[0].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[0].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:tomato red', label='He + He')
    ax[0].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[0].text(0.675, 0.875, model+', SNR > 7: {}'.format(len(Heasd)), fontsize=20, transform=ax[0].transAxes,
              horizontalalignment='center')
    ax[0].set_xlim(4e-5, 5e-1)
    ax[0].set_ylim(top=1e-15)
    ax[0].tick_params(labelsize=20)

    plot_sensitivity_curve(fig=fig, ax=ax[2], show=False, t_obs=t_obs)
    ax[2].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[2].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:pink', label='CO + CO')
    ax[2].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[2].text(0.675, 0.875, model+', SNR > 7: {}'.format(len(COasd)), fontsize=20, 
               transform=ax[2].transAxes, horizontalalignment='center')
    ax[2].set_xlim(4e-5, 5e-1)
    ax[2].set_ylim(top=1e-15)
    ax[2].tick_params(labelsize=20)
    ax[2].set_ylabel('')
    ax[2].set_yticks([])

    plot_sensitivity_curve(fig=fig, ax=ax[1], show=False, t_obs=t_obs)
    ax[1].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[1].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:blurple', label='CO + He')
    ax[1].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[1].text(0.675, 0.875, model+', SNR > 7: {}'.format(len(COHeasd)), fontsize=20, transform=ax[1].transAxes,
              horizontalalignment='center')
    ax[1].set_xlim(4e-5, 5e-1)
    ax[1].set_ylim(top=1e-15)
    ax[1].tick_params(labelsize=20)
    ax[1].set_ylabel('')
    ax[1].set_yticks([])

    plot_sensitivity_curve(fig=fig, ax=ax[3], show=False, t_obs=t_obs)
    ax[3].scatter(He.loc[He.snr>7].f_gw, Heasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(CO.loc[CO.snr>7].f_gw, COasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(COHe.loc[COHe.snr>7].f_gw, COHeasd, zorder=10, color='xkcd:light grey')
    ax[3].scatter(ONe.loc[ONe.snr>7].f_gw, ONeasd, zorder=10, color='xkcd:light blue', label='ONe + X')
    ax[3].legend(loc='lower left', bbox_to_anchor= (0.0, 1.01), ncol=4, borderaxespad=0, frameon=False, 
              fontsize=20, markerscale=2)
    ax[3].text(0.675, 0.875, model+', SNR > 7: {}'.format(len(ONeasd)), fontsize=20, 
               transform=ax[3].transAxes, horizontalalignment='center')
    ax[3].set_xlim(4e-5, 5e-1)
    ax[3].set_ylim(top=1e-15)
    ax[3].tick_params(labelsize=20)
    ax[3].set_ylabel('')
    ax[3].set_yticks([])

    plt.subplots_adjust(wspace=0.01)
    for i in range(4):
        ax[i].set_xticks([])
        ax[i].set_xticklabels('')
        ax[i].set_xlabel('')
    plt.show()
    return