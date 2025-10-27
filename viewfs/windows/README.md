# WinFsp plan
- Use WinFsp (C API) or Dokan as fallback.
- Map the same CAS+overlay logic to a virtual directory.
- Keep a stable path: `providers/<prov>/.<prov>/agents`.
- Start with a materialization fallback until the driver is ready.
