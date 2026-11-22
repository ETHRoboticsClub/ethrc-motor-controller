"""Split a plan with stage marks into the stage-1+3 part (pattern copy) and the stage-2 part (long runs).
usage: split_plan.py plan.json outA.json outB.json"""
import sys,json
p=json.load(open(sys.argv[1])); m1,m2=p['marks']
A={k:(v[:m1[k]]+v[m2[k]:]) for k,v in p.items() if k!='marks'}
B={k:v[m1[k]:m2[k]] for k,v in p.items() if k!='marks'}
json.dump(A,open(sys.argv[2],'w')); json.dump(B,open(sys.argv[3],'w'))
print('A',{k:len(v) for k,v in A.items()},'\nB',{k:len(v) for k,v in B.items()})
