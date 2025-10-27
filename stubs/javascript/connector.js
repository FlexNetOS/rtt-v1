#!/usr/bin/env node
import readline from 'node:readline';
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl){
  if(!line.trim()) continue;
  const req = JSON.parse(line);
  process.stdout.write(JSON.stringify({id:req.id||"0", result:{ok:true}, error:null})+"\n");
}
