#!/usr/bin/env python3
import subprocess, shlex, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
cli = ROOT/"llama_cli"
if not cli.exists(): sys.exit(0)
prompt = sys.argv[1] if len(sys.argv)>1 else "Suggest symbol connections"
cmd = f"{cli} -m ./models/model.gguf -p {shlex.quote(prompt)}"
subprocess.run(cmd, shell=True, check=False)
