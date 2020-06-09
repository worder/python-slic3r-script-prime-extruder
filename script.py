import sys
import re
import os
import time

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


def modFirstLayer(val):
    m = re.search('G1 Z\d+.\d+ F\d+.\d+ ; move to next layer \(0\)\s*'
                  '(?P<retract>G1 E.?\d+\.\d+ (F\d+\.\d+ )?; retract\s*'
                  # consider reset as a part of retraction process
                  'G92 E0 ; reset extrusion distance\s*)'
                  'G1 X\d+\.\d+ Y\d+\.\d+ (F\d+.\d+ )?; move to first skirt point\s*'
                  '(?P<unretract>G1 E(?P<unretractValue>\d+.\d+) (F\d+.\d+ )?; unretract\s*)', val)

    if m:
        retract = m.group('retract')
        unretract = m.group('unretract')
        unretractValue = m.group('unretractValue')

        # delete retraction
        val = val.replace(retract, '; --- deleted: retraction ---\n')
        val = val.replace(unretract, '; --- deleted: unretrcation ---\n')

        # add extruder prime command and continue extruding when positioning to skirt start
        val = re.sub('(?P<start>G1 X\d+\.\d+ Y\d+\.\d+)\s(?P<end>F\d+.\d+ ; move to first skirt point)(?P<nl>\s*)',
                     'G1 E14 F300 ; --- prime extruder ---\n'
                     '\g<start> E20 \g<end> --- edited: add extrusion ---\g<nl>'
                     'G92 E%s ; --- re-init extruder position ---\n' % unretractValue, val)

        return val
    else:
        return False


processed = False
buffer = ""
i = 0

try:
    origPath = sys.argv[1]
except:
    print("Nothing to do")
    input("press anykey")
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