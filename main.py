import argparse
import importlib
import timeit
import sys
import streamlit as st

import numpy as np

from problems.api import Problem

def run_langchain_agent(problem: Problem, llvmir: str):
    problem.optimize(llvmir)

    


def run_agent(problem: Problem, ref_out, agent_llvm_ir=None):
    # Use provided LLVM IR if available, otherwise use problem's default
    llvmir = problem.cfn_src

    print('Agent input:')
    print('\n================================')
    print(llvmir)
    st.session_state.llvm_ir = llvmir
    print('================================\n')

    # run your agent here!
    # TODO: for now just return a copy of the original IR

    if agent_llvm_ir:

        print('Agent Output:')
        print('\n================================')
        print(agent_llvm_ir)
        print('================================\n')

        optimized = str(agent_llvm_ir)
    else:
        optimized = str(llvmir)

    # try to compile the agent-generated IR
    problem.reset()
    problem.optimize(optimized)

    # after calling .optimize(), you can use "problem.ai_cfn(*ref_out)" to run your function
    # and perhaps compare it with the reference output
    # if you want to recompile, please call "problem.reset()" before calling "problem.optimize()"
    # again


def benchmark(fn, data):
    # return in milliseconds
    return timeit.timeit('fn(*data)', globals={ 'fn': fn, 'data': data }, number=100) * 1000


def check_the_same(a, b):
    assert a is not b
    if isinstance(a, np.ndarray):
        if a.dtype == np.float32:
            return np.allclose(a, b)
        else:
            return (a == b).all()
    return (a == b)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--problem', required=True, type=int, help='Problem number to run')
    parser.add_argument('--llvm_ir', required=False, type=str, help='LLVM IR to optimize')
    args = parser.parse_args()

    pidx = args.problem
    try:
        pmod = importlib.import_module(f'problems.problem{pidx}')
    except:
        import traceback
        print(f'Failed to import the problem with the provided id={pidx}')
        traceback.print_exc()
        return 1

    p = pmod.problem

    ref = p.fn(*p.get_test_data())
    cref = p.cfn(*p.get_test_data())
    check_the_same(ref, cref)

   
    run_agent(p, ref, args.llvm_ir)

    ai = p.ai_cfn(*p.get_test_data())
    if not check_the_same(cref, ai):
        raise ValueError('Output mismatch!')

    print('All outputs match. Benchmarking...')
    # Calculate benchmark values once
    base_time = benchmark(p.fn, p.get_test_data())
    compiled_time = benchmark(p.cfn, p.get_test_data())
    ai_opt_time = benchmark(p.ai_cfn, p.get_test_data())
    
    # Print to console
    print('Base:', base_time)
    print('Compiled:', compiled_time)
    print('AI-Opt:', ai_opt_time)

    # Create new benchmark entry
    new_metrics = f"Base: {base_time}\nCompiled: {compiled_time}\nAI-Opt: {ai_opt_time}\n{'-'*40}\n"
    
    # Initialize benchmark_metrics if it doesn't exist
    if 'benchmark_metrics' not in st.session_state:
        st.session_state.benchmark_metrics = []
    
    # Append new metrics as a new entry in the list
    st.session_state.benchmark_metrics.append(new_metrics)
    
    st.session_state.test_data = p.get_test_data()

if __name__ == '__main__':
    sys.exit(main() or 0)