api: listen: {
  unix: =~"^\./\.rtt/sockets/.*\.sock$"
  npipe?: string
}
scan: { roots: [...string]; ignore: [...string] }
routing: { prefer: [...string] & ["shm","uds","tcp"]; rewire_atomic: true }
security: { strict_manifests: bool; allow_unsigned?: [...string] }
health: { heartbeat_ms: >=100 & <=5000; trip_threshold: { errors: >=1, window_ms: >=1000 } }
