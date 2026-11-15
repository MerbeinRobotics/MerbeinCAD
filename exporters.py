"""Interchange adapters; keep 2D document separate from CAD kernels."""
import math
import shutil
import subprocess
import tempfile
from pathlib import Path


def export_dxf(doc, path):
    try: import ezdxf
    except ImportError as exc: raise RuntimeError('DXF export requires: pip install ezdxf') from exc
    dwg=ezdxf.new('R2013',setup=True)
    dwg.header['$INSUNITS']=4  # millimetres
    msp=dwg.modelspace()
    for layer in doc.layers:
        if layer not in dwg.layers: dwg.layers.new(layer)
    for e in doc.entities:
        t=e['type']; attrs={'layer':e.get('layer','0')}
        if t=='line': msp.add_line(e['a'],e['b'],dxfattribs=attrs)
        elif t=='rectangle':
            x1,y1=e['a']; x2,y2=e['b']
            msp.add_lwpolyline([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],close=True,dxfattribs=attrs)
        elif t=='circle': msp.add_circle(e['center'],e['radius'],dxfattribs=attrs)
        elif t=='polyline': msp.add_lwpolyline(e['points'],close=e.get('closed',False),dxfattribs=attrs)
        elif t=='dimension':
            a,b=e['a'],e['b']; mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
            # Dimension geometry and measurement are real model-space entities.
            msp.add_line(a,b,dxfattribs=attrs)
            v=math.dist(a,b)
            msp.add_text(f'{v:.2f}',dxfattribs={**attrs,'height':2.5,'insert':mid})
    dwg.saveas(str(path))


def export_dwg(doc,path,converter):
    """ODA File Converter converts a temporary R2013 DXF into a genuine DWG."""
    binary=Path(converter).expanduser()
    if not binary.is_file(): raise RuntimeError('Set an installed ODAFileConverter.exe path in Export > Configure DWG converter.')
    with tempfile.TemporaryDirectory(prefix='merbeincad_') as tmp:
        source=Path(tmp)/'input';target=Path(tmp)/'output';source.mkdir();target.mkdir()
        export_dxf(doc,source/'drawing.dxf')
        command=[str(binary),str(source),str(target),'ACAD2013','DWG','0','1','*.dxf']
        result=subprocess.run(command,capture_output=True,text=True,timeout=120)
        if result.returncode: raise RuntimeError(f'ODA converter failed: {result.stderr or result.stdout}')
        converted=target/'drawing.dwg'
        if not converted.exists():
            matches=list(target.glob('*.dwg'))
            if not matches: raise RuntimeError('ODA converter did not generate a DWG file.')
            converted=matches[0]
        shutil.copyfile(converted,path)


def export_step(doc,path,thickness):
    """Prototype 3D bridge: extrude closed 2D profiles into independent STEP solids."""
    if thickness<=0: raise ValueError('Thickness must be greater than zero')
    try: import cadquery as cq
    except ImportError as exc: raise RuntimeError('STEP export requires CadQuery installed in this Python environment.') from exc
    solids=[]; skipped=0
    for e in doc.entities:
        t=e['type']; wire=None
        if t=='rectangle':
            (x1,y1),(x2,y2)=e['a'],e['b'];w=abs(x2-x1);h=abs(y2-y1)
            if w>1e-8 and h>1e-8:
                wire=cq.Workplane('XY').center((x1+x2)/2,(y1+y2)/2).rect(w,h)
        elif t=='circle' and e['radius']>1e-8:
            wire=cq.Workplane('XY').center(*e['center']).circle(e['radius'])
        elif t=='polyline' and e.get('closed') and len(e['points'])>=3:
            wire=cq.Workplane('XY').polyline([tuple(p) for p in e['points']]).close()
        if wire is not None:
            try: solids.append(wire.extrude(thickness).val())
            except Exception as exc: raise RuntimeError(f'Cannot extrude {t}: {exc}') from exc
        else: skipped+=1
    if not solids: raise ValueError('No closed rectangles, circles or polylines available for STEP export.')
    cq.exporters.export(cq.Compound.makeCompound(solids),str(path),exportType='STEP')
    return len(solids),skipped
