import fnmatch
def allowed(policy, sfrom, sto):
    for r in policy.get('allow', [{'from':'*','to':'*'}]):
        if fnmatch.fnmatch(sfrom, r.get('from','*')) and fnmatch.fnmatch(sto, r.get('to','*')):
            return True
    return False
