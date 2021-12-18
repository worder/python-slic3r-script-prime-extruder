import sys
import re
import os
import time
import math

'''
-------------------------------------------------------
modifying this:
-------------------------------------------------------
G1 Z0.200 F3000.000 ; move to next layer (0)
G1 E-7.00000 F4800.00000 ; retract
G92 E0 ; reset extrusion distance
G1 X96.201 Y95.831 F3000.000 ; move to first skirt point
G1 E7.00000 F4800.00000 ; unretract
----------------- or (no feedrate case) ---------------
G1 Z0.200 F1800.000 ; move to next layer (0)
G1 E-5.00000 ; retract
G92 E0 ; reset extrusion distance
G1 X108.760 Y66.909 ; move to first skirt point
G1 E5.00000 ; unretract
----------------- or (new prusa 2.4.0. beta case) ---------------
G1 Z.2 F4200 ; move to next layer (0)
G1 E-4 F2400 ; retract
G92 E0 ; reset extrusion distance
G1 X26.479 Y33.761 F4200 ; move to first skirt point
G1 E4 F2400 ;  ; unretract
-------------------------------------------------------
to this:
-------------------------------------------------------
G1 Z0.200 F3000.000 ; move to next layer (0)
; *** delted: retration ***
G92 E0 ; reset extrusion distance
G1 E5 F100 ; *** added: prime extruder ***
G1 X96.201 Y95.831 E8 F3000.000 ; move to first skirt point *** edited: add extrusion ***
G92 E7.000 ; *** re-init extruder position ***
; *** deleted: unretration ***
-------------------------------------------------------
'''

EXTRUSION_RATE_CONST = 0.0445 # how much mm extrude per mm of XY movement

def modFirstLayer(val):
    m = re.search('G1 Z\d*\.?\d+ (?P<feedrate_initial>F\d*\.?\d+) ; move to next layer \(0\)\s*'
                  '(?P<move_to_skirt>'
                  'G1 E.?\d*\.?\d+ (F\d*\.?\d+ )?; retract\s*'
                  'G92 E0 ; reset extrusion distance\s*'
                  'G1 X(?P<skirt_x>\d*\.?\d+) Y(?P<skirt_y>\d*\.?\d+) (?P<feedrate>(F\d*.?\d+ )?); move to first skirt point\s*'
                  'G1 E(?P<e_initial>\d*\.?\d+) (F\d*\.?\d+)? ;(\s*;)? unretract\s*)', val)

    if m:
        feedrate_initial = m.group('feedrate_initial')
        feedrate = m.group('feedrate')
        e_initial = m.group('e_initial')
        skirt_x = float(m.group('skirt_x'))
        skirt_y = float(m.group('skirt_y'))
        zero_to_skirt_distance = math.sqrt(math.pow(skirt_x, 2) + math.pow(skirt_y, 2)) # hypotenuse

        initial_move_extrusion_value = round(EXTRUSION_RATE_CONST * zero_to_skirt_distance, 3)
        initial_move_feedrate = feedrate if feedrate else feedrate_initial

        move_to_skirt_block = m.group('move_to_skirt')
        new_move_to_skirt_block = ('; >>> primer script START <<< \n'
            'G92 E0 ; reset extrusion distance\n'
            'G1 E10 F300 ; prime extruder\n'
            'G92 E0 ; reset extrusion distance\n'
            'G1 X%s Y%s E%s %s ; move to first skirt point\n' 
            'G92 E%s ; initialize extruder\n' 
            '; >>> primer script END <<<\n'% (skirt_x, skirt_y, initial_move_extrusion_value, initial_move_feedrate, e_initial))

        new_val = val.replace(move_to_skirt_block, new_move_to_skirt_block)

        if val != new_val:
            return new_val
        else:
            return False

    else:
        return False

processed = False
buffer = ""
i = 0

try:
    origPath = sys.argv[1]
except:
    print("No input file, press any key...")
    exit()

doBackup = False

origPath = os.path.join('.', origPath)
origDir = os.path.dirname(origPath)
origFilename = os.path.basename(origPath)

tempFilename = "_temp_" + origFilename
tempPath = os.path.join(origDir, tempFilename)

backupPath = os.path.join(origDir, '_bak_' + origFilename)

try:
    outputPath = sys.argv[2]
except:
    #    doBackup = True
    outputPath = origPath

cnt = 0
progress = 0

try:
    with open(origPath, "r") as f:       

        print("Input file: %s" % origPath)
        print("Temp file: %s" % tempPath)

        num_lines = sum(1 for line in open(origPath))
        print("Lines: %s" % num_lines)
        newFile = open(tempPath, 'w')

        for line in f:
            new_progress = round(cnt / num_lines * 100)
            if new_progress != progress and ((new_progress % 10 == 0) or (new_progress - progress > 9)):
                progress = new_progress
                print("Line: %s out of %s (%s%%)" % (cnt, num_lines, progress))

            buffer += line
            cnt += 1
            if processed == False and cnt < 100:
                newVal = modFirstLayer(buffer)
                if newVal != False:
                    buffer = newVal
                    processed = True
                    print("First layer modified successfuly")
            elif processed and (cnt % 5000 == 0):
                newFile.write(buffer)
                buffer = ""
        
        newFile.write(buffer)
        newFile.close()

    if processed:
        if doBackup:
            print("Backup file: " + backupPath)
            os.replace(origPath, backupPath)
        else:
            print("Backup option disabled")
    else:
        print("No match found, press any key to exit...")
        input()
        exit()  

    os.replace(tempPath, outputPath)
    time.sleep(0.2)

except (FileExistsError, FileNotFoundError):
    print('File "%s" not found, press any key to exit...' % origPath)
    input()
    exit()