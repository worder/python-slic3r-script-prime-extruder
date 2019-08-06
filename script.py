import sys
import re

'''
-------------------------------------------------------
modifying this:
-------------------------------------------------------
G1 Z0.200 F3000.000 ; move to next layer (0)
G1 E-7.00000 F4800.00000 ; retract
G92 E0 ; reset extrusion distance
G1 X96.201 Y95.831 F3000.000 ; move to first skirt point
G1 E7.00000 F4800.00000 ; unretract
-------------------------------------------------------
to this:
-------------------------------------------------------
G1 Z0.200 F3000.000 ; move to next layer (0)
; *** delted: retration ***
G92 E0 ; reset extrusion distance
G1 E5 ; *** added: prime extruder ***
G1 X96.201 Y95.831 E8 F3000.000 ; move to first skirt point *** edited: add extrusion ***
; *** deleted: unretration ***
-------------------------------------------------------
'''

def modFirstLayer(val):
    m = re.search('G1 Z\d+.\d+ F\d+.\d+ ; move to next layer \(0\)\s*'
        '(?P<retract>G1 E.?\d+\.\d+ F\d+\.\d+ ; retract\s*'
        'G92 E0 ; reset extrusion distance\s*)' # consider reset as a part of retraction process
        'G1 X\d+\.\d+ Y\d+\.\d+ F\d+.\d+ ; move to first skirt point\s*'
        '(?P<unretract>G1 E\d+.\d+ F\d+.\d+ ; unretract\s*)', val)
    
    if m:
        retract = m.group('retract')
        unretract = m.group('unretract')

        # delete retraction
        val = val.replace(retract, '; --- delted: retration ---\n')
        val = val.replace(unretract, '; --- delted: unretration ---\n')

        # add prime and  extrusion to skirt positioning
        val = re.sub('(?P<start>G1 X\d+\.\d+ Y\d+\.\d+)\s(?P<end>F\d+.\d+ ; move to first skirt point)(?P<nl>\s*)', 
            'G1 E5 ; prime extruder\n'
            '\g<start> E8 \g<end> --- edited: add extrusion ---\g<nl>', val)
        
        return val
    else:
        return False

processed = False
buffer = ""
i = 0

gcodeFilePath = sys.argv[1]

with open(gcodeFilePath, "r") as f:
    for line in f:
        buffer += line
        if processed == False:
            newVal = modFirstLayer(buffer)
            if newVal != False:
                buffer = newVal
                processed = True
                print("bingo!")

newFile = open('out.gcode', 'w')
newFile.write(buffer)