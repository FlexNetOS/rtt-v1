import re
def parse(ver:str):
    parts = ver.split('.')
    while len(parts)<3: parts.append('0')
    return tuple(int(p) for p in parts[:3])
def cmp(a,b):
    return (a>b) - (a<b)
def check_set(version:str, expr:str)->bool:
    v = parse(version)
    toks = expr.replace(',', ' ').split()
    ok = True
    i = 0
    def test(tok, ver_tuple):
        if tok.startswith('>='): return cmp(ver_tuple, parse(tok[2:]))>=0
        if tok.startswith('>'):  return cmp(ver_tuple, parse(tok[1:]))>0
        if tok.startswith('<='): return cmp(ver_tuple, parse(tok[2:]))<=0
        if tok.startswith('<'):  return cmp(ver_tuple, parse(tok[1:]))<0
        if tok.startswith('=='): return cmp(ver_tuple, parse(tok[2:]))==0
        if tok[0].isdigit():     return cmp(ver_tuple, parse(tok))==0
        return True
    while i < len(toks):
        tok = toks[i]
        if not tok: i+=1; continue
        if not test(tok, v): return False
        i+=1
    return ok
