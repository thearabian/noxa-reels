import asyncio, json, sys, edge_tts
D=sys.argv[1]; spec=json.load(open(f"{D}/script.json"))
async def go():
    meta={}
    for reel,lines in spec.items():
        meta[reel]=[]
        for key,text in lines:
            c=edge_tts.Communicate(text,"en-GB-RyanNeural",rate="+4%",pitch="-2Hz",boundary="WordBoundary")
            words=[]
            with open(f"{D}/vo/{reel}_{key}.mp3","wb") as f:
                async for ch in c.stream():
                    if ch["type"]=="audio": f.write(ch["data"])
                    elif ch["type"]=="WordBoundary": words.append({"t":ch["offset"]/1e7,"d":ch["duration"]/1e7,"w":ch["text"]})
            meta[reel].append({"key":key,"text":text,"words":words})
    json.dump(meta,open(f"{D}/vo/meta.json","w"))
asyncio.run(go())
