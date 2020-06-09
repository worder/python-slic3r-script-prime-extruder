import re

val = "G1 E-5.00000 ; retract"

m = re.search('(?P<retract>G1 E.?\d+\.\d+ (F\d+\.\d+ )?; retract\s*)', val)

print(m.group('retract'))