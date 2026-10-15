"""Shared paid-video approval, REST transport, persisted jobs and local outputs."""
import argparse
import base64
import hashlib
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

API = "https://generativelanguage.googleapis.com"
MAX_BYTES = 256*1024*1024
VIDEO_MIMES={"video/mp4","video/mpeg","video/mpg","video/mov","video/avi","video/x-flv","video/webm","video/wmv","video/3gpp"}


def mime_for(path):
    return {".mov":"video/mov",".avi":"video/avi",".wmv":"video/wmv",".m4v":"video/mp4"}.get(
        Path(path).suffix.lower(),mimetypes.guess_type(str(path))[0])


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value,ensure_ascii=False,separators=(",", ":"),sort_keys=True).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    require(not Path(path).is_symlink(),"Refusing symlink metadata")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic(path, data):
    path=Path(path)
    require(not path.is_symlink(),"Refusing symlink output")
    temporary=path.with_name(path.name+".tmp-"+uuid.uuid4().hex)
    try:
        temporary.write_bytes(data)
        os.replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)


def save(path, value):
    atomic(path,(json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())


def identifier(value):
    require(isinstance(value,str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}",value),"Invalid clip ID")
    return value


def file_name(uri):
    require(isinstance(uri,str),"Expected Gemini file URI")
    if re.fullmatch(r"files/[A-Za-z0-9_-]+",uri):
        return uri
    parsed=urllib.parse.urlsplit(uri)
    require(parsed.scheme=="https" and parsed.hostname=="generativelanguage.googleapis.com"
            and not parsed.username and not parsed.password and parsed.port in (None,443),"Use a Google Gemini Files URI")
    match=re.fullmatch(r"/(?:download/)?v1beta/(files/[A-Za-z0-9_-]+)(?::download)?",parsed.path)
    require(match,"Invalid Gemini file URI")
    require(not any(k.lower() in {"key","api_key"} for k,_ in urllib.parse.parse_qsl(parsed.query)),"Do not put API keys in file URIs")
    return match[1]


def media(base, value, kind, references):
    """Resolve local bytes or a Gemini file, recording fingerprints without dumps."""
    value={"path":value} if isinstance(value,str) else value
    require(isinstance(value,dict) and ("path" in value)!=("uri" in value),"Media needs either path or uri")
    mime=value.get("mimeType")
    if "uri" in value:
        name=file_name(value["uri"])
        mime=mime or ("video/mp4" if kind=="video" else "image/png")
        require(mime in ({"image/png","image/jpeg","image/webp"} if kind=="image" else VIDEO_MIMES),"Unsupported media MIME type")
        references.append({"kind":kind,"uri":API+"/v1beta/"+name,"mimeType":mime})
        return {"uri":API+"/v1beta/"+name,"mimeType":mime}
    path=(Path(base)/value["path"]).expanduser().resolve()
    require(path.is_file() and path.stat().st_size<=18*1024*1024,"Inline media must be under 18 MiB; upload larger video using file-upload")
    mime=mime or mime_for(path)
    require(mime in ({"image/png","image/jpeg","image/webp"} if kind=="image" else VIDEO_MIMES),"Unsupported media MIME type")
    data=path.read_bytes()
    if kind=="image":
        try:
            from PIL import Image
            import io
            with Image.open(io.BytesIO(data)) as image:
                actual={"PNG":"image/png","JPEG":"image/jpeg","WEBP":"image/webp"}.get(image.format)
                image.verify()
            require(actual==mime,"Image bytes and MIME type differ")
        except ImportError:
            raise ValueError("Install the suite image requirements (Pillow)") from None
    references.append({"kind":kind,"sha256":sha(data),"bytes":len(data),"mimeType":mime})
    return {"data":base64.b64encode(data).decode(),"mimeType":mime}


def probe(path):
    try:
        result=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)],
                              capture_output=True,text=True,timeout=30,check=True)
    except FileNotFoundError:
        raise ValueError("FFprobe is required to verify video duration, dimensions and audio") from None
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
        raise ValueError("FFprobe could not inspect video") from None
    info=json.loads(result.stdout)
    video=next((s for s in info.get("streams",[]) if s.get("codec_type")=="video"),None)
    require(video,"Downloaded file has no video stream")
    rate=video.get("avg_frame_rate","0/1").split("/")
    fps=float(rate[0])/float(rate[1]) if len(rate)==2 and float(rate[1]) else 0
    return {"width":int(video["width"]),"height":int(video["height"]),
            "duration":float(info["format"]["duration"]),"fps":fps,"codec":video.get("codec_name"),
            "hasAudio":any(s.get("codec_type")=="audio" for s in info["streams"])}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def read_stream(response,on_progress=None):
    """Assemble documented step-based SSE without keeping thoughts/input dumps."""
    interaction,steps={},{}
    total=0
    block=[]
    def consume(lines):
        payload="\n".join(line[5:].lstrip() for line in lines if line.startswith("data:"))
        if not payload or payload=="[DONE]":
            return
        event=json.loads(payload)
        kind=event.get("event_type",event.get("type"))
        if isinstance(event.get("interaction"),dict):
            interaction.update(event["interaction"])
        if kind=="interaction.status_update":
            interaction.update({"id":event["interaction_id"],"status":event["status"]})
        if kind=="step.start":
            step=event.get("step",{})
            if step.get("type")=="model_output":
                steps[event["index"]]={"type":"model_output","content":[]}
        if kind=="step.delta" and event.get("index") in steps:
            delta=event.get("delta",{})
            if delta.get("type")=="video":
                content=steps[event["index"]]["content"]
                if content and "data" in delta and "data" in content[-1] and not delta.get("uri"):
                    content[-1]["data"]+=delta["data"]
                else:
                    content.append(delta)
        if kind in {"interaction.created","interaction.completed","step.stop"} and on_progress:
            partial={**interaction,"steps":[steps[index] for index in sorted(steps)]}
            if partial.get("id"):
                on_progress(partial)
    for raw in response:
        total+=len(raw)
        require(total<=MAX_BYTES,"SSE response exceeds local 256 MiB guard")
        line=raw.decode().rstrip("\r\n")
        if not line:
            consume(block)
            block=[]
        else:
            block.append(line)
    if block:
        consume(block)
    return {**interaction,"steps":[steps[index] for index in sorted(steps)]}


