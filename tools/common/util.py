import json
def canon(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def version_of_saddr(saddr:str)->str:
    if '@' in saddr: return saddr.split('@',1)[1].split('#',1)[0]
    return '1.0.0'
