"""Build portable student apps and unpacked extensions; does not publish anything.

Run from a valid project workspace after installing each site's dependencies.
The same compiled interface is used by the local app and extension workspace.
"""

from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("thread",)

LAUNCHER = '''from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
parser = argparse.ArgumentParser(description="Run the local student app")
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
try:
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parent / "app")))
except OSError as error:
    parser.exit(1, f"Could not start: {error}\\nTry --port 8001.\\n")
print(f"Open http://127.0.0.1:{server.server_port} — Ctrl+C to stop", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
'''


def archive(folder, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                output.write(file, folder.name + "/" + str(file.relative_to(folder)))


def main():
    for name in NAMES:
        site = ROOT
        subprocess.run(["node", "--test", "engine/test.mjs"], cwd=site, check=True)
        subprocess.run([
            "node", "node_modules/vite/bin/vite.js", "build",
            "--config", "standalone/vite.config.mjs",
        ], cwd=site, check=True)
        built = site / "portable-dist"
        if not (built / "index.html").is_file():
            raise RuntimeError(f"{name}: no built entry point")

        manifest = {
            "name": name.title(), "short_name": name.title(),
            "start_url": "/", "display": "standalone",
            "background_color": "#f5f0e5", "theme_color": "#2247ac",
            "icons": [{"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml"}],
        }
        (site / "public/manifest.webmanifest").write_text(json.dumps(manifest, indent=2))
        shutil.copy2(site / "public/manifest.webmanifest", built / "manifest.webmanifest")
        shutil.copy2(site / "public/icon.svg", built / "icon.svg")
        assets = ["/", "/icon.svg", "/manifest.webmanifest"] + [
            "/" + str(file.relative_to(built))
            for file in (built / "assets").rglob("*") if file.is_file()
        ]
        worker = (
            "const CACHE=" + json.dumps(name + "-portable-v1") + ";"
            "self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE)"
            ".then(c=>c.addAll(" + json.dumps(assets) + ")).then(()=>self.skipWaiting())));"
            "self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));"
            "self.addEventListener('fetch',e=>{if(e.request.method!=='GET'||"
            "new URL(e.request.url).origin!==self.location.origin)return;"
            "e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();"
            "caches.open(CACHE).then(c=>c.put(e.request,copy));}return r;})"
            ".catch(()=>caches.match(e.request).then(r=>r||"
            "(e.request.mode==='navigate'?caches.match('/'):Response.error()))));});"
        )
        (built / "sw.js").write_text(worker)
        # Hosted builds have different asset names. Cache the page and runtime
        # requests without trying to precache nonexistent portable asset paths.
        hosted_worker = worker.replace(json.dumps(assets), json.dumps(["/", "/icon.svg", "/manifest.webmanifest"]))
        (site / "public/sw.js").write_text(hosted_worker)

        output = site / "public/downloads"
        output.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=name + "-package-") as temp:
            stage = Path(temp)
            local = stage / (name + "-local")
            local.mkdir()
            shutil.copytree(built, local / "app")
            (local / "serve.py").write_text(LAUNCHER)
            (local / "START-HERE.md").write_text(
                "# " + name.title() + " locally\n\n"
                "Extract all files. Install Python 3.10+ if needed. Open a terminal "
                "in this folder and run `python3 serve.py` (Windows: `py -3 serve.py`). "
                "Open http://127.0.0.1:8000. Keep the terminal open; Ctrl+C stops it. "
                "Use --port 8001 if port 8000 is busy. No Node installation is needed "
                "for this prebuilt download. Export backups before clearing browser storage.\n"
            )
            extension = stage / (name + "-extension")
            shutil.copytree(site / "extension", extension)
            shutil.copytree(built, extension / "workspace")
            # Extension workspaces use their own storage and cannot register
            # a website service worker or fetch remote resources.
            (extension / "workspace/sw.js").unlink(missing_ok=True)
            (extension / "workspace/manifest.webmanifest").unlink(missing_ok=True)
            html = (extension / "workspace/index.html").read_text()
            html = html.replace('<link rel="manifest" href="./manifest.webmanifest">', "")
            (extension / "workspace/index.html").write_text(html)

            for folder in (local, extension):
                notices = folder / "third-party-licenses"
                notices.mkdir()
                for dependency in ("react", "react-dom", "scheduler"):
                    shutil.copy2(site / "node_modules" / dependency / "LICENSE", notices / (dependency + ".txt"))
                license_file = site / "LICENSE"
                if license_file.exists():
                    shutil.copy2(license_file, folder / "LICENSE")
                archive(folder, output / (folder.name + ".zip"))
            shutil.copy2(local / "START-HERE.md", output / "START-HERE.md")
            shutil.copy2(extension / "INSTALL.md", output / "INSTALL-EXTENSION.md")
        sums = []
        for suffix in ("local", "extension"):
            file = output / (name + "-" + suffix + ".zip")
            sums.append(hashlib.sha256(file.read_bytes()).hexdigest() + "  " + file.name)
        (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
        print(name + ": local app and unpacked extension packaged")


if __name__ == "__main__":
    main()
