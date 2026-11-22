"""Coordinate frame on the LAN9253 (U9) west face: s runs along the face from pin 52 towards pin 63 (0.5 mm per pin),
d points outwards (north-west). Shared by the step 5 EtherCAT escape scripts."""
import math
R2=1/math.sqrt(2); U=(-R2,R2); N=(-R2,-R2)
class Frame:
    def __init__(self,W): self.o=W.pad('U9','52')
    def xy(self,s,d): return (round(self.o[0]+s*U[0]+d*N[0],4),round(self.o[1]+s*U[1]+d*N[1],4))
    def sd(self,x,y): dx,dy=x-self.o[0],y-self.o[1]; return (dx*U[0]+dy*U[1],dx*N[0]+dy*N[1])
    def pin_s(self,k): return (k-52)*0.5
