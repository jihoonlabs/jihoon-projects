"""Original grid drawings baked into 72x32 VLSB pictures; Pillow is build-only."""
import argparse
import json
from PIL import Image, ImageDraw


def pictures():
    result=[]
    # Departure: large traveller with pack and walking stick, gate behind him.
    im=Image.new('1',(72,32));d=ImageDraw.Draw(im)
    d.polygon([(1,10),(5,10),(10,6),(23,6),(29,10),(33,10),(29,12),(3,12)],fill=1)
    d.rectangle((6,13,27,24),fill=1);d.rectangle((12,16,20,25),fill=0)
    d.line((16,16,16,23),fill=1);d.rectangle((4,25,29,26),fill=1)
    d.line((21,27,36,31),fill=1);d.line((30,24,69,31),fill=1)
    d.polygon([(46,3),(52,2),(56,5),(56,8),(59,9),(56,11),(55,13),(48,13),(45,9)],fill=1)
    d.rectangle((46,5,56,6),fill=0);d.rectangle((53,8,54,8),fill=0)
    d.polygon([(46,13),(54,13),(59,22),(56,25),(43,25),(42,19)],fill=1)
    d.rectangle((40,13,44,20),fill=1);d.line((41,15,43,18),fill=0)
    d.line((48,15,50,22),fill=0);d.polygon([(45,25),(50,25),(45,30),(42,30)],fill=1)
    d.polygon([(52,25),(56,25),(61,29),(61,31),(56,31)],fill=1)
    d.line((56,17,63,19),fill=1,width=2);d.line((63,13,64,31),fill=1)
    d.line((34,4,37,3),fill=1);d.point((39,4),fill=1)
    result.append(im)
    # Three destinations: schematic islands and a dotted journey, not a real map.
    im=Image.new('1',(72,32));d=ImageDraw.Draw(im)
    for poly in ([(1,8),(5,4),(12,5),(17,9),(14,15),(5,16),(1,12)],
                 [(26,13),(30,10),(38,11),(43,15),(40,22),(32,24),(26,19)],
                 [(56,7),(59,4),(65,6),(70,10),(68,15),(61,16),(56,13)]):
        d.polygon(poly,outline=1)
    for x,y in ((19,12),(22,14),(45,15),(48,13),(51,11)):
        d.rectangle((x,y,x+1,y+1),fill=1)
    d.polygon([(22,27),(26,30),(34,30),(38,27)],fill=1)
    d.line((30,22,30,27),fill=1);d.polygon([(31,22),(36,26),(31,26)],fill=1)
    d.line((2,29,6,29),fill=1);d.line((45,29,48,29),fill=1);d.line((63,28,69,28),fill=1)
    result.append(im)
    # Completion: raised sword, big hero and three pennants.
    im=Image.new('1',(72,32));d=ImageDraw.Draw(im)
    for x in (8,56,64):
        d.line((x,6,x,25),fill=1);d.polygon([(x+1,6),(x+7,8),(x+1,11)],fill=1)
    d.polygon([(30,11),(36,9),(41,12),(41,18),(37,20),(31,19),(28,15)],fill=1)
    d.rectangle((29,13,41,14),fill=0);d.point((38,16),fill=0)
    d.polygon([(31,20),(39,20),(45,31),(25,31)],fill=1)
    d.line((32,22,30,28),fill=0)
    d.polygon([(38,22),(42,18),(46,11),(48,12),(46,20),(42,26)],fill=1)
    d.line((48,2,48,12),fill=1,width=2);d.line((44,11,52,11),fill=1)
    d.line((43,2,40,0),fill=1);d.line((53,3,57,1),fill=1)
    d.line((11,29,21,29),fill=1);d.line((49,29,68,29),fill=1)
    result.append(im)
    # Return: house, open doorway and two larger people greeting each other.
    im=Image.new('1',(72,32));d=ImageDraw.Draw(im)
    d.polygon([(33,10),(40,10),(47,3),(59,3),(66,10),(71,10),(67,13),(36,13)],fill=1)
    d.rectangle((39,14,66,30),fill=1);d.rectangle((46,14,58,31),fill=0)
    d.rectangle((42,17,45,20),fill=0);d.rectangle((61,17,64,20),fill=0)
    for cx,cy in ((19,11),(52,19)):
        d.ellipse((cx-3,cy-4,cx+3,cy+2),fill=1)
        d.polygon([(cx-3,cy+3),(cx+3,cy+3),(cx+5,31),(cx-5,31)],fill=1)
        d.line((cx-2,cy+6,cx-2,30),fill=0)
    d.rectangle((16,9,22,10),fill=0);d.point((21,12),fill=0)
    d.line((22,18,30,15),fill=1,width=2);d.line((49,24,36,18),fill=1,width=2)
    d.line((4,30,10,30),fill=1);d.line((61,31,71,31),fill=1)
    result.append(im)
    return result


def encode(im):
    return bytes(sum(int(bool(im.getpixel((x,page*8+bit))))<<bit for bit in range(8))
                 for page in range(4) for x in range(72))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--emit',action='store_true')
    args=parser.parse_args()
    if args.emit:
        print(json.dumps([repr(encode(im)) for im in pictures()]))
