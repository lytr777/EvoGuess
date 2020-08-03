import argparse
from multiprocessing import Pool
from operator import itemgetter

from pysat import solvers as slvs

from method import *

solvers = {
    'cd': slvs.Cadical,
    'g3': slvs.Glucose3,
    'g4': slvs.Glucose4,
}

instances = [
    'sgen:6_200',
    'sgen:6_220',
    'sgen:6_240',
    'crafted:challenge',
    'crafted:eulcbip',
    'crafted:pmg',
    'crafted:clqcolor',
    'crafted:mod'
]

parser = argparse.ArgumentParser(description='EvoGuess')
parser.add_argument('-t', metavar='36', type=int, default=36, help='threads')
args = parser.parse_args()


def worker_f(inst, solver_key):
    Solver = solvers[solver_key]
    solver = Solver(bootstrap_with=inst.clauses(), use_timer=True)

    status = solver.solve()
    stats = solver.accum_stats()
    conflicts = stats.get('conflicts', None)
    time = None if status is None else solver.time()
    solver.delete()

    return conflicts, time


def check():
    res_list, results = [], {}
    pool = Pool(processes=args.t)

    for inst_key in instances:
        for slv_key in solvers.keys():
            inst = instance.get(inst_key)

            res = pool.apply_async(worker_f, (inst, slv_key))
            res_list.append((inst_key, slv_key, res))

    while len(res_list) > 0:
        res_list[0][2].wait()
        while len(res_list) > 0 and res_list[0][2].ready():
            inst_key, slv_key, res = res_list.pop(0)

            try:
                measures = res.get()
            except Exception as e:
                print("Error on %s with %s (%s)" % (inst_key, slv_key, e))
                continue

            if inst_key in results:
                results[inst_key][slv_key] = measures
            else:
                results[inst_key] = {
                    slv_key: measures
                }

    for inst_key, inst_res in results.items():
        print("Results for %s:" % instance.get(inst_key))
        for slv_key, slv_res in inst_res.items():
            print("-- %s: %.7g (%.7g s)" % (slv_key, slv_res[0], slv_res[1]))
        print()


if __name__ == "__main__":
    check()
