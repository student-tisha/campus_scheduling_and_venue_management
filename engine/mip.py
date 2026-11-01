"""Thin MILP wrapper (SciPy / HiGHS). Swap this file to move to OR-Tools CP-SAT."""
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import coo_matrix

INF = float("inf")


class MIP:
    def __init__(self):
        self.lb, self.ub, self.c, self.integ = [], [], [], []
        self.r, self.cidx, self.v = [], [], []
        self.rlo, self.rhi = [], []
        self.const = 0.0

    def var(self, lb=0.0, ub=1.0, obj=0.0, integer=False):
        self.lb.append(lb); self.ub.append(ub); self.c.append(obj); self.integ.append(1 if integer else 0)
        return len(self.c) - 1

    def add(self, terms, lo=-INF, hi=INF):
        """terms: iterable of (var, coef)."""
        row = len(self.rlo)
        acc = {}
        for j, a in terms:
            acc[j] = acc.get(j, 0.0) + a
        for j, a in acc.items():
            self.r.append(row); self.cidx.append(j); self.v.append(a)
        self.rlo.append(lo); self.rhi.append(hi)

    def solve(self, time_limit=60, rel_gap=0.0):
        n = len(self.c)
        if not self.rlo:
            A = coo_matrix((0, n))
        else:
            A = coo_matrix((self.v, (self.r, self.cidx)), shape=(len(self.rlo), n)).tocsr()
        res = milp(c=np.array(self.c), integrality=np.array(self.integ),
                   bounds=Bounds(np.array(self.lb), np.array(self.ub)),
                   constraints=LinearConstraint(A, np.array(self.rlo), np.array(self.rhi)),
                   options={"time_limit": time_limit, "mip_rel_gap": rel_gap, "presolve": True})
        # status: 0 optimal, 1 limit reached, 2 infeasible, 3 unbounded, 4 other
        if res.x is None:
            return ("infeasible" if res.status == 2 else "no_solution"), None, None
        return ("optimal" if res.status == 0 else "feasible"), res.x, res.fun + self.const
