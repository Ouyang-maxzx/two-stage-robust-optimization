# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 17:21:33 2023

@author: wyx
"""
from ExampleMatrix import Ay, by, G, E, M, h, bias
from gurobipy import *
import numpy as np

MP = Model('MP')

# construct main problem
c = np.array([400, 414, 326])
a = np.array([18, 25, 20])
b = np.array([22, 33, 24, 33, 23, 30, 20, 25, 27])
bigM = 10**3
LB = -GRB.INFINITY
UB = GRB.INFINITY
epsilon = 1e-5
k = 1
u = []
l = []
y = MP.addMVar((3,), obj=c, vtype=GRB.BINARY)
z = MP.addMVar((3,), obj=a, vtype=GRB.CONTINUOUS)
d = MP.addMVar((3,), lb=0, name='d')
eta = MP.addMVar((1,), obj=1, vtype=GRB.CONTINUOUS)

# construct the MP
MP.addConstr(Ay[:, :3]@y+Ay[:, 3:]@z >= by)
MP.optimize()
MP_obj = MP.ObjVal
LB = max(MP_obj, LB)

SP = Model('SP')
x = SP.addMVar((9,), vtype=GRB.CONTINUOUS, name='x')
pi = SP.addMVar(G.shape[0], vtype=GRB.CONTINUOUS, name='pi')
g = SP.addMVar((3,), ub=1, vtype=GRB.CONTINUOUS, name='g')
v = SP.addMVar((G.shape[0],), vtype=GRB.BINARY, name='v')
w = SP.addMVar((G.shape[1],), vtype=GRB.BINARY, name='w')

G1 = SP.addConstr(G@x >= h-M@g-E@np.concatenate([y.x, z.x]), name="G1")
SP.addConstr(G.T@pi <= b, name='pi')
SP.addConstr(pi <= bigM*v, name='v')
G2 = SP.addConstr(
    G@x-h+E@np.concatenate([y.x, z.x])+M@g <= bigM*(1-v), name='G2')
SP.addConstr(x <= bigM*w, name='w1')
SP.addConstr(b-G.T@pi <= bigM*(1-w), name='w2')
SP.addConstr(g[:2].sum() <= 1.2, name='g1')
SP.addConstr(g.sum() <= 1.8, name='g2')
SP.setObjective(b@x, GRB.MAXIMIZE)
SP.optimize()
SP_obj = SP.ObjVal
UB = min(UB, c@y.x+a@z.x+SP_obj)
MP.reset()
while abs(UB-LB) >= epsilon:
    # add x^{k+1}
    x_new = MP.addMVar((9,), vtype=GRB.CONTINUOUS)
    # eta>=bTx^{k+1}
    MP.addConstr(eta >= (h-E[:, :3]@y-E[:, 3:]@z-M@g.x)@pi.x)
    # Ey+Gx^{k+1}>=h-Mu_{k+1}
    # MP.addConstr(E[:,:3]@y+E[:,3:]@z+G@x_new>=h-M@g.x)
    MP.optimize()
    SP.reset()
    LB = max(LB, MP.objval)
    # update the SP constrs according to the MP solution
    SP.remove(G1)
    SP.remove(G2)
    G1 = SP.addConstr(G@x >= h-M@g-E@np.concatenate([y.x, z.x]), name="G1")
    G2 = SP.addConstr(G@x-h+E@np.concatenate([y.x, z.x])+M@g <= bigM*(1-v), name='G2')
    SP.optimize()
    # obtain the optimal y^{k+1}
    SP_obj = SP.ObjVal
    UB = min(UB, c@y.x+a@z.x+SP_obj)
    MP.reset()
    k += 1
    u.append(UB)
    l.append(LB)
    # go back to the MP
    print("经过{}次迭代".format(k))
    print("上界为：{}".format(UB))
    print("下界为：{}".format(LB))
