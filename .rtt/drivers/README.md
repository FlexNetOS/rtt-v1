# Connector protocol (JSON over stdio)
Methods: Probe, Open, Tx, Rx, Close, Health
Envelope:
{ "id": "<uuid>", "method": "Probe", "params": {...} }
Response:
{ "id": "<uuid>", "result": {...}, "error": null }
