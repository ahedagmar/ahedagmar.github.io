"""Optimize public image files in place, without renaming or increasing size."""
from PIL import Image, ImageOps
from pathlib import Path
from io import BytesIO
import sys

def optimize(path):
    original=path.stat().st_size
    with Image.open(path) as source:
        if getattr(source,'is_animated',False): return
        ext=path.suffix.lower()
        im=ImageOps.exif_transpose(source)
        if im.mode=='CMYK': return # do not alter color-managed print originals
        im.thumbnail((2400,2400),Image.Resampling.LANCZOS)
        options={}
        if source.info.get('icc_profile'): options['icc_profile']=source.info['icc_profile']
        if ext in ('.jpg','.jpeg'):
            fmt='JPEG'; im=im.convert('RGB'); options.update(quality=85,optimize=True,progressive=True)
        elif ext=='.webp':
            fmt='WEBP'; options.update(quality=86,method=6)
        elif ext=='.png':
            fmt='PNG'; options.update(optimize=True)
            if source.info.get('transparency') is not None and im.mode in ('P','L','RGB'):
                options['transparency']=source.info['transparency']
        else: return
        out=BytesIO(); im.save(out,fmt,**options)
        result=out.getvalue()
    if len(result)<original:
        path.write_bytes(result)
        print(f'{path}: {original:,} → {len(result):,} bytes')

if __name__=='__main__':
    paths=[Path(p) for p in sys.argv[1:]] or list(Path('images').rglob('*'))
    for p in paths:
        if p.is_file() and not p.is_symlink() and 'images' in p.parts and p.suffix.lower() in ('.jpg','.jpeg','.webp','.png'):
            try: optimize(p)
            except Exception as e: print(f'Skipped {p}: {e}',file=sys.stderr)
