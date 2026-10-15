#!/usr/bin/env python3
"""Prepare and explicitly approve Omni Flash generation, edits and extensions."""
import math
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
V=runpy.run_path(str(Path(__file__).resolve().parents[2]/"motion-video-producer/scripts/video_provider.py"))
require,read,media=V["require"],V["read"],V["media"]
PROVIDER="omni"
DEFAULT_MODEL="gemini-omni-1.1-flash"
MODES={"text","image","interpolate","loop","reference","edit","extend","upscale"}


def interaction_id(value):
    require(isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9_-]+",value),"Invalid Omni interaction ID")
    return value


def prepare(path):
    path=Path(path).resolve()
    config=read(path)
    require(config.get("schemaVersion")==1,"Unsupported Omni config version")
    allowed={"schemaVersion","id","model","mode","prompt","media","previousInteractionId","previousRun",
             "sourceDurationSeconds","aspectRatio","durationSeconds","resolution","delivery","background","store","stream","task","costEstimate"}
    require(set(config)<=allowed,"Unknown Omni config fields; audio references, voice editing, system instructions and sampler/negative-prompt controls are unsupported")
    model=config.get("model",DEFAULT_MODEL)
    require(model in {DEFAULT_MODEL,"gemini-omni-flash-preview"},"Use a documented Omni Flash model")
    mode=config.get("mode","text")
    require(mode in MODES,"Unsupported Omni mode")
    prompt=config.get("prompt","")
    require(isinstance(prompt,str) and prompt.strip(),"Omni needs a prompt describing the requested video or edit")
    duration=config.get("durationSeconds",5)
    ratio=config.get("aspectRatio","16:9")
    resolution=config.get("resolution","720p")
    delivery=config.get("delivery","uri")
    require(type(duration) is int and 3<=duration<=10,"Omni durationSeconds must be 3..10")
    require(ratio in {"16:9","9:16"},"Omni native ratios are 16:9 and 9:16; recompose other canvases in the producer")
    require(resolution in {"360p","720p","1080p","4k"},"Unsupported Omni resolution")
    require(delivery in {"inline","uri"},"Delivery must be inline or uri")
    for field in ("background","store","stream"):
        require(type(config.get(field,False if field!="store" else True)) is bool,f"{field} must be boolean")
    require(not config.get("background",False) or config.get("store",True),"Background jobs require store=true for recovery")
    previous=config.get("previousInteractionId")
    require(not (previous and config.get("previousRun")),"Use previousInteractionId or previousRun, not both")
    references=[]
    source_duration=config.get("sourceDurationSeconds")
    if config.get("previousRun"):
        source=(path.parent/config["previousRun"]).resolve()
        _,prior=V["read_run"](source,PROVIDER)
        require(prior.get("stored",True),"Previous interaction used store=false; use its downloaded video as a new source")
        require(prior.get("status") in {"completed","downloaded","completed-with-warnings"},"Previous Omni run is not completed")
        previous=prior.get("interactionId")
        source_duration=prior["expected"]["durationSeconds"]
        if (source/"assets.json").exists():
            source_duration=read(source/"assets.json")["assets"][0]["duration"]
        references.append({"kind":"provenance","previousInteractionId":previous,
                           "sourceRunSha256":V["sha"]((source/"state.json").read_bytes())})
    if previous:
        interaction_id(previous)
    inputs=[]
    sources=[]
    bindings=[]
    counts={"first_frame":0,"last_frame":0,"image_reference":0,"video_source":0,"video_reference":0}
    image_count=video_count=0
    first_binding=None
    values=config.get("media",[])
    require(isinstance(values,list),"media must be a list")
    for value in values:
        require(isinstance(value,dict),"Media entries need type, role and path/uri")
        kind,role=value.get("type"),value.get("role")
        require(kind in {"image","video"} and role in counts,"Unsupported media type or role; standalone audio references are not supported")
        require((kind=="image")== (role in {"first_frame","last_frame","image_reference"}),"Media type differs from its role")
        counts[role]+=1
        if kind=="video":
            if "path" in value:
                measured=V["probe"]((path.parent/value["path"]).resolve())
                seconds=measured["duration"]
            else:
                seconds=value.get("durationSeconds")
            require(isinstance(seconds,(int,float)) and not isinstance(seconds,bool) and math.isfinite(seconds)
                    and 0<seconds<=(3.05 if role=="video_reference" else 10.05),"Uploaded edit/source videos must be <=10s; likeness reference videos <=3s")
            if role=="video_source":
                source_duration=seconds
            references_extra={"durationSeconds":seconds}
        else:
            references_extra={}
        part=media(path.parent,value,kind,references)
        references[-1].update({"role":role,**references_extra})
        inputs.append({"type":kind,"mime_type":part["mimeType"],**({"uri":part["uri"]} if "uri" in part else {"data":part["data"]})})
        if kind=="image":
            image_count+=1
            name=f"Image{image_count}"
        else:
            video_count+=1
            name=f"Video{video_count}"
        if role=="first_frame":
            first_binding=name
            sources.append(f"<FIRST_FRAME>@{name}")
        elif role=="last_frame":
            sources.append(f"<LAST_FRAME>@{name}")
        elif role=="video_source":
            sources.append(f"<VIDEO_0>@{name}")
        elif role=="image_reference":
            bindings.append(f"<IMAGE_REF_{counts[role]-1}>@{name}")
        else:
            bindings.append(f"<VIDEO_REF_{counts[role]-1}>@{name}")
    require(counts["first_frame"]<=1 and counts["last_frame"]<=1 and counts["video_source"]<=1
            and counts["video_reference"]<=3,"Only one source/first/last frame and at most three likeness reference videos")
    require(not previous or counts["video_source"]==0,"Do not combine a previous interaction and an uploaded source video")
    if mode=="text":
        require(not values and not previous,"Text mode has no input media; choose a source/reference mode")
    elif mode in {"image","interpolate","loop"}:
        require(counts["first_frame"]==1 and not counts["video_source"] and not previous,"Image-driven mode needs one first_frame and no source video/previous turn")
        require(counts["last_frame"]==(1 if mode=="interpolate" else 0),"Interpolation needs last_frame; loop reuses its first frame")
        if mode=="loop":
            sources.append(f"<LAST_FRAME>@{first_binding}")
    elif mode=="reference":
        require(bindings and not sources and not previous,"Reference mode needs references without source frames/video")
    else:
        require(bool(previous) != bool(counts["video_source"]),"Edit/extend/upscale needs exactly one source video or previous interaction")
        require(not counts["first_frame"] and not counts["last_frame"],"Editing uses a video source rather than frame sources")
    if mode=="upscale":
        require(isinstance(source_duration,(int,float)) and 3<=source_duration<=10.05,"Upscale needs a known 3..10s source duration")
        if "durationSeconds" not in config:
            duration=round(source_duration)
        require(abs(duration-source_duration)<=.5,"Upscale should preserve source duration; use edit for a deliberate duration change")
    expected_duration=duration
    if mode=="extend":
        require(isinstance(source_duration,(int,float)) and not isinstance(source_duration,bool)
                and math.isfinite(source_duration) and 0<source_duration and source_duration+duration<=40,
                "Extension requires known sourceDurationSeconds and a combined runtime <=40s")
        expected_duration=source_duration+duration
        prompt="Continue the scene at the end of the existing video. "+prompt
    if mode=="upscale":
        require(resolution in {"1080p","4k"},"Upscale requests need 1080p or 4k")
        prompt="Upscale the supplied video, preserving its content and motion. "+prompt
    if sources:
        prompt="[# Sources "+" ".join(sources)+"] "+prompt
    if bindings:
        prompt="[# References "+" ".join(bindings)+"] "+prompt
    inputs.append({"type":"text","text":prompt})
    body={"model":model,"input":inputs,"response_format":{"type":"video","aspect_ratio":ratio,
        "duration":f"{duration}s","resolution":resolution,"delivery":delivery},
        "background":config.get("background",False),"store":config.get("store",True),"stream":config.get("stream",False)}
    if previous:
        body["previous_interaction_id"]=previous
    if "task" in config:
        expected_task={"text":"text_to_video","image":"image_to_video","interpolate":"image_to_video","loop":"image_to_video",
                       "reference":"reference_to_video","edit":"edit","upscale":"edit","extend":"extend"}[mode]
        require(config["task"]==expected_task,"Explicit task differs from selected mode")
        body["generation_config"]={"video_config":{"task":config["task"]}}
    body,meta=V["prepared"](path,PROVIDER,model,mode,body,references,
        {"aspectRatio":ratio,"durationSeconds":expected_duration,"resolution":resolution,"fps":24,"nativeAudio":True})
    # Include recovery/privacy choices in the approved fingerprint.
    meta.update({"stored":body["store"],"background":body["background"],"stream":body["stream"]})
    meta["requestSha256"]=V["sha"](V["encoded"]({"body":body,"metadata":{k:v for k,v in meta.items() if k!="requestSha256"}}))
    return body,meta


