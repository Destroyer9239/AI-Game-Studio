"""Original periodic authored surface fields; normals derive from explicit microheight."""
from pathlib import Path
import numpy as np
from PIL import Image
import json
ROOT=Path(__file__).resolve().parents[2]; out=ROOT/'game/assets/textures/hero_surfaces';out.mkdir(parents=True,exist_ok=True)
n=1024;y,x=np.mgrid[0:n,0:n]/(n-1)*2*np.pi
rng=np.random.default_rng(7182);field=np.zeros((n,n))
for i in range(48):
 a,b=rng.integers(6,180,2);field+=np.sin(a*x+b*y+rng.uniform(0,6.28))/(1+i*.25)
field/=np.max(np.abs(field));height=field*.00012
# One texture repeat represents two meters. This is authored relief, not inferred depth.
dy,dx=np.gradient(height,2/(n-1));normal=np.stack([-dx,dy,np.ones_like(dx)],2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
for name,data in {'normal':np.round((normal*.5+.5)*255),'roughness':np.round((.75+field*.12)*255),'aggregate':np.round((.45+field*.12)*255)}.items():
 data=np.clip(data,0,255).astype('uint8');data[-1]=data[0];data[:,-1]=data[:,0];Image.fromarray(data).save(out/(name+'.png'))
(out/'material.json').write_text(json.dumps({'source':'original seeded analytic aggregate microrelief','seed':7182,'resolution':1024,'repeat_m':2,'height_amplitude_m':.00012,'normal':'OpenGL','roughness':'authored .63-.87','maps':'linear data; aggregate is an artistic tint field','credits':0},indent=2))
print('HERO_SURFACE_PASS')
