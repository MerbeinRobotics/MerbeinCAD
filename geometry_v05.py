"""MerbeinCAD v0.5 exact 2D edit construction (mm, degrees)."""
import copy
import math
from geometry_tools import infinite_intersection, sub, add, mul, rotate_entity
from model import distance, move_entity

EPS=1e-8

def edited_group(entities, dx=0, dy=0, angle=0, pivot=(0,0)):
    return [rotate_entity(move_entity(e,dx,dy),pivot,angle) for e in entities]

def group_rectangular_array(entities, rows, columns, dx, dy):
    if rows<1 or columns<1 or rows*columns*len(entities)>5000:
        raise ValueError('Array must contain between 1 and 5000 total items.')
    return [move_entity(e,c*dx,r*dy) for r in range(rows) for c in range(columns) if r or c for e in entities]

def group_polar_array(entities, center, count, sweep=360):
    if count<2 or count*len(entities)>5000:
        raise ValueError('Array must contain between 2 and 5000 total items.')
    step=sweep/count if abs(sweep)==360 else sweep/(count-1)
    return [rotate_entity(e,center,i*step) for i in range(1,count) for e in entities]

def corner_edit(first,second,size,fillet=False):
    """Fillet/chamfer two LINEs at their nearest endpoints to infinite intersection.

    Returns modified line1, line2 and a joining polyline. A fillet is sampled
    as a 32 segment circular arc so legacy DXF and project readers can open it.
    """
    if first['type']!='line' or second['type']!='line':
        raise ValueError('Select exactly two straight LINE entities.')
    if not math.isfinite(size) or size<=0:raise ValueError('Enter a positive radius/distance.')
    result=infinite_intersection(first['a'],first['b'],second['a'],second['b'])
    if result is None:raise ValueError('Parallel lines cannot make a corner.')
    intersection=result[0]
    def ray(e):
        # The endpoint closest to the intersection is the end being trimmed.
        end='a' if distance(e['a'],intersection)<=distance(e['b'],intersection) else 'b'
        other=e['b'] if end=='a' else e['a']
        v=sub(other,intersection);length=math.hypot(*v)
        if length<EPS:raise ValueError('Line has no usable direction from corner.')
        return end,(v[0]/length,v[1]/length),length
    key1,u,len1=ray(first);key2,v,len2=ray(second)
    dot=max(-1,min(1,u[0]*v[0]+u[1]*v[1]));theta=math.acos(dot)
    if theta<1e-5 or abs(theta-math.pi)<1e-5:
        raise ValueError('Lines must form a non-straight corner.')
    tangent_distance=size/math.tan(theta/2) if fillet else size
    if tangent_distance>=min(len1,len2)-EPS:
        raise ValueError('Corner needs longer lines or a smaller radius/distance.')
    p=add(intersection,mul(u,tangent_distance));q=add(intersection,mul(v,tangent_distance))
    one=copy.deepcopy(first);two=copy.deepcopy(second)
    one[key1]=list(p);two[key2]=list(q)
    layer=first.get('layer','0')
    if not fillet:
        join={'type':'line','a':list(p),'b':list(q),'layer':layer}
        return one,two,join
    # Centre lies along inward angle bisector.
    bis=add(u,v);norm=math.hypot(*bis)
    center=add(intersection,mul(bis,size/math.sin(theta/2)/norm))
    a1=math.atan2(p[1]-center[1],p[0]-center[0]);a2=math.atan2(q[1]-center[1],q[0]-center[0])
    da=(a2-a1+math.pi)%(2*math.pi)-math.pi
    points=[[center[0]+size*math.cos(a1+da*j/32),center[1]+size*math.sin(a1+da*j/32)] for j in range(33)]
    return one,two,{'type':'polyline','points':points,'closed':False,'layer':layer}
