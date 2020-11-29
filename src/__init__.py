from src.pparser.Lexer import PLexer
from src.pparser.Parser import PParser
from src.compiler.compiler import Compiler

import llvmlite.binding as llvm
from ctypes import CFUNCTYPE, c_int, c_float
from time import time


def run_code(code):
    compiler = Compiler()
    lexer = PLexer()
    tokens = lexer.tokenize(code)
    parser = PParser()
    parser.parse(tokens)
    ast = parser.ast
    ast = ast[1]['body']
    #print(pprint.pformat(ast))
    compiler.compile(ast)
    module = compiler.module

    module.triple = llvm.get_default_triple()
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    llvm_ir_parsed = llvm.parse_assembly(str(module))
    llvm_ir_parsed.verify()

    target_machine = llvm.Target.from_default_triple().create_target_machine()
    engine = llvm.create_mcjit_compiler(llvm_ir_parsed, target_machine)
    engine.finalize_object()

    # Run the function with name func_name. This is why it makes sense to have a 'main' function that calls other functions.
    entry = engine.get_function_address('main')
    cfunc = CFUNCTYPE(c_int)(entry)

    print('The llvm IR generated is:')
    print(module)
    print()
    start_time = time()
    result = cfunc()
    end_time = time()

    print(f'It returns {result}')
    print('\nExecuted in {:f} sec'.format(end_time - start_time))