from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
#from matplotlib.colors import LogNorm
import matplotlib.colors as mplcolors
import numpy as np
import matplotlib.ticker as mtik
try:
    import scipy.ndimage
    from scipy.stats import norm
    haveScipy = True
except ImportError:
    haveScipy = False

__all__ = ['plotGTC']


#################### Create a full GTC

def plotGTC(chains, **kwargs):
    r"""Make a great looking Giant Triangle Confusogram (GTC) with one line of code!
    A GTC is a lot like a triangle (or corner) plot, but you get to put as many
    sets of data, and overlay as many truths as you like. That's what can make
    it so *confusing*!

    Parameters
    ----------
    chains : array-like[nDims , samples] or a list[[nDims, samples1], ...]
        All chains (where a chain is [nDims, samples]) in the list must have
        the same number of dimensions. Note: If you are using ``emcee``
        (http://dan.iel.fm/emcee/current/) - and you should! - each element
        of chains is an ``EnsembleSampler.flatchain`` object.

    Keyword Arguments
    -----------------
    weights : array-like[nSamples] or a list[[nSamples1], ...]
        Weights for the sample points. If a 1d array is passed, the same
        weights are used for all dimension in chains. If a list of 1d arrays
        is passed, there must be a weights array for each dimension of
        `chains`. Default weight is 1.

    chainLabels : array-like[nChains]
        A list of text labels describing each chain passed to chains.
        len(chainLabels) must equal len(chains). chainLabels supports LaTex
        commands enclosed in $..$. Additionally, you can pass None as a
        label. Default is ``None``.

    paramNames : list-like[nDims]
        A list of text labels describing each dimension of chains.
        len(paramNames) must equal len(chains[0]). paramNames supports LaTex
        commands enclosed in $..$. Additionally, you can pass None as a
        label. Default is None, however if you pass a ``pandas.DataFrame``
        object, `paramNames` defaults to the ``DataFrame`` column names.

    truths : list-like[nDims] or [[nDims], ...]
        A list of parameter values, one for each parameter in `chains` to hilite
        in the GTC parameter space, or a list of lists of values to hilite in
        the parameter space. For each set of truths passed to `truths`, there
        must be a value corresponding to every dimension in `chains`, although
        any value may be ``None``. Default is ``None``.

    truthLabels : list-like[nTruths]
        A list of labels, one for each list passed to truths. truthLabels
        supports LaTex commands enclosed in $..$. Additionally, you can pass
        ``None`` as a label. Default is ``None``.

    truthColors : list-like[nTruths]
        User-defined colors for the truth lines, must be one per set of
        truths passed to `truths`. Default color is gray ``#4d4d4d``
        for up to three lines.

    truthLineStyles : list-like[nTruths]
        User-defined line styles for the truth lines, must be one per set of
        truths passed to `truths`. Default line styles
        are ``['--',':','dashdot']``.

    priors : list of tuples [(mu1, sigma1), ...]
        Each tuple describes a Gaussian to be plotted over that parameter's
        histogram. The number of priors must equal the number of dimensions
        in `chains`. Default is ``None``.

    plotName : string
        A path to save the GTC to in pdf form. Default is ``None``.

    nConfidenceLevels : int
        The number of contours to plot in the 2d histograms. Each contour
        corresponds to a sigma. May be 1, 2, or 3. Default is 2.

    GaussianConfLevels : bool
        Whether you want non-standard 2d Gaussian "sigma" confidence levels
        instead of the usual 68%, 95%, 99% confidence levels. Default is ``False``.

    nBins : int
        An integer describing the number of bins used to compute the
        histograms. Default is 30.

    smoothingKernel : float
        A number describing the size of the Gaussian smoothing kernel in
        bins. Default is 1. Set to 0 for no smoothing.

    filledPlots : bool
        Whether you want the 2d contours and the 1d histograms to be
        filled. Default is ``True``.

    plotDensity : bool
        Whether you want to see the 2d density of points. Default is ``False``.

    figureSize : float or string
        A number in inches describing the length = width of the GTC, or a
        string indicating a predefined journal setting and whether the
        figure will span one column or the full page width. Default is 70/dpi
        where ``dpi = plt.rcParams['figure.dpi']``. Options to choose from
        are ``'APJ_column'``, ``'APJ_page'``, ``'MNRAS_column'``,
         ``'MNRAS_page'``, ``'AandA_column'``, ``'AandA_page'``.

    panelSpacing : string
        Options are ``'loose'`` or ``'tight'``. Determines whether there is
        some space between the subplots of the GTC or not. Default is
        ``'tight'``.

    legendMarker : string
        Options are ``'All'``, ``'None'``, ``'Auto'``. ``'All'`` and ``'None'``
        force-show or force-hide all label markers. ``'Auto'`` shows label
        markers if two or more truths are plotted.

    paramRanges : list of tuples [nDim]
        Set the boundaries of each paramter range. Must provide a tuples for
        each dimension of `chains`. If ``None`` is provided for a
        parameter, the range defaults to the width of the histogram.
    
    labelRotation : tuple [2]
        Rotate the tick labels by 45 degrees for less overlap. Can be set for
        the x- and y-axis separately. Options are ``(True,True)``,
        ``(True,False)``, ``(False,True)``, ``(False,False)``. Default is
        ``(True,True)``.

    colorsOrder : list-like[nDims]
        The color order for chains passed to `chains`. Default is
        ``['blues', 'greens', 'yellows', 'reds', 'purples']``. Currently,
        ``pygtc`` is limited to these color values, so you can reorder them,
        but can't yet define your own colors.

    do1dPlots : bool
        Whether or not 1d histrograms are plotted on the diagonal. Default
        is ``True``.

    doOnly1dPlot : bool
        Plot only ONE 1d histogram. If this is True, then chains must have
        shape ``(samples,1)``. Default is ``False``.

    mathTextFontSet : string
        Set consistent font family in rcParams. Default is ``stixsans``. Set
        to ``'None'`` to use the setting in your matplotlib rc.

    Returns
    -------
    fig : ``matplotlib.figure`` object
        You can do all sorts of fun things with this in terms of
        customization after it gets returned. If you are using a ``JuPyter``
        notebook with inline plotting enabled, you should assign a variable
        to catch the return or else the figure will plot twice.

    """

    ##### Figure setting

    #Set up some colors
    truthsDefaultColors = ['#4d4d4d', '#4d4d4d', '#4d4d4d']
    truthsDefaultLS = ['--',':','dashdot']
    colorsDict = { 'blues' : ('#4c72b0','#7fa5e3','#b2d8ff'),
                    'greens' : ('#55a868','#88db9b','#bbffce'),
                    'yellows' : ('#f5964f','#ffc982','#fffcb5'),
                    'reds' : ('#c44e52','#f78185','#ffb4b8'),
                    'purples' : ('#8172b2','#b4a5e5','#37d8ff')}
    colorsOrder = ['blues', 'greens', 'yellows', 'reds', 'purples']
    colors = [colorsDict[cs] for cs in colorsOrder]
    priorColor = '#333333'

    #Angle of tick labels
    tickAngle = 45

    #Dictionary of size types or whatever:
    mplPPI = plt.rcParams['figure.dpi'] #Matplotlib dots per inch
    figSizeDict = { 'APJ_column' : 245.26653 / mplPPI,
                    'APJ_page' : 513.11743 / mplPPI,
                    'MNRAS_column' : 240. / mplPPI,
                    'MNRAS_page' : 504. / mplPPI,
                    'AandA_column' : 256.0748 / mplPPI,
                    'AandA_page' : 523.5307 / mplPPI}


    ##### Check the validity of the chains argument:

    # Numpy really doesn't like lists of Pandas DataFrame objects
    # So if it gets one, extract array vals and throw away the rest
    dfColNames = None
    try: # Not a list of DFs, but might be a single DF
        try:
            # Check if single numpy 2d chain
            if chains.ndim == 2:
                chains = [chains]
        except:
            pass

        # Read in column names from Pandas DataFrame if exists
        # Also convert DataFrame to simple numpy array to avoid later conflicts
        if hasattr(chains[0], 'columns'):
            # Set param names from DataFrame column names, can be overridden later
            dfColNames = list(chains[0].columns.values)
            chains = [df.values for df in chains]

    except ValueError: # Probably a list of pandas DFs
        if hasattr(chains[0], 'columns') and hasattr(chains[0], 'values'):
            dfColNames = list(chains[0].columns.values)
            chains = [df.values for df in chains]

    # Get number of chains
    nChains = len(chains)
    assert nChains<=len(colorsOrder), "currently only supports up to "+str(len(colorsOrder))+" chains"

    # Check that each chain looks reasonable (2d shape)
    for i in range(nChains):
        assert len(chains[i].shape)==2, "unexpected shape of chain %d"%(chains[i])

    # Number of dimensions (parameters), check all chains have same nDim
    nDim = len(chains[0][0,:])
    for i in range(nChains):
        nDimi = len(chains[i][0,:])
        assert nDimi==nDim, "chain %d has unexpected number of dimensions %d"%(i,nDimi)

    # Labels for multiple chains, goes in plot legend
    chainLabels = kwargs.pop('chainLabels', None)
    if chainLabels is not None:
        # Convert to list if only one label
        if __isstr(chainLabels):
            chainLabels = [chainLabels]
        # Check that number of labels equals number of chains
        assert len(chainLabels) == nChains, "chainLabels mismatch with number of chains"
        # Check that it's a list of strings
        assert all(__isstr(s) for s in chainLabels), "chainLabels must be list of strings"

    # Label the x and y axes, supports latex
    paramNames = kwargs.pop('paramNames', None)
    if paramNames is not None:
        # Convert to list if only one name
        if __isstr(paramNames):
            paramNames = [paramNames]
        # Check that number of paramNames equals nDim
        assert len(paramNames) == nDim, "paramNames mismatch with number of dimensions"
        # Check that it's a list of strings
        assert all(__isstr(s) for s in paramNames), "paramNames must be list of strings"
    elif dfColNames is not None:
        paramNames = dfColNames

    # Custom parameter range
    paramRanges = kwargs.pop('paramRanges', None)
    if paramRanges is not None:
        assert len(paramRanges)==nDim, "paramRanges must match number of parameters"

    # Rotated tick labels
    labelRotation = kwargs.pop('labelRotation', (True,True))
    
    # User-defined color ordering
    customColorsOrder = kwargs.pop('colorsOrder', None) #Labels for multiple chains, goes in plot legend
    if customColorsOrder is not None:
        # Convert to list if only one entry
        if __isstr(customColorsOrder):
            customColorsOrder = [customColorsOrder]
        lencustomColorsOrder = len(customColorsOrder)
        if not all(color in colorsDict.keys() for color in customColorsOrder):
            raise ValueError("Bad color name in colorsOrder=%s, pick from %s"%(customColorsOrder,colorsDict.keys()))
        colorsOrder[:lencustomColorsOrder] = customColorsOrder[:lencustomColorsOrder]
        colors = [colorsDict[cs] for cs in colorsOrder]

    # Highlight a point (or several) in parameter space by lines
    truthColors = kwargs.pop('truthColors', truthsDefaultColors) #Default supports up to three truths
    truthLineStyles = kwargs.pop('truthLineStyles', truthsDefaultLS)
    truths = kwargs.pop('truths', None)
    if truths is not None:
        # Convert to list if needed
        if len(np.shape(truths))==1:
            truths = [truths]
        truths = np.array(truths)
        assert np.shape(truths)[0]<=len(truthColors), "More truths than available colors. Set colors with truthColors = [colors...]"
        assert np.shape(truths)[0]<=len(truthLineStyles), "More truths than available line styles. Set line styles with truthLineStyles = [ls...]"
        assert np.shape(truths)[1]==nDim, "Each list of truths must match number of parameters"

    # Labels for the different truth lines
    truthLabels = kwargs.pop('truthLabels', None) #Labels for multiple truths, goes in plot legend
    if truthLabels is not None:
        # Convert to list if only one label
        if __isstr(truthLabels):
            truthLabels = [truthLabels]
        # Check that it's a list of strings
        assert all(__isstr(s) for s in truthLabels), "truthLabels must be list of strings"
        assert len(truthLabels) == len(truths), "truthLabels mismatch with number of truths"

    # Show Gaussian PDF on 1d plots (to show Gaussian priors)
    priors = kwargs.pop('priors', None)
    if priors is not None:
        assert haveScipy==True, "You need to have scipy installed to display Gaussian priors"
        assert len(priors)==nDim, "List of priors must match number of parameters"
        for i in range(nDim):
            if priors[i]:
                assert priors[i][1]>0, "Prior width must be positive"

    # Manage the sample point weights
    weights = kwargs.pop('weights', None)
    if weights==None:
        # Set unit weights if no weights are provided
        weights = [np.ones(len(chains[i])) for i in range(nChains)]
    else:
        if len(weights)==len(chains[0]):
            weights = [weights]
        for i in range(nChains):
            assert len(weights[i])==len(chains[i]), "missmatch in chain/weights #%d: len(chain) %d, len(weights) %d"%(i,len(chains[i]),len(weights[i]))

    # Set plotName to save the plot to plotName
    plotName = kwargs.pop('plotName', None) #Um... the name of the plot?!
    if plotName is not None:
        assert __isstr(plotName), "plotName must be a string type"

    # Define which confidence levels to show
    nConfidenceLevels = kwargs.pop('nConfidenceLevels', 2) #How many of the confidence levels to show
    assert nConfidenceLevels in [1,2,3], "nConfidenceLevels must be 1, 2, or 3"

    # 2d confidence levels: Gaussian or (68%, 95%, 99%)
    GaussianConfLevels = kwargs.pop('GaussianConfLevels', False)
    confLevels = (.3173, .0455, .0027)
    if GaussianConfLevels:
        #1d confidence levels
        confLevels = (.6065, .1353, .0111)


    # Data binning and smoothing
    nBins = kwargs.pop('nBins', 30) # Number of bins for 1d and 2d histograms. 30 works...
    smoothingKernel = kwargs.pop('smoothingKernel', 1) #Don't you like smooth data?
    if not haveScipy:
        print "Warning: You don't have Scipy installed. Your curves will not be smoothed."
        smoothingKernel = 0
    if smoothingKernel>=nBins/10:
        print("Wow, that's a huge smoothing kernel! You sure you want its scale to be %.1f percent of the plot?!"%(100.*float(smoothingKernel)/float(nBins)))

    # Filled contours and histograms
    filledPlots = kwargs.pop('filledPlots', True)

    # Filled contours and histograms
    plotDensity = kwargs.pop('plotDensity', False)

    # Figure size: choose size to fit journal, use reasonable default, or provide your own
    figureSize = kwargs.pop('figureSize', None) #Figure size descriptor or figure width=height in inches
    if figureSize is None:
        # If no figure size is given, use resolution of 70 ppp (pixel per panel)
        figureWidth = nDim*70. / mplPPI
    else:
        # User-defined width=height in inches
        if not __isstr(figureSize):
            figureWidth = figureSize
        else:
            # Choose from a couple of presets to fit your publication
            if figureSize in figSizeDict.keys():
                figureWidth = figSizeDict[figureSize]
            else:
                raise ValueError("figureSize %s unknown"%figureSize)

    # Space between panels
    panelSpacing = kwargs.pop('panelSpacing', 'tight')

    # Marker lines in legend
    showLegendMarker = False
    legendMarker = kwargs.pop('legendMarker', 'Auto')
    assert legendMarker in ('All','None','Auto'), "legendMarker must be one of 'All', 'None', 'Auto'"
    if legendMarker=='Auto':
        if truthLabels is not None:
            if len(truthLabels)>1: showLegendMarker = True
    elif legendMarker=='All': showLegendMarker = True

    # Plot 1d histograms
    do1dPlots = kwargs.pop('do1dPlots', True)

    # Plot ONLY 1d histograms
    doOnly1dPlot = kwargs.pop('doOnly1dPlot', False)
    if doOnly1dPlot:
        for i in range(nChains):
            assert chains[i].shape[1]==1, "Provide chains of shape(Npoints,1) if you only want the 1d histogram"
        do1dPlots = True

    # Set font in rcParams
    mathTextFontSet = kwargs.pop('mathTextFontSet', 'stixsans')
    if not mathTextFontSet=='None':
        plt.rcParams['mathtext.fontset'] = mathTextFontSet

    # Check to see if there are any remaining keyword arguments
    keys = ''
    for key in iter(kwargs.keys()):
        keys = keys + key + ' '
        raise NameError("illegal keyword arguments: " + keys)



    ##### Define colormap
    myColorMap = setCustomColorMaps(colors)

    ##### Matplotlib and figure settings
    axisColor = '#333333'
    # Create the figure, and empty list for first column / last row
    fig = plt.figure(figsize=(figureWidth,figureWidth))
    axV, axH = [], []

    # These are needed to compute the confidence levels
    nBinsFlat = np.linspace(0., nBins**2, nBins**2)

    # Left and right panel boundaries
    panelXrange = np.empty((nDim,2))
    xTicks, yTicks = nDim*[None], nDim*[None]

    ########## 2D contour plots
    if not doOnly1dPlot:
        for i in range(nDim): # row
            for j in range(nDim): # column
                if j<i:
                    ##### Create subplot
                    if do1dPlots:
                        ax = fig.add_subplot(nDim,nDim,(i*nDim)+j+1)
                    else:
                        ax = fig.add_subplot(nDim-1,nDim-1,((i-1)*(nDim-1))+j+1)

                    ##### Draw contours and truths
                    # Extract 2d chains
                    chainsForPlot2D = [[chains[k][:,j], chains[k][:,i]] for k in range(nChains)]
                    # Extract 2d truths
                    truthsForPlot2D = None
                    if truths is not None:
                        truthsForPlot2D = [[truths[k,i], truths[k,j]] for k in range(len(truths))]
                    # Plot!
                    ax = __plot2d(ax, nChains, chainsForPlot2D, weights, nBins,
                                nBinsFlat, smoothingKernel, filledPlots, colors,
                                nConfidenceLevels, confLevels, truthsForPlot2D,
                                truthColors, truthLineStyles, plotDensity, myColorMap)

                    ##### Range
                    if paramRanges is not None:
                        if paramRanges[j]:
                            ax.set_xlim(paramRanges[j][0],paramRanges[j][1])
                        if paramRanges[i]:
                            ax.set_ylim(paramRanges[i][0],paramRanges[i][1])

                    ##### Tick labels without offset and scientific notation
                    ax.get_xaxis().get_major_formatter().set_useOffset(False)
                    ax.get_xaxis().get_major_formatter().set_scientific(False)
                    ax.get_yaxis().get_major_formatter().set_useOffset(False)
                    ax.get_yaxis().get_major_formatter().set_scientific(False)

                    ##### x-labels at bottom of plot only
                    if i==nDim-1:
                        if paramNames is not None:
                            ax.set_xlabel(paramNames[j], fontsize=9)
                    else:
                        ax.get_xaxis().set_ticklabels([])

                    ##### y-labels for left-most panels only
                    if j==0:
                        if paramNames is not None:
                            ax.set_ylabel(paramNames[i], fontsize=9)
                    else:
                        ax.get_yaxis().set_ticklabels([])

                    ##### Panel layout
                    ax.grid(False)
                    #ax.set_axis_bgcolor('none')
                    for axis in ['top','bottom','left','right']:
                        ax.spines[axis].set_color(axisColor)
                        ax.spines[axis].set_linewidth(1)

                    ##### Global tick properties
                    ax.tick_params(direction='in', pad=4, colors=axisColor, size=4, width=.5, labelsize=6)

                    ##### x limits to be applied to 1d histograms
                    panelXrange[j] = ax.get_xlim()

                    ##### Ticks x axis
                    if xTicks[j] is None:
                        # 5 ticks max
                        ax.xaxis.set_major_locator(mtik.MaxNLocator(5))
                        # Remove xticks that are too close (5% of panel size) to panel edge
                        deltaX = panelXrange[j,1]-panelXrange[j,0]
                        LoHi = (panelXrange[j,0]+.05*deltaX, panelXrange[j,1]-.05*deltaX)
                        tickLocs = ax.xaxis.get_ticklocs()
                        idx = np.where((tickLocs>LoHi[0])&(tickLocs<LoHi[1]))[0]
                        xTicks[j] = tickLocs[idx]
                    ax.xaxis.set_ticks(xTicks[j])

                    ##### Ticks y axis
                    if yTicks[i] is None:
                        # 5 ticks max
                        ax.yaxis.set_major_locator(mtik.MaxNLocator(5))
                        # Remove xticks that are too close (5% of panel size) to panel edge
                        panelYrange = ax.get_ylim()
                        deltaY = panelYrange[1]-panelYrange[0]
                        LoHi = (panelYrange[0]+.05*deltaY, panelYrange[1]-.05*deltaY)
                        tickLocs = ax.yaxis.get_ticklocs()
                        idx = np.where((tickLocs>LoHi[0])&(tickLocs<LoHi[1]))[0]
                        yTicks[i] = tickLocs[idx]
                    ax.yaxis.set_ticks(yTicks[i])

                    ##### Rotate tick labels
                    for xLabel in ax.get_xticklabels():
                        if labelRotation[0]:
                            xLabel.set_rotation(tickAngle)
                        if (any(xTicks[j]>=1000))|(any(xTicks[j]<=-100)):
                            xLabel.set_horizontalalignment('right')
                    for yLabel in ax.get_yticklabels():
                        if labelRotation[1]:
                            yLabel.set_rotation(tickAngle)
                        if (any(yTicks[i]>=1000))|(any(yTicks[i]<=-100)):
                            yLabel.set_verticalalignment('top')

                    ##### First column and last row are needed to align labels
                    if j==0:
                        axV.append(ax)
                    if i==nDim-1:
                        axH.append(ax)




    if do1dPlots:
        ########## 1D histograms
        for i in range(nDim):
            ##### Create subplot
            ax = fig.add_subplot(nDim,nDim,(i*nDim)+i+1)

            ##### Plot histograms, truths, Gaussians
            # Extract 1d chains
            chainsForPlot1D = [chains[k][:,i] for k in range(nChains)]
            # Extract 1d truths
            truthsForPlot1D = None
            if truths is not None:
                truthsForPlot1D = [truths[k,i] for k in range(len(truths))]
            # Extract 1d prior
            prior1d = None
            if priors is not None:
                if priors[i] and priors[i][1]>0:
                    prior1d = priors[i]
            # Plot!
            ax = __plot1d(ax, nChains, chainsForPlot1D, weights, nBins,
                        smoothingKernel, filledPlots, colors, truthsForPlot1D,
                        truthColors, truthLineStyles, prior1d, priorColor)


            ##### Panel layout
            ax.grid(False)
            ax.set_axis_bgcolor('w')
            for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_color(axisColor)
                ax.spines[axis].set_linewidth(1)

            ##### Global tick properties
            ax.tick_params(direction='in', pad=4, colors=axisColor, size=4, width=.5, labelsize=6)

            ##### Tick labels without offset and scientific notation
            ax.get_xaxis().get_major_formatter().set_useOffset(False)
            ax.get_xaxis().get_major_formatter().set_scientific(False)

            ##### No ticks or labels on y-axes, lower limit 0
            ax.yaxis.set_ticks([])
            ax.set_ylim(bottom=0)
            ax.xaxis.set_ticks_position('bottom')

            ##### x-label for bottom-right panel only
            if i==nDim-1:
                if paramNames is not None:
                    ax.set_xlabel(paramNames[i], fontsize=9)
            else:
                ax.set_xlim(panelXrange[i])
                ax.get_xaxis().set_ticklabels([])

            ##### Ticks x axis
            if i==nDim-1:
                # 5 ticks max
                ax.xaxis.set_major_locator(mtik.MaxNLocator(5))
                # Remove xticks that are too close (5% of panel size) to panel edge
                panelXrange[i] = ax.get_xlim()
                deltaX = panelXrange[i,1]-panelXrange[i,0]
                LoHi = (panelXrange[i,0]+.05*deltaX, panelXrange[i,1]-.05*deltaX)
                tickLocs = ax.xaxis.get_ticklocs()
                idx = np.where((tickLocs>LoHi[0])&(tickLocs<LoHi[1]))[0]
                xTicks[i] = tickLocs[idx]
            ax.xaxis.set_ticks(xTicks[i])

            ##### Rotate tick labels
            for xLabel in ax.get_xticklabels():
                if labelRotation[0]:
                    xLabel.set_rotation(tickAngle)
                if (any(xTicks[i]>=1000))|(any(xTicks[i]<=-100)):
                    xLabel.set_horizontalalignment('right')

            ##### y label for top-left panel
            if i==0:
                if doOnly1dPlot:
                    ax.set_ylabel('Probability')
                elif paramNames is not None:
                    ax.set_ylabel(paramNames[i], fontsize=9)

            ##### First column and last row are needed to align labels
            if i==0:
                axV.append(ax)
            elif i==nDim-1:
                axH.append(ax)



    ########## Align labels if there is more than one panel
    if len(axH)>1:
        fig.canvas.draw()
        bboxSize = np.empty(len(axH))

        ##### x labels
        # Get label length of the bottom row
        for i in range(len(axH)):
            bboxTickLabel = axH[i].xaxis.get_ticklabel_extents(fig.canvas.renderer)[0].get_points()
            bboxSize[i] = bboxTickLabel[1,1]-bboxTickLabel[0,1]
            panelWidth = axH[i].get_window_extent().transformed(fig.dpi_scale_trans.inverted()).width
        # Apply longest spacing to all panels in last row
        longestTickLabel = 3+np.amax(bboxSize)
        loc = (longestTickLabel/mplPPI/panelWidth)
        for i in range(len(axH)):
            axH[i].get_xaxis().set_label_coords(.5, -loc)


        ##### y labels
        # Get label length of the left column
        for i in range(len(axV)):
            bboxTickLabel = axV[i].yaxis.get_ticklabel_extents(fig.canvas.renderer)[0].get_points()
            bboxSize[i] = bboxTickLabel[1,0]-bboxTickLabel[0,0]
            panelHeight = axV[i].get_window_extent().transformed(fig.dpi_scale_trans.inverted()).height
        # Apply longest spacing to all panels in first column
        longestTickLabel = 2+np.amax(bboxSize)
        loc = (longestTickLabel/mplPPI/panelHeight)
        for i in range(len(axV)):
            axV[i].get_yaxis().set_label_coords(-loc, .5)




    ########## Legend
    if (chainLabels is not None) or (truthLabels is not None):
        ##### Dummy plot for label line color
        labelColors = []
        if not doOnly1dPlot:
            ax = fig.add_subplot(nDim,nDim,nDim)
            ax.axis('off')
        else:
            labelPanelRange = ax.get_xlim()

        ##### Label the data sets
        if chainLabels is not None:
            # Label for each chain
            for k in range(nChains):
                ax.plot(0,0, color=colors[k][0], lw=4, label=chainLabels[k])
                labelColors.append(colors[k][0])

        ##### Label the truth lines
        if truthLabels is not None:
            # Label for each truth
            for k in range(len(truthLabels)):
                ax.plot(0, 0, lw=1, color=truthColors[k], label=truthLabels[k], ls=truthsDefaultLS[k])
                labelColors.append(truthColors[k])

        ##### Set xlim back to what the data wanted
        if doOnly1dPlot:
            ax.set_xlim(labelPanelRange)


        ##### Legend and label colors according to plot
        leg = plt.legend(loc='upper right', fancybox=True, handlelength=3, fontsize=9)
        leg.get_frame().set_alpha(0.)
        for color,text in zip(labelColors,leg.get_texts()):
            text.set_color(color)
        # Remove markers in legend
        if showLegendMarker is not True:
            for item in leg.legendHandles:
                item.set_visible(False)



    ########## Panel spacing, save to file (optional) and return

    # Space between panels
    space = 0
    if panelSpacing=='loose':
        space = .05
    fig.subplots_adjust(hspace=space)
    fig.subplots_adjust(wspace=space)

    # Save figure
    if plotName is not None:
        plt.savefig(plotName, bbox_inches='tight')

    # Revert to default rcParams
    #plt.rcdefaults()

    return fig