class Client:
    def __init__(self):
        self.key=os.environ.get("GEMINI_API_KEY")
        require(self.key,"Export GEMINI_API_KEY; .env is not loaded automatically")
        self.opener=urllib.request.build_opener(NoRedirect())
        self.on_progress=None

    def send(self,method,endpoint,body=None,headers=None,raw=False):
        url=endpoint if endpoint.startswith("https://") else API+endpoint
        parsed=urllib.parse.urlsplit(url)
        require(parsed.scheme=="https" and parsed.hostname=="generativelanguage.googleapis.com"
                and not parsed.username and not parsed.password and parsed.port in (None,443),"Untrusted API URL")
        payload=body if isinstance(body,bytes) else encoded(body) if body is not None else None
        req=urllib.request.Request(url,data=payload,method=method,
            headers={"x-goog-api-key":self.key,"Content-Type":"application/json",**(headers or {})})
        if isinstance(body,dict) and body.get("stream"):
            req.add_header("Accept","text/event-stream")
        try:
            with self.opener.open(req,timeout=180) as response:
                if not raw and "text/event-stream" in response.headers.get("Content-Type",""):
                    return read_stream(response,self.on_progress),dict(response.headers)
                data=response.read(MAX_BYTES+1)
                require(len(data)<=MAX_BYTES,"API response exceeds local 256 MiB guard")
                return (data if raw else json.loads(data or b"{}")),dict(response.headers)
        except urllib.error.HTTPError as error:
            raise ValueError(f"Gemini HTTP {error.code}; no automatic retry") from None
        except (urllib.error.URLError,TimeoutError):
            raise ValueError("Request failed or timed out; inspect saved state before resubmitting") from None

    def download(self,uri):
        name=file_name(uri)
        url=API+f"/v1beta/{name}:download?alt=media"
        for _ in range(6):
            parsed=urllib.parse.urlsplit(url)
            host=parsed.hostname or ""
            require(parsed.scheme=="https" and not parsed.username and not parsed.password
                    and parsed.port in (None,443) and (host=="generativelanguage.googleapis.com"
                    or host=="storage.googleapis.com" or host.endswith(".googleusercontent.com")
                    or host.endswith(".googlevideo.com")),"Untrusted video download redirect")
            headers={"x-goog-api-key":self.key} if host=="generativelanguage.googleapis.com" else {}
            try:
                with self.opener.open(urllib.request.Request(url,headers=headers),timeout=180) as response:
                    data=response.read(MAX_BYTES+1)
                    require(len(data)<=MAX_BYTES,"Video exceeds local 256 MiB guard")
                    return data
            except urllib.error.HTTPError as error:
                if error.code in {301,302,303,307,308} and error.headers.get("Location"):
                    url=urllib.parse.urljoin(url,error.headers["Location"])
                    continue
                raise ValueError(f"Video download HTTP {error.code}; retry download, not generation") from None
            except (urllib.error.URLError,TimeoutError):
                raise ValueError("Download failed; retry download without regenerating") from None
        raise ValueError("Too many video download redirects")


