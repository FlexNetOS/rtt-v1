import readline from 'node:readline';
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  if (!line.trim()) continue;
  const req = JSON.parse(line);
  const res = { id: req.id, result: { ok: true }, error: null };
  process.stdout.write(JSON.stringify(res) + "\n");
}
