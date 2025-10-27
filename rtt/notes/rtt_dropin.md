Delivered. Drop this at repo root.

* Download: [rtt_dropin.zip](sandbox:/mnt/data/rtt_dropin.zip)
* Validate locally: `python tests/validate.py`
* Edit `.rtt/panel.yaml`, `.rtt/policy.json`, `.rtt/routes.json` to fit your graph.
* Put connector binaries or modules in `.rtt/drivers/`.

Contents:

```
.rtt/
  panel.yaml
  policy.json
  routes.json
  manifests/
    core.api.metrics.json
    core.bus.events.json
    idp.api.auth.json
    obs.extension.logger.ndjson.json
    ui.hook.refresh.json
  drivers/               # drop your connectors here
  cache/.keep
  wal/.keep
  sockets/.keep
schemas/
  rtt.symbol.schema.json
  rtt.policy.schema.json
  rtt.routes.schema.json
tests/
  validate.py            # no external deps
README.md
```

Need code stubs for Rust drivers or SHM ring next?