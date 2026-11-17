"""Supersampled crisp toolbar icons, rendered from resolution-independent paths.

Pillow is optional: falls back to Tk Canvas paths when not installed.
"""
from math import cos,sin,pi

def draw_icon(kind, scale=4, size=38):
    from PIL import Image,ImageDraw,ImageFont,ImageTk
    S=scale; W=size*S
    im=Image.new('RGBA',(W,W),(241,245,249,255));d=ImageDraw.Draw(im)
    navy=(25,49,75,255);accent=(20,132,178,255)
    def pt(p):return (round(p[0]*S),round(p[1]*S))
    def line(points,color=navy,width=2):d.line([pt(p) for p in points],fill=color,width=max(1,int(S*width)),joint='curve')
    def oval(box,color=navy,width=2):d.ellipse(tuple(pt(p) for p in box),outline=color,width=max(1,int(S*width)))
    def rect(box,color=navy,width=2):d.rectangle(tuple(pt(p) for p in box),outline=color,width=max(1,int(S*width)))
    def dot(p):d.ellipse((pt((p[0]-2,p[1]-2))+pt((p[0]+2,p[1]+2))),fill=accent)
    if kind=='select':
        d.polygon([pt(p) for p in [(10,6),(10,30),(17,24),(22,32),(26,30),(21,22),(30,22)]],outline=navy,fill=(231,239,247,255));line([(10,6),(30,22)])
    elif kind=='line':line([(7,29),(30,8)]);dot((7,29));dot((30,8))
    elif kind=='rectangle':rect(((7,8),(30,29)))
    elif kind=='circle':oval(((7,7),(31,31)))
    elif kind=='polyline':line([(5,29),(14,10),(23,22),(32,8)]);dot((5,29));dot((32,8))
    elif kind=='dimension':
        line([(6,27),(32,27)],accent,1);line([(6,20),(6,32)],width=1);line([(32,20),(32,32)],width=1)
        line([(6,27),(12,24),(12,30),(6,27)],accent,1);line([(32,27),(26,24),(26,30),(32,27)],accent,1)
        d.text(pt((14,8)),'12',fill=navy,stroke_width=0)
    elif kind=='bitangent':oval(((4,12),(19,27)));oval(((23,16),(34,27)));line([(12,12),(28,16)],accent)
    elif kind=='trim':line([(5,29),(32,6)]);line([(6,7),(32,31)]);line([(17,19),(29,30)],(218,62,62,255),3)
    elif kind=='extend':line([(6,30),(21,17)]);line([(21,17),(33,6)],accent,1);line([(26,7),(33,6),(31,14)],accent,2)
    elif kind=='delete':rect(((11,11),(28,31)));line([(8,9),(31,9)]);line([(15,6),(24,6)]);line([(17,15),(17,27)],width=1);line([(23,15),(23,27)],width=1)
    elif kind=='fillet':
        line([(5,29),(16,29)]);line([(29,16),(29,5)]);d.arc((*pt((16,16)),*pt((42,42))),180,270,fill=accent,width=3*S)
    elif kind=='chamfer':line([(5,29),(18,29),(29,18),(29,5)]);line([(18,29),(29,18)],accent,3)
    elif kind=='move':line([(19,5),(19,33)]);line([(5,19),(33,19)]);line([(19,5),(15,11)]);line([(19,5),(23,11)]);line([(5,19),(11,15)]);line([(5,19),(11,23)])
    elif kind=='copy':rect(((6,14),(24,32)));rect(((14,6),(32,24)),accent)
    elif kind=='rotate':d.arc((*pt((6,6)),*pt((32,32))),30,300,fill=navy,width=3*S);line([(29,8),(32,18),(23,15)],accent,2)
    elif kind=='rectarray':
        for x in [6,17,28]:
            for y in [8,19]:rect(((x,y),(x+6,y+6)),accent,1)
    elif kind=='polararray':
        for a in range(0,360,60):
            x=19+12*cos(a*pi/180);y=19+12*sin(a*pi/180);oval(((x-2,y-2),(x+2,y+2)),accent,1)
        dot((19,19))
    elif kind=='print':rect(((8,14),(30,28)));rect(((12,6),(26,15)));rect(((12,23),(26,33)),accent)
    else:line([(7,28),(30,9)])
    im=im.resize((size,size),Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(im)