#################### Create single 1d panel

def __plot1d(ax, nChains, chains1d, weights, nBins, smoothingKernel,
            filledPlots, colors, truths1d, truthColors, truthLineStyles,
            prior1d, priorColor):
    r"""Plot the 1d histogram and optional prior.

    Parameters
    ----------
    ax : matplotlib.pyplot.axis
        Axis on which to plot the histogram(s)

    nChains : int
        How many chains are you passing?

    chains1d : list-like
        A list of `nChains` 1d chains: [chain1, chain2, etc...]

    weights : list-like
        A list of `nChains` weights.

    nBins : int
        How many histogram bins?

    smoothingKernel : int
        Number of bins to smooth over

    filledPlots : bool
        Want the area under the curve filled in?

    colors : list-like
        List of `nChains` tuples. Each tuple must have at least two colors.

    truths1d : list-like
        List of truths to overplot on the histogram.

    truthColors : list-like
        One color for each truth.

    truthLineStyles : list-like
        One matplotlib linestyle specifier per truth.

    prior1d : tuple
        Normal distribution paramters (mu, sigma)

    priorColor : color
        The color to plot the prior.

    Note
    ----
    You should really just call this from the plotGTC function unless you have
    a strong need to work only with an axis instead of a figure...

    """

    ##### 1D histogram
    plotData = []
    # With smoothing
    if smoothingKernel>0:
        for k in reversed(range(nChains)):
            # create 1d histogram
            hist1d, edges = np.histogram(chains1d[k], weights=weights[k], normed=True, bins=nBins)
            # Bin center between histogram edges
            centers = (edges[1:]+edges[:-1])/2
            # Filter data
            plotData.append( scipy.ndimage.gaussian_filter1d((centers,hist1d), sigma=smoothingKernel) )
            if filledPlots:
                # Filled smooth histogram
                plt.fill_between(plotData[-1][0], plotData[-1][1], 0, color=colors[k][1])
        # Line for hidden histogram
        for k in reversed(range(nChains)):
            plt.plot(plotData[nChains-1-k][0], plotData[nChains-1-k][1], lw=1, ls='-', color=colors[k][1])

    # No smoothing
    else:
        if filledPlots:
            for k in reversed(range(nChains)):
            # Filled stepfilled histograms
                plt.hist(chains1d[k], weights=weights[k], normed=True, bins=nBins, histtype='stepfilled', edgecolor='None', color=colors[k][1])
        for k in reversed(range(nChains)):
            # Step curves for hidden histogram(s)
            plt.hist(chains1d[k], weights=weights[k], normed=True, bins=nBins, histtype='step', color=colors[k][1])

    ##### Truth line
    if truths1d is not None:
        for k in range(len(truths1d)):
            if truths1d[k] is not None:
                ax.axvline(truths1d[k], lw=1, color=truthColors[k], ls=truthLineStyles[k])

    ##### Gaussian prior
    if prior1d is not None:
        # Plot prior in -4 to +4 sigma range
        arr = np.linspace(prior1d[0]-4*prior1d[1], prior1d[0]+4*prior1d[1], 40)
        plt.plot(arr,norm.pdf(arr,prior1d[0],prior1d[1]), lw=1, color=priorColor)

    return ax



