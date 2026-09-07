"""Original low-level placeholder loops. Standard library only; no downloads."""
import array,json,math,random,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
destination=ROOT/'game/assets/audio';destination.mkdir(parents=True,exist_ok=True)
rate=22050;count=rate*4;rng=random.Random(8412);reports={}
for kind in ('wind','city','rain','interior','event'):
    values=[];low=0.0
    for i in range(count):
        t=i/rate;noise=rng.uniform(-1,1);low=.96*low+.04*noise
        if kind=='wind':v=low*.3*(.7+.3*math.sin(2*math.pi*t/4))
        elif kind=='city':v=.035*math.sin(2*math.pi*60*t)+.016*math.sin(2*math.pi*120*t)+low*.05
        elif kind=='rain':v=noise*.075+low*.1
        elif kind=='interior':v=low*.12+.02*math.sin(2*math.pi*90*t)
        else:v=.08*math.sin(2*math.pi*(330+30*math.sin(t*2))*t)*math.exp(-t*3)
        # Smooth loop endpoints / event envelope; no abrupt sample discontinuity.
        fade=min(1,i/440,(count-1-i)/440)
        values.append(int(max(-.9,min(.9,v*fade))*32767))
    path=destination/(kind+'.wav')
    with wave.open(str(path),'wb') as file:
        file.setnchannels(1);file.setsampwidth(2);file.setframerate(rate);file.writeframes(array.array('h',values).tobytes())
    reports[kind]={'samples':count,'peak':max(abs(v) for v in values)/32767,'rms':math.sqrt(sum(v*v for v in values)/count)/32767,'source':'original procedural placeholder, seed 8412'}
    assert reports[kind]['peak']<.9 and reports[kind]['rms']>0
(destination/'provenance.json').write_text(json.dumps(reports,indent=2))
print('AUDIO_SYNTHESIS_PASS: five original non-clipping PCM fixtures')
