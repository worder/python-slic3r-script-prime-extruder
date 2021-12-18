import re

val = "G1 Z.2 F4200 ; move to next layer (0)"

m = re.search('G1 Z\d*\.\d+ (?P<feedrate_initial>F\d*\.?\d+) ; move to next layer \(0\)\s*', val)

print(m)