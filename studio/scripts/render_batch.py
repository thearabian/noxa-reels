import asyncio, sys, json, subprocess, time, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path(sys.argv[1]); reel=sys.argv[2]; mode=sys.argv[3]
async def main():
    tl=json.load(open(D/f"tl_{reel}.json"))
    async with async_playwright() as pw:
        b=await pw.chromium.launch(channel="msedge",args=["--allow-file-access-from-files"])
        p=await b.new_page(viewport={"width":1080,"height":1920})
        p.on("pageerror", lambda e: print("pageerror:", e))
        await p.goto((D/"batch.html").as_uri()+f"?reel={reel}"); await p.evaluate("window.READY")
        if mode=="contact":
            ts=[float(x) for x in sys.argv[4].split(",")] if len(sys.argv)>4 else [round(i*tl["total"]/12,2) for i in range(12)]
            out=D/"sheets"; out.mkdir(exist_ok=True); files=[]
            for i,t in enumerate(ts):
                await p.evaluate(f"renderAt({t})"); f=out/f"{reel}_{i:02d}.jpg"; await p.screenshot(path=str(f),type="jpeg",quality=70); files.append(f)
            cols=6; rows=(len(files)+cols-1)//cols
            args=[];[args.extend(["-i",str(f)]) for f in files]
            n=len(files); pad=cols*rows-n
            fl="".join(f"[{i}]scale=270:480[v{i}];" for i in range(n))
            for k in range(pad): fl+=f"color=black:s=270x480[p{k}];"
            fl+="".join(f"[v{i}]" for i in range(n))+"".join(f"[p{k}]" for k in range(pad))+f"xstack=inputs={cols*rows}:layout="+"|".join(f"{(i%cols)*270}_{(i//cols)*480}" for i in range(cols*rows))
            subprocess.run(["ffmpeg","-v","error","-y",*args,"-filter_complex",fl,str(out/f"{reel}_sheet.jpg")],check=True)
            for f in files: f.unlink()
            print(out/f"{reel}_sheet.jpg")
        else:
            outp=sys.argv[4]; n=tl["frames"]; fps=tl["fps"]
            ff=subprocess.Popen(["ffmpeg","-v","error","-y","-f","image2pipe","-framerate",str(fps),"-i","-","-i",str(D/f"{reel}.wav"),
              "-c:v","libx264","-preset","medium","-profile:v","high","-level","4.0","-crf","20","-pix_fmt","yuv420p","-vf","scale=in_range=pc:out_range=tv","-color_range","tv","-af","loudnorm=I=-14:TP=-1:LRA=11","-c:a","aac","-ac","2","-b:a","160k","-ar","48000","-shortest","-movflags","+faststart",outp],stdin=subprocess.PIPE)
            t0=time.time()
            for f in range(n):
                await p.evaluate(f"renderAt({f/fps})"); ff.stdin.write(await p.screenshot(type="jpeg",quality=93))
            ff.stdin.close(); ff.wait(); print("done",outp,round(time.time()-t0),"s")
        await b.close()
asyncio.run(main())