def prepared(config_path, provider, model, mode, body, references, expected):
    config=read(config_path)
    identifier(config.get("id"))
    cost=config.get("costEstimate")
    if cost is not None:
        require(isinstance(cost,dict) and isinstance(cost.get("usd"),(int,float))
                and not isinstance(cost["usd"],bool) and math.isfinite(cost["usd"]) and cost["usd"]>=0
                and isinstance(cost.get("source"),str) and cost["source"].startswith("https://")
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}",cost.get("checkedAt","")),"Invalid costEstimate: provide usd, source and checkedAt")
    require(len(encoded(body))<20*1024*1024,"Request exceeds 20 MiB; upload videos with file-upload")
    metadata={"schemaVersion":1,"id":config["id"],"provider":provider,"model":model,"mode":mode,
              "prompt":config.get("prompt",""),
              "configSha256":sha(Path(config_path).read_bytes()),"references":references,
              "expected":expected,"costEstimate":cost,"requestCount":1}
    metadata["requestSha256"]=sha(encoded({"body":body,"metadata":metadata}))
    return body,metadata


def new_run(output,state):
    path=Path(output).expanduser()
    require(not path.is_symlink(),"Refusing symlink run directory")
    root=path.resolve()
    root.mkdir(parents=True,exist_ok=False)
    save(root/"state.json",state)
    return root


def read_run(directory,provider):
    root=Path(directory).expanduser()
    require(not root.is_symlink(),"Refusing symlink run directory")
    root=root.resolve()
    state=read(root/"state.json")
    require(state.get("provider")==provider,"Wrong provider run")
    if provider!="gemini-file":
        identifier(state.get("id"))
    return root,state


def approve(metadata,digest,note,body):
    require(digest==metadata["requestSha256"] and isinstance(note,str) and note.strip(),
            "Paid generation requires --approve-request with the current dry-run SHA and --approval-note after explicit user approval")
    require(metadata.get("costEstimate") is not None,"Prepare a current costEstimate before asking for paid-generation approval")
    current={k:v for k,v in metadata.items() if k!="requestSha256"}
    require(sha(encoded({"body":body,"metadata":current}))==digest,"Prepared request changed; obtain approval for the current fingerprint")


def persist(root,state,result,adapter):
    update,outputs=adapter.parse_response(result)
    state.update(update)
    save(root/"state.json",state)  # Identity survives failures while decoding output.
    stored=[]
    for index,output in enumerate(outputs):
        item={k:v for k,v in output.items() if k!="data"}
        previous=state.get("outputs",[])[index] if index<len(state.get("outputs",[])) else {}
        if "uri" not in item and previous.get("uri"):
            item["uri"]=previous["uri"]
        if item.get("uri") and item["uri"]==previous.get("uri"):
            item.update({key:previous[key] for key in ("receivedPath","sha256") if key in previous})
        if "data" in output:
            data=base64.b64decode(output["data"],validate=True)
            require(len(data)<=MAX_BYTES and data[4:8]==b"ftyp","Expected MP4 video bytes")
            path=root/f"received-{index+1}.mp4"
            if path.exists():
                require(not path.is_symlink() and sha(path.read_bytes())==sha(data),"Existing received video differs")
            else:
                atomic(path,data)
            item.update({"receivedPath":path.name,"sha256":sha(data)})
        stored.append(item)
    if stored:
        state["outputs"]=stored
    save(root/"state.json",state)
    return state


def check_files(client,references):
    for name in sorted({file_name(r["uri"]) for r in references if "uri" in r}):
        info,_=client.send("GET","/v1beta/"+name)
        require(info.get("state")=="ACTIVE",f"Input file {name} is not ACTIVE; check file-status before generation")