def endpoint(metadata):
    return "/v1beta/interactions"


def status_endpoint(state):
    require(state.get("stored",True),"store=false disables later interaction retrieval; download preserved creation output")
    value=state.get("interactionId")
    return "/v1beta/interactions/"+interaction_id(value) if value else None


def parse_response(result):
    value=result.get("id")
    update={"status":result.get("status","pending")}
    if value:
        update["interactionId"]=interaction_id(value)
    require(value or result.get("error"),"Omni returned no interaction identity; inspect unknown submission")
    outputs=[]
    for step in result.get("steps",[]):
        if step.get("type")=="model_output":
            outputs.extend(item for item in step.get("content",[]) if item.get("type")=="video")
    if not outputs and isinstance(result.get("output_video"),dict):
        outputs=[result["output_video"]]
    videos=[]
    for output in outputs:
        require(output.get("mime_type",output.get("mimeType","video/mp4"))=="video/mp4","Expected Omni MP4 output")
        if output.get("uri"):
            V["file_name"](output["uri"])
            videos.append({"uri":output["uri"],"mimeType":"video/mp4"})
        elif output.get("data"):
            videos.append({"data":output["data"],"mimeType":"video/mp4"})
    if update["status"]=="completed" and not videos:
        update["status"]="filtered-or-empty"
    if result.get("usage"):
        update["usage"]=result["usage"]
    return update,videos


def cancel(directory,client=None):
    root,state=V["read_run"](directory,PROVIDER)
    require(state.get("background"),"Only background Omni interactions support cancellation")
    endpoint=status_endpoint(state)
    require(endpoint,"No interaction identity to cancel")
    result,_=(client or V["Client"]()).send("POST",endpoint+"/cancel",{})
    require(result.get("id")==state["interactionId"],"Cancellation interaction identity differs")
    return V["persist"](root,state,result,SimpleNamespace(parse_response=parse_response))


if __name__=="__main__":
    V["main"](sys.modules[__name__])
