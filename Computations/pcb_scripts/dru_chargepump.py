"""HV-clearance exemption for the DRV8353 charge-pump nodes. usage: dru_chargepump.py file.kicad_dru
VCP and CPH ride at most ~11 V above VM (+VBAT), so the 0.5 mm high-voltage clearance is not needed between
them and +VBAT. CPL is not exempt: it swings between GND and VM."""
import sys
p=sys.argv[1]; t=open(p).read()
hv="""!(B.NetName == '*SNUB*') && !(A.Type != 'Zone'"""
ex="""!(B.NetName == '*SNUB*') && !(A.NetName == '+VBAT' && (B.NetName == '*VCP' || B.NetName == '*CPH')) && !(A.Type != 'Zone'"""
assert hv in t or 'VCP' in t
if 'VCP' not in t:
    t=t.replace(hv,ex)
    t=t.replace("""# mid-point nets SNUB*, which exist only on the 1 mm link between each snubber's R and C.""","""# mid-point nets SNUB*, which exist only on the 1 mm link between each snubber's R and C.
# +VBAT against the charge-pump nodes VCP and CPH is excluded too: they ride at most ~11 V above VM.""")
open(p,'w').write(t); print('rules updated')
