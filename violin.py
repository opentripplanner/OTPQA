# -*- coding: utf-8 -*-
# based on http://pyinsci.blogspot.fr/2009/09/violin-plot-with-matplotlib.html
# by Flavio Coelho 

from matplotlib.pyplot import figure, show
from scipy.stats import gaussian_kde
from numpy.random import normal
from numpy import arange

def violin_plot(data, bp=False, scale=False, labels=None):
    '''
    create violin plots on an axis
    '''
    fig=figure()
    ax = fig.add_subplot(111)
    dist = len(data)
    w = min(0.15*max(dist,1.0),0.5)
    for p,d in enumerate(data):
        k = gaussian_kde(d) #calculates the kernel density
        m = k.dataset.min() #lower bound of violin
        M = k.dataset.max() #upper bound of violin
        x = arange(m,M,(M-m)/100.) # support for violin
        v = k.evaluate(x) #violin profile (density curve)
        if scale :
            v = v/v.max()*w #scaling the violin to the available space
        ax.fill_betweenx(x,p,v+p,facecolor='y',alpha=0.3)
        ax.fill_betweenx(x,p,-v+p,facecolor='y',alpha=0.3)
    if bp:
        ax.boxplot(data,notch=1,positions=range(len(data)),vert=1)
    if labels != None :
        ax.set_xticklabels(labels)
    show()

if __name__=="__main__":
    pos = range(5)
    data = [normal(size=100) for i in pos]
    violin_plot(data, bp=True, labels=['0xabc05','8cf9b3','af77c3','91b3cf','233c2a', 'extra label'])

