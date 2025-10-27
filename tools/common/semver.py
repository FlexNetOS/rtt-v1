def parse(ver:str):
    parts = ver.split('.')
    while len(parts)<3: parts.append('0')
    return tuple(int(p) for p in parts[:3])
def cmp(a,b): return (a>b) - (a<b)
def check_set(version:str, expr:str)->bool:
    v = parse(version)
    toks = expr.replace(',', ' ').split()
    for tok in toks:
        if not tok: continue
        if tok.startswith('>=') and not (cmp(v, parse(tok[2:]))>=0): return False
        if tok.startswith('>')  and not (cmp(v, parse(tok[1:]))>0):  return False
        if tok.startswith('<=') and not (cmp(v, parse(tok[2:]))<=0): return False
        if tok.startswith('<')  and not (cmp(v, parse(tok[1:]))<0):  return False
        if tok.startswith('==') and not (cmp(v, parse(tok[2:]))==0): return False
        if tok[0].isdigit() and not (cmp(v, parse(tok))==0): return False
    return True
