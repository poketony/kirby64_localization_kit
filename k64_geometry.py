"""JP Rev3 geometry inspection and fixed Korean boss-result replacements. Never writes a ROM."""
from pathlib import Path
import struct,math,json,hashlib,itertools
import numpy as np
from PIL import Image,ImageDraw
HEADERS=[442596,454960,461204,468948,475244,476556,482040,489852]
DELTA=0x80056D40
def geo_index(rom):
 rows=[]
 for bank,head in enumerate(HEADERS):
  h=struct.unpack_from('>8I',rom,head);table=h[0]-DELTA;count=(h[2]-h[0])//8
  for index in range(1,count):
   start,end=struct.unpack_from('>2I',rom,table+index*8)
   if not 0<start<end<=len(rom):raise ValueError('invalid geometry table')
   rows.append(dict(bank=bank,index=index,file_id=(bank<<16)|index,offset=start,end=end,table_entry=table+index*8))
 return rows
def parse_dl(block,start):
 cache={};triangles=[];loads=[];colors=[];textures=[];visited=set()
 def walk(pos,depth=0):
  if depth>24 or pos in visited or not 0<=pos<len(block):return
  visited.add(pos);half1=None
  for off in range(pos,len(block)-7,8):
   w0,w1=struct.unpack_from('>2I',block,off);op=w0>>24
   if op==1 and w1>>24==4:
    n=(w0>>12)&255;v0=((w0>>1)&127)-n;ptr=w1&0xffffff
    if not (0<n<=32 and 0<=v0 and v0+n<=32 and 32<=ptr and ptr+16*n<=len(block)):continue
    loads.append(dict(command=off,vertex_offset=ptr,count=n,cache_start=v0))
    for k in range(n):cache[v0+k]=list(struct.unpack_from('>3h',block,ptr+16*k))
   elif op in (5,6,7):
    for v in [w0&0xffffff]+([w1&0xffffff] if op in (6,7) else []):
     ids=[((v>>s)&255)//2 for s in (16,8,0)]
     if len(set(ids))==3 and all(k in cache for k in ids):triangles.append([cache[k] for k in ids])
   elif op==0xe1:half1=w1
   elif op==4 and half1 is not None and half1>>24==4:
    # Static audit visits both LOD branches; this does not emulate the Z test.
    saved=dict(cache);walk(half1&0xffffff,depth+1);cache.clear();cache.update(saved)
   elif op==0xfa:colors.append(list(w1.to_bytes(4,'big')))
   elif op==0xfd:textures.append(dict(command=off,image_id=w1,word0=w0))
   elif op==0xde:
    if w1>>24==4:walk(w1&0xffffff,depth+1)
    if (w0>>16)&1:return
   elif op==0xdf:return
 walk(start)
 return dict(triangles=triangles,vertex_loads=loads,primitive_colors=colors,texture_calls=textures)
def rotations(r):
 x,y,z=r;cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def parse_model(block):
 h=struct.unpack_from('>8I',block,0);mode=h[2];lp=h[0]&0xffffff;nodes=[];world_tri=[];unsupported=[]
 if mode in [0x17,0x18,0x1a,0x1b,0x1c,0x1d,0x1e]:
  parents={};count=min(h[7]+1,1024)
  if lp+44>len(block):return dict(header=list(h),nodes=[],triangles=[],unsupported=['layout out of range'])
  for i in range(count):
   off=lp+i*44
   if off+44>len(block):break
   command,entry,*v=struct.unpack_from('>2I9f',block,off);depth=command&0xfff
   if depth==0x12:break
   if depth>17:unsupported.append('layout command '+hex(depth));continue
   if not np.isfinite(v).all():unsupported.append('nonfinite transform');continue
   local=np.eye(4);local[:3,:3]=rotations(v[3:6])@np.diag(v[6:9]);local[:3,3]=v[:3];matrix=parents.get(depth-1,np.eye(4))@local;parents[depth]=matrix
   dls=[]
   if entry and entry>>24==4:
    p=entry&0xffffff
    if mode==0x17:dls=[p]
    elif mode==0x1b:
     dls=[x&0xffffff for x in struct.unpack_from('>2I',block,p) if x>>24==4]
    else:
     # EntryPoint lists contain a kind followed by one/two display-list pointers and a terminal kind=4.
     members=2 if mode==0x1c else 1;step=4*(members+1)
     for e in range(p,min(p+0x400,len(block)-step+1),step):
      vals=struct.unpack_from('>'+str(members+1)+'I',block,e)
      if vals[0]==4:break
      if vals[0]>4:unsupported.append('entry kind '+hex(vals[0]));break
      dls.extend(x&0xffffff for x in vals[1:] if x>>24==4)
   parsed=[parse_dl(block,p) for p in dls];tri=[t for x in parsed for t in x['triangles']]
   a=np.array(tri,float)
   if len(a):a=a@matrix[:3,:3].T+matrix[:3,3];world_tri.extend(a.tolist())
   nodes.append(dict(node=i,command=command,entry=entry,translation=v[:3],rotation=v[3:6],scale=v[6:9],display_lists=dls,triangles=a.tolist() if len(a) else [],local_triangles=tri,vertex_loads=[q for x in parsed for q in x['vertex_loads']],primitive_colors=[q for x in parsed for q in x['primitive_colors']],texture_calls=[q for x in parsed for q in x['texture_calls']]))
 elif mode in [0x13,0x14]:
  starts=[lp] if mode==0x13 else []
  if mode==0x14:
   for p in range(lp,min(lp+0x800,len(block)-7),8):
    kind,dl=struct.unpack_from('>2I',block,p)
    if kind==4:break
    if dl>>24==4:starts.append(dl&0xffffff)
  for i,p in enumerate(starts):
   d=parse_dl(block,p);d.update(node=i,command=0,entry=p|0x04000000,translation=[0,0,0],rotation=[0,0,0],scale=[1,1,1],local_triangles=d['triangles']);nodes.append(d);world_tri.extend(d['triangles'])
 else:unsupported.append('render mode '+hex(mode))
 return dict(header=list(h),nodes=nodes,triangles=world_tri,unsupported=sorted(set(unsupported)))
def render_model(model,size=(1000,240),color=(255,189,153)):
 canvas=Image.new('RGB',size,(0,0,0));a=np.array(model['triangles'],float)
 if not len(a):return canvas
 p=a[:,:,:2];lo=p.reshape(-1,2).min(0);hi=p.reshape(-1,2).max(0);factor=min((size[0]-20)/max(1,hi[0]-lo[0]),(size[1]-20)/max(1,hi[1]-lo[1]));xy=(p-lo)*factor;xy[:,:,0]+=(size[0]-(hi[0]-lo[0])*factor)/2;xy[:,:,1]=size[1]-10-xy[:,:,1];d=ImageDraw.Draw(canvas)
 for t in xy:d.polygon([tuple(v) for v in t],fill=color)
 return canvas
def font_contours(font_path,text):
 from fontTools.ttLib import TTFont
 from fontTools.pens.basePen import BasePen
 font=TTFont(font_path,recalcTimestamp=False);gs=font.getGlyphSet();cmap=font.getBestCmap()
 class Pen(BasePen):
  def __init__(self):super().__init__(gs);self.contours=[];self.points=[]
  def _moveTo(self,p):
   if self.points:self._closePath()
   self.points=[tuple(p)]
  def _lineTo(self,p):self.points.append(tuple(p))
  def _qCurveToOne(self,p1,p2):
   def flatten(a,b,c):
    if np.linalg.norm(np.array(b)-(np.array(a)+np.array(c))/2)<4:
     self.points.append(tuple(c));return
    ab=(np.array(a)+b)/2;bc=(np.array(b)+c)/2;mid=(ab+bc)/2;flatten(a,ab,mid);flatten(mid,bc,c)
   flatten(self.points[-1],np.array(p1),np.array(p2))
  def _curveToOne(self,p1,p2,p3):
   p0=np.array(self.points[-1]);p1,p2,p3=map(np.array,(p1,p2,p3))
   for i in range(1,25):
    t=i/24;self.points.append(tuple((1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3))
  def _closePath(self):
   if self.points and self.points[-1]==self.points[0]:self.points.pop()
   if len(self.points)>2:self.contours.append(self.points)
   self.points=[]
  def _endPath(self):self._closePath()
 results=[]
 for ch in text:
  if ord(ch) not in cmap:raise ValueError('font missing '+ch)
  pen=Pen();gs[cmap[ord(ch)]].draw(pen);pen._closePath();results.append(pen.contours)
 name=font['name'].getDebugName(1);font.close();return results,name
def tessellate(contours):
 # Nonzero-winding sweep; holes remain unfilled without introducing a triangulation dependency.
 contours=[list(dict.fromkeys((int(round(x)),int(round(y))) for x,y in c)) for c in contours]
 edges=[]
 for c in contours:
  for a,b in zip(c,c[1:]+c[:1]):
   if a[1]!=b[1]:edges.append((a,b,1 if b[1]>a[1] else -1))
 levels=sorted({p[1] for c in contours for p in c});tri=[]
 def cross_x(e,y):
  a,b,_=e;return a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
 for y0,y1 in zip(levels,levels[1:]):
  mid=(y0+y1)/2;active=sorted([e for e in edges if min(e[0][1],e[1][1])<mid<max(e[0][1],e[1][1])],key=lambda e:cross_x(e,mid));winding=0;left=None
  for edge in active:
   old=winding;winding+=edge[2]
   if old==0 and winding!=0:left=edge
   elif old!=0 and winding==0 and left is not None:
    poly=[(round(cross_x(left,y0)),y0,0),(round(cross_x(edge,y0)),y0,0),(round(cross_x(edge,y1)),y1,0),(round(cross_x(left,y1)),y1,0)]
    for t in [[poly[0],poly[1],poly[2]],[poly[0],poly[2],poly[3]]]:
     a,b,c=map(np.array,t)
     if np.cross(b-a,c-a)[2]!=0:tri.append([list(p) for p in t])
  if winding!=0:raise ValueError('unclosed font winding')
 return tri
def pack_word_model(old,original,node_tri,material,postamble=b''):
 blob=bytearray(b'\0'*32);vertex_refs=[];dl_offsets={};batches_by_node={}
 def align(n):
  while len(blob)%n:blob.append(0)
 def cmd(a,b):blob.extend(struct.pack('>2I',a,b))
 for node in range(1,len(original['nodes'])):
  tris=node_tri.get(node,[]);batches=[];points=[];pointmap={};indices=[]
  for triangle in tris:
   missing=[tuple(p) for p in triangle if tuple(p) not in pointmap]
   if len(points)+len(set(missing))>32:
    batches.append((points,indices));points=[];pointmap={};indices=[]
   ids=[]
   for p in triangle:
    p=tuple(p)
    if p not in pointmap:pointmap[p]=len(points);points.append(p)
    ids.append(pointmap[p])
   indices.append(ids)
  if points:batches.append((points,indices))
  offsets=[]
  for points,indices in batches:
   align(16);ptr=len(blob)
   for x,y,z in points:
    if not all(-32768<=v<=32767 for v in (x,y,z)):raise ValueError('vertex out of range')
    blob.extend(struct.pack('>3hH2h4B',x,y,z,0,0,0,255,255,255,255))
   offsets.append((ptr,len(points),indices))
  batches_by_node[node]=offsets
 for node in range(1,len(original['nodes'])):
  align(8);dl_offsets[node]=len(blob)
  if node==1:blob.extend(material)
  for ptr,n,triangles in batches_by_node[node]:
   vertex_refs.append(len(blob));cmd(0x01000000|(n<<12)|(n<<1),0x04000000|ptr)
   def triword(t):return (t[0]*2<<16)|(t[1]*2<<8)|(t[2]*2)
   for i in range(0,len(triangles),2):
    if i+1<len(triangles):cmd(0x06000000|triword(triangles[i]),triword(triangles[i+1]))
    else:cmd(0x05000000|triword(triangles[i]),0)
  if node==len(original['nodes'])-1:blob.extend(postamble)
  cmd(0xdf000000,0)
 align(4);image_refs=len(blob);blob.extend(b'\0'*4);vertex_list=len(blob)
 for ptr in vertex_refs:blob.extend(struct.pack('>I',0x04000000|ptr))
 blob.extend(b'\0'*4);align(4);layout=len(blob);oldlp=original['header'][0]&0xffffff;rawlayout=bytearray(old[oldlp:oldlp+44*(len(original['nodes'])+1)])
 for node in range(1,len(original['nodes'])):struct.pack_into('>I',rawlayout,node*44+4,0x04000000|dl_offsets[node])
 blob.extend(rawlayout);align(4);animrefs=len(blob);oldap=original['header'][6]&0xffffff;blob.extend(old[oldap:oldap+4*original['header'][5]]);align(16)
 header=[0x04000000|layout,original['header'][1],original['header'][2],0x04000000|image_refs,0x04000000|vertex_list,original['header'][5],0x04000000|animrefs,original['header'][7]];struct.pack_into('>8I',blob,0,*header)
 result=bytes(blob);parsed=parse_model(result)
 if len(parsed['triangles'])!=sum(len(t) for t in node_tri.values()):raise ValueError('readback triangles differ')
 for before,after in zip(original['nodes'],parsed['nodes']):
  for key in ['node','command','translation','rotation','scale']:
   if before[key]!=after[key]:raise ValueError('original animation node changed')
 if result[animrefs:animrefs+4*original['header'][5]]!=old[oldap:oldap+4*original['header'][5]]:raise ValueError('animation references changed')
 return result,parsed

def build_failure(rom,font_path):
 if hashlib.sha1(rom).hexdigest()!='03257c820b7705400c32bde1bcc3161c55814605':raise ValueError('This tool requires the unchanged Japan Rev 3 ROM')
 text='형편없네요';index=next(x for x in geo_index(rom) if x['file_id']==0x30005);old=rom[index['offset']:index['end']];original=parse_model(old)
 if original['header'][2]!=0x17 or len(original['nodes'])!=8:raise ValueError('unexpected source model')
 contours,family=font_contours(font_path,text);allp=np.array([p for cs in contours for c in cs for p in c]);low,high=allp.min(0),allp.max(0);oldpoints=np.array(original['triangles']).reshape(-1,3);oldlo,oldhi=oldpoints.min(0),oldpoints.max(0)
 scale=(oldhi[1]-oldlo[1])*.98/(high[1]-low[1]);bounds=[(np.array([p for c in cs for p in c]).min(0),np.array([p for c in cs for p in c]).max(0)) for cs in contours];gap=15.;total=sum((b[1][0]-b[0][0])*scale for b in bounds)+gap*4;cap=(oldhi[0]-oldlo[0])*1.12
 if total>cap:scale*=(cap-gap*4)/(total-gap*4);total=cap
 cursor=(oldlo[0]+oldhi[0]-total)/2;centers=[]
 for lo,hi in bounds:
  width=(hi[0]-lo[0])*scale;centers.append(cursor+width/2);cursor+=width+gap
 available=sorted(original['nodes'][1:],key=lambda n:n['translation'][0]);chosen=min(itertools.combinations(available,5),key=lambda ns:sum((n['translation'][0]-x)**2 for n,x in zip(ns,centers)));node_tri={};glyph_rows=[]
 for ch,cs,bb,node,xcenter in zip(text,contours,bounds,chosen,centers):
  dx=xcenter-node['translation'][0];dy=(oldlo[1]+oldhi[1])/2-node['translation'][1];center=(bb[0][0]+bb[1][0])/2;yc=(low[1]+high[1])/2
  transformed=[[( (x-center)*scale+dx,(y-yc)*scale+dy) for x,y in c] for c in cs];tri=tessellate(transformed);node_tri[node['node']]=tri;glyph_rows.append(dict(character=ch,node=node['node'],center_x=float(xcenter),triangle_count=len(tri)))
 # Copy the original untextured primitive-color material, excluding its call to the old vertex DL.
 material=old[0x920:0x948]
 if struct.unpack_from('>I',material,24)[0]!=0xfa000000:raise ValueError('unexpected original material')
 result,parsed=pack_word_model(old,original,node_tri,material)
 manifest=dict(resource_type='geometry',file_id='0x30005',bank=3,index=5,text=text,font_path=str(font_path),font_family=family,font_sha256=hashlib.sha256(Path(font_path).read_bytes()).hexdigest(),source_rom_sha1=hashlib.sha1(rom).hexdigest(),source_offset=index['offset'],source_end=index['end'],table_entry=index['table_entry'],source_size=len(old),replacement_size=len(result),sha256=hashlib.sha256(result).hexdigest(),requires_relocation=len(result)!=len(old),rom_assembly='deferred until explicit user ROM-build instruction',root_and_7_nodes_preserved=True,animation_refs_preserved=['0x30009','0x3000A','0x3000B'],empty_nodes=sorted(set(range(1,8))-set(node_tri)),glyphs=glyph_rows,triangles=len(parsed['triangles']),render_mode='0x17',texture_refs=0)
 return result,manifest,parsed



def build_success(rom,font_path):
 if hashlib.sha1(rom).hexdigest()!='03257c820b7705400c32bde1bcc3161c55814605':raise ValueError('This tool requires the unchanged Japan Rev 3 ROM')
 text='축하합니다';index=next(x for x in geo_index(rom) if x['file_id']==0x30006);old=rom[index['offset']:index['end']];original=parse_model(old)
 if original['header'][2]!=0x17 or len(original['nodes'])!=11 or original['header'][5]!=3:raise ValueError('unexpected success model')
 contours,family=font_contours(font_path,text);nodes=original['nodes'][1:];common=rotations(nodes[0]['rotation'])
 if any(not np.allclose(rotations(n['rotation']),common) or n['scale']!=[1.,1.,1.] for n in nodes):raise ValueError('unexpected success text plane')
 flat_orig=np.array(original['triangles']).reshape(-1,3)@common;oldlo,oldhi=flat_orig[:,:2].min(0),flat_orig[:,:2].max(0);centers=[];heights=[]
 for n in nodes:
  p=np.array(n['triangles']).reshape(-1,3)@common;lo,hi=p[:,:2].min(0),p[:,:2].max(0);centers.append((lo+hi)/2);heights.append(hi[1]-lo[1])
 centers=np.array(centers);arc=np.polyfit(centers[:,0],centers[:,1],2);font_points=np.array([p for cs in contours for c in cs for p in c]);font_lo,font_hi=font_points.min(0),font_points.max(0);scale=float(np.median(heights))*1.15/(font_hi[1]-font_lo[1]);x_positions=np.linspace(oldlo[0]+(oldhi[0]-oldlo[0])*.12,oldhi[0]-(oldhi[0]-oldlo[0])*.12,5);placed=[];placement=[]
 for cs,x in zip(contours,x_positions):
  a=np.array([p for c in cs for p in c]);lo,hi=a.min(0),a.max(0);center=np.array([(lo[0]+hi[0])/2,(font_lo[1]+font_hi[1])/2]);angle=float(np.clip(np.arctan(np.polyval(np.polyder(arc),x)),-.45,.45));rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);xy=np.array([x,np.polyval(arc,x)]);placed.append([((np.array(c)-center)*scale@rotation.T+xy) for c in cs]);placement.append((xy,angle))
 p=np.concatenate([c for cs in placed for c in cs]);lo,hi=p.min(0),p.max(0);fit=float(min(1.05,*((oldhi-oldlo)/(hi-lo))));shift=(oldlo+oldhi)/2-(lo+hi)*fit/2;placed=[[c*fit+shift for c in cs] for cs in placed];placement=[(xy*fit+shift,angle) for xy,angle in placement]
 # Keep the existing node identities and compensate in each glyph's local geometry.
 available=sorted(nodes,key=lambda n:n['translation'][0]);chosen=min(itertools.combinations(available,5),key=lambda ns:sum(np.linalg.norm((np.array(n['translation'])@common)[:2]-xy)**2 for n,(xy,_) in zip(ns,placement)));node_tri={};glyph_rows=[]
 for ch,cs,node,(xy,angle) in zip(text,placed,chosen,placement):
  translation=np.array(node['translation'])@common;local=[(c-translation[:2]).tolist() for c in cs];tri=tessellate(local);node_tri[node['node']]=tri;glyph_rows.append(dict(character=ch,node=node['node'],center_flat_xy=xy.tolist(),rotation_z_radians=angle,triangle_count=len(tri)))
 # Material setup and final renderer-state restoration are copied from the source DLs.
 material=old[0xe00:0xe30];postamble=old[0x1258:0x12f0]
 if struct.unpack_from('>2I',material,24)!=(0xfa000000,0x524327ff):raise ValueError('unexpected success material')
 result,parsed=pack_word_model(old,original,node_tri,material,postamble)
 animrefs=struct.unpack_from('>3I',result,parsed['header'][6]&0xffffff)
 manifest=dict(resource_type='geometry',file_id='0x30006',bank=3,index=6,text=text,font_path=str(font_path),font_family=family,font_sha256=hashlib.sha256(Path(font_path).read_bytes()).hexdigest(),source_rom_sha1=hashlib.sha1(rom).hexdigest(),source_offset=index['offset'],source_end=index['end'],table_entry=index['table_entry'],source_size=len(old),replacement_size=len(result),sha256=hashlib.sha256(result).hexdigest(),requires_relocation=len(result)!=len(old),rom_assembly='deferred until explicit user ROM-build instruction',root_and_10_nodes_preserved=True,animation_refs_preserved=[f'0x{x:05X}' for x in animrefs],empty_nodes=sorted(set(range(1,11))-set(node_tri)),glyphs=glyph_rows,triangles=len(parsed['triangles']),render_mode='0x17',texture_refs=0,primitive_rgba=[82,67,39,255],material_setup_preserved=True,render_state_postamble_preserved=True,layout='arch fitted to original glyph centers in the original -10 degree text plane',arc_fit_coefficients=arc.tolist(),font_scale_in_world_units=scale*fit)
 return result,manifest,parsed


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 sub=parser.add_subparsers(dest='command',required=True)
 for command in ['build-failure','build-success']:
  build=sub.add_parser(command,help='Create a fixed Korean geometry asset; never assemble a ROM')
  build.add_argument('--rom',type=Path,required=True)
  build.add_argument('--font',type=Path,required=True)
  build.add_argument('--out-dir',type=Path,required=True)
 inspect=sub.add_parser('inspect',help='Read a standalone geometry block')
 inspect.add_argument('model',type=Path)
 inspect.add_argument('--preview',type=Path)
 args=parser.parse_args()
 if args.command in ['build-failure','build-success']:
  builder=build_failure if args.command=='build-failure' else build_success
  blob,manifest,model=builder(args.rom.read_bytes(),args.font)
  success=args.command=='build-success'
  model_name='geo_b3_0006.bin' if success else 'geo_b3_0005.bin'
  manifest_name='geo_b3_0006.manifest.json' if success else 'model-manifest.json'
  preview_name='geo_b3_0006-preview.png' if success else 'korean-model-readback.png'
  args.out_dir.mkdir(parents=True,exist_ok=True)
  (args.out_dir/model_name).write_bytes(blob)
  (args.out_dir/manifest_name).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  render_model(model,color=tuple(manifest.get('primitive_rgba',[255,189,153])[:3])).save(args.out_dir/preview_name)
  print(json.dumps({'file_id':manifest['file_id'],'text':manifest['text'],'bytes':len(blob),'sha256':manifest['sha256'],'requires_relocation':manifest['requires_relocation'],'rom_written':False},ensure_ascii=False))
 else:
  blob=args.model.read_bytes();m=parse_model(blob)
  if args.preview:
   if args.preview.suffix.lower()!='.png':parser.error('preview must end with .png')
   colors=[c for n in m['nodes'] for c in n.get('primitive_colors',[])]
   render_model(m,color=tuple(colors[0][:3]) if colors else (255,189,153)).save(args.preview)
  print(json.dumps({'bytes':len(blob),'header':[hex(x) for x in m['header']],'nodes':len(m['nodes']),'triangles':len(m['triangles']),'unsupported':m['unsupported']},ensure_ascii=False))

if __name__=='__main__':
 main()
