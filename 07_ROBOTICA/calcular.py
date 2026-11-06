import argparse
import json
from load_model import estimate
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Single static load estimate, no motor control')
    parser.add_argument('--mass-kg',type=float,required=True);parser.add_argument('--lever-m',type=float,required=True)
    parser.add_argument('--angle-deg',type=float,default=90);parser.add_argument('--gear-ratio',type=float,default=1)
    parser.add_argument('--efficiency',type=float,default=1);parser.add_argument('--design-factor',type=float,default=2)
    parser.add_argument('--motor-continuous-nm',type=float)
    args=parser.parse_args()
    try:print(json.dumps(estimate(**vars(args)),indent=2,allow_nan=False))
    except ValueError as exc:parser.exit(1,str(exc)+'\n')
