"""Two-link planar kinematics (radians). Simulation only, no motor commands."""
import math
def _numeric(*args):
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in args):
        raise ValueError("All arguments must be finite real numbers")
def forward(l1,l2,theta1,theta2):
    _numeric(l1,l2,theta1,theta2)
    if min(l1,l2)<=0: raise ValueError("Positive link lengths required")
    return (l1*math.cos(theta1)+l2*math.cos(theta1+theta2),
            l1*math.sin(theta1)+l2*math.sin(theta1+theta2))
def inverse(l1,l2,x,y):
    _numeric(l1,l2,x,y)
    if min(l1,l2)<=0: raise ValueError("Positive link lengths required")
    cosine=(x*x+y*y-l1*l1-l2*l2)/(2*l1*l2)
    if not -1-1e-12<=cosine<=1+1e-12: raise ValueError("Unreachable point")
    cosine=max(-1,min(1,cosine))
    solutions=[]
    for sign in (1,-1):
        angle2=sign*math.acos(cosine)
        angle1=math.atan2(y,x)-math.atan2(l2*math.sin(angle2),l1+l2*math.cos(angle2))
        if not any(abs(angle1-a)<1e-12 and abs(angle2-b)<1e-12 for a,b in solutions):
            solutions.append((angle1,angle2))
    return solutions
