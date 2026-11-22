"""usage: clipper.py raw.ts out.mp4 start dur credit platform -> prints JSON {title,tags,lang}"""
import sys,os,json,subprocess,re
from faster_whisper import WhisperModel
src,out,start,dur,credit,platform=sys.argv[1:7]
run=lambda *a:subprocess.run(a,check=True,capture_output=True)
wav=out+'.wav'
run('ffmpeg','-y','-ss',start,'-t',dur,'-i',src,'-vn','-ac','1','-ar','16000',wav)
model=WhisperModel(os.environ.get('WHISPER','small'),compute_type='int8')
segs,info=model.transcribe(wav,word_timestamps=True,vad_filter=True)
segs=list(segs);words=[w for s in segs for w in s.words];os.remove(wav)
lang=info.language if segs else 'en';ar=lang=='ar'
font='Noto Sans Arabic' if ar else 'Arial'
esc=lambda t:re.sub(r'[{}\\]','',t.strip())
ts=lambda x:'%d:%02d:%05.2f'%(x//3600,x%3600//60,x%60)
text=' '.join(s.text.strip() for s in segs)
hook=' '.join(text.split()[:8]) or ('استنى للآخر 😂' if ar else 'WAIT FOR IT 😂')
if not ar:hook=hook.upper()
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV
Style: Cap,{font},84,&H00FFFFFF,&H00000000,&H00000000,1,1,7,0,2,60,60,520
Style: Hook,{font},66,&H00FFFFFF,&H00B040FF,&H00B040FF,1,3,14,0,8,70,70,170
Style: Cred,{font},46,&H00FFFFFF,&H00000000,&H00000000,1,1,4,0,2,60,60,130
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
Dialogue: 1,{ts(0)},{ts(float(dur))},Hook,,0,0,0,,{esc(hook)}
Dialogue: 1,{ts(0)},{ts(float(dur))},Cred,,0,0,0,,@{esc(credit)} · {platform}
"""
for i in range(0,len(words),4):                       # word-by-word: 4-word line, active word highlighted
    ch=words[i:i+4]
    for j,w in enumerate(ch):
        end=ch[j+1].start if j+1<len(ch) else w.end
        t=' '.join(('{\\c&H00E5FF&}%s{\\c&HFFFFFF&}' if k==j else '%s')%esc(x.word) for k,x in enumerate(ch))
        ass+=f"Dialogue: 0,{ts(w.start)},{ts(max(end,w.start+.1))},Cap,,0,0,0,,{t}\n"
open(out+'.ass','w',encoding='utf8').write(ass)
fc="[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,ass="+out+".ass[v]"
run('ffmpeg','-y','-ss',start,'-t',dur,'-i',src,'-filter_complex',fc,'-map','[v]','-map','0:a?','-c:v','libx264','-preset','veryfast','-crf','23','-c:a','aac','-b:a','128k','-movflags','+faststart',out)
os.remove(out+'.ass')
tags=' '.join(['#clips',f'#{platform}',f'#{re.sub(r"[^A-Za-z0-9_]","",credit)}','#viral','#fyp']+(['#كليب'] if ar else ['#shorts']))
title=hook.strip('… ')+' 🔥'
open(out[:-4]+'.txt','w',encoding='utf8').write(title+'\n'+tags)
print(json.dumps({'title':title,'tags':tags,'lang':lang},ensure_ascii=False))
