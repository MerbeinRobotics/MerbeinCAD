"""Dependency-free 3D wireframe geometry for MerbeinCAD v0.7; millimetre units.
STEP serialization is handled separately by the CadQuery adapter.
"""
import math


def profile_points(entity, samples=48):
    kind=entity['type']
    if kind=='rectangle':
        (x1,y1),(x2,y2)=entity['a'],entity['b']
        result=[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
    elif kind=='circle':
        x,y=entity['center'];r=entity['radius']
        result=[[x+r*math.cos(i*2*math.pi/samples),y+r*math.sin(i*2*math.pi/samples)] for i in range(samples)]
    elif kind=='polyline' and entity.get('closed'):
        result=[list(p) for p in entity['points']]
    else:
        raise ValueError('Select a closed rectangle, circle, or polyline as the 3D profile.')
    if len(result)<3 or abs(signed_area(result))<1e-9:
        raise ValueError('Profile has zero area.')
    return result


def signed_area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2


def make_solid(profile, operation, amount, axis='Y', steps=48):
    """Return points and edge index pairs; no dependency on a native CAD kernel."""
    poly=profile_points(profile)
    n=len(poly)
    if operation=='extrude':
        if amount<=0:raise ValueError('Extrusion depth must be positive.')
        vertices=[[x,y,z] for z in (0,float(amount)) for x,y in poly]
        edges=[(base+i,base+(i+1)%n) for base in (0,n) for i in range(n)]
        edges += [(i,n+i) for i in range(n)]
    elif operation=='revolve':
        if axis not in ('X','Y'):raise ValueError('Revolve axis must be X or Y.')
        if not 0<amount<=360:raise ValueError('Revolve angle must be between 0 and 360 degrees.')
        full=abs(amount-360)<1e-8
        rings=steps if full else max(2,math.ceil(steps*amount/360)+1)
        vertices=[]
        for j in range(rings):
            theta=math.radians(amount)*(j/rings if full else j/(rings-1))
            c,s=math.cos(theta),math.sin(theta)
            for x,y in poly:
                if axis=='Y':vertices.append([x*c,y,x*s])
                else:vertices.append([x,y*c,y*s])
        edges=[]
        for j in range(rings):
            for i in range(n):edges.append((j*n+i,j*n+(i+1)%n))
            if full or j<rings-1:
                next_j=(j+1)%rings
                for i in range(n):edges.append((j*n+i,next_j*n+i))
    else:raise ValueError('Unknown 3D operation.')
    return vertices,edges


def project(point, azimuth=35, elevation=25, scale=1, origin=(0,0), pan=(0,0)):
    """Orthographic orbit projection; looking toward the origin."""
    x,y,z=point; a=math.radians(azimuth); e=math.radians(elevation)
    horizontal=x*math.cos(a)-y*math.sin(a)
    depth=x*math.sin(a)+y*math.cos(a)
    vertical=z*math.cos(e)-depth*math.sin(e)
    return (origin[0]+(horizontal+pan[0])*scale,origin[1]-(vertical+pan[1])*scale)


def export_solid_step(solids, out_path):
    try:import cadquery as cq
    except ImportError as exc:
        raise RuntimeError('STEP export requires CadQuery (and a supported Python environment). See README for installation.') from exc
    shapes=[]
    for entry in solids:
        profile=entry['profile'];operation=entry['operation'];amount=float(entry['amount'])
        t=profile['type']
        if t=='circle':wp=cq.Workplane('XY').center(*profile['center']).circle(profile['radius'])
        elif t=='rectangle':
            (x1,y1),(x2,y2)=profile['a'],profile['b'];wp=cq.Workplane('XY').polyline([(x1,y1),(x2,y1),(x2,y2),(x1,y2)]).close()
        else:wp=cq.Workplane('XY').polyline([tuple(p) for p in profile['points']]).close()
        if operation=='extrude':solid=wp.extrude(amount).val()
        elif operation=='revolve':
            axis=entry.get('axis','Y')
            solid=wp.revolve(amount,(0,0),(1,0) if axis=='X' else (0,1)).val()
        else:raise ValueError('Unsupported solid operation')
        shapes.append(solid)
    if not shapes:raise ValueError('No 3D solids to export. Extrude or revolve a closed profile first.')
    cq.exporters.export(cq.Compound.makeCompound(shapes),str(out_path),exportType='STEP')
    return len(shapes)
