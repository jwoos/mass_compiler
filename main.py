import functools
import sys
import os

from code.generate import generate
from parser.ast import Node
from parser.parser import parser
from scanner.scanner import lexer
from semantics import handler, checker
from semantics.symbol_table import SymbolTable, SymbolScope, SymbolType, Symbol, info
import error
import log
import utils


def main():
    filename = None

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'test/test.c'

    with open(filename) as r:
        result = parser.parse(r.read())

    log.info(result)

    if result is None:
        log.error('AST is None - exiting')
        return

    node_stack = [result]
    table_stack = [SymbolTable(SymbolScope.GLOBAL)]
    table_cache = {}

    while node_stack:
        node = node_stack.pop()
        log.debug(node)

        if not node:
            continue

        if node.symbol == 'function_def':
            signal = handler.handle_function_def(node_stack, table_stack, node)
            if signal == handler.Signal.CONTINUE:
                continue

        elif node.symbol == 'function_def_end':
            table_cache[node.args[0].symbol] = table_stack[-1]
            handler.handle_function_def_end(node_stack, table_stack, node)

        elif node.symbol == 'function_decl':
            handler.handle_function_decl(node_stack, table_stack, node)

        elif node.symbol == 'decl':
            handler.handle_decl(node_stack, table_stack, node)

        else:
            if node.attrs.get('name') == 'identifier':
                if table_stack[-1].get(node.symbol) is None:
                    if table_stack[-1].scope == SymbolScope.LOCAL and table_stack[0].get(node.symbol) is None:
                        log.error(f'{node.symbol} referenced before declaration')
                    else:
                        info(table_stack[0].get(node.symbol), usage=node.attrs.get('line', True))

                else:
                    info(table_stack[-1].get(node.symbol), usage=node.attrs.get('line', True))

                continue

            elif node.symbol == 'function_call':
                func = table_stack[0].get(node.args[0].symbol)
                if func:
                    func.attrs['call'] = True
                    checker.check_function_call(node_stack, table_stack, node)

            elif node.symbol in checker.PROPAGATING_UNARY_SYMBOLS:
                if len(node.args) == 1:
                    checker.check_unary(node_stack, table_stack, node)
                else:
                    checker.check_binary(node_stack, table_stack, node)

            elif node.symbol in checker.PROPAGATING_BINARY_SYMBOLS:
                checker.check_binary(node_stack, table_stack, node)

            for child in reversed(node.args):
                if child:
                    node_stack.append(child)

    # node_stack = [result]
    # while node_stack:
        # node = node_stack.pop()
        # if node is None:
            # continue
        # print(node)
        # for child in reversed(node.args):
            # if child:
                # node_stack.append(child)

    # check if a declared function was called, it was later defined
    for v in table_stack[0].table.values():
        if not v.attrs.get('init') and v.attrs.get('call'):
            log.error(f'Function {v} declared and called but never defined')

    # check if main was defined
    if 'main' not in table_stack[0].table:
        log.error('main is not defined')

    # if there was an error do not generate code
    if error.ERROR:
        log.info('Exiting without any code generation')
    else:
        log.info('Generating code')
        output = generate(result, table_cache, table_stack[0])
        log.info(output)

        flattened_output = utils.flatten_array(output)
        log.info(flattened_output)

        string_ouput = functools.reduce(lambda x, y: '\n'.join((str(x), str(y))), flattened_output)
        log.info(string_ouput)

        f = open(f'{filename.split(".")[0]}.mass', 'w+')
        f.write(f'{string_ouput}\n')

if __name__ == '__main__':
    main()
