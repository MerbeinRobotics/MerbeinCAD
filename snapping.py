"""Pure 2D object snapping engine (all coordinates in millimetres).

Snap tolerance is supplied in model-space units by the GUI (pixel radius / zoom).
"""
import math
from dataclasses import dataclass
from model import distance


@dataclass(frozen=True)
class SnapResult:
    point: tuple
    kind: str
    entity_index: int = -1


def segments(e):
    t = e.get('type')
    if t in ('line', 'dimension'):
        return [(e['a'], e['b'])]
    if t == 'rectangle':
        x1, y1 = e['a']; x2, y2 = e['b']
        p = [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
        return list(zip(p, p[1:] + p[:1]))
    if t == 'polyline':
        p = e.get('points', [])
        if len(p) < 2: return []
        return list(zip(p, p[1:] + (p[:1] if e.get('closed') else [])))
    return []


def line_intersection(a, b, c, d, epsilon=1e-10):
    """Finite segment/segment intersection, ignoring coincident overlaps."""
    rx,ry=b[0]-a[0],b[1]-a[1]
    sx,sy=d[0]-c[0],d[1]-c[1]
    cross=rx*sy-ry*sx
    if abs(cross) <= epsilon * max(1, math.hypot(rx,ry)*math.hypot(sx,sy)):
        return None
    qx,qy=c[0]-a[0],c[1]-a[1]
    t=(qx*sy-qy*sx)/cross
    u=(qx*ry-qy*rx)/cross
    if -epsilon<=t<=1+epsilon and -epsilon<=u<=1+epsilon:
        return (a[0]+t*rx,a[1]+t*ry)
    return None


def circle_line_intersections(center, radius, a, b):
    """Exact intersections of a finite segment and circle."""
    dx,dy=b[0]-a[0],b[1]-a[1]
    fx,fy=a[0]-center[0],a[1]-center[1]
    A=dx*dx+dy*dy
    if A < 1e-20:return []
    B=2*(fx*dx+fy*dy)
    C=fx*fx+fy*fy-radius*radius
    D=B*B-4*A*C
    if D < -1e-9*max(1.,B*B,4*A*abs(C)):return []
    roots=[-B/(2*A)] if D<=0 else [(-B-math.sqrt(D))/(2*A),(-B+math.sqrt(D))/(2*A)]
    return [(a[0]+t*dx,a[1]+t*dy) for t in roots if -1e-9<=t<=1+1e-9]


def circle_circle_intersections(c1,r1,c2,r2):
    d=distance(c1,c2)
    if d<1e-12 or d>r1+r2+1e-9 or d<abs(r1-r2)-1e-9:return []
    a=(r1*r1-r2*r2+d*d)/(2*d)
    h2=r1*r1-a*a
    if h2 < -1e-8:return []
    ux,uy=(c2[0]-c1[0])/d,(c2[1]-c1[1])/d
    mid=(c1[0]+a*ux,c1[1]+a*uy)
    h=math.sqrt(max(0,h2))
    if h<1e-10:return [mid]
    return [(mid[0]-h*uy,mid[1]+h*ux),(mid[0]+h*uy,mid[1]-h*ux)]


def tangent_points(point, center, radius):
    """Two possible tangent contacts from an external fixed point."""
    dx,dy=point[0]-center[0],point[1]-center[1]
    d2=dx*dx+dy*dy;r2=radius*radius
    if d2<r2-1e-9:return []
    factor=r2/d2 if d2 else 0
    h=radius*math.sqrt(max(0,d2-r2))/d2 if d2 else 0
    base=(center[0]+factor*dx,center[1]+factor*dy)
    if h<1e-12:return [base]
    return [(base[0]-h*dy,base[1]+h*dx),(base[0]+h*dy,base[1]-h*dx)]


def intersections(entities):
    """Generator of line-segment intersections, including within a polyline/rectangle."""
    edges=[(i,a,b) for i,e in enumerate(entities) for a,b in segments(e)]
    for j, (i,a,b) in enumerate(edges):
        for k,c,d in edges[j+1:]:
            p=line_intersection(a,b,c,d)
            if p is not None:
                yield SnapResult(p, 'Intersection', i)
    circles=[(i,e) for i,e in enumerate(entities) if e.get('type')=='circle']
    for i,e in circles:
        for j,a,b in edges:
            for p in circle_line_intersections(e['center'],e['radius'],a,b):
                yield SnapResult(p,'Intersection',i)
    for n,(i,e) in enumerate(circles):
        for j,other in circles[n+1:]:
            for p in circle_circle_intersections(e['center'],e['radius'],other['center'],other['radius']):
                yield SnapResult(p,'Intersection',i)


def snap_candidates(entities, modes=None):
    modes = modes or {'Endpoint', 'Midpoint', 'Centre', 'Quadrant', 'Intersection'}
    for i,e in enumerate(entities):
        if e.get('type')=='circle':
            x,y=e['center'];r=e['radius']
            if 'Centre' in modes: yield SnapResult((x,y),'Centre',i)
            if 'Quadrant' in modes:
                for p in ((x+r,y),(x-r,y),(x,y+r),(x,y-r)):
                    yield SnapResult(p,'Quadrant',i)
        else:
            edge_list=segments(e)
            if 'Endpoint' in modes:
                pts=[]
                if e['type'] in ('line','dimension'):pts=[e['a'],e['b']]
                elif e['type']=='rectangle':
                    x1,y1=e['a'];x2,y2=e['b'];pts=[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
                elif e['type']=='polyline':pts=e.get('points',[])
                for p in pts: yield SnapResult(tuple(p),'Endpoint',i)
            if 'Midpoint' in modes:
                for a,b in edge_list:
                    yield SnapResult(((a[0]+b[0])/2,(a[1]+b[1])/2),'Midpoint',i)
    if 'Intersection' in modes:
        yield from intersections(entities)


def nearest_snap(cursor, entities, tolerance, modes=None, anchor=None):
    best=None;best_distance=tolerance
    for candidate in snap_candidates(entities,modes):
        d=distance(cursor,candidate.point)
        if d <= best_distance:
            best=candidate;best_distance=d
    if anchor is not None and (modes is None or 'Tangent' in modes):
        for i,e in enumerate(entities):
            if e.get('type')!='circle':continue
            for p in tangent_points(anchor,e['center'],e['radius']):
                d=distance(cursor,p)
                if d <= best_distance:
                    best=SnapResult(p,'Tangent',i);best_distance=d
    return best
