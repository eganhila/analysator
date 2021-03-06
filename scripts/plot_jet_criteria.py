import pytools as pt
import sys, os, socket
import numpy as np

# Custom expression function                                                                                            
def exprPlaschke(exprmaps):
    # Plaschke criterion:                                                                                               
    # Ratio of dyn. pressure over sw dyn pressure                                                                       
    swrho = 1.0e6
    swvx = 750.e3
    # eprmaps consists of [rho, V]                                                                                      
    rho = exprmaps[0][:,:]
    Vx = exprmaps[1][:,:,0]

    Pla = rho*Vx*Vx/(swrho*swvx*swvx)
    return Pla

# Custom expression function                                                                                            
def exprrhocm3(pass_maps):
    # Plot density as cm^-3
    if type(pass_maps[0]) is not list:
        thesemaps = pass_maps # Just a single time step
    else:
        # Multiple time steps were found
        ntimes = len(pass_maps)
        curri = (ntimes-1)/2
        thesemaps = pass_maps[curri]

    thisrho = np.ma.masked_less_equal(thesemaps[0][:,:], 0)
    return thisrho*1.e-6

# Helper function for drawing on existing panel                                                                         
def jetcontours(ax, XmeshXY,YmeshXY, pass_maps):
    # pass_maps is a list of numpy arrays
    # Each array has 2 dimensions [ysize, xsize]
    # or 3 dimensions [ysize, xsize, components]

    # for time averaging, it's a list of lists, where the top level
    # is 2N+1 timesteps with the middle one the requested time step

    # This custom expression returns a map with values of
    # either 0 (solar wind), 0.5 (caviton), or 1.0 (SHFA), calculated against
    # time-averaged background values. This version doesn't do intelligent checks for the
    # format of the incoming data.
    if type(pass_maps[0]) is not list:
        # Not a list of time steps, calculating this value does not make sense.
        print("expected a list of timesteps to average from, but got a single timestep. Exiting.")
        quit()

    # Multiple time steps were found
    ntimes = len(pass_maps)
    curri = (ntimes-1)/2
    thesemaps = pass_maps[curri]

    thisrho = np.ma.masked_less_equal(thesemaps[0][:,:], 0)
    thisv = thesemaps[1][:,:,:]
    thisvx = thesemaps[1][:,:,0]
    thispdyn = thisrho * ( np.linalg.norm(thisv,axis=-1)**2)

    # SW values for Plaschke criterion
    swrho = 1.0e6
    swvx = 750.e3

    # Time-averaged values
    avgrho = np.zeros(np.array(thisrho.shape))
    avgpdyn = np.zeros(np.array(thisrho.shape))
    
    for i in range(ntimes):
        if i==curri: # Exclude current frame from background value averaging
            continue
        nowmaps = pass_maps[i]
        avgrho = np.add(avgrho, nowmaps[0])
        nowpdyn = nowmaps[0] * (np.linalg.norm(nowmaps[1], axis=-1)**2)
        avgpdyn = np.add(avgpdyn, nowpdyn)

    avgrho = np.divide(np.ma.masked_less_equal(avgrho,0), np.array([ntimes-1]))
    avgpdyn = np.divide(np.ma.masked_less_equal(avgpdyn,0), np.array([ntimes-1]))
    
    # Mask valid area of averages
    avgrho = np.ma.masked_less_equal(avgrho, 0)
    avgpdyn = np.ma.masked_less_equal(avgpdyn, 0)

    # Calculate criteria ratios
    Plaschke = thisrho*(thisvx**2)/(swrho*(swvx**2))
    ArcherHorbury = np.divide(thispdyn,avgpdyn)
    Karlsson = np.divide(thisrho,avgrho)
    print("Plaschke ",np.amin(Plaschke), np.amax(Plaschke))
    print("ArcherHorbury ",np.amin(ArcherHorbury), np.amax(ArcherHorbury))
    print("Karlsson ",np.amin(Karlsson), np.amax(Karlsson))

    # draw contours                                                                                                     
    contour_cr1 = ax.contour(XmeshXY,YmeshXY,Plaschke,[0.25],
                             linewidths=1.2, colors='black',label='Plaschke 0.25')
    #contour_cr2 = ax.contour(XmeshXY,YmeshXY,Plaschke,[0.5],
    #                         linewidths=1.2, colors='white',label='Plaschke 0.5')

    contour_cr3 = ax.contour(XmeshXY,YmeshXY,Karlsson,[1.5],
                             linewidths=1.2, colors='magenta',label='Karlsson')

    contour_cr4 = ax.contour(XmeshXY,YmeshXY,ArcherHorbury,[2],
                             linewidths=1.2, colors='blue',label='Archer & Horbury')


fileLocation="/proj/vlasov/2D/ABA/bulk/"
outputLocation=outputdir=os.path.expandvars('$HOME/ABA/')

timetot = [611]
for j in timetot:
    # Source data file                                                                                                  
    bulkname = "bulk."+str(j).rjust(7,'0')+".vlsv"
    print(bulkname)

    pt.plot.plot_colormap(filename=fileLocation+bulkname,
                          run="ABA",
                          colormap='parula',
                          step=j,
                          outputdir=outputLocation+'fig5_',
                          lin=1,
                          expression=exprrhocm3,
                          pass_vars=['rho','v'], pass_times=180,
                          vmin=0.8, vmax=5, 
                          external=jetcontours,
                          boxre=[8,16,-6,6],
                          cbtitle='$n_\mathrm{p}$ [cm$^{-3}$]', 
                          title='', usesci=0, thick=1.2)




