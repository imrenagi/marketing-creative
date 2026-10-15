#!/usr/bin/env python3
"""Import supplied/generated media and local scene resources into one project."""
import argparse
import copy
import json
import mimetypes
from pathlib import Path
import runpy
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/"project.py"))
C=runpy.run_path(str(HERE/"video_provider.py"))
require=C["require"]
RESOURCE_EXTENSIONS={".glb",".gltf",".bin",".js",".mjs",".css",".html",".glsl",".vert",".frag",".woff",".woff2",".ttf",".otf",".json"}


def describe(path,kind):
    mime=C["mime_for"](path)
    if kind=="auto":
        kind="image" if mime and mime.startswith("image/") else "video" if mime in C["VIDEO_MIMES"] else "audio" if mime and mime.startswith("audio/") else "resource"
    if kind=="image":
        if path.suffix.lower()==".svg":
            root=ET.fromstring(path.read_bytes())
            require(root.tag.split("}")[-1]=="svg","Expected an SVG image")
            return kind,{"mimeType":"image/svg+xml"}
        try:
            from PIL import Image
        except ImportError:
            raise ValueError("Install the suite image requirements (Pillow)") from None
        with Image.open(path) as image:
            require(image.format in {"PNG","JPEG","WEBP"},"Use PNG, JPEG, WEBP or SVG images")
            details={"width":image.width,"height":image.height,"mimeType":Image.MIME[image.format]}
            image.verify()
        return kind,details
    if kind=="video":
        require(mime in C["VIDEO_MIMES"],"Unsupported video format")
        return kind,{"mimeType":mime,**C["probe"](path)}
    if kind=="audio":
        require(mime and mime.startswith("audio/"),"Expected an audio file")
        result=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)],
                              capture_output=True,text=True,timeout=30,check=True)
        info=json.loads(result.stdout)
        audio=next((s for s in info["streams"] if s.get("codec_type")=="audio"),None)
        require(audio,"File has no audio stream")
        return kind,{"mimeType":mime,"duration":float(info["format"]["duration"]),"codec":audio.get("codec_name"),
                     "channels":audio.get("channels"),"sampleRate":int(audio["sample_rate"])}
    require(kind=="resource" and path.suffix.lower() in RESOURCE_EXTENSIONS,"Unsupported local scene resource")
    return kind,{"mimeType":mime or "application/octet-stream"}


