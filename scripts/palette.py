#!/usr/bin/env python3
"""Design + validate the categorical palette (--s1..--s8) in src/shell.html.

Prints hex values per theme, adjacent-slot OKLab dE under normal vision and
protan/deutan/tritan simulation (Machado 2009), and contrast vs the surface.
Edit THEMES, run, then copy the hex values into the .viz-root custom properties.

    python scripts/palette.py
"""
import math
def lin(c): c/=255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def delin(c): c=12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055; return max(0,min(255,round(c*255)))
def oklch2rgb(L,C,h):
    a=C*math.cos(math.radians(h)); b=C*math.sin(math.radians(h))
    l=(L+0.3963377774*a+0.2158037573*b)**3; m=(L-0.1055613458*a-0.0638541728*b)**3; s=(L-0.0894841775*a-1.2914855480*b)**3
    return [delin(4.0767416621*l-3.3077115913*m+0.2309699292*s),delin(-1.2684380046*l+2.6097574011*m-0.3413193965*s),delin(-0.0041960863*l-0.7034186147*m+1.7076147010*s)]
def oklab(rgb):
    r,g,b=[lin(x) for x in rgb]
    l=(0.4122214708*r+0.5363325363*g+0.0514459929*b)**(1/3); m=(0.2119034982*r+0.6806995451*g+0.1073969566*b)**(1/3); s=(0.0883024619*r+0.2817188376*g+0.6299787005*b)**(1/3)
    return [0.2104542553*l+0.7936177850*m-0.0040720468*s,1.9779984951*l-2.4285922050*m+0.4505937099*s,0.0259040371*l+0.7827717662*m-0.8086757660*s]
# Machado et al. 2009, severity 1.0, applied in linear RGB
CVD={'protan':[[0.152286,1.052583,-0.204868],[0.114503,0.786281,0.099216],[-0.003882,-0.048116,1.051998]],
     'deutan':[[0.367322,0.860646,-0.227968],[0.280085,0.672501,0.047413],[-0.011820,0.042940,0.968881]],
     'tritan':[[1.255528,-0.076749,-0.178779],[-0.078411,0.930809,0.147602],[0.004733,0.691367,0.303900]]}
def sim(rgb,M):
    v=[lin(x) for x in rgb]; return [delin(max(0,min(1,sum(M[i][j]*v[j] for j in range(3))))) for i in range(3)]
def dE(a,b): A,B=oklab(a),oklab(b); return 100*math.dist(A,B)
def lum(rgb): r,g,b=[lin(x) for x in rgb]; return 0.2126*r+0.7152*g+0.0722*b
def cr(a,b): la,lb=sorted([lum(a),lum(b)],reverse=True); return (la+0.05)/(lb+0.05)
hexs=lambda c:'#%02x%02x%02x'%tuple(c)
def hexrgb(h): h=h.lstrip('#'); return [int(h[i:i+2],16) for i in (0,2,4)]
def mix(c1,c2,t):
    a,b=oklab(c1),oklab(c2); L,A,B=[x*t+y*(1-t) for x,y in zip(a,b)]
    # oklab->rgb
    l=(L+0.3963377774*A+0.2158037573*B)**3; m=(L-0.1055613458*A-0.0638541728*B)**3; s=(L-0.0894841775*A-1.2914855480*B)**3
    return [delin(4.0767416621*l-3.3077115913*m+0.2309699292*s),delin(-1.2684380046*l+2.6097574011*m-0.3413193965*s),delin(-0.0041960863*l-0.7034186147*m+1.7076147010*s)]

# slot order alternates dark/light so ring neighbours separate on lightness
THEMES={
 'light':{'surface':'#fcfcfb','slots':[(0.47,0.085,252),(0.76,0.045,240),(0.57,0.035,255),(0.84,0.025,248),(0.40,0.045,258),(0.67,0.070,242),(0.53,0.015,250),(0.79,0.060,232)]},
 'dark': {'surface':'#1a1a19','slots':[(0.50,0.085,252),(0.74,0.045,240),(0.59,0.035,255),(0.81,0.025,248),(0.42,0.045,258),(0.67,0.070,242),(0.55,0.015,250),(0.78,0.060,232)]},
}
for name,t in THEMES.items():
    surf=hexrgb(t['surface']); cols=[oklch2rgb(*s) for s in t['slots']]
    print(f"\n{name}: "+' '.join(hexs(c) for c in cols))
    pairs=[(i,(i+1)%8) for i in range(8)]
    for mode in ['normal','protan','deutan','tritan']:
        f=(lambda c:c) if mode=='normal' else (lambda c,M=CVD[mode]:sim(c,M))
        ds=[dE(f(cols[i]),f(cols[j])) for i,j in pairs]
        print(f"  adjacent dE {mode:<7} min {min(ds):5.1f}  (" + ' '.join(f'{d:.0f}' for d in ds)+")")
    print("  contrast vs surface:", ' '.join(f'{cr(c,surf):.2f}' for c in cols))
    print("  max chroma:", max(s[1] for s in t['slots']))
    # depth tints actually rendered (step .16 cap .5, band .22)
    worst=min(cr(mix(c,surf,1-min(0.5,2*0.16)),surf) for c in cols)
    print(f"  worst outer-ring (depth+2) contrast vs surface {worst:.2f}")
