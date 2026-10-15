"""Local generated/supplied asset registration and mixed-media integration."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SKILLS=ROOT/"plugins/marketing-creative/skills"


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


A=module("asset_importer",SKILLS/"motion-video-producer/scripts/assets.py")
P=module("assembly_project",SKILLS/"motion-video-producer/scripts/project.py")
Q=module("assembly_qa",SKILLS/"motion-video-qa/scripts/check.py")
try:
    from PIL import Image
except ImportError:
    Image=None


@unittest.skipUnless(Image,"Install Pillow for image imports")
class AssetAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.project=self.base/"project"
        P.init(self.project,"combined",list(P.PRESETS),8)
        self.image=self.base/"source.png"
        Image.new("RGB",(48,32),"green").save(self.image)

    def test_dry_run_writes_no_assets_or_backups(self):
        before=(self.project/"assets/manifest.json").read_bytes()
        result=A.imported(self.project,self.image,"product",dry_run=True)
        self.assertFalse(result["writes"])
        self.assertEqual((self.project/"assets/manifest.json").read_bytes(),before)
        self.assertFalse((self.project/"assets/imported").exists())
        self.assertFalse((self.project/"assets/backups").exists())

    def generated(self):
        run=self.base/"generated"
        run.mkdir()
        P.write(run/"assets.json",{"schemaVersion":1,"requestSha256":"synthetic-request","assets":[{"id":"demo","path":"source.png",
            "sha256":P.digest(self.image),"width":48,"height":32,"reviewed":False,"reviewIssues":["inspect copy"]}]})
        P.write(run/"state.json",{"provider":"gemini-image","model":"gemini-nano-banana-2.1","requestSha256":"synthetic-request"})
        return run/"assets.json"

    def test_generated_image_import_preserves_provenance_and_manifest_backup(self):
        report=self.generated()
        before=(self.project/"assets/manifest.json").read_bytes()
        result=A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")
        asset=result["asset"]
        self.assertEqual(asset["provenance"]["assetId"],"demo")
        self.assertEqual(asset["provenance"]["model"],"gemini-nano-banana-2.1")
        self.assertEqual(asset["reviewIssues"],["inspect copy"])
        self.assertFalse(asset["reviewed"])
        self.assertEqual((self.project/result["backup"]).read_bytes(),before)
        self.assertEqual((self.project/asset["path"]).read_bytes(),self.image.read_bytes())
        with self.assertRaisesRegex(ValueError,"already exists"):
            A.imported(self.project,self.image,"hero")

    def test_manifest_request_identity_survives_without_sibling_state(self):
        report=self.generated()
        (report.parent/"state.json").unlink()
        asset=A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")["asset"]
        self.assertEqual(asset["generation"]["requestSha256"],"synthetic-request")
        self.assertEqual(asset["provenance"]["requestSha256"],"synthetic-request")
        self.assertNotIn("approvalRequestSha256",asset["provenance"])

    def test_conflicting_manifest_state_and_approval_requests_are_rejected(self):
        report=self.generated()
        original=P.read(report)
        state_file=report.parent/"state.json"
        state=P.read(state_file)
        scenarios=[({"generation":{"requestSha256":"other-request"}},state),
                   ({},{**state,"requestSha256":"other-request"}),
                   ({},{**state,"approval":{"requestSha256":"other-request"}})]
        for entry_changes,state_changes in scenarios:
            data=json.loads(json.dumps(original))
            data["assets"][0].update(entry_changes)
            P.write(report,data)
            P.write(state_file,state_changes)
            with self.assertRaisesRegex(ValueError,"request identities differ|request differs"):
                A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")
            self.assertFalse((self.project/"assets/imported").exists())
        data=json.loads(json.dumps(original))
        data.pop("requestSha256")
        data["assets"][0]["generation"]={"requestSha256":"synthetic-request"}
        P.write(report,data)
        P.write(state_file,{**state,"approval":{"requestSha256":"synthetic-request"}})
        asset=A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")["asset"]
        self.assertEqual(asset["provenance"]["approvalRequestSha256"],"synthetic-request")

    def test_unbound_sibling_state_does_not_attribute_provider_or_approval(self):
        report=self.generated()
        data=P.read(report)
        data.pop("requestSha256")
        P.write(report,data)
        asset=A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")["asset"]
        self.assertNotIn("model",asset["provenance"])
        self.assertNotIn("requestSha256",asset["provenance"])
        self.assertNotIn("approvalRequestSha256",asset["provenance"])

    def test_provider_hash_dimensions_and_path_mismatches_are_rejected(self):
        report=self.generated()
        original=P.read(report)
        for updates in ({"sha256":"wrong"},{"width":100},{"path":"../source.png"}):
            data=json.loads(json.dumps(original))
            data["assets"][0].update(updates)
            P.write(report,data)
            with self.assertRaises(ValueError):
                A.imported(self.project,self.image,"hero",provider_manifest=report,generated_id="demo")
            self.assertFalse((self.project/"assets/imported").exists())

    def test_symlink_output_parent_is_refused(self):
        outside=self.base/"outside"
        outside.mkdir()
        (self.project/"assets/imported").symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):
            A.imported(self.project,self.image,"hero")
        self.assertFalse(list(outside.iterdir()))

    def test_custom_html_and_threejs_resources_share_project_contract(self):
        resource=self.base/"model.glb"
        resource.write_bytes(b"synthetic model fixture, not renderable")
        model=A.imported(self.project,resource,"model",kind="resource")["asset"]
        component=self.base/"component.html"
        component.write_text("<div>Fixture component</div>")
        html=A.imported(self.project,component,"component",kind="resource")["asset"]
        project=P.read(self.project/"project.json")
        project["generator"]="build.mjs"
        P.write(self.project/"project.json",project)
        (self.project/"build.mjs").write_text("// Fixture contract only; no Three.js render asserted\n")
        board=P.read(self.project/"storyboard.json")
        board["beats"][0]["visual"]={"mode":"custom:three-d","asset":"model"}
        board["beats"][1]["visual"]={"mode":"custom:html-component","asset":"component"}
        P.write(self.project/"storyboard.json",board)
        P.resolve(self.project)
        hashes=P.input_hashes(self.project)
        self.assertIn(model["path"],hashes)
        self.assertIn(html["path"],hashes)
        self.assertIn("build.mjs",hashes)

    @unittest.skipUnless(shutil.which("ffprobe"),"FFprobe required")
    def test_audio_import_records_measured_duration_and_mix_policy(self):
        audio=self.base/"music.wav"
        with wave.open(str(audio),"wb") as wav:
            wav.setparams((1,2,8000,0,"NONE","not compressed"))
            wav.writeframes(b"\x00\x00"*8000)
        asset=A.imported(self.project,audio,"music",audio_policy="mix")["asset"]
        self.assertEqual(asset["kind"],"audio")
        self.assertEqual(asset["duration"],1)
        self.assertEqual(asset["audioPolicy"],"mix")

    def clip(self,audio=False):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg/FFprobe required")
        clip=self.base/("audible.mp4" if audio else "clip.mp4")
        command=["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=160x90:r=24"]
        if audio:
            command += ["-f","lavfi","-i","sine=frequency=440:sample_rate=44100","-c:a","aac"]
        command += ["-t","4","-c:v","libx264","-pix_fmt","yuv420p",str(clip)]
        subprocess.run(command,check=True,capture_output=True)
        return clip

    def test_images_footage_and_overlays_compose_in_all_four_ratios(self):
        A.imported(self.project,self.image,"hero")
        asset=A.imported(self.project,self.clip(),"clip",audio_policy="mute")["asset"]
        board=P.read(self.project/"storyboard.json")
        board["beats"][0]["visual"]={"mode":"image","asset":"hero"}
        board["beats"][1]["visual"]={"mode":"footage","asset":"clip","sourceStart":.2,"hasAudio":False,"text":"Overlay"}
        P.write(self.project/"storyboard.json",board)
        P.resolve(self.project)
        result=subprocess.run(["node",str(SKILLS/"motion-composer/scripts/compose.mjs"),str(self.project)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        report=Q.check(self.project)
        self.assertEqual(len(report["variants"]),4)
        self.assertTrue(any("review pending" in w for w in report["warnings"]))
        for variant in P.read(self.project/"project.json")["variants"]:
            path=self.project/"variants"/variant["id"]
            self.assertTrue((path/asset["path"]).is_file())
            page=(path/"index.html").read_text()
            self.assertIn("data-media-start=\"0.2\"",page)
            self.assertIn("muted",page)
        A.imported(self.project,self.image,"another")
        with self.assertRaisesRegex(ValueError,"Stale resolved timing"):
            Q.check(self.project)

    def test_measured_audio_policy_must_match_footage_wiring(self):
        A.imported(self.project,self.clip(audio=True),"audible",audio_policy="retain")
        board=P.read(self.project/"storyboard.json")
        board["beats"][0]["visual"]={"mode":"footage","asset":"audible","hasAudio":False}
        P.write(self.project/"storyboard.json",board)
        with self.assertRaisesRegex(ValueError,"Retained/mixed"):
            P.resolve(self.project)
        board["beats"][0]["visual"]["hasAudio"]=True
        P.write(self.project/"storyboard.json",board)
        P.resolve(self.project)
        manifest=P.read(self.project/"assets/manifest.json")
        manifest["assets"][0]["audioPolicy"]="mute"
        P.write(self.project/"assets/manifest.json",manifest)
        with self.assertRaisesRegex(ValueError,"muted asset"):
            P.resolve(self.project)


if __name__=="__main__":
    unittest.main()
