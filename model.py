"""MerbeinCAD's kernel-independent, millimetre-based sketch document."""
import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def entity_points(e):
    t=e['type']
    if t=='line': return [e['a'], e['b']]
    if t=='rectangle':
        x1,y1=e['a']; x2,y2=e['b']; return [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
    if t=='circle':
        x,y=e['center']; r=e['radius']; return [[x-r,y-r],[x+r,y+r],[x,y-r],[x,y+r]]
    if t=='polyline': return e['points']
    if t=='dimension': return [e['a'],e['b']]
    return []


def endpoints(e):
    if e['type']=='circle': return [e['center']]
    return entity_points(e)


def move_entity(e, dx, dy):
    out=copy.deepcopy(e)
    for k in ('a','b','center'):
        if k in out: out[k]=[out[k][0]+dx,out[k][1]+dy]
    if 'points' in out: out['points']=[[p[0]+dx,p[1]+dy] for p in out['points']]
    return out


def bounding_box(entities):
    pts=[p for e in entities for p in entity_points(e)]
    if not pts: return (-100,-100,100,100)
    return (min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))


@dataclass
class Document:
    entities: list = field(default_factory=list)
    layers: list = field(default_factory=lambda:['0','Construction','Dimensions'])
    units: str = 'mm'

    def save(self,path):
        Path(path).write_text(json.dumps({'version':1,'units':self.units,'layers':self.layers,'entities':self.entities},indent=2),encoding='utf-8')

    @classmethod
    def load(cls,path):
        d=json.loads(Path(path).read_text(encoding='utf-8'))
        if d.get('version')!=1 or d.get('units')!='mm' or not isinstance(d.get('entities'),list):
            raise ValueError('Unsupported project format')
        valid={'line','rectangle','circle','polyline','dimension'}
        if any(e.get('type') not in valid for e in d['entities']): raise ValueError('Unsupported entity')
        return cls(d['entities'],d.get('layers',['0','Construction','Dimensions']),'mm')
