"""Rule-file changes that go with the Kelvin net-tie move. usage: dru_kelvin.py file.kicad_dru"""
import sys
p=sys.argv[1]; t=open(p).read()
old="""(condition "A.NetClass == 'High Power' && A.Net != B.Net && !(A.Type == 'Pad' && B.Type == 'Pad') && !(A.Type != 'Zone' && (A.intersectsCourtyard('U6') || A.intersectsCourtyard('U2'))) && !(B.Type != 'Zone' && (B.intersectsCourtyard('U6') || B.intersectsCourtyard('U2')))"))"""
new="""(condition "A.NetClass == 'High Power' && !(A.NetName == '*SRC_LS_?') && A.Net != B.Net && !(A.Type == 'Pad' && B.Type == 'Pad') && !A.memberOfFootprint('NT*') && !B.memberOfFootprint('NT*') && !(A.Type != 'Zone' && (A.intersectsCourtyard('U6') || A.intersectsCourtyard('U2'))) && !(B.Type != 'Zone' && (B.intersectsCourtyard('U6') || B.intersectsCourtyard('U2')))"))"""
if old in t:
    t=t.replace(old,new)
    t=t.replace("""# exempt (a board-wide GND zone always touches those courtyards).""","""# exempt (a board-wide GND zone always touches those courtyards). The low-side source nets SRC_LS_x sit within
# a shunt drop of GND, so they are not treated as high voltage; net-tie pads are excluded as well.""")
hv="""!B.memberOfFootprint('NT*') && !(A.Type != 'Zone'"""
ex="""!B.memberOfFootprint('NT*') && !(A.NetName == '*PHA' && B.NetName == '*SHA') && !(A.NetName == '*PHB' && B.NetName == '*SHB') && !(A.NetName == '*PHC' && B.NetName == '*SHC') && !(B.NetName == '*SNUB*') && !(A.Type != 'Zone'"""
if hv in t and 'SNUB' not in t:
    t=t.replace(hv,ex)
    t=t.replace("""# a shunt drop of GND, so they are not treated as high voltage; net-tie pads are excluded as well.""","""# a shunt drop of GND, so they are not treated as high voltage; net-tie pads are excluded as well.
# Also excluded: each switch-node sense net SHx against its own phase (same potential) and the snubber
# mid-point nets SNUB*, which exist only on the 1 mm link between each snubber's R and C.""")
if 'Net-tie pads connect solid to pours' not in t:
    t=t.rstrip('\\n')+"""

# Kelvin net ties (under the shunts, at the high-side source pads) join pours of their own net solid.
(rule "Net-tie pads connect solid to pours"
(constraint zone_connection solid)
(condition "A.Type == 'Pad' && A.memberOfFootprint('NT*')"))
"""
open(p,'w').write(t); print('rules updated')