def imported(root,source,asset_id,kind="auto",source_label=None,provider_manifest=None,generated_id=None,
             audio_policy="mute",review_note=None,dry_run=False):
    requested=Path(root).expanduser()
    require(not requested.is_symlink(),"Refusing symlink project directory")
    root=requested.resolve()
    source=Path(source).expanduser().resolve()
    require(source.is_file(),"Source file is missing")
    C["identifier"](asset_id)
    require(audio_policy in {"mute","retain","mix"},"Unknown audio policy")
    _,_,_,manifest,_=P["load"](root)
    require(not any(a["id"]==asset_id for a in manifest["assets"]),"Asset ID already exists; use a new version/ID")
    manifest_file=P["safe_output"](root,"assets/manifest.json")
    original=manifest_file.read_bytes()
    data=source.read_bytes()
    digest=C["sha"](data)
    kind,details=describe(source,kind)
    require(C["sha"](source.read_bytes())==digest,"Source changed during inspection; prepare the import again")
    entry=None
    provenance=None
    if provider_manifest:
        report_path=Path(provider_manifest).resolve()
        report=C["read"](report_path)
        key=generated_id or asset_id
        matches=[a for a in report.get("assets",[]) if a.get("id")==key]
        require(len(matches)==1,"Generated manifest needs one matching item ID; use --generated-id when renaming")
        entry=matches[0]
        relative=Path(entry["path"])
        require(not relative.is_absolute() and ".." not in relative.parts,"Unsafe generated asset path")
        require(entry.get("sha256")==digest,"Generated file hash differs from provider manifest")
        require(entry.get("kind",kind)==kind,"Provider asset kind differs from measured file")
        for field in ("width","height"):
            require(field not in entry or entry[field]==details.get(field),"Generated dimensions differ from measured file")
        generation=copy.deepcopy(entry.get("generation",{}))
        identities=[value for value in (generation.get("requestSha256"),entry.get("requestSha256"),
                                       report.get("requestSha256")) if value]
        require(len(set(identities))<=1,"Generated manifest request identities differ")
        request_id=identities[0] if identities else None
        if request_id:
            generation["requestSha256"]=request_id
        provenance={"manifestSha256":C["sha"](report_path.read_bytes()),"assetId":key,"assetSha256":digest,
                    "generation":generation}
        if request_id:
            provenance["requestSha256"]=request_id
        state_file=report_path.parent/"state.json"
        if state_file.exists() and request_id:
            state=C["read"](state_file)
            require(state.get("requestSha256")==request_id,"Provider state request differs from generated manifest")
            approval_id=(state.get("approval") or {}).get("requestSha256")
            require(not state.get("approval") or approval_id==request_id,
                    "Provider approval request differs from generated manifest")
            provenance.update({"provider":state.get("provider","gemini-image"),"model":state.get("model"),
                               "requestSha256":request_id})
            if state.get("approval"):
                provenance["approvalRequestSha256"]=approval_id
            source_label=source_label or entry.get("source") or f"{provenance['provider']}:{provenance['model']}"
        else:
            source_label=source_label or entry.get("source") or "generated:provider-not-recorded"
    require(source_label is None or isinstance(source_label,str) and source_label.strip(),"Source label must be text")
    relative=f"assets/imported/{asset_id}/{asset_id}{source.suffix.lower()}"
    destination=P["safe_output"](root,relative)
    require(not destination.parent.exists(),"Import directory exists; refusing overwrite")
    asset={"id":asset_id,"path":relative,"kind":kind,"source":source_label or "user-supplied",
           "sha256":digest,**details,"reviewed":bool(review_note)}
    if kind in {"video","audio"}:
        asset["audioPolicy"]=audio_policy
    if provenance:
        asset["provenance"]=provenance
        asset["generation"]=provenance["generation"]
        asset["reviewIssues"]=entry.get("reviewIssues",[])
    if review_note:
        require(isinstance(review_note,str) and review_note.strip(),"Review note must describe the actual inspection")
        asset["reviewNote"]=review_note
    if dry_run:
        return {"asset":asset,"writes":False,"invalidates":"resolved timing, builds and export records"}
    backup=P["safe_output"](root,"assets/backups/"+uuid.uuid4().hex+"/manifest.json")
    backup.parent.mkdir(parents=True,exist_ok=False)
    C["atomic"](backup,original)
    destination.parent.mkdir(parents=True,exist_ok=False)
    C["atomic"](destination,data)
    require(manifest_file.read_bytes()==original,"Manifest changed during import; copied file/backup retained for reconciliation")
    updated=copy.deepcopy(manifest)
    updated["assets"].append(asset)
    C["save"](manifest_file,updated)
    return {"asset":asset,"backup":str(backup.relative_to(root)),"next":"resolve timing, rebuild and review affected variants"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--file",required=True)
    parser.add_argument("--id",required=True)
    parser.add_argument("--kind",choices=("auto","image","video","audio","resource"),default="auto")
    parser.add_argument("--source")
    parser.add_argument("--provider-manifest")
    parser.add_argument("--generated-id")
    parser.add_argument("--audio-policy",choices=("mute","retain","mix"),default="mute")
    parser.add_argument("--review-note")
    parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args()
    result=imported(args.project,args.file,args.id,args.kind,args.source,args.provider_manifest,args.generated_id,
                    args.audio_policy,args.review_note,args.dry_run)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    try:
        main()
    except (ValueError,KeyError,OSError,TypeError,subprocess.CalledProcessError,subprocess.TimeoutExpired,ET.ParseError) as error:
        print(f"assets: {error}",file=sys.stderr)
        sys.exit(1)
