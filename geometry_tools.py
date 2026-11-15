"""Geometric edits and array constructions for MerbeinCAD, coordinates in mm."""
import copy
import math
from model import distance, move_entity
from snapping import segments

EPS=1e-8

def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def mul(a,k):return (a[0]*k,a[1]*k)

def infinite_intersection(a,b,c,d):
    r=sub(b,a);s=sub(d,c);den=cross(r,s)
    if abs(den)<EPS*max(1,math.hypot(*r)*math.hypot(*s)):return None
    t=cross(sub(c,a),s)/den
    u=cross(sub(c,a),r)/den
    return add(a,mul(r,t)),t,u

def circle_line_infinite(center,radius,a,b):
    v=sub(b,a);f=sub(a,center);A=v[0]**2+v[1]**2
    if A<EPS**2:return []
    B=2*(f[0]*v[0]+f[1]*v[1]);C=f[0]**2+f[1]**2-radius**2
    disc=B*B-4*A*C
    if disc< -EPS:return []
    disc=max(0,disc)
    return [(add(a,mul(v,t)),t) for t in ((-B-math.sqrt(disc))/(2*A),(-B+math.sqrt(disc))/(2*A))]

def cut_parameters(line, boundaries):
    a,b=line['a'],line['b'];out=[]
    for e in boundaries:
        for c,d in segments(e):
            result=infinite_intersection(a,b,c,d)
            if result and -EPS<=result[2]<=1+EPS:out.append(result[1])
        if e['type']=='circle':out.extend(t for p,t in circle_line_infinite(e['center'],e['radius'],a,b))
    return sorted(set(round(t,10) for t in out))

def trim_line(line,boundaries,click):
    """Remove clicked interval between cuts, returning zero, one, or two lines."""
    if line['type']!='line':raise ValueError('Trim currently supports straight LINE entities only.')
    a,b=line['a'],line['b'];v=sub(b,a);den=v[0]**2+v[1]**2
    if den<EPS:return []
    t=max(0,min(1,((click[0]-a[0])*v[0]+(click[1]-a[1])*v[1])/den))
    cuts=[0]+[q for q in cut_parameters(line,boundaries) if EPS<q<1-EPS]+[1]
    if len(cuts)==2:raise ValueError('No cutting boundary intersects this line.')
    idx=next((i for i in range(len(cuts)-1) if cuts[i]-EPS<=t<=cuts[i+1]+EPS),len(cuts)-2)
    left,right=cuts[idx:idx+2]
    result=[]
    for lo,hi in ((0,left),(right,1)):
        if hi-lo>EPS:result.append({**line,'a':list(add(a,mul(v,lo))),'b':list(add(a,mul(v,hi)))})
    return result

def extend_line(line,boundaries,click):
    if line['type']!='line':raise ValueError('Extend currently supports straight LINE entities only.')
    a,b=line['a'],line['b'];v=sub(b,a);den=v[0]**2+v[1]**2
    if den<EPS:raise ValueError('Zero-length line.')
    t=((click[0]-a[0])*v[0]+(click[1]-a[1])*v[1])/den
    params=cut_parameters(line,boundaries)
    if t<=.5:
        choices=[q for q in params if q< -EPS]
        if not choices:raise ValueError('No boundary lies beyond this endpoint.')
        p=add(a,mul(v,max(choices)))
        return {**line,'a':list(p)}
    choices=[q for q in params if q>1+EPS]
    if not choices:raise ValueError('No boundary lies beyond this endpoint.')
    p=add(a,mul(v,min(choices)))
    return {**line,'b':list(p)}

def circle_tangents(c1,r1,c2,r2):
    """All common tangent segments (external and internal), excluding degenerate ones.
    Based on orthogonal decomposition of normal; returns (endpoint1,endpoint2,kind).
    """
    v=sub(c2,c1);z=v[0]*v[0]+v[1]*v[1]
    if z<EPS:return []
    out=[]
    for side in (1,-1):
        dr=r1-side*r2
        h2=z-dr*dr
        if h2< -EPS:continue
        for orient in (-1,1):
            h=math.sqrt(max(0,h2))
            n=((v[0]*dr-v[1]*h*orient)/z,(v[1]*dr+v[0]*h*orient)/z)
            p1=add(c1,mul(n,r1));p2=add(c2,mul(n,side*r2))
            if distance(p1,p2)>EPS and not any(distance(p1,x[0])<EPS and distance(p2,x[1])<EPS for x in out):
                out.append((p1,p2,'External' if side==1 else 'Internal'))
    return out

def rotate_point(p,center,angle):
    a=math.radians(angle);c=math.cos(a);s=math.sin(a);x=p[0]-center[0];y=p[1]-center[1]
    return [center[0]+x*c-y*s,center[1]+x*s+y*c]

def rotate_entity(entity,center,angle):
    e=copy.deepcopy(entity)
    if e['type']=='rectangle' and abs(angle%180)>1e-9:
        (x1,y1),(x2,y2)=e['a'],e['b']
        e={'type':'polyline','points':[[x1,y1],[x2,y1],[x2,y2],[x1,y2]],'closed':True,'layer':e.get('layer','0')}
    for name in ('a','b','center'):
        if name in e:e[name]=rotate_point(e[name],center,angle)
    if 'points' in e:e['points']=[rotate_point(p,center,angle) for p in e['points']]
    return e

def rectangular_array(entity,rows,columns,dx,dy):
    if not (1<=rows<=100 and 1<=columns<=100):raise ValueError('Rows/columns must be 1–100')
    if rows*columns>2500:raise ValueError('Array limited to 2500 entities')
    return [move_entity(entity,c*dx,r*dy) for r in range(rows) for c in range(columns) if r or c]

def polar_array(entity,center,count,sweep=360):
    if not 2<=count<=360:raise ValueError('Number of items must be 2–360')
    step=sweep/count if abs(sweep)==360 else sweep/(count-1)
    return [rotate_entity(entity,center,i*step) for i in range(1,count)]
