"""
torus9.py
Eric Huang
18/05/2014
"""

import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import mwmatching
import time
import datetime

def main():
    plotCurves([3,5,7,9,11],.08,.14,10,10000) # adjust these parameters
    #plotCurves([3,5,7],.10,.12,10,1000) # adjust these parameters

def plotCurves(Lvalues,pmin,pmax,npoints,N):
    f = open('data.csv','a')
    colormap = plt.cm.gist_ncar
    plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0,0.9,max(Lvalues)*2)])
    for L in Lvalues:
        startTime = time.clock()
        (x,y) = sampleCurve(L,pmin,pmax,npoints,N,f)
        #z = np.polyfit(x,y,int(math.ceil(math.log(npoints*L+1))))
        z = np.polyfit(x,y,2)
        p = np.poly1d(z)
        xp = np.linspace(pmin,pmax,100)
        plt.plot(xp,p(xp))
        plt.errorbar(x,y,xerr=(pmax-pmin)/npoints/math.sqrt(N),yerr=np.sqrt(y*(1-y)/N+.25/N/N),fmt='.',label='$L = %i$'%L)
        t = time.clock()-startTime
        print('Polyfit for L = %i, N = %i, npoints = %i, from %f to %f'%(L,N,npoints,pmin,pmax))
        print(z)
        print('Simulation completed for L = %i in %f seconds'%(L,t))
    #plt.ylim(-0.05,1.05)
    plt.xlabel('Bit flip probability $p$')
    plt.ylabel('Unrecoverable probability $1-p_{recover}$')
    plt.title('Plot of $1-p_{recover}$ vs. $p$')
    plt.legend(loc='upper left')
    fileName = 'Figure%s.pdf'%datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    plt.savefig(fileName)
    plt.show()
    f.close()
        

def sampleCurve(L,pmin,pmax,npoints,N,f):
    pflip = np.empty(0,dtype=float)
    precover = np.empty(0,dtype=float)
    for p in np.linspace(pmin,pmax,npoints):
        startTime = time.clock()
        n = 0
        for i in xrange(N):
            if (generateErrors(L,p)):
                n += 1
        pur = 1-float(n)/N
        pflip = np.append(pflip,p)
        precover = np.append(precover,pur)
        t = time.clock() - startTime
        f.write('%i, %f, %f, %i, %f\n'%(L,p,pur,N,t))
    return (pflip,precover)

def generateErrors(L,p):
    # Generate errors on each edge independently with probability p
    edgesX = np.less(np.random.rand(L,L),p) # Errors on horizontal edges
    edgesY = np.less(np.random.rand(L,L),p) # Errors on vertical edges
    
    A = findSyndromes(edgesX,edgesY,L)
    pairsA = findPairs(A,edgesX,edgesY,L)
    correctErrorsA(edgesX,edgesY,pairsA,L)
    
    A = findSyndromes(edgesX,edgesY,L)
    pairsA = findPairs(A,edgesX,edgesY,L)
    correctErrorsA(edgesX,edgesY,pairsA,L)
    return logicalX(edgesX,L)&logicalZ(edgesY,L)

def findPairs(A,edgesX,edgesY,L):
    # Generate the graphs for input into mwmatching algorithm
    nA = len(A)
    graphEdgesA = [] # List of graph edges corresponding to path lengths A
    for i in xrange(nA-1):
        for j in xrange(i+1,nA):
            graphEdgesA.append((i,j,2*L-minDistance(A[i],A[j],L)))
    matchesA = mwmatching.maxWeightMatching(graphEdgesA)
    pairsA = []
    for i in xrange(len(matchesA)):
        p = [A[i],A[matchesA[i]]]
        p.sort()
        pairsA.append(p)
    # Remove duplicates
    pairsA = dict((x[0], x) for x in pairsA).values()
    return pairsA

def findSyndromes(edgesX,edgesY,L):
    A = np.empty(0,dtype=int) # Syndromes on vertices
    # Find syndromes on vertices
    for x in xrange(L):
        for y in xrange(L):
            if (edgesX[x,y]^edgesY[x,y]
                ^edgesX[(x-1)%L,y]
                ^edgesY[x,(y-1)%L]):
                A = np.append(A,index((x,y),L))
                
    return A
def findSyndromesZ(edgesX,edgesY,L):
    B = np.empty(0,dtype=int)
    for x in xrange(L):
        for y in xrange(L):
            if (edgesX[x,y]^edgesY[x,y]
                ^edgesX[x,(y+1)%L]
                ^edgesY[(x+1)%L,y]):
                B = np.append(B,index((x,y),L))
    return B


def correctErrorsA(edgesX,edgesY,pairsA,L):
    for pair in pairsA:
        drawShortestPathA(edgesX,edgesY,pair,L)

def drawShortestPathA(edgesX,edgesY,pair,L):
    (x0,y0) = coordinates(pair[0],L)
    (x1,y1) = coordinates(pair[1],L)
    dx = x1 - x0
    dy = y1 - y0
    if dx != 0:
        if dx < 0: # make x0 the lower one
            temp = x0
            x0 = x1
            x1 = temp
        if abs(dx) <= L/2: # going through the middle shortest
            xline = range(x0,x1)
        else: # going around edges shortest
            xline = range(x1,L)
            if x0 != 0: # handling edge case
                xline += range(0,x0)
        for x in xline:
            edgesX[x,y0] ^= True # flip spins along horizontal line
    if dy != 0:
        if dy < 0:
            temp = y0
            y0 = y1
            y1 = temp
        if abs(dy) <= L/2:
            yline = range(y0,y1)
        else:
            yline = range(y1,L)
            if y0 != 0:
                yline += (range(0,y0))
        for y in yline:
            edgesY[x0,y] ^= True # flip spins along y line

def logicalX(edgesX,L):
    n = True
    for y in xrange(L):
        n ^= edgesX[0,y]
    return n

def logicalZ(edgesY,L):
    n = True
    for x in xrange(L):
        n ^= edgesY[x,0]
    return n
    
def getMatchingPairs(adjacency):
    return True

def coordinates(i,L):
    return (i%L,i/L)

def index(coord,L):
    return coord[0]+L*coord[1]

def minDistanceAxis(xi,xj,L):
    x0 = abs(xi-xj)
    x1 = L-max(xi,xj)+min(xi,xj)
    return min(x0,x1)

def minDistance(i,j,L):
    (xi,yi) = coordinates(i,L)
    (xj,yj) = coordinates(j,L)
    return minDistanceAxis(xi,xj,L)+minDistanceAxis(yi,yj,L)

def printLattice(A,B,edgesX,edgesY,L):
    for y in xrange(L):
        row1 = ''
        row2 = ''
        for x in xrange(L):
            if index((x,y),L) in A:
                row1 += 'X'
            else:
                row1 += ' '
            if edgesX[x,y]:
                row1 += '.'
            else:
                row1 += ' ' #'0'
            if edgesY[x,y]:
                row2 += '.'
            else:
                row2 += ' ' #'0'

            if index((x,y),L) in B:
                row2 += 'Z'
            else:
                row2 += ' '
        print(row1)
        print(row2)

if __name__ == '__main__':
    main()
