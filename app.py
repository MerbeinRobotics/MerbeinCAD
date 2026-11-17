"""MerbeinCAD v0.6 - lightweight engineering 2D CAD prototype."""
import copy
import json
import math
import os
import threading
import subprocess
import sys
import zipfile
import tempfile
import shutil
from updater import latest_release, compare_version, download_release, unpack_release, clean_repo
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from model import Document, bounding_box, distance, endpoints, move_entity
from exporters import export_dxf, export_dwg, export_step
from snapping import nearest_snap
from geometry_tools import trim_line, extend_line, circle_tangents
from geometry_v05 import group_rectangular_array, group_polar_array, corner_edit, edited_group

CONFIG=Path.home()/'.merbeincad_settings.json'
COLORS=['#e3ebf5','#38bdf8','#f59e0b','#a78bfa','#34d399','#fb7185']

class CAD(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MerbeinCAD 0.6  |  Untitled')
        self.geometry('1250x800');self.minsize(850,560)
        self.doc=Document();self.path=None;self.history=[];self.future=[]
        self.tool='select';self.pending=[];self.preview=None;self.selected=None;self.selection=set();self.drag=None;self.marquee=None
        self.zoom=3.0;self.cx=0.0;self.cy=0.0
        self.tangent_first=None;self.tangent_choices=[]
        self.array_pick=None
        self.grid_on=tk.BooleanVar(value=True);self.snap_on=tk.BooleanVar(value=True)
        self.snap_size=tk.StringVar(value='5');self.snap_marker=None
        self.snap_modes={k:tk.BooleanVar(value=True) for k in ('Endpoint','Midpoint','Centre','Quadrant','Intersection','Tangent')}
        self.circle_method=tk.StringVar(value='Point on circumference')
        self.circle_size=tk.StringVar(value='10')
        self.layer=tk.StringVar(value='0')
        self.status=tk.StringVar(value='Ready — units: mm')
        self.config_data=self.load_config()
        self.build_ui();self.bind_all('<Escape>',self.escape_command)
        self.bind('<Delete>',lambda e:self.delete_selected())
        self.bind('<Control-z>',lambda e:self.undo())
        self.bind('<Control-y>',lambda e:self.redo())
        self.bind('<Control-s>',lambda e:self.save())
        self.bind('<Control-o>',lambda e:self.open_project())
        self.bind('<Control-n>',lambda e:self.new_project())
        self.after(150,self.redraw)

    def load_config(self):
        try:return json.loads(CONFIG.read_text(encoding='utf-8'))
        except Exception:return {}
    def save_config(self):
        CONFIG.write_text(json.dumps(self.config_data,indent=2),encoding='utf-8')

    def build_ui(self):
        menu=tk.Menu(self);self.config(menu=menu)
        file=tk.Menu(menu,tearoff=0);menu.add_cascade(label='File',menu=file)
        for label,callback in [('New',self.new_project),('Open project…',self.open_project),('Save',self.save),('Save as…',self.save_as),('Import DXF…',self.import_dxf)]:file.add_command(label=label,command=callback)
        file.add_separator();file.add_command(label='Print / PDF…',command=self.print_drawing)
        file.add_separator();file.add_command(label='Exit',command=self.destroy)
        exports=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Export',menu=exports)
        exports.add_command(label='DXF…',command=self.save_dxf)
        exports.add_command(label='DWG (ODA converter)…',command=self.save_dwg)
        exports.add_command(label='STEP (extruded profiles)…',command=self.save_step)
        exports.add_separator();exports.add_command(label='Configure DWG converter…',command=self.configure_oda)
        edit=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Edit',menu=edit)
        for name,callback in [('Undo',self.undo),('Redo',self.redo),('Delete selected',self.delete_selected),('Edit selected geometry…',self.edit_selected),('Fit drawing',self.fit),('Rectangular array…',self.rectangular_array),('Polar array…',self.polar_array),('Move by…',self.move_precise),('Copy by…',self.copy_precise),('Rotate by…',self.rotate_precise),('Fillet two lines…',self.fillet),('Chamfer two lines…',self.chamfer),('Circle radius dimension…',self.radius_dimension),('Circle diameter dimension…',self.diameter_dimension)]:edit.add_command(label=name,command=callback)
        helpmenu=tk.Menu(menu,tearoff=0);menu.add_cascade(label='Help',menu=helpmenu)
        helpmenu.add_command(label='Check for Updates (GitHub)…',command=self.check_updates)
        helpmenu.add_command(label='Configure GitHub repository…',command=self.configure_github)
        helpmenu.add_separator()
        helpmenu.add_command(label='Version',command=lambda:messagebox.showinfo('MerbeinCAD','MerbeinCAD v0.6\nMouse-picked polar centre, Esc to Select, and toolbar tooltips.'))
        helpmenu.add_command(label='How to draw',command=lambda:messagebox.showinfo('Controls','Left click: points / select\nRight click: finish polyline\nMiddle mouse drag: pan\nWheel: zoom\nCtrl+click: alternate pan\nEsc: cancel command and return to Select\nDelete: delete selected\nDouble-click selected: edit exact coordinates\n\nCoordinate box: type x,y and press Add point.\nCoordinates and dimensions are in millimetres.'))
        tools=ttk.Frame(self,padding=4);tools.pack(side='top',fill='x')
        # Grouped toolbars keep icons readable on laptop screens and at 125% DPI.
        self.icon_buttons={};self.icon_images=[]
        from tooltips_v06 import ToolTip
        self.ToolTip=ToolTip
        for title,items in [('Draw',[('select','Select / Move'),('line','Line'),('rectangle','Rectangle'),('circle','Circle'),('polyline','Polyline'),('dimension','Dimension'),('bitangent','Tangent between circles')]),('Modify',[('trim','Trim'),('extend','Extend'),('fillet','Fillet'),('chamfer','Chamfer'),('delete','Delete'),('move','Move by'),('copy','Copy by'),('rotate','Rotate by')]),('Pattern',[('rectarray','Rectangular array'),('polararray','Polar array')]),('Output',[('print','Print PDF')])]:
            group=ttk.Frame(tools);group.pack(side='left',padx=(0,9))
            row=ttk.Frame(group);row.pack()
            for key,label in items:self.make_icon_button(row,key,label)
            ttk.Label(group,text=title,foreground='#526377',anchor='center').pack(fill='x')
        aux=ttk.Frame(self,padding=(6,2));aux.pack(side='top',fill='x')
        self.make_text_button(aux,'Fit',self.fit,'Fit the entire drawing to the window',padx=4)
        self.make_text_button(aux,'Undo',self.undo,'Undo last drawing change')
        self.make_text_button(aux,'Redo',self.redo,'Redo last undone change')
        ttk.Label(aux,text='  Layer').pack(side='left')
        self.layerbox=ttk.Combobox(aux,textvariable=self.layer,values=self.doc.layers,width=13,state='readonly');self.layerbox.pack(side='left')
        self.make_text_button(aux,'+',self.add_layer,'Add drawing layer',width=3)
        ttk.Checkbutton(aux,text='Grid',variable=self.grid_on,command=self.redraw).pack(side='left',padx=(8,0))
        ttk.Checkbutton(aux,text='Snap',variable=self.snap_on).pack(side='left')
        ttk.Label(aux,text='Spacing').pack(side='left');ttk.Entry(aux,textvariable=self.snap_size,width=5).pack(side='left')
        self.make_text_button(aux,'Check for Updates',self.check_updates,'Check GitHub for a newer MerbeinCAD release',side='right',padx=5)
        snapbar=ttk.Frame(self,padding=(8,1));snapbar.pack(side='top',fill='x')
        ttk.Label(snapbar,text='Object snaps:').pack(side='left')
        for key in self.snap_modes:
            ttk.Checkbutton(snapbar,text=key,variable=self.snap_modes[key],command=self.redraw).pack(side='left',padx=(7,0))
        ttk.Label(snapbar,text='   Hover near a snap point: green marker  |  Objects take priority over grid').pack(side='left')
        coord=ttk.Frame(self,padding=(8,2));coord.pack(fill='x')
        ttk.Label(coord,text='Exact point (mm):').pack(side='left')
        self.coord_entry=ttk.Entry(coord,width=22);self.coord_entry.pack(side='left',padx=5);self.coord_entry.bind('<Return>',lambda e:self.add_exact_point())
        self.make_text_button(coord,'Add point',self.add_exact_point,'Add a point at the typed X,Y coordinates')
        ttk.Label(coord,text='  Circle:').pack(side='left')
        ttk.Combobox(coord,textvariable=self.circle_method,values=['Point on circumference','Radius','Diameter'],width=23,state='readonly').pack(side='left',padx=3)
        ttk.Label(coord,text='Size (mm):').pack(side='left')
        ttk.Entry(coord,textvariable=self.circle_size,width=8).pack(side='left',padx=3)
        self.canvas=tk.Canvas(self,bg='#101827',highlightthickness=0,cursor='crosshair');self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.redraw())
        self.canvas.bind('<ButtonPress-1>',self.mouse_down)
        self.canvas.bind('<B1-Motion>',self.mouse_drag)
        self.canvas.bind('<ButtonRelease-1>',self.mouse_up)
        self.canvas.bind('<Motion>',self.motion)
        self.canvas.bind('<Double-Button-1>',lambda e:self.edit_selected())
        self.canvas.bind('<Button-3>',lambda e:self.finish_polyline())
        self.canvas.bind('<ButtonPress-2>',self.pan_start)
        self.canvas.bind('<B2-Motion>',self.pan_move)
        self.canvas.bind('<MouseWheel>',self.wheel)
        self.canvas.bind('<Button-4>',lambda e:self.zoom_at(e.x,e.y,1.1))
        self.canvas.bind('<Button-5>',lambda e:self.zoom_at(e.x,e.y,1/1.1))
        ttk.Label(self,textvariable=self.status,anchor='w',padding=5).pack(fill='x')

    def make_icon_button(self,parent,kind,label):
        button=tk.Button(parent,relief='flat',bd=1,background='#eff3f8',activebackground='#d5e9f7',cursor='hand2',padx=1,pady=1)
        try:
            from icons_v05 import draw_icon
            img=draw_icon(kind,scale=4,size=36)
            self.icon_images.append(img)  # Keep PhotoImage alive.
            button.configure(image=img,width=38,height=38)
        except ImportError:
            button.configure(text=label[:3],width=4,height=2)
        actions={'rectarray':self.rectangular_array,'polararray':self.polar_array,'print':self.print_drawing,'move':self.move_precise,'copy':self.copy_precise,'rotate':self.rotate_precise,'fillet':self.fillet,'chamfer':self.chamfer}
        button.configure(command=actions.get(kind,lambda k=kind:self.set_tool(k)))
        button.pack(side='left',padx=1)
        self.ToolTip(button,label + '  (' + kind + ')')
        button.bind('<Enter>',lambda e,n=label:self.status.set(n))
        button.bind('<Leave>',lambda e:self.status.set('Ready — units: mm'))
        self.icon_buttons[kind]=button

    def make_text_button(self,parent,label,command,tip,side='left',**pack):
        width=pack.pop('width',None)
        button=ttk.Button(parent,text=label,command=command,**({'width':width} if width else {}))
        button.pack(side=side,**pack)
        self.ToolTip(button,tip)
        return button

    def escape_command(self,event=None):
        """CAD-standard Esc: cancel in-progress operation and return to selection."""
        self.array_pick=None
        self.cancel()
        self.tool='select'
        self.status.set('Command cancelled — Select tool active')
        return 'break'

    def world(self,x,y):return ((x-self.canvas.winfo_width()/2)/self.zoom+self.cx,(self.canvas.winfo_height()/2-y)/self.zoom+self.cy)
    def screen(self,p):return ((p[0]-self.cx)*self.zoom+self.canvas.winfo_width()/2,(self.cy-p[1])*self.zoom+self.canvas.winfo_height()/2)
    def grid_spacing(self):
        try:return max(.001,float(self.snap_size.get()))
        except ValueError:return 5.0
    def snapped_at(self,x,y):
        p=self.world(x,y)
        if not self.snap_on.get():return list(p), None
        modes={name for name,enabled in self.snap_modes.items() if enabled.get()}
        anchor=self.pending[-1] if self.tool in ('line','polyline') and self.pending else None
        result=nearest_snap(p,self.doc.entities,11/self.zoom,modes,anchor=anchor) if modes else None
        if result is not None:return list(result.point),result
        step=self.grid_spacing()
        return [round(p[0]/step)*step,round(p[1]/step)*step],None
    def point_at(self,x,y):
        return self.snapped_at(x,y)[0]
    def draw_snap_marker(self):
        if not self.snap_marker or not self.snap_on.get():return
        result=self.snap_marker
        x,y=self.screen(result.point)
        color='#4ade80';size=7;kind=result.kind
        if kind=='Endpoint':self.canvas.create_rectangle(x-size,y-size,x+size,y+size,outline=color,width=2)
        elif kind=='Midpoint':self.canvas.create_polygon(x,y-size,x-size,y+size,x+size,y+size,outline=color,fill='',width=2)
        elif kind=='Centre':self.canvas.create_oval(x-size,y-size,x+size,y+size,outline=color,width=2)
        elif kind=='Quadrant':
            self.canvas.create_polygon(x,y-size,x+size,y,x,y+size,x-size,y,outline=color,fill='',width=2)
        elif kind=='Tangent':
            self.canvas.create_oval(x-size,y-size,x+size,y+size,outline=color,width=2)
            self.canvas.create_line(x-size,y+size,x+size,y+size,fill=color,width=2)
        elif kind=='Intersection':
            self.canvas.create_line(x-size,y-size,x+size,y+size,fill=color,width=2)
            self.canvas.create_line(x+size,y-size,x-size,y+size,fill=color,width=2)
        self.canvas.create_text(x+12,y-12,text=kind,anchor='sw',fill=color,font=('Segoe UI',10,'bold'))
    def set_tool(self,tool):
        self.array_pick=None;self.tool=tool;self.cancel();self.tangent_first=None;self.tangent_choices=[]
        self.status.set({'bitangent':'Click first circle then second circle; choose tangent line', 'trim':'Click the portion of a LINE to remove (other objects are cutting boundaries)', 'extend':'Click near an end of a LINE to extend it to the nearest boundary', 'delete':'Click an object to delete it'}.get(tool,f'{tool.title()} tool — mm'))
    def cancel(self):self.pending=[];self.preview=None;self.snap_marker=None;self.drag=None;self.marquee=None;self.tangent_first=None;self.tangent_choices=[];self.redraw()
    def snapshot(self):self.history.append(copy.deepcopy(self.doc.entities));self.history=self.history[-80:];self.future.clear()
    def undo(self):
        if self.history:self.future.append(copy.deepcopy(self.doc.entities));self.doc.entities=self.history.pop();self.selected=None;self.selection.clear();self.redraw()
    def redo(self):
        if self.future:self.history.append(copy.deepcopy(self.doc.entities));self.doc.entities=self.future.pop();self.selected=None;self.selection.clear();self.redraw()
    def add_entity(self,e):
        self.snapshot();e['layer']=self.layer.get();self.doc.entities.append(e);self.selected=len(self.doc.entities)-1;self.selection={self.selected};self.redraw()
    def accept_point(self,p):
        if self.tool=='select':return
        if self.tool=='polyline':self.pending.append(p);self.redraw();return
        self.pending.append(p)
        if self.tool=='circle' and len(self.pending)==1 and self.circle_method.get()!='Point on circumference':
            try:
                size=float(self.circle_size.get())
                if not math.isfinite(size) or size<=0:raise ValueError()
            except ValueError:
                self.pending=[];messagebox.showerror('Circle size','Enter a positive radius or diameter in millimetres.');return
            self.pending=[]
            radius=size/2 if self.circle_method.get()=='Diameter' else size
            self.add_entity({'type':'circle','center':p,'radius':radius});return
        if len(self.pending)<2:self.redraw();return
        a,b=self.pending[:2];self.pending=[]
        if distance(a,b)<1e-8:return
        if self.tool=='line':e={'type':'line','a':a,'b':b}
        elif self.tool=='rectangle':e={'type':'rectangle','a':a,'b':b}
        elif self.tool=='circle':e={'type':'circle','center':a,'radius':distance(a,b)}
        elif self.tool=='dimension':e={'type':'dimension','a':a,'b':b,'layer':'Dimensions'}
        else:return
        self.add_entity(e)
    def finish_polyline(self):
        if self.tool!='polyline' or len(self.pending)<2:self.cancel();return
        if len(self.pending)>=3:
            result=messagebox.askyesnocancel('Finish polyline','Close polyline into a profile?\nYes: closed / No: open / Cancel: keep drawing')
            if result is None:return
        else:result=False
        points=self.pending[:];self.pending=[];self.add_entity({'type':'polyline','points':points,'closed':result})
    def add_exact_point(self):
        try:
            numbers=self.coord_entry.get().replace(';',',').split(',')
            if len(numbers)!=2:raise ValueError()
            x,y=map(float,numbers)
        except ValueError:messagebox.showerror('Coordinates','Enter exact X,Y, for example 125,75');return
        self.accept_point([x,y]);self.coord_entry.delete(0,'end')
    def point_segment_distance(self,p,a,b):
        x,y=p;dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/den)) if den else 0
        return distance(p,[a[0]+t*dx,a[1]+t*dy])
    def hit(self,p):
        tol=10/self.zoom
        for i in reversed(range(len(self.doc.entities))):
            e=self.doc.entities[i];t=e['type']
            if t=='circle':d=abs(distance(p,e['center'])-e['radius'])
            else:
                if t=='line' or t=='dimension':pts=[e['a'],e['b']]
                elif t=='rectangle':
                    (x1,y1),(x2,y2)=e['a'],e['b'];pts=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]
                else:pts=e['points']+([e['points'][0]] if e.get('closed') else [])
                d=min((self.point_segment_distance(p,a,b) for a,b in zip(pts,pts[1:])),default=float('inf'))
            if d<=tol:return i
        return None
    def mouse_down(self,event):
        if self.array_pick is not None:
            self.complete_polar_array(self.point_at(event.x,event.y))
            return
        if event.state & 0x0004:self.pan_start(event);self.drag=('pan',event.x,event.y);return
        if self.tool in ('trim','extend','delete'):
            index=self.hit(self.world(event.x,event.y))
            if index is None:return
            if self.tool=='delete':
                self.snapshot();del self.doc.entities[index];self.selected=None;self.redraw();return
            selected=self.doc.entities[index]
            if selected['type']!='line':
                self.status.set('Trim/Extend currently works on LINE entities, not circles or polylines.');return
            boundaries=[e for j,e in enumerate(self.doc.entities) if j!=index]
            try:
                edited=trim_line(selected,boundaries,self.world(event.x,event.y)) if self.tool=='trim' else [extend_line(selected,boundaries,self.world(event.x,event.y))]
                self.snapshot();self.doc.entities[index:index+1]=edited;self.selected=None;self.redraw()
            except ValueError as exc:self.status.set(str(exc));self.bell()
            return
        if self.tool=='bitangent':
            world=self.world(event.x,event.y)
            if self.tangent_choices:
                def dist_to_segment(t):return self.point_segment_distance(world,t[0],t[1])
                a,b,style=min(self.tangent_choices,key=dist_to_segment)
                self.tangent_first=None;self.tangent_choices=[]
                self.add_entity({'type':'line','a':list(a),'b':list(b)});
                self.status.set('Created '+style.lower()+' common tangent');return
            idx=self.hit(world)
            if idx is None or self.doc.entities[idx]['type']!='circle':
                self.status.set('Select a circle circumference.');return
            if self.tangent_first is None:
                self.tangent_first=idx;self.status.set('Now click the second circle.');return
            if idx==self.tangent_first:
                self.status.set('Select a different circle.');return
            first=self.doc.entities[self.tangent_first];second=self.doc.entities[idx]
            self.tangent_choices=circle_tangents(first['center'],first['radius'],second['center'],second['radius'])
            if not self.tangent_choices:self.status.set('No common tangents for these circles.');self.tangent_first=None
            else:self.status.set('Click near the desired dotted tangent line.');self.redraw()
            return
        if self.tool=='select':
            index=self.hit(self.world(event.x,event.y))
            shift=bool(event.state & 0x0001)
            if index is None:
                if not shift:self.selection.clear();self.selected=None
                self.drag=('marquee',event.x,event.y,shift);self.marquee=(event.x,event.y,event.x,event.y)
            else:
                if shift:
                    if index in self.selection:self.selection.remove(index)
                    else:self.selection.add(index)
                    self.selected=next(iter(sorted(self.selection)),None)
                else:
                    if index not in self.selection:self.selection={index}
                    self.selected=index
                    originals={i:copy.deepcopy(self.doc.entities[i]) for i in self.selection}
                    self.drag=('movegroup',event.x,event.y,originals)
            self.redraw();return
        self.accept_point(self.point_at(event.x,event.y))
    def mouse_drag(self,event):
        if not self.drag:return
        if self.drag[0]=='pan':self.pan_move(event);return
        if self.drag[0]=='marquee':
            self.marquee=(self.drag[1],self.drag[2],event.x,event.y);self.redraw();return
        if self.drag[0]=='movegroup':
            _,ox,oy,originals=self.drag
            if abs(event.x-ox)+abs(event.y-oy)<2:return
            if not getattr(self,'drag_snapshot',False):self.snapshot();self.drag_snapshot=True
            dx=(event.x-ox)/self.zoom;dy=(oy-event.y)/self.zoom
            for i,original in originals.items():self.doc.entities[i]=move_entity(original,dx,dy)
            self.redraw()
    def mouse_up(self,event):
        if self.drag and self.drag[0]=='marquee':
            _,x0,y0,additive=self.drag
            x1,y1=event.x,event.y
            if abs(x1-x0)>3 or abs(y1-y0)>3:
                left,right=sorted((x0,x1));top,bottom=sorted((y0,y1))
                # Left-to-right: fully inside; right-to-left: crossing selection.
                crossing=x1<x0
                from model import entity_points
                for i,e in enumerate(self.doc.entities):
                    points=[self.screen(p) for p in entity_points(e)]
                    if not points:continue
                    a,b=min(p[0] for p in points),max(p[0] for p in points)
                    c,d=min(p[1] for p in points),max(p[1] for p in points)
                    if (a<=right and b>=left and c<=bottom and d>=top) if crossing else (left<=a and b<=right and top<=c and d<=bottom):
                        self.selection.add(i)
                self.selected=next(iter(sorted(self.selection)),None)
            self.marquee=None;self.redraw()
        self.drag=None;self.drag_snapshot=False
    def pan_start(self,event):self.pan_origin=(event.x,event.y,self.cx,self.cy)
    def pan_move(self,event):
        x,y,cx,cy=self.pan_origin;self.cx=cx+(x-event.x)/self.zoom;self.cy=cy+(event.y-y)/self.zoom;self.redraw()
    def wheel(self,event):self.zoom_at(event.x,event.y,1.15 if event.delta>0 else 1/1.15)
    def zoom_at(self,x,y,scale):
        before=self.world(x,y);self.zoom=min(250,max(.03,self.zoom*scale));after=self.world(x,y)
        self.cx+=before[0]-after[0];self.cy+=before[1]-after[1];self.redraw()
    def motion(self,event):
        p,self.snap_marker=self.snapped_at(event.x,event.y);self.preview=p
        label=('  |  SNAP: '+self.snap_marker.kind) if self.snap_marker else ''
        self.status.set(f'{"Pick array centre" if self.array_pick is not None else self.tool.title()}  |  X {p[0]:.2f} mm   Y {p[1]:.2f} mm  |  Zoom {self.zoom:.2f} px/mm   |  {len(self.doc.entities)} entities{label}')
        self.redraw()
    def line(self,a,b,fill,width=2,dash=None):
        self.canvas.create_line(*self.screen(a),*self.screen(b),fill=fill,width=width,dash=dash)
    def draw_entity(self,e,selected=False):
        color='#fb7185' if selected else COLORS[self.doc.layers.index(e.get('layer','0'))%len(COLORS)] if e.get('layer','0') in self.doc.layers else '#e3ebf5'
        t=e['type']
        if t=='line':self.line(e['a'],e['b'],color)
        elif t=='rectangle':
            x1,y1=e['a'];x2,y2=e['b'];self.canvas.create_rectangle(*self.screen([x1,y1]),*self.screen([x2,y2]),outline=color,width=2)
        elif t=='circle':
            x,y=self.screen(e['center']);r=e['radius']*self.zoom;self.canvas.create_oval(x-r,y-r,x+r,y+r,outline=color,width=2)
        elif t=='polyline':
            pts=e['points']+([e['points'][0]] if e.get('closed') and e['points'] else [])
            for a,b in zip(pts,pts[1:]):self.line(a,b,color)
        elif t=='dimension':
            a,b=e['a'],e['b'];self.line(a,b,color,1)
            for p in (a,b):
                x,y=self.screen(p);self.canvas.create_line(x-4,y-4,x+4,y+4,fill=color);self.canvas.create_line(x+4,y-4,x-4,y+4,fill=color)
            a2=self.screen(a);b2=self.screen(b);length=distance(a,b)
            self.canvas.create_text((a2[0]+b2[0])/2,(a2[1]+b2[1])/2-12,text=(('Ø' if e.get('kind')=='diameter' else 'R')+f'{e.get("value",length):.2f} mm') if e.get('kind') in ('radius','diameter') else f'{length:.2f} mm',fill=color,font=('Segoe UI',10,'bold'))
    def redraw(self):
        if not hasattr(self,'canvas'):return
        c=self.canvas;c.delete('all');w=c.winfo_width();h=c.winfo_height()
        if w<10:return
        if self.grid_on.get():
            step=self.grid_spacing()
            while step*self.zoom<22:step*=2
            if step*self.zoom<1500:
                left,bottom=self.world(0,h);right,top=self.world(w,0)
                for i in range(math.floor(left/step),math.ceil(right/step)+1):
                    x=self.screen([i*step,0])[0];c.create_line(x,0,x,h,fill='#233044')
                for j in range(math.floor(bottom/step),math.ceil(top/step)+1):
                    y=self.screen([0,j*step])[1];c.create_line(0,y,w,y,fill='#233044')
        x0,y0=self.screen([0,0]);c.create_line(x0,0,x0,h,fill='#54718a');c.create_line(0,y0,w,y0,fill='#54718a')
        for i,e in enumerate(self.doc.entities):self.draw_entity(e,i in self.selection)
        if self.pending:
            for a,b in zip(self.pending,self.pending[1:]):self.line(a,b,'#fbbf24',2)
            if self.preview:self.line(self.pending[-1],self.preview,'#fbbf24',1,(4,4))
            for p in self.pending:
                x,y=self.screen(p);c.create_oval(x-3,y-3,x+3,y+3,fill='#fbbf24')
        if self.tangent_choices:
            for a,b,style in self.tangent_choices:self.line(a,b,'#4ade80' if style=='External' else '#fbbf24',2,(4,3))
        if self.marquee:
            x0,y0,x1,y1=self.marquee;c.create_rectangle(x0,y0,x1,y1,outline='#38bdf8',dash=(4,3),width=1)
        self.draw_snap_marker()
        c.create_text(w-12,12,anchor='ne',text='MERBEIN ROBOTICS  |  CAD v0.6',fill='#7697b4',font=('Segoe UI',10,'bold'))
    def selected_entities(self):
        return [self.doc.entities[i] for i in sorted(self.selection) if i<len(self.doc.entities)]
    def selection_required(self):
        if self.selected_entities():return True
        messagebox.showinfo('Selection required','Select one or more objects using the arrow tool. Shift+click adds objects; drag an empty area for window selection.');return False
    def rectangular_array(self):
        if not self.selection_required():return
        rows=simpledialog.askinteger('Rectangular array','Number of rows:',initialvalue=2,minvalue=1,maxvalue=100,parent=self)
        if rows is None:return
        cols=simpledialog.askinteger('Rectangular array','Number of columns:',initialvalue=3,minvalue=1,maxvalue=100,parent=self)
        if cols is None:return
        dx=simpledialog.askfloat('Rectangular array','Column spacing (mm):',initialvalue=25,parent=self)
        if dx is None:return
        dy=simpledialog.askfloat('Rectangular array','Row spacing (mm):',initialvalue=25,parent=self)
        if dy is None:return
        try:items=group_rectangular_array(self.selected_entities(),rows,cols,dx,dy)
        except ValueError as exc:messagebox.showerror('Array',str(exc));return
        if items:self.snapshot();self.doc.entities.extend(items);self.redraw()
    def ask_xy(self,title,prompt='X,Y in millimetres:',default='0,0'):
        raw=simpledialog.askstring(title,prompt,initialvalue=default,parent=self)
        if raw is None:return None
        try:
            xy=[float(t.strip()) for t in raw.split(',')]
            if len(xy)!=2 or not all(math.isfinite(t) for t in xy):raise ValueError()
            return xy
        except ValueError:
            messagebox.showerror(title,'Enter two finite numbers separated by a comma, e.g. 25,-10');return None
    def polar_array(self):
        if not self.selection_required():return
        count=simpledialog.askinteger('Polar array','Total items including originals:',initialvalue=6,minvalue=2,maxvalue=360,parent=self)
        if count is None:return
        sweep=simpledialog.askfloat('Polar array','Angular sweep in degrees:',initialvalue=360,parent=self)
        if sweep is None:return
        # Yes -> choose in canvas; No -> type coordinates; Cancel -> abandon.
        pick=messagebox.askyesnocancel('Polar array centre',
            'Pick the centre on the drawing using your mouse?\n\n'
            'Yes: pick a point (object snaps enabled)\n'
            'No: enter X,Y coordinates\nCancel: abandon array',parent=self)
        if pick is None:return
        if pick:
            self.array_pick=(count,sweep)
            self.pending=[];self.preview=None
            self.status.set('Polar array: click the centre (Esc cancels). Snapping is active.')
            self.canvas.configure(cursor='crosshair')
            return
        center=self.ask_xy('Polar array','Centre X,Y (mm):')
        if center is not None:self.create_polar_array(center,count,sweep)

    def complete_polar_array(self,centre):
        if self.array_pick is None:return
        count,sweep=self.array_pick
        self.array_pick=None
        self.create_polar_array(centre,count,sweep)
        self.status.set(f'Polar array created around X {centre[0]:.2f}, Y {centre[1]:.2f} mm')

    def create_polar_array(self,centre,count,sweep):
        try:items=group_polar_array(self.selected_entities(),centre,count,sweep)
        except ValueError as exc:messagebox.showerror('Array',str(exc));return
        if items:
            self.snapshot();self.doc.entities.extend(items);self.redraw()

    def move_precise(self):
        if not self.selection_required():return
        delta=self.ask_xy('Move','Movement X,Y in mm:')
        if delta is None:return
        self.snapshot()
        for i in self.selection:self.doc.entities[i]=move_entity(self.doc.entities[i],*delta)
        self.redraw()
    def copy_precise(self):
        if not self.selection_required():return
        delta=self.ask_xy('Copy','Copy offset X,Y in mm:',default='25,0')
        if delta is None:return
        self.snapshot();self.doc.entities.extend([move_entity(e,*delta) for e in self.selected_entities()]);self.redraw()
    def rotate_precise(self):
        if not self.selection_required():return
        pivot=self.ask_xy('Rotate','Pivot X,Y (mm):')
        if pivot is None:return
        angle=simpledialog.askfloat('Rotate','Angle (degrees, counterclockwise):',initialvalue=90,parent=self)
        if angle is None:return
        from geometry_tools import rotate_entity
        self.snapshot()
        for i in self.selection:self.doc.entities[i]=rotate_entity(self.doc.entities[i],pivot,angle)
        self.redraw()
    def corner_tool(self,fillet):
        if len(self.selection)!=2:
            messagebox.showinfo('Corner tool','Select exactly two straight lines (click first, then Shift+click second).');return
        size=simpledialog.askfloat('Fillet radius' if fillet else 'Chamfer distance','Radius (mm):' if fillet else 'Distance along each line (mm):',initialvalue=5,minvalue=.000001,parent=self)
        if size is None:return
        i,j=sorted(self.selection)
        try:a,b,join=corner_edit(self.doc.entities[i],self.doc.entities[j],size,fillet)
        except ValueError as exc:messagebox.showerror('Corner tool',str(exc));return
        self.snapshot();self.doc.entities[i]=a;self.doc.entities[j]=b;self.doc.entities.append(join)
        self.selection={i,j,len(self.doc.entities)-1};self.selected=i;self.redraw()
    def fillet(self):self.corner_tool(True)
    def chamfer(self):self.corner_tool(False)
    def circle_dimension(self,diameter=False):
        if len(self.selection)!=1:
            messagebox.showinfo('Dimension','Select exactly one circle first.');return
        e=self.doc.entities[next(iter(self.selection))]
        if e['type']!='circle':messagebox.showerror('Dimension','Select a circle.');return
        center=e['center'];end=[center[0]+e['radius'],center[1]]
        self.add_entity({'type':'dimension','a':list(center),'b':end,'kind':'diameter' if diameter else 'radius','value':(2 if diameter else 1)*e['radius']})
    def radius_dimension(self):self.circle_dimension(False)
    def diameter_dimension(self):self.circle_dimension(True)

    def print_drawing(self):
        """Vector PDF preview/print (A4/A3); opens system PDF viewer for printing."""
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4,A3,landscape
        except ImportError:
            messagebox.showerror('Printing requires ReportLab','Run: py -m pip install reportlab');return
        if not self.doc.entities:messagebox.showinfo('Print','There is nothing to print.');return
        size=simpledialog.askstring('Print / PDF','Page size and orientation: A4L, A4P, A3L or A3P',initialvalue='A4L',parent=self)
        if size is None:return
        size=size.strip().upper()
        if size not in ('A4L','A4P','A3L','A3P'):messagebox.showerror('Print','Choose A4L, A4P, A3L or A3P.');return
        file=filedialog.asksaveasfilename(title='Save printable drawing',defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='MerbeinCAD_drawing.pdf')
        if not file:return
        from model import bounding_box
        page=A4 if size.startswith('A4') else A3
        if size.endswith('L'):page=landscape(page)
        w,h=page;margin=40
        x1,y1,x2,y2=bounding_box(self.doc.entities)
        dx=max(x2-x1,1);dy=max(y2-y1,1)
        scale=min((w-2*margin)/dx,(h-2*margin)/dy)
        ox=w/2-scale*(x1+x2)/2;oy=h/2-scale*(y1+y2)/2
        def pt(p):return (ox+scale*p[0],oy+scale*p[1])
        pdf=pdf_canvas.Canvas(file,pagesize=page)
        pdf.setTitle('MerbeinCAD drawing');pdf.setStrokeColorRGB(0,0,0);pdf.setLineWidth(.65)
        from snapping import segments
        for e in self.doc.entities:
            if e['type']=='circle':
                x,y=pt(e['center']);pdf.circle(x,y,e['radius']*scale,stroke=1,fill=0)
            else:
                for a,b in segments(e):pdf.line(*pt(a),*pt(b))
                if e['type']=='dimension':
                    a,b=e['a'],e['b'];x,y=pt([(a[0]+b[0])/2,(a[1]+b[1])/2]);pdf.setFont('Helvetica',9)
                    pdf.drawString(x+4,y+5, (('D' if e.get('kind')=='diameter' else 'R')+f'{e.get("value",distance(a,b)):.2f} mm') if e.get('kind') in ('radius','diameter') else f'{distance(a,b):.2f} mm')
        pdf.setFont('Helvetica',8);pdf.drawString(margin,20,'MerbeinCAD v0.6 | mm | Fit to page - NOT 1:1 scale')
        pdf.showPage();pdf.save()
        self.status.set('Print PDF saved: '+file)
        if messagebox.askyesno('PDF ready','Drawing saved to PDF. Open it for printing?'):
            if sys.platform=='win32':os.startfile(file)
            else:messagebox.showinfo('Saved',file)

    def delete_selected(self):
        if not self.selection:return
        self.snapshot();self.doc.entities=[e for i,e in enumerate(self.doc.entities) if i not in self.selection];self.selected=None;self.selection.clear();self.redraw()
    def edit_selected(self):
        if self.selected is None:return
        e=self.doc.entities[self.selected]
        text=simpledialog.askstring('Edit exact geometry (mm)','Edit coordinates as JSON. Keep entity type unchanged.',initialvalue=json.dumps(e,indent=2),parent=self)
        if text is None:return
        try:
            changed=json.loads(text)
            if changed.get('type')!=e['type']:raise ValueError('Type cannot change')
            self.snapshot();self.doc.entities[self.selected]=changed;self.redraw()
        except Exception as exc:messagebox.showerror('Invalid geometry',str(exc))
    def add_layer(self):
        name=simpledialog.askstring('New layer','Layer name:',parent=self)
        if name and name not in self.doc.layers:self.doc.layers.append(name);self.layerbox['values']=self.doc.layers;self.layer.set(name)
    def fit(self):
        x1,y1,x2,y2=bounding_box(self.doc.entities);self.cx=(x1+x2)/2;self.cy=(y1+y2)/2
        w=max(x2-x1,30);h=max(y2-y1,30)
        self.zoom=max(.03,min(200,.82*min(self.canvas.winfo_width()/w,self.canvas.winfo_height()/h)));self.redraw()
    def new_project(self):
        if not messagebox.askyesno('New project','Discard current unsaved work?'):return
        self.doc=Document();self.path=None;self.history.clear();self.future.clear();self.selected=None;self.selection.clear();self.layer.set('0');self.layerbox['values']=self.doc.layers;self.title('MerbeinCAD 0.6 | Untitled');self.redraw()
    def open_project(self):
        filename=filedialog.askopenfilename(filetypes=[('MerbeinCAD projects','*.mrcad')]);
        if not filename:return
        try:self.doc=Document.load(filename);self.path=filename;self.layerbox['values']=self.doc.layers;self.layer.set(self.doc.layers[0]);self.history.clear();self.future.clear();self.selected=None;self.selection.clear();self.title('MerbeinCAD 0.6 | '+Path(filename).name);self.fit()
        except Exception as exc:messagebox.showerror('Open failed',str(exc))
    def configure_github(self):
        current=self.config_data.get('github_repo','')
        repo=simpledialog.askstring('GitHub updates','Public GitHub repository (owner/repository or GitHub URL):',initialvalue=current,parent=self)
        if repo is None:return
        try:repo=clean_repo(repo)
        except ValueError as exc:messagebox.showerror('Invalid repository',str(exc));return
        self.config_data['github_repo']=repo;self.save_config()
        messagebox.showinfo('GitHub configured','Updates will be checked from: '+repo+'\n\nPublish a GitHub Release with an attached MerbeinCAD_Update.zip asset.')

    def check_updates(self):
        repo=self.config_data.get('github_repo')
        if not repo:
            self.configure_github();repo=self.config_data.get('github_repo')
            if not repo:return
        self.status.set('Checking GitHub releases for '+repo+'…')
        def worker():
            try:
                release=latest_release(repo)
                self.after(0,lambda:self.update_found(release,repo))
            except Exception as exc:
                error=str(exc)
                self.after(0,lambda:messagebox.showerror('Update check failed',error))
                self.after(0,lambda:self.status.set('Update check failed'))
        threading.Thread(target=worker,daemon=True).start()

    def update_found(self,release,repo):
        tag=release.get('tag_name','')
        try:newer=compare_version(tag,'0.6')>0
        except ValueError:
            messagebox.showwarning('Unrecognised version',f'GitHub release tag {tag!r} is not a numeric version (e.g. v0.5).');return
        if not newer:
            self.status.set('MerbeinCAD v0.6 is current')
            messagebox.showinfo('Updates','MerbeinCAD v0.6 is up to date. Latest GitHub release: '+tag);return
        assets=[a for a in release.get('assets',[]) if a.get('name')=='MerbeinCAD_Update.zip']
        if not assets:
            messagebox.showinfo('New release available',f'Version {tag} is available but has no MerbeinCAD_Update.zip asset.\n\nVisit: {release.get("html_url", "GitHub Releases")}');return
        if not messagebox.askyesno('Update available',f'MerbeinCAD {tag} is available.\n\nDownload and install the GitHub release update?\nYour existing application will be backed up. Drawings will not be changed.'):
            return
        self.status.set('Downloading '+tag+'…')
        def worker():
            try:
                root=Path(__file__).resolve().parent.parent
                if root.name.lower()!='merbeincad' or not (root/'Application').is_dir():
                    raise RuntimeError('GitHub installer requires the standard C:\\MerbeinCAD\\Application folder structure.')
                target=root/'Updates'/('MerbeinCAD_'+tag+'_Update.zip')
                download_release(assets[0],target,repo,tag)
                # Inspect ZIP before starting external updater.
                unpack_dir=unpack_release(target,root/'Updates'/('ready_'+tag))
                self.after(0,lambda:self.install_downloaded(unpack_dir,tag))
            except Exception as exc:
                error=str(exc)
                self.after(0,lambda:messagebox.showerror('Update download failed',error))
        threading.Thread(target=worker,daemon=True).start()

    def install_downloaded(self,folder,tag):
        script=folder/'Install_Update.ps1'
        if not script.is_file():messagebox.showerror('Update failed','Installer missing from downloaded package.');return
        if not messagebox.askyesno('Install '+tag,'Save any unsaved drawings first.\n\nClose MerbeinCAD and install the update now?'):
            return
        # Updater is a separate PowerShell process, waits for CAD to close.
        try:
            subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),'-WaitForExit'],creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as exc:messagebox.showerror('Cannot start installer',str(exc));return
        self.destroy()

    def save(self,event=None):
        if not self.path:return self.save_as()
        try:self.doc.save(self.path);self.status.set('Saved '+self.path)
        except Exception as exc:messagebox.showerror('Save failed',str(exc))
    def save_as(self):
        filename=filedialog.asksaveasfilename(defaultextension='.mrcad',filetypes=[('MerbeinCAD project','*.mrcad')]);
        if filename:self.path=filename;self.save();self.title('MerbeinCAD 0.6 | '+Path(filename).name)
    def save_dxf(self):
        path=filedialog.asksaveasfilename(defaultextension='.dxf',filetypes=[('AutoCAD DXF','*.dxf')]);
        if path:
            try:export_dxf(self.doc,path);messagebox.showinfo('DXF exported',path)
            except Exception as exc:messagebox.showerror('DXF error',str(exc))
    def configure_oda(self):
        path=filedialog.askopenfilename(title='Select ODAFileConverter.exe',filetypes=[('Executable','*.exe'),('All files','*.*')])
        if path:self.config_data['oda']=path;self.save_config()
    def save_dwg(self):
        if not self.config_data.get('oda'):
            messagebox.showinfo('ODA needed','Install ODA File Converter (free download), then select its .exe.');self.configure_oda()
        if not self.config_data.get('oda'):return
        path=filedialog.asksaveasfilename(defaultextension='.dwg',filetypes=[('AutoCAD DWG','*.dwg')]);
        if path:
            try:export_dwg(self.doc,path,self.config_data['oda']);messagebox.showinfo('DWG exported',path)
            except Exception as exc:messagebox.showerror('DWG error',str(exc))
    def save_step(self):
        value=simpledialog.askfloat('Extrude profiles to STEP','Extrusion thickness (mm):',minvalue=.001,initialvalue=5,parent=self)
        if value is None:return
        path=filedialog.asksaveasfilename(defaultextension='.step',filetypes=[('STEP 3D solid','*.step')]);
        if path:
            try:
                count,skipped=export_step(self.doc,path,value)
                messagebox.showinfo('STEP exported',f'Exported {count} independent solid(s).\nSkipped {skipped} open/dimension entities.\nOverlapping profiles are not fused or subtracted.')
            except Exception as exc:messagebox.showerror('STEP error',str(exc))
    def import_dxf(self):
        path=filedialog.askopenfilename(filetypes=[('DXF','*.dxf')]);
        if not path:return
        try:
            import ezdxf
            source=ezdxf.readfile(path);new=[]
            for obj in source.modelspace():
                t=obj.dxftype();layer=obj.dxf.layer
                if layer not in self.doc.layers:self.doc.layers.append(layer)
                if t=='LINE':new.append({'type':'line','a':list(obj.dxf.start[:2]),'b':list(obj.dxf.end[:2]),'layer':layer})
                elif t=='CIRCLE':new.append({'type':'circle','center':list(obj.dxf.center[:2]),'radius':obj.dxf.radius,'layer':layer})
                elif t=='LWPOLYLINE':
                    if any(abs(p[4])>1e-9 for p in obj.get_points('xyseb')):continue # arcs not approximated
                    new.append({'type':'polyline','points':[list(p) for p in obj.get_points('xy')],'closed':obj.closed,'layer':layer})
            self.snapshot();self.doc.entities.extend(new);self.layerbox['values']=self.doc.layers;self.fit()
            messagebox.showinfo('DXF import',f'Imported {len(new)} supported line, circle and straight polyline entities.\nUnsupported geometry skipped.')
        except Exception as exc:messagebox.showerror('Import failed',str(exc))

if __name__=='__main__':CAD().mainloop()
