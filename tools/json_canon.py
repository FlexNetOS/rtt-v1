#!/usr/bin/env python3
import sys, json
def canon(obj): return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
def main():
    obj = json.load(open(sys.argv[1], 'r', encoding='utf-8')) if len(sys.argv)>1 else json.load(sys.stdin)
    sys.stdout.buffer.write(canon(obj))
if __name__ == "__main__": main()