def submit(body,metadata,output,adapter,approval=None,note=None,client=None):
    approve(metadata,approval,note,body)
    client=client or Client()
    state={**metadata,"status":"preflight","approval":{"requestSha256":approval,"note":note},"outputs":[]}
    root=new_run(output,state)
    try:
        check_files(client,metadata["references"])
        state["status"]="submitting"
        save(root/"state.json",state)
        if body.get("stream"):
            client.on_progress=lambda partial: persist(root,state,partial,adapter)
        result,_=client.send("POST",adapter.endpoint(metadata),body)
        return persist(root,state,result,adapter)
    except BaseException:
        state["status"]="blocked-before-submission" if state["status"]=="preflight" else "failed-or-unknown"
        save(root/"state.json",state)
        raise


def status(directory,adapter,client=None):
    root,state=read_run(directory,adapter.PROVIDER)
    endpoint=adapter.status_endpoint(state)
    require(endpoint,"No provider job identity; inspect provider records before any new submission")
    result,_=(client or Client()).send("GET",endpoint)
    if state.get("operationName"):
        require(result.get("name")==state["operationName"],"Operation identity differs")
    if state.get("interactionId"):
        require(result.get("id")==state["interactionId"],"Interaction identity differs")
    return root,persist(root,state,result,adapter)


def download(directory,adapter,client=None):
    root,state=read_run(directory,adapter.PROVIDER)
    if not state.get("outputs"):
        client=client or Client()
        root,state=status(directory,adapter,client)
    require(state.get("status") in {"completed","downloaded","completed-with-warnings"},"Video is not completed; use status later")
    require(state.get("outputs"),"Completed request returned no video; do not automatically regenerate")
    assets=[]
    previous=read(root/"assets.json").get("assets",[]) if (root/"assets.json").exists() else []
    for index,item in enumerate(state["outputs"]):
        filename=f"{state['id']}-{index+1}.mp4"
        path=root/filename
        require(not path.is_symlink(),"Refusing symlink video")
        known=next((a for a in previous if a.get("path")==filename
                    and a.get("generation",{}).get("requestSha256")==state["requestSha256"]),None)
        if path.exists() and known:
            data=path.read_bytes()
            require(sha(data)==known["sha256"],"Existing output changed; refusing local recovery")
        elif item.get("receivedPath"):
            source=root/item["receivedPath"]
            require(source.parent==root and not source.is_symlink(),"Unsafe received-video path")
            data=source.read_bytes()
            require(sha(data)==item["sha256"],"Received video changed")
        else:
            client=client or Client()
            name=file_name(item["uri"])
            info,_=client.send("GET","/v1beta/"+name)
            require(info.get("state")=="ACTIVE","Output video file is not ACTIVE; retry download later")
            data=client.download(item["uri"])
        require(data[4:8]==b"ftyp","Download is not an MP4; preserved run can be retried")
        digest=sha(data)
        if not item.get("receivedPath"):
            received=root/f"received-{index+1}.mp4"
            if received.exists():
                require(not received.is_symlink() and sha(received.read_bytes())==digest,"Existing received output differs")
            else:
                atomic(received,data)
            item.update({"receivedPath":received.name,"sha256":digest})
            save(root/"state.json",state)
        if path.exists():
            require(sha(path.read_bytes())==digest,"Existing output differs; preserve it before retrying download")
        else:
            atomic(path,data)
        details=probe(path)
        expected=state["expected"]
        w,h=map(int,expected["aspectRatio"].split(":"))
        issues=[]
        if abs(details["width"]/details["height"]-w/h)/(w/h)>.025:
            issues.append("aspect ratio differs")
        if abs(details["duration"]-expected["durationSeconds"])>.5:
            issues.append("duration differs; inspect extension/edit semantics and timeline")
        if abs(details["fps"]-24)>.1:
            issues.append("frame rate differs from provider specification")
        expected_edge={"360p":360,"720p":720,"1080p":1080,"4k":2160}[expected["resolution"]]
        if min(details["width"],details["height"])!=expected_edge:
            issues.append("resolution differs from request")
        if not details["hasAudio"]:
            issues.append("no audio stream; review intended sound")
        asset={"id":state["id"] if len(state["outputs"])==1 else f"{state['id']}-{index+1}",
               "path":filename,"kind":"video","source":state["provider"]+":"+state["model"],
               "sha256":digest,**details,"reviewed":False,"reviewIssues":issues,
               "generation":{"requestSha256":state["requestSha256"],"operationName":state.get("operationName"),
                             "interactionId":state.get("interactionId")}}
        assets.append(asset)
        save(root/"assets.json",{"schemaVersion":1,"assets":assets,"collectionComplete":False})
    save(root/"assets.json",{"schemaVersion":1,"assets":assets,"collectionComplete":True})
    state["status"]="completed-with-warnings" if any(a["reviewIssues"] for a in assets) else "downloaded"
    save(root/"state.json",state)
    return assets


