"""TPSM861253 (U5): its pads 1-4 are solder-mask defined and meant to sit in pours, so connect them solid. usage: dru_u5.py file.kicad_dru"""
import sys
p=sys.argv[1]; t=open(p).read()
if 'U5 pads connect solid' not in t:
    t=t.rstrip('\n')+"""

# TPSM861253 (U5): pads 1-4 are solder-mask defined (RDX0007A land pattern), so pours join them without thermal spokes.
(rule "U5 pads connect solid"
(constraint zone_connection solid)
(condition "A.Type == 'Pad' && A.memberOfFootprint('U5')"))
"""
open(p,'w').write(t); print('rules updated')
