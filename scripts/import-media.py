import hashlib, json, pathlib, urllib.request, time
manifest=json.loads(pathlib.Path("migration-manifest.json").read_text())["files"]
receipts={}
for path, meta in manifest.items():
    target=pathlib.Path("assets") / path.lstrip("/")
    if ".." in target.parts: raise ValueError("Invalid path")
    def valid(data):
        return len(data)==meta["size"] and hashlib.sha256(data).hexdigest()==meta["sha256"]
    if target.exists() and valid(target.read_bytes()):
        receipts[path]=meta["sha256"]
        continue
    for attempt in range(3):
        try:
            req=urllib.request.Request("https://akashicnet.org"+path,headers={"User-Agent":"AkashicNET-media-migration","Accept-Encoding":"identity"})
            with urllib.request.urlopen(req,timeout=120) as response:
                data=response.read(meta["size"]+1)
            if not valid(data): raise ValueError("Original checksum mismatch: "+path)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
            receipts[path]=meta["sha256"]
            print("Verified",path,flush=True)
            break
        except Exception:
            if attempt==2: raise
            time.sleep(3)
pathlib.Path("verification.json").write_text(json.dumps({"source":"https://akashicnet.org","verified":receipts},indent=2)+"\n")
print("Verified",len(receipts),"files")
