#!/usr/bin/env python3
# 2DoArchive - Archive.org downloader
# Create By RXx8
# Compatible with Termux, Windows, Linux and macOS.
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

APP_NAME = "2DoArchive"
VERSION = "1.0.0"
DEFAULT_DIR = Path.home() / "Carpeta Descargas Archive-ORG"
CONFIG_DIR = Path.home() / ".2doarchive"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

UA = f"2DoArchive/{VERSION} (+https://archive.org/)"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nPresiona ENTER para continuar...")

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            p = data.get("download_dir")
            if p:
                return Path(p).expanduser()
        except Exception:
            pass
    return DEFAULT_DIR

def save_config(path: Path):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({"download_dir": str(path)}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def add_history(url, files):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    history = load_history()
    history.insert(0, {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "files": files,
    })
    HISTORY_FILE.write_text(
        json.dumps(history[:100], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def logo():
    print(r"""
████     █   █     ███    
█░░░█     █ █ ░   █ ░░█   
████░░     █ ░ ░   ███░░  
█░░█░ ░   █ █ ░   █ ░░█ ░ 
█░░░█░   █ ░ █     ███░░  
 ░░  ░    ░ ░ ░     ░░░ ░ 
  ░   ░    ░   ░     ░░░                                                
 ▗▖         ▐    ▝                              
 ▐▌  ▖▄  ▄▖ ▐▗▖ ▗▄  ▗ ▗  ▄▖          ▄▖  ▖▄  ▄▄ 
 ▌▐  ▛ ▘▐▘▝ ▐▘▐  ▐  ▝▖▞ ▐▘▐         ▐▘▜  ▛ ▘▐▘▜ 
 ▙▟  ▌  ▐   ▐ ▐  ▐   ▙▌ ▐▀▀         ▐ ▐  ▌  ▐ ▐ 
▐  ▌ ▌  ▝▙▞ ▐ ▐ ▗▟▄  ▐  ▝▙▞  ▐      ▝▙▛  ▌  ▝▙▜ 
                                             ▖▐ 
                                             ▝▘ 
""")
    print("                         Create By RXx8")
    print(f"                         v{VERSION}")
    print()

def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def extract_identifier(url):
    u = urllib.parse.urlparse(url.strip())
    host = u.netloc.lower()
    if host not in {"archive.org", "www.archive.org"}:
        return None
    parts = [p for p in u.path.split("/") if p]
    # /details/IDENTIFIER or /download/IDENTIFIER[/FILE]
    if len(parts) >= 2 and parts[0] in ("details", "download"):
        return urllib.parse.unquote(parts[1])
    return None

def safe_name(name):
    # Keep subdirectories returned by Archive.org, but block traversal.
    name = name.replace("\\", "/").lstrip("/")
    parts = [p for p in name.split("/") if p not in ("", ".", "..")]
    return "/".join(parts) or "archivo"

def human_size(n):
    try:
        n = float(n)
    except Exception:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.1f} {unit}"
        n /= 1024
    return "?"

def archive_metadata(identifier):
    url = "https://archive.org/metadata/" + urllib.parse.quote(identifier, safe="")
    return request_json(url)

def choose_files(meta):
    raw = meta.get("files") or []
    entries = []
    for f in raw:
        name = f.get("name")
        if not name:
            continue
        fmt = str(f.get("format", ""))
        # Archive.org metadata contains XML/JSON/checksum/admin files.
        # They are shown, but the default selection favors normal downloadable files.
        size = f.get("size", "")
        entries.append({
            "name": name,
            "format": fmt,
            "size": size,
            "source": f
        })
    entries.sort(key=lambda x: x["name"].lower())
    return entries

def print_files(entries):
    for i, f in enumerate(entries, 1):
        print(f"  [{i:3}] {f['name']}  ({human_size(f['size'])})")

def select_files(entries):
    print("\nArchivos encontrados:")
    print_files(entries)
    print("\nEscribe:")
    print("  A  = descargar todos")
    print("  1,3,5 = seleccionar archivos")
    print("  espacio doble (dos espacios) = volver")
    while True:
        ans = input("\nSelección: ")
        if ans == "  ":
            return []
        if ans.strip().lower() == "a":
            return entries
        nums = []
        ok = True
        for part in ans.split(","):
            part = part.strip()
            if not part.isdigit():
                ok = False
                break
            n = int(part)
            if n < 1 or n > len(entries):
                ok = False
                break
            nums.append(n)
        if ok and nums:
            return [entries[n-1] for n in dict.fromkeys(nums)]
        print("Selección no válida.")

def download_file(url, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    existing = temp.stat().st_size if temp.exists() else 0
    if existing:
        req.add_header("Range", f"bytes={existing}-")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status = getattr(r, "status", 200)
            # If server ignores Range, restart instead of corrupting the file.
            if existing and status != 206:
                existing = 0
                temp.unlink(missing_ok=True)
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                r.close()
                with urllib.request.urlopen(req, timeout=60) as r2:
                    return stream_copy(r2, temp, destination, 0)
            return stream_copy(r, temp, destination, existing)
    except urllib.error.HTTPError as e:
        if existing and e.code == 416:
            temp.unlink(missing_ok=True)
            return download_file(url, destination)
        raise

def stream_copy(response, temp, destination, existing):
    total = response.headers.get("Content-Length")
    total = int(total) + existing if total and total.isdigit() else None
    done = existing
    mode = "ab" if existing else "wb"
    started = time.time()
    with open(temp, mode) as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            elapsed = max(time.time() - started, 0.01)
            speed = done / elapsed
            if total:
                pct = done * 100 / total
                msg = f"\r  {pct:6.2f}% | {human_size(done)}/{human_size(total)} | {human_size(speed)}/s"
            else:
                msg = f"\r  {human_size(done)} | {human_size(speed)}/s"
            print(msg, end="", flush=True)
    print()
    temp.replace(destination)
    return True

def download_item(url, download_dir):
    identifier = extract_identifier(url)
    if not identifier:
        # Permit a direct archive.org/download/... file URL.
        u = urllib.parse.urlparse(url)
        if u.netloc.lower() in {"archive.org", "www.archive.org"} and u.path.startswith("/download/"):
            name = Path(urllib.parse.unquote(u.path)).name or "archivo"
            target = download_dir / safe_name(name)
            print(f"\nDescargando: {name}")
            download_file(url, target)
            print(f"Guardado en: {target}")
            add_history(url, [name])
            return
        print("No reconocí un enlace válido de Archive.org.")
        print("Ejemplo: https://archive.org/details/IDENTIFIER")
        return

    print(f"\nConsultando Archive.org: {identifier}")
    try:
        meta = archive_metadata(identifier)
    except Exception as e:
        print(f"Error consultando Archive.org: {e}")
        return

    if meta.get("is_dark"):
        print("Este elemento no está disponible públicamente.")
        return

    entries = choose_files(meta)
    if not entries:
        print("No se encontraron archivos descargables.")
        return

    selected = select_files(entries)
    if not selected:
        return

    download_dir.mkdir(parents=True, exist_ok=True)
    completed = []
    print(f"\nDestino: {download_dir}\n")
    for f in selected:
        name = safe_name(f["name"])
        target = download_dir / name
        # Archive.org supports /download/IDENTIFIER/FILENAME.
        encoded = "/".join(urllib.parse.quote(p, safe="") for p in name.split("/"))
        dl = f"https://archive.org/download/{urllib.parse.quote(identifier, safe='')}/{encoded}"
        try:
            print(f"→ {name}")
            download_file(dl, target)
            completed.append(name)
            print(f"✓ Guardado: {target}\n")
        except Exception as e:
            print(f"\n✗ Error en {name}: {e}\n")
    if completed:
        add_history(url, completed)
        print(f"Completados: {len(completed)}/{len(selected)}")

def change_directory(current):
    print("\nCARPETA DE DESCARGAS")
    print(f"Actual: {current}")
    print("\n1. Usar una ruta existente")
    print("2. Crear/usar una ruta nueva")
    print("  Espacio doble = cancelar")
    ans = input("\nOpción: ")
    if ans == "  ":
        return current
    if ans not in ("1", "2"):
        print("Opción no válida.")
        return current
    raw = input("Escribe la ruta: ").strip()
    if raw == "  " or not raw:
        return current
    p = Path(os.path.expandvars(os.path.expanduser(raw))).resolve()
    try:
        p.mkdir(parents=True, exist_ok=True)
        save_config(p)
        print(f"✓ Carpeta configurada: {p}")
        return p
    except Exception as e:
        print(f"✗ No se pudo crear la carpeta: {e}")
        return current

def show_history():
    history = load_history()
    print("\nHISTORIAL")
    if not history:
        print("No hay descargas registradas.")
        return
    for item in history[:20]:
        print(f"\n[{item.get('date','')}]")
        print(item.get("url", ""))
        for f in item.get("files", []):
            print(f"  • {f}")

def menu():
    download_dir = load_config()
    download_dir.mkdir(parents=True, exist_ok=True)
    while True:
        clear()
        logo()
        print(f"Carpeta actual: {download_dir}\n")
        print("╔════════════════════════════════════════════╗")
        print("║              MENÚ PRINCIPAL               ║")
        print("╠════════════════════════════════════════════╣")
        print("║  [1] Descargar desde Archive.org         ║")
        print("║  [2] Carpeta Descargas Archive-ORG       ║")
        print("║  [3] Historial de descargas               ║")
        print("║  [4] Información / ayuda                  ║")
        print("║  [0] Salir                                 ║")
        print("╚════════════════════════════════════════════╝")
        print("\nEscribe un número. Dos espacios = salir de una sección.")
        choice = input("\n2DoArchive > ")
        if choice == "  " or choice == "0":
            print("\nSaliendo de 2DoArchive...")
            break
        if choice == "1":
            clear(); logo()
            url = input("Pega el enlace de Archive.org: ").strip()
            if url == "  ":
                continue
            download_item(url, download_dir)
            pause()
        elif choice == "2":
            clear(); logo()
            download_dir = change_directory(download_dir)
            pause()
        elif choice == "3":
            clear(); logo()
            show_history()
            pause()
        elif choice == "4":
            clear(); logo()
            print("2DoArchive descarga archivos públicos de Archive.org.")
            print("\nAcepta enlaces como:")
            print("  https://archive.org/details/IDENTIFIER")
            print("  https://archive.org/download/IDENTIFIER/archivo.ext")
            print("\nFunciones:")
            print("  • Selección individual o todos los archivos")
            print("  • Reanudación básica mediante .part cuando el servidor lo permite")
            print("  • Carpeta configurable")
            print("  • Historial local")
            print("  • Sin dependencias externas")
            print("\nUse el programa únicamente para contenido que tenga derecho a descargar.")
            pause()
        else:
            print("Opción no válida.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\nSalida solicitada.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        if os.environ.get("2DOARCHIVE_DEBUG"):
            raise