#################### Create single 2d panel

def __plot2d(ax, nChains, chains2d, weights, nBins, nBinsFlat, smoothingKernel,
            filledPlots, colors, nConfidenceLevels, confLevels, truths2d,
            truthColors, truthLineStyles, plotDensity, myColorMap):
    r"""Plot a 2D histogram in a an axis object and return the axis with plot.

    Parameters
    ----------

    ax : matplotlib.pyplot.axis
        The axis on which to plot the 2D histogram

    nChains : int
        The number of chains to plot

    chains2d : list-like
        A list of pairs of chains in the form:
        [[chain1_x, chain1_y], [chain2_x, chain2_y], ...].

    weights : list-like
        Weights for the chains2d.

    nBins : int
        Number of bins for the 2d histogram

    nBinsFlat : int
        nBinsFlat = np.linspace(0., nBins**2, nBins**2)

    smoothingKernel : int
        number describing the size of the Gaussian smoothing kernel in
        bins. Default is 1. Set to 0 for no smoothing.

    filledPlots : bool
        Just contours, or filled contours?

    colors : list-like
        List of `nChains` tuples. Each tuple must have at least nConfidenceLevels
        colors.

    nConfidenceLevels : int {2,1,3}
        How many confidence levels? Default is 2.

    confLevels : list-like
        List of at least `nConfidenceLevels` values for confidence levels.

    truths2d : list-like
        A list of nChains tuples of the form: [(truth1_x, truth1_y), etc...].

    truthColors : list-like
        A list of colors for the truths.

    truthLineStyles : list-like
        A list of matplotlib linestyle descriptors, one for each truth.

    plotDensity : bool
        Whether to show points density in addition to contours. Default is False.

    myColorMap : list-like
        A list of `nChains` matplotlib colormap specifiers, or actual colormaps.

    Note
    ----
    You should really just call this from the plotGTC function unless you have
    a strong need to work only with an axis instead of a figure...

    """
    # Empty arrays needed below
    chainLevels = np.ones((nChains,nConfidenceLevels+1))
    extents = np.empty((nChains,4))

    ##### The filled contour plots
    plotData = []
    # Draw filled contours in reversed order to have first chain in list on top
    for k in reversed(range(nChains)):
        # Create 2d histogram
        hist2d, xedges, yedges = np.histogram2d(chains2d[k][0], chains2d[k][1], weights=weights[k], bins=nBins)
        # image extent, needed below for contour lines
        extents[k] = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        # Normalize
        hist2d = hist2d/np.sum(hist2d)
        # Cumulative 1d distribution
        histOrdered = np.sort(hist2d.flat)
        histCumulative = np.cumsum(histOrdered)

        # Compute confidence levels (from low to high for technical reasons)
        for l in range(nConfidenceLevels):
            # Find location of confidence level in 1d histCumulative
            temp = np.interp(confLevels[l], histCumulative, nBinsFlat)
            # Find "height" of confidence level
            chainLevels[k][nConfidenceLevels-1-l] = np.interp(temp, nBinsFlat, histOrdered)

        # Apply Gaussian smoothing and plot filled contours if requested
        if smoothingKernel>0:
            plotData.append( scipy.ndimage.gaussian_filter(hist2d.T, sigma=smoothingKernel) )
        else:
            plotData.append( hist2d.T )
        if filledPlots:
            xbins = (xedges[1:]+xedges[:-1])/2
            ybins = (yedges[1:]+yedges[:-1])/2
            ax.contourf(xbins, ybins, plotData[-1], levels=chainLevels[k], colors=colors[k][:nConfidenceLevels][::-1])

        # Plot density
        if plotDensity:
            if filledPlots:
                ax.imshow(hist2d.T, extent=extents[k], origin='lower', cmap=myColorMap[k], aspect='auto', clim=(0,chainLevels[k][0]))
            else:
                ax.imshow(hist2d.T, extent=extents[k], origin='lower', cmap=myColorMap[k], aspect='auto')


    ###### Draw contour lines in order to see contours lying on top of each other
    for k in range(nChains):
        for l in range(nConfidenceLevels):
            ax.contour(plotData[nChains-1-k], [chainLevels[k][nConfidenceLevels-1-l]], extent=extents[k], origin='lower', linewidths=1, colors=colors[k][l])

    ##### Truth lines
    if truths2d is not None:
        for k in range(len(truths2d)):
            # horizontal line
            if truths2d[k][0] is not None:
                ax.axhline(truths2d[k][0], lw=1, color=truthColors[k], ls=truthLineStyles[k])
            # vertical line
            if truths2d[k][1] is not None:
                ax.axvline(truths2d[k][1], lw=1, color=truthColors[k], ls=truthLineStyles[k])

    return ax

#################### Custom colormap for density plots
def CustomCmap(to_rgb):
    # from color r,g,b
    r1,g1,b1 = 1,1,1
    # to color r,g,b
    r2,g2,b2 = mplcolors.hex2color(to_rgb)

    cdict = {'red': ((0, r1, r1), (1, r2, r2)),
           'green': ((0, g1, g1), (1, g2, g2)),
           'blue': ((0, b1, b1), (1, b2, b2))}

    cmap = LinearSegmentedColormap('custom_cmap', cdict)
    return cmap

def setCustomColorMaps(colors):
    customColorMaps = [CustomCmap(color[0]) for color in colors]
    return customColorMaps

#################### Check for basestring in python 2/3 compatible way
def __isstr(s):
    try:
        isinstance("", basestring)
        return isinstance(s, basestring)
    except NameError:
        return isinstance(s, str)