def upload(path,output,client=None,dry_run=False):
    path=Path(path).expanduser().resolve()
    require(path.is_file() and path.stat().st_size<100*1024*1024,"Local upload guard is 100 MiB")
    mime=mime_for(path)
    require(mime in VIDEO_MIMES|{"image/png","image/jpeg","image/webp"},"Unsupported upload MIME type")
    data=path.read_bytes()
    info={"schemaVersion":1,"provider":"gemini-file","sha256":sha(data),"bytes":len(data),"mimeType":mime}
    if mime in VIDEO_MIMES:
        info["mediaMetadata"]=probe(path)
    if dry_run:
        return {**info,"billableSubmission":False}
    client=client or Client()
    info.update({"status":"uploading","displayName":"marketing-video-"+uuid.uuid4().hex})
    root=new_run(output,info)
    try:
        _,headers=client.send("POST","/upload/v1beta/files",{"file":{"displayName":info["displayName"]}},
            {"X-Goog-Upload-Protocol":"resumable","X-Goog-Upload-Command":"start",
             "X-Goog-Upload-Header-Content-Length":str(len(data)),"X-Goog-Upload-Header-Content-Type":mime})
        url=next((v for k,v in headers.items() if k.lower()=="x-goog-upload-url"),None)
        require(url,"No upload session URL; do not automatically upload again")
        result,_=client.send("POST",url,data,{"Content-Type":mime,"X-Goog-Upload-Offset":"0","X-Goog-Upload-Command":"upload, finalize"})
        file=result["file"]
        name=file_name(file.get("uri") or file["name"])
        info.update({"name":name,"uri":API+"/v1beta/"+name,"status":file.get("state","PROCESSING")})
        save(root/"state.json",info)
        return info
    except BaseException:
        info["status"]="failed-or-unknown"
        save(root/"state.json",info)
        raise


def cli(adapter):
    parser=argparse.ArgumentParser(description=adapter.__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    commands=("submit","continue") if hasattr(adapter,"continue_run") else ("submit",)
    for command in commands:
        p=sub.add_parser(command)
        if command=="continue":
            p.add_argument("run")
        p.add_argument("config")
        p.add_argument("--out",required=True)
        p.add_argument("--dry-run",action="store_true")
        p.add_argument("--approve-request")
        p.add_argument("--approval-note")
    if hasattr(adapter,"history"):
        sub.add_parser("history").add_argument("run")
    for command in ("status","download"):
        sub.add_parser(command).add_argument("run")
    if hasattr(adapter,"cancel"):
        sub.add_parser("cancel").add_argument("run")
    p=sub.add_parser("file-upload")
    p.add_argument("file")
    p.add_argument("--out",required=True)
    p.add_argument("--dry-run",action="store_true")
    sub.add_parser("file-status").add_argument("run")
    args=parser.parse_args()
    if args.command=="continue":
        result=adapter.continue_run(args.run,args.config,args.out,args.dry_run,args.approve_request,args.approval_note)
    elif args.command=="history":
        result=adapter.history(args.run)
    elif args.command=="submit":
        body,meta=adapter.prepare(args.config)
        if args.dry_run:
            result={**meta,"billableSubmission":False,"approvalRequired":True}
        else:
            result=submit(body,meta,args.out,adapter,args.approve_request,args.approval_note)
    elif args.command=="status":
        _,result=status(args.run,adapter)
    elif args.command=="download":
        result=download(args.run,adapter)
    elif args.command=="file-upload":
        result=upload(args.file,args.out,dry_run=args.dry_run)
    elif args.command=="cancel":
        result=adapter.cancel(args.run)
    else:
        root,state=read_run(args.run,"gemini-file")
        file,_=Client().send("GET","/v1beta/"+file_name(state["uri"]))
        state["status"]=file.get("state","UNKNOWN")
        save(root/"state.json",state)
        result=state
    print(json.dumps(result,ensure_ascii=False,indent=2))


def main(adapter):
    try:
        cli(adapter)
    except (ValueError,KeyError,OSError,TypeError) as error:
        print(f"{adapter.PROVIDER}: {error}",file=sys.stderr)
        sys.exit(1)
