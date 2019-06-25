def print_tree(tree, depth=0):
    "simple depiction of slimit parsed javascript AST"
    print('    '*depth, tree.__class__.__name__)
    for arg in dir(tree):
        if (not(arg.startswith('_')) and arg not in ['children', 'to_ecma']):
            print('    '*(depth+1), arg, end='')
            if arg == 'value':
                print(':', tree.value[:20])
            else:
                print()
    if len(tree.children()) > 0:
        print('    '*(depth+1), '---------')
    for child in tree.children():
        print_tree(child, depth+1)
