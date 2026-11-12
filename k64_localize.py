"""Japanese Rev 3 Kirby 64 localization workspace: fixed-size image/font/text edits."""
import argparse
import hashlib
import html
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from k64_images import decode, encode, preview

HERE=Path(__file__).resolve().parent
BASE_SHA1='03257c820b7705400c32bde1bcc3161c55814605'
ROWS=json.loads((HERE/'data/image_blocks.json').read_text(encoding='utf-8'))
IMAGES={r['id']:r for r in ROWS if 'format' in r}
STRINGS={r['id']:r for r in json.loads((HERE/'data/strings.json').read_text(encoding='utf-8'))}
FONTS=json.loads((HERE/'data/fonts.json').read_text(encoding='utf-8'))
PRINTF=re.compile(r"%[-+ #0']*(?:\d+|\*)?(?:\.(?:\d+|\*))?[hlL]*[diuoxXfFeEgGcspn%]")

def digest(data):return hashlib.sha1(data).hexdigest()
def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def new_path(path):
    if path.exists():raise ValueError(f'Output already exists: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
def read_base(path):
    rom=path.read_bytes()
    if len(rom)!=0x2000000 or digest(rom)!=BASE_SHA1:
        raise ValueError('Expected the original Japan Rev 3 .z64 ROM, SHA-1 '+BASE_SHA1)
    return rom

def format_tokens(text):
    if '%' in PRINTF.sub('',text):raise ValueError('Unsupported or incomplete printf token')
    return PRINTF.findall(text)

def checksum(rom):
    """CIC-6103; its boot-code signature is checked rather than guessed."""
    if zlib.crc32(rom[0x40:0x1000])!=0x0B050EE0:raise ValueError('Unexpected CIC boot code')
    mask=0xffffffff
    t1=t2=t3=t4=t5=t6=0xA3886759
    for (d,) in struct.iter_unpack('>I',rom[0x1000:0x101000]):
        total=t6+d
        if total>mask:t4=(t4+1)&mask
        t6=total&mask;t3^=d
        n=d&31;r=((d<<n)|(d>>((32-n)%32)))&mask
        t5=(t5+r)&mask
        t2^=r if t2>d else t6^d
        t1=(t1+(t5^d))&mask
    return ((t6^t4)+t3)&mask,((t5^t2)+t1)&mask

def crash_atlas(rom):
    count=FONTS['crash_glyph_count'];off=FONTS['crash_font_offset']
    words=struct.unpack_from('>64I',rom,off)
    image=Image.new('L',(15*6,3*7),0)
    for glyph in range(count):
        for y in range(7):
            for x in range(6):
                bit=31-(glyph%5)*6-x
                if words[glyph//5*7+y]&(1<<bit):image.putpixel((glyph%15*6+x,glyph//15*7+y),255)
    return image

def encode_crash(rom,image):
    if image.size!=(90,21):raise ValueError('Crash font atlas must be 90x21 (45 cells, 6x7 each)')
    off=FONTS['crash_font_offset'];words=list(struct.unpack_from('>64I',rom,off))
    image=image.convert('L')
    for glyph in range(45):
        for y in range(7):
            for x in range(6):
                bit=1<<(31-(glyph%5)*6-x);word=glyph//5*7+y
                if image.getpixel((glyph%15*6+x,glyph//15*7+y))>=128:words[word]|=bit
                else:words[word]&=~bit
    return struct.pack('>64I',*words)

def hud_atlas(rom):
    image=Image.new('RGBA',(16*6,10*6),(0,0,0,0))
    for n,index in enumerate(range(8,161)):
        image.paste(decode(rom,IMAGES[f'b5_{index:04d}']),(n%16*6,n//16*6))
    return image

def write_fonts(rom,out):
    out.mkdir(parents=True,exist_ok=True)
    crash_atlas(rom).save(out/'crash.atlas.png')
    hud_atlas(rom).save(out/'hud_small.atlas.png')
    table=rom[FONTS['crash_map_offset']:FONTS['crash_map_offset']+128]
    glyphs=[]
    for glyph in range(45):
        chars=''.join(chr(i) for i,v in enumerate(table) if v==glyph)
        glyphs.append({'glyph':glyph,'characters':chars,'atlas_xy':[glyph%15*6,glyph//15*7],'cell':[6,7]})
    small=[]
    for n,index in enumerate(range(8,161)):
        label='symbol; inspect image'
        if 8<=index<=33:label=chr(65+index-8)+' / white'
        elif 34<=index<=59:label=chr(65+index-34)+' / red'
        elif 60<=index<=69:label=str(index-60)+' / white'
        elif 70<=index<=79:label=str(index-70)+' / red'
        small.append({'id':f'b5_{index:04d}','visual_label':label,'atlas_xy':[n%16*6,n//16*6],'cell':[6,6]})
    save_json(out/'glyph_map.json',{'crash_renderer':'7-bit input; ASCII lowercase aliases uppercase; no Unicode/Hangul renderer',
                                  'crash':glyphs,'hud_small':'Visual A-Z/digit identification; precise runtime character-code mapping not established',
                                  'hud_small_cells':small})

def make_catalog(out):
    labels=json.loads((HERE/'data/labels.json').read_text(encoding='utf-8'))
    entries=[]
    for id,r in IMAGES.items():
        label=labels.get(id,{'category':'not_text_or_unreviewed','text':'','status':'review'})
        entries.append({'id':id,'width':r['width'],'height':r['height'],'format':r['format'],**label})
    save_json(out/'catalog.json',entries)
    cards=[]
    for e in entries:
        text=f"{e['id']} {e['category']} {e.get('text','')} {e.get('description','')} {e.get('status','')}".lower()
        description=e.get('text','') or e.get('description','')
        cards.append(f'<article data-search="{html.escape(text,quote=True)}"><a href="originals/{e["id"]}.png"><img loading="lazy" src="originals/{e["id"]}.png"></a><b>{e["id"]}</b><small>{e["width"]}×{e["height"]} {e["format"]} | {html.escape(e["category"])}</small><p>{html.escape(description)}</p><small>{html.escape(e.get("status","review"))}</small></article>')
    content='''<!doctype html><meta charset="utf-8"><title>Kirby 64 JP Rev3 localization inventory</title>
<style>body{font:15px system-ui;background:#20242a;color:#eee;margin:24px}input{padding:12px;width:min(700px,90%);font:inherit}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:20px}article{background:#353b44;padding:14px;border-radius:8px}img{display:block;max-width:100%;height:110px;object-fit:contain;image-rendering:pixelated;background:repeating-conic-gradient(#777 0% 25%,#555 0% 50%) 0/16px 16px;margin-bottom:12px}b,small{display:block}small{color:#bfcad8}p{min-height:1.3em;white-space:pre-wrap}a{color:#9cd6ff}</style>
<h1>별의 커비 64 일본어판 Rev3 — 그래픽 목록</h1><p>실제 롬 테이블로 확인한 이미지. 검색: 파일 ID, menu, minigame, credits, collection, tutorial, hud, glyph, optional.</p><input id="q" placeholder="검색 / search"><span id="count"></span><main>'''+''.join(cards)+'''</main><script>let q=document.querySelector('#q'),cards=[...document.querySelectorAll('article')];function update(){let s=q.value.toLowerCase().trim(),n=0;for(let c of cards){let show=s.split(/\\s+/).every(t=>c.dataset.search.includes(t));c.hidden=!show;if(show)n++;}document.querySelector('#count').textContent=' '+n+' images';}q.oninput=update;update();</script>'''
    (out/'catalog.html').write_text(content,encoding='utf-8')

def extract(rom,out):
    new_path(out)
    (out/'originals').mkdir(parents=True)
    for id,r in IMAGES.items():decode(rom,r).save(out/'originals'/f'{id}.png')
    write_fonts(rom,out/'fonts')
    save_json(out/'native_strings.json',list(STRINGS.values()))
    labels=json.loads((HERE/'data/labels.json').read_text(encoding='utf-8'))
    jobs=[{'id':id,'original':v.get('text',''),'source_note':v.get('description',''),'category':v['category'],'translation':'','font_size':0}
          for id,v in labels.items() if v.get('status') in ('translate','optional','review_text')]
    save_json(out/'translations.json',jobs)
    (out/'edits'/'fonts').mkdir(parents=True)
    make_catalog(out)
    print(f'Extracted {len(IMAGES)} images; {len(STRINGS)} source-confirmed internal ASCII strings.')

def render_jobs(jobs,font_path,edits):
    written=[]
    for job in json.loads(jobs.read_text(encoding='utf-8-sig')):
        text=job.get('translation','').replace('\\n','\n')
        if not text:continue
        id=job['id'];r=IMAGES[id]
        if not r['format'].startswith(('i4','i8','ia')):
            raise ValueError(f'{id}: styled/color image needs a manually prepared PNG')
        w,h=r['width'],r['height']; requested=int(job.get('font_size',0))
        size=requested or max(6,h-2)
        while size>=6:
            font=ImageFont.truetype(str(font_path),size)
            box=ImageDraw.Draw(Image.new('L',(1,1))).multiline_textbbox((0,0),text,font=font,spacing=1,align='center',stroke_width=0)
            tw,th=box[2]-box[0],box[3]-box[1]
            if tw<=w-2 and th<=h-2:break
            if requested:raise ValueError(f'{id}: text overflows at font size {requested}')
            size-=1
        else:raise ValueError(f'{id}: text cannot fit even at 6px; shorten or edit layout manually')
        mask=Image.new('L',(w,h),0)
        ImageDraw.Draw(mask).multiline_text(((w-tw)//2-box[0],(h-th)//2-box[1]),text,font=font,fill=255,spacing=1,align='center')
        if r['format'].startswith('ia'):
            image=Image.new('LA',(w,h),(255,0));image.putalpha(mask)
        else:image=mask
        path=edits/f'{id}.png';new_path(path);image.save(path)
        written.append({'id':id,'font_size':size,'text':text,'warning':'small text; review readability' if size<10 else ''})
    return written

def collect_changes(rom,edits,string_path,quantize):
    if not edits.is_dir():raise ValueError(f'Edits directory does not exist: {edits}')
    patches=[];claimed=set()
    def add(kind,id,start,data):
        if id in claimed:raise ValueError(f'Duplicate edit source for {id} (atlas and individual PNG?)')
        claimed.add(id);patches.append({'kind':kind,'id':id,'start':start,'data':data})
    for path in sorted(edits.glob('*.png')):
        id=path.stem
        if id not in IMAGES:raise ValueError(f'Unknown image edit: {path.name}')
        r=IMAGES[id]
        with Image.open(path) as im:
            if im.format!='PNG' or getattr(im,'n_frames',1)!=1:raise ValueError('Expected a single PNG')
            data=encode(rom,r,im,quantize)
        add('image',id,r['offset'],data)
    crash=edits/'fonts'/'crash.atlas.png'
    if crash.exists():
        with Image.open(crash) as image:data=encode_crash(rom,image)
        add('crash_font','crash_font',FONTS['crash_font_offset'],data)
    hud=edits/'fonts'/'hud_small.atlas.png'
    if hud.exists():
        with Image.open(hud) as image:
            if image.size!=(96,60):raise ValueError('HUD atlas must be 96x60')
            for n,index in enumerate(range(8,161)):
                id=f'b5_{index:04d}';r=IMAGES[id];x=n%16*6;y=n//16*6
                add('image',id,r['offset'],encode(rom,r,image.crop((x,y,x+6,y+6)),quantize))
    if string_path:
        for edit in json.loads(string_path.read_text(encoding='utf-8-sig')):
            value=edit.get('replacement','')
            if not value:continue
            id=edit['id']
            if id not in STRINGS:raise ValueError(f'Unknown text ID: {id}')
            r=STRINGS[id]
            if re.fullmatch(r'(?:M\d|G\d|ABE\d|ENETEST|ITEM\d|BREAKTEST|EXERCISE).*',r['original']):
                raise ValueError(f'{id}: internal level identifier, not a translation target')
            try:data=value.encode('ascii')+b'\0'
            except UnicodeEncodeError:raise ValueError(f'{id}: native renderer is ASCII; render Korean UI as images instead')
            if len(data)>r['capacity']:raise ValueError(f'{id}: exceeds fixed {r["capacity"]}-byte slot')
            if format_tokens(value)!=format_tokens(r['original']):raise ValueError(f'{id}: printf tokens must stay identical')
            if '\0' in value or any(ord(c)<32 and c not in '\r\n\t' for c in value):raise ValueError('Invalid control byte')
            # Leave the tail alone, so existing suffix data is not needlessly cleared.
            add('text',id,r['offset'],data)
    return patches

def allowed_ranges(report):
    ranges=[]
    for p in report['patches']:
        if p['kind']=='image':
            r=IMAGES[p['id']];ranges.append((r['offset'],r['end']))
        elif p['kind']=='crash_font':ranges.append((FONTS['crash_font_offset'],FONTS['crash_font_offset']+256))
        elif p['kind']=='text':
            r=STRINGS[p['id']];ranges.append((r['offset'],r['offset']+r['capacity']))
        else:raise ValueError('Unknown patch kind in report')
    ranges.append((0x10,0x18))
    return ranges

def verify(rom,candidate,report):
    if len(candidate)!=len(rom):raise ValueError('ROM size changed')
    if digest(candidate)!=report['output_sha1']:raise ValueError('Candidate does not match build report')
    allowed=np.zeros(len(rom),dtype=bool)
    for start,end in allowed_ranges(report):allowed[start:end]=True
    diff=np.frombuffer(rom,dtype=np.uint8)!=np.frombuffer(candidate,dtype=np.uint8)
    if np.any(diff&~allowed):raise ValueError('ROM changed outside declared edits')
    for p in report['patches']:
        if p['kind']!='image':continue
        r=IMAGES[p['id']]
        # Re-encode the saved candidate over the original to independently check
        # its header, padding, and every non-image byte in the resource block.
        rebuilt=encode(rom,r,decode(candidate,r))
        if rebuilt!=candidate[r['offset']:r['end']]:raise ValueError(f'{r["id"]}: header, padding or trailing data changed')
    actual=struct.unpack_from('>2I',candidate,0x10)
    if checksum(candidate)!=actual:raise ValueError('N64 checksum mismatch')
    return {'changed_bytes':int(diff.sum()),'only_declared_resources_changed':True,
            'image_headers_and_padding_preserved':True,'n64_checksum_valid':True,
            'output_sha1':digest(candidate),'emulator_test':'not_run'}

def build(rom,edits,strings,out,quantize):
    new_path(out)
    new_path(out.with_suffix('.report.json'))
    patches=collect_changes(rom,edits,strings,quantize)
    candidate=bytearray(rom)
    for p in patches:candidate[p['start']:p['start']+len(p['data'])]=p['data']
    if candidate[0x1000:0x101000]!=rom[0x1000:0x101000]:
        struct.pack_into('>2I',candidate,0x10,*checksum(candidate))
    report={'source_sha1':BASE_SHA1,'output_sha1':digest(candidate),
            'patches':[{k:v for k,v in p.items() if k!='data'} for p in patches]}
    report['verification']=verify(rom,candidate,report)
    with out.open('xb') as stream:stream.write(candidate)
    save_json(out.with_suffix('.report.json'),report)
    return report

def roundtrip(rom,workspace):
    candidate=bytearray(rom);failures=[]
    for id,r in IMAGES.items():
        with Image.open(workspace/'originals'/f'{id}.png') as image:rebuilt=encode(rom,r,image)
        if rebuilt!=rom[r['offset']:r['end']]:failures.append(id)
        candidate[r['offset']:r['end']]=rebuilt
    with Image.open(workspace/'fonts'/'crash.atlas.png') as image:
        font=encode_crash(rom,image)
    off=FONTS['crash_font_offset'];candidate[off:off+256]=font
    with Image.open(workspace/'fonts'/'hud_small.atlas.png') as image:
        for n,index in enumerate(range(8,161)):
            id=f'b5_{index:04d}';r=IMAGES[id];x=n%16*6;y=n//16*6
            block=encode(rom,r,image.crop((x,y,x+6,y+6)))
            candidate[r['offset']:r['end']]=block
    if candidate!=rom or failures:raise ValueError('Roundtrip failed: '+', '.join(failures))
    return {'image_png_roundtrips':len(IMAGES),'hud_atlas_cells':153,'crash_font_cells':45,
            'complete_rom_byte_identical':True,'source_sha1':BASE_SHA1,
            'original_n64_checksum_matches_calculation':checksum(rom)==struct.unpack_from('>2I',rom,0x10)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for cmd in ('extract','build','roundtrip','verify','reextract'):
        p=sub.add_parser(cmd);p.add_argument('--rom',type=Path,required=True)
        if cmd=='extract':p.add_argument('--out',type=Path,required=True)
        if cmd=='roundtrip':p.add_argument('--workspace',type=Path,required=True)
        if cmd=='build':
            p.add_argument('--edits',type=Path,required=True);p.add_argument('--strings',type=Path)
            p.add_argument('--out',type=Path,required=True);p.add_argument('--quantize',action='store_true')
        if cmd in ('verify','reextract'):
            p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
        if cmd=='reextract':p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('render-text');p.add_argument('--jobs',type=Path,required=True)
    p.add_argument('--font',type=Path,required=True);p.add_argument('--edits',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='render-text':result=render_jobs(args.jobs,args.font,args.edits)
    else:
        rom=read_base(args.rom)
        if args.command=='extract':extract(rom,args.out);return
        elif args.command=='roundtrip':result=roundtrip(rom,args.workspace)
        elif args.command=='build':result=build(rom,args.edits,args.strings,args.out,args.quantize)
        else:
            candidate=args.candidate.read_bytes();report=json.loads(args.report.read_text(encoding='utf-8'))
            result=verify(rom,candidate,report)
            if args.command=='reextract':
                new_path(args.out);args.out.mkdir()
                for p in report['patches']:
                    if p['kind']=='image':decode(candidate,IMAGES[p['id']]).save(args.out/(p['id']+'.png'))
                write_fonts(candidate,args.out/'fonts')
                save_json(args.out/'verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError) as error:
        print('ERROR: '+str(error),file=sys.stderr);sys.exit(1)
