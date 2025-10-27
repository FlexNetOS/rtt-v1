import fnmatch
def allowed(policy:dict, sfrom:str, sto:str)->bool:
    for rule in policy.get('allow', []):
        if fnmatch.fnmatch(sfrom, rule.get('from','*')) and fnmatch.fnmatch(sto, rule.get('to','*')):
            return True
    return False
