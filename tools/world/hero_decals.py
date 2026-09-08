"""Original projected marks: authored typography, paint wear and drainage stains."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np,json
root=Path(__file__).resolve().parents[2];out=root/'game/assets/textures/hero_decals';out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(4801);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',62)
for name in ['service','warning','stain','repair']:
 im=Image.new('RGBA',(512,512));d=ImageDraw.Draw(im)
 if name=='service':
  d.rectangle((55,65,455,445),outline=(230,224,194,210),width=8);d.text((82,125),'SERVICE',font=font,fill=(230,224,194,230));d.text((185,255),'04',font=font,fill=(230,224,194,230))
 elif name=='warning':
  for i in range(-512,1024,96):d.polygon([(i,95),(i+48,95),(i+320,415),(i+272,415)],fill=(221,155,52,210))
 elif name=='repair':
  d.rounded_rectangle((50,80,460,420),radius=28,fill=(35,38,39,190));d.line((80,125,415,380),fill=(90,86,75,110),width=6)
 else:
  for i in range(70):
   x=int(rng.integers(50,460));y=int(rng.integers(30,190));d.ellipse((x,y,x+int(rng.integers(2,24)),y+int(rng.integers(50,290))),fill=(28,23,16,int(rng.integers(12,50))))
  im=im.filter(ImageFilter.GaussianBlur(9))
 a=np.array(im);wear=rng.random((512,512));a[:,:,3]=(a[:,:,3]*(.65+.35*wear)).astype('uint8');Image.fromarray(a).save(out/(name+'.png'))
# Pavement joints belong in the repeatable surface, not dozens of mesh strips.
base=np.asarray(Image.open(root/'game/assets/textures/hero_surfaces/aggregate.png')).copy();base[:5,:]=35;base[:,:5]=35;base[-1]=base[0];base[:,-1]=base[:,0];Image.fromarray(base).save(out/'pavement.png')
(out/'provenance.json').write_text(json.dumps({'source':'original local procedural graphics and authored text','seed':4801,'resolution':512,'pavement_resolution':1024,'maps':'sRGB color/alpha only; no fabricated material maps','credits':0},indent=2))
print('HERO_DECALS_PASS: four alpha marks and one pavement tile')
