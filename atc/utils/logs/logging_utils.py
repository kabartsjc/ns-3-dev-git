import json, time
def log_event(fp, etype, **payload):
    evt = {"t": time.time(), "type": etype, **payload}
    fp.write(json.dumps(evt)+"\n"); fp.flush()