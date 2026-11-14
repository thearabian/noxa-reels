import asyncio, json, sys, edge_tts
D=sys.argv[1]
NEW={"e":"Drop your pick in the comments.","f":"And a gift. Three winners get an OpenAI API key for three days, each with a one thousand dollar cap. To enter, just comment NOXA. Winners in twenty-four hours."}
async def go():
    meta=json.load(open(f"{D}/vo/meta.json"))
    lines=[l for l in meta["pickone"] if l["key"] not in NEW]
    for key,text in NEW.items():
        c=edge_tts.Communicate(text,"en-GB-RyanNeural",rate="+4%",pitch="-2Hz",boundary="WordBoundary"); words=[]
        with open(f"{D}/vo/pickone_{key}.mp3","wb") as f:
            async for ch in c.stream():
                if ch["type"]=="audio": f.write(ch["data"])
                elif ch["type"]=="WordBoundary": words.append({"t":ch["offset"]/1e7,"d":ch["duration"]/1e7,"w":ch["text"]})
        lines.append({"key":key,"text":text,"words":words}); print(key,[(w["w"],round(w["t"],2)) for w in words])
    meta["pickone"]=lines; json.dump(meta,open(f"{D}/vo/meta.json","w"))
asyncio.run(go())
