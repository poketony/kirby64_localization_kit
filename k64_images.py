import struct
import numpy as np
from PIL import Image

def rgba16(word):
    return tuple((((word>>s)&31)<<3)|(((word>>s)&31)>>2) for s in (11,6,1))+((word&1)*255,)

def color16(color):
    r,g,b,a=color
    return ((r*31+127)//255)<<11 | ((g*31+127)//255)<<6 | ((b*31+127)//255)<<1 | int(a>=128)

def decode(rom,r):
    fmt=r['format']; w=r['width'];h=r['height'];stride=r['stride_bytes']
    raw=np.frombuffer(rom[r['pixel_offset']:r['pixel_offset']+r['pixel_size']],dtype=np.uint8).reshape(h,stride)
    depth=int(''.join(c for c in fmt if c.isdigit()))
    if depth==4:
        values=np.empty((h,stride*2),dtype=np.uint8)
        values[:,::2]=raw>>4;values[:,1::2]=raw&15
        values=values[:,:w].copy()
    elif depth==8: values=raw[:,:w].copy()
    else: values=raw[:,:w*(depth//8)].copy()
    if fmt.startswith('ci'):
        n=min(r.get('palette_count',256),16 if depth==4 else 256)
        pal=struct.unpack_from(f'>{n}H',rom,r['palette_offset'])
        colors=[rgba16(v) for v in pal]
        im=Image.fromarray(values,'P')
        im.putpalette([v for c in colors for v in c[:3]])
        im.info['transparency']=bytes(c[3] for c in colors)
        return im
    if fmt=='rgba16':
        words=values.reshape(h,w,2).astype(np.uint16)
        words=(words[:,:,0]<<8)|words[:,:,1]
        out=np.empty((h,w,4),dtype=np.uint8)
        for k,s in enumerate((11,6,1)):
            v=(words>>s)&31;out[:,:,k]=(v<<3)|(v>>2)
        out[:,:,3]=(words&1)*255
        return Image.fromarray(out,'RGBA')
    if fmt=='rgba32':return Image.fromarray(values.reshape(h,w,4),'RGBA')
    if fmt.startswith('ia'):
        if depth==4:
            v=values>>1; gray=(v.astype(np.uint16)*255+3)//7;alpha=(values&1)*255
        elif depth==8:gray=(values>>4)*17;alpha=(values&15)*17
        else:
            v=values.reshape(h,w,2);gray=v[:,:,0];alpha=v[:,:,1]
        return Image.fromarray(np.stack((gray,alpha),axis=-1).astype(np.uint8),'LA')
    return Image.fromarray(values*17 if depth==4 else values,'L')

def preview(im):
    if im.mode=='L':
        rgba=Image.new('RGBA',im.size,'white');rgba.putalpha(im);return rgba
    return im.convert('RGBA')

def encode(rom, r, image, quantize=False):
    """Return an asset-sized block; preserve all headers and row padding."""
    if image.size != (r['width'], r['height']):
        raise ValueError(f"{r['id']}: expected {r['width']}x{r['height']}, got {image.size}")
    fmt=r['format']; w=r['width'];h=r['height'];stride=r['stride_bytes']
    depth=int(''.join(c for c in fmt if c.isdigit()))
    block=bytearray(rom[r['offset']:r['end']])
    p=r['pixel_offset']-r['offset']
    raw=np.frombuffer(bytes(block[p:p+r['pixel_size']]),dtype=np.uint8).reshape(h,stride).copy()
    if fmt.startswith('ci'):
        count=r['palette_count'];capacity=min(count,16 if depth==4 else 256)
        pal_pos=r['palette_offset']-r['offset']
        palette=list(struct.unpack_from(f'>{count}H',block,pal_pos))
        if image.mode=='P':
            indices=np.asarray(image).copy()
            if int(indices.max())>=capacity:
                raise ValueError(f"{r['id']}: index exceeds this asset's {capacity}-color palette")
            rgb=image.getpalette('RGB');transparency=image.info.get('transparency')
            if rgb is None:raise ValueError('Indexed image has no palette')
            for i in np.unique(indices):
                i=int(i);alpha=255
                if isinstance(transparency,int):alpha=0 if i==transparency else 255
                elif isinstance(transparency,bytes) and i<len(transparency):alpha=transparency[i]
                palette[i]=color16((*rgb[i*3:i*3+3],alpha))
        else:
            rgba=image.convert('RGBA')
            words=[color16(c) for c in rgba.getdata()]
            if len(set(words))>capacity:
                if not quantize:raise ValueError(f"{r['id']}: more than {capacity} colors; use indexed PNG or --quantize")
                rgba=rgba.quantize(colors=capacity,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGBA')
                words=[color16(c) for c in rgba.getdata()]
            wanted=set(words);mapping={}
            for i,v in enumerate(palette[:capacity]):
                if v in wanted:mapping.setdefault(v,i)
            free=iter(i for i in range(capacity) if i not in mapping.values())
            for v in dict.fromkeys(words):
                if v not in mapping:
                    i=next(free);mapping[v]=i;palette[i]=v
            indices=np.array([mapping[v] for v in words],dtype=np.uint8).reshape(h,w)
        block[pal_pos:pal_pos+count*2]=struct.pack(f'>{count}H',*palette)
        values=indices
    elif fmt=='rgba16':
        words=np.array([color16(c) for c in image.convert('RGBA').getdata()],dtype=np.uint16).reshape(h,w)
        values=np.empty((h,w*2),dtype=np.uint8)
        values[:,::2]=words>>8;values[:,1::2]=words&255
    elif fmt=='rgba32':values=np.asarray(image.convert('RGBA')).reshape(h,w*4)
    elif fmt.startswith('ia'):
        a=np.asarray(image.convert('LA')).astype(np.uint16)
        if depth==4:values=(((a[:,:,0]*7+127)//255)<<1)|(a[:,:,1]>=128)
        elif depth==8:values=(((a[:,:,0]*15+127)//255)<<4)|((a[:,:,1]*15+127)//255)
        else:values=a.astype(np.uint8).reshape(h,w*2)
    else:
        a=np.asarray(image.convert('L')).astype(np.uint16)
        values=(a*15+127)//255 if depth==4 else a
    if depth==4:
        expanded=np.empty((h,stride*2),dtype=np.uint8)
        expanded[:,::2]=raw>>4;expanded[:,1::2]=raw&15
        expanded[:,:w]=values
        raw=(expanded[:,::2]<<4)|expanded[:,1::2]
    else:
        raw[:,:w*(depth//8)]=values
    block[p:p+r['pixel_size']]=raw.tobytes()
    return bytes(block)
