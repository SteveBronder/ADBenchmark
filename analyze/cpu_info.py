#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sys_bench_report.py — Human-readable system profile for benchmarking on Linux.

Features (best effort, degrades gracefully):
- CPU: model, sockets/cores/threads, SMT, base/max freq, governor, boost state
- Caches (L1d/i, L2, L3), SIMD flags (AVX2/AVX-512, etc.)
- NUMA topology (nodes and CPU lists)
- Memory: total/available/swap, hugepages; DIMM speed via dmidecode if root
- GPU: NVIDIA via nvidia-smi; AMD via rocm-smi; OpenGL renderer via glxinfo -B
- Storage: physical devices (SSD/HDD), size, model (lsblk)
- OS/Kernel: distro, kernel, arch
- Extras: cpufreq driver, scaling info
"""

import json
import os
import re
import shutil
import subprocess
import sys
import platform
from collections import defaultdict

USE_COLOR_DEFAULT = sys.stdout.isatty()
IS_DARWIN = platform.system() == "Darwin"

def which(cmd): return shutil.which(cmd)

def run(cmd):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def human_bytes(n):
    try:
        n = float(n)
    except Exception:
        return str(n)
    units = ["B","KiB","MiB","GiB","TiB","PiB"]
    i = 0
    while n >= 1024 and i < len(units)-1:
        n /= 1024.0
        i += 1
    return f"{n:.1f} {units[i]}"

def mhz_to_ghz(mhz):
    try:
        ghz = float(mhz)/1000.0
        return f"{ghz:.2f} GHz"
    except Exception:
        return None

def colorize(s, color=None, bold=False, use_color=USE_COLOR_DEFAULT):
    if not use_color: return s
    codes = []
    if bold: codes.append("1")
    ctab = dict(grey="90", red="31", green="32", yellow="33", blue="34", magenta="35", cyan="36", white="37")
    if color: codes.append(ctab.get(color, "0"))
    if not codes: return s
    return f"\x1b[{';'.join(codes)}m{s}\x1b[0m"

def parse_os_release():
    if IS_DARWIN:
        d = {}
        txt = run(["sw_vers"])
        for line in txt.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                d[k.strip()] = v.strip()
        return {
            "distro": d.get("ProductName") or "macOS",
            "id": "macos",
            "version": d.get("ProductVersion"),
        }
    d = {}
    txt = read_text("/etc/os-release")
    for line in txt.splitlines():
        if "=" in line:
            k,v = line.split("=",1)
            d[k] = v.strip().strip('"')
    return {
        "distro": d.get("PRETTY_NAME") or d.get("NAME"),
        "id": d.get("ID"),
        "version": d.get("VERSION"),
    }

def uname_info():
    u = os.uname()
    return {
        "kernel": f"{u.sysname} {u.release}",
        "kernel_release": u.release,
        "kernel_version": u.version,
        "machine": u.machine,
        "nodename": u.nodename,
    }

def parse_lscpu():
    if IS_DARWIN:
        info = {}
        info["Architecture"] = run(["uname", "-m"])
        logical = run(["sysctl", "-n", "hw.logicalcpu"])
        physical = run(["sysctl", "-n", "hw.physicalcpu"])
        sockets = run(["sysctl", "-n", "hw.packages"])
        if sockets.isdigit():
            info["Socket(s)"] = sockets
        if physical.isdigit() and sockets.isdigit() and int(sockets):
            info["Core(s) per socket"] = str(int(physical)//int(sockets))
        if logical.isdigit() and physical.isdigit() and int(physical):
            info["Thread(s) per core"] = str(int(logical)//int(physical))
        if logical:
            info["CPU(s)"] = logical
        model = run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if model:
            info["Model name"] = model

        # Apple Silicon exposes separate performance and efficiency levels
        perf = run(["sysctl", "-n", "hw.perflevel0.physicalcpu"])
        eff = run(["sysctl", "-n", "hw.perflevel1.physicalcpu"])
        if perf.isdigit():
            info["Performance cores"] = perf
        if eff.isdigit():
            info["Efficiency cores"] = eff

        def pl_cache(key):
            p = run(["sysctl", "-n", f"hw.perflevel0.{key}"])
            e = run(["sysctl", "-n", f"hw.perflevel1.{key}"])
            parts = []
            if p.isdigit():
                parts.append(f"P {human_bytes(int(p))}")
            if e.isdigit():
                parts.append(f"E {human_bytes(int(e))}")
            if parts:
                return ", ".join(parts)
            base = run(["sysctl", "-n", f"hw.{key}"])
            if base.isdigit():
                return human_bytes(int(base))
            return None

        l1d = pl_cache("l1dcachesize")
        l1i = pl_cache("l1icachesize")
        l2 = pl_cache("l2cachesize")
        l3 = pl_cache("l3cachesize")
        if l1d: info["L1d cache"] = l1d
        if l1i: info["L1i cache"] = l1i
        if l2:  info["L2 cache"] = l2
        if l3:  info["L3 cache"] = l3

        freq = run(["sysctl", "-n", "hw.cpufrequency"])
        maxf = run(["sysctl", "-n", "hw.cpufrequency_max"])
        if freq.isdigit(): info["CPU MHz"] = f"{int(freq)//1000000}"
        if maxf.isdigit(): info["CPU max MHz"] = f"{int(maxf)//1000000}"
        flags = (run(["sysctl", "-n", "machdep.cpu.features"]) + " " +
                 run(["sysctl", "-n", "machdep.cpu.leaf7_features"]))
        flags = flags.strip()
        if flags:
            info["Flags"] = flags
        return {k:v for k,v in info.items() if v}
    info = {}
    txt = run(["lscpu"])
    for line in txt.splitlines():
        if ":" in line:
            k,v = [x.strip() for x in line.split(":",1)]
            info[k] = v
    return info

def proc_cpuinfo():
    if IS_DARWIN:
        model = run(["sysctl", "-n", "machdep.cpu.brand_string"])
        features = run(["sysctl", "-n", "machdep.cpu.features"])
        features += " " + run(["sysctl", "-n", "machdep.cpu.leaf7_features"])
        flags = features.split()
        sockets = run(["sysctl", "-n", "hw.packages"])
        physical = run(["sysctl", "-n", "hw.physicalcpu"])
        sockets_int = int(sockets) if sockets.isdigit() else None
        phys_int = int(physical) if physical.isdigit() else None
        cores_per_socket = None
        if sockets_int and phys_int:
            cores_per_socket = phys_int // sockets_int if sockets_int else None
        return {
            "model_name": model or None,
            "flags": sorted(flags) if flags else [],
            "sockets": sockets_int,
            "cores_per_socket": cores_per_socket,
        }
    txt = read_text("/proc/cpuinfo")
    sockets = {}
    flags_set = set()
    model_name = None
    for block in txt.split("\n\n"):
        if not block.strip(): continue
        d = {}
        for line in block.splitlines():
            if ":" in line:
                k,v = [x.strip() for x in line.split(":",1)]
                d[k] = v
        if not model_name and "model name" in d:
            model_name = d["model name"]
        if "flags" in d:
            flags_set.update(d["flags"].split())
        phys_id = d.get("physical id", "0")
        core_id = d.get("core id", "NA")
        sockets.setdefault(phys_id, set()).add(core_id)
    return {
        "model_name": model_name,
        "flags": sorted(list(flags_set)),
        "sockets": len(sockets) if sockets else None,
        "cores_per_socket": max((len(v) for v in sockets.values()), default=None) if sockets else None,
    }

def cpufreq_info():
    if IS_DARWIN:
        base = run(["sysctl", "-n", "hw.cpufrequency"])
        maxf = run(["sysctl", "-n", "hw.cpufrequency_max"])
        return {
            "base_freq_mhz": f"{int(base)//1000000}" if base.isdigit() else None,
            "max_freq_mhz": f"{int(maxf)//1000000}" if maxf.isdigit() else None,
            "governor": None,
            "driver": None,
            "boost": None,
        }
    # Aggregate from /sys
    base_mhz = None
    max_mhz = None
    governor = None
    driver = read_text("/sys/devices/system/cpu/cpufreq/policy0/scaling_driver") or read_text("/sys/devices/system/cpu/cpufreq/driver")
    gov = read_text("/sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
    if gov: governor = gov
    max_khz = read_text("/sys/devices/system/cpu/cpufreq/policy0/cpuinfo_max_freq")
    base_khz = read_text("/sys/devices/system/cpu/cpufreq/policy0/base_frequency")  # intel only
    if not base_khz:
        # Try "cpu MHz" average across cores
        mhz_vals = []
        txt = read_text("/proc/cpuinfo")
        for line in txt.splitlines():
            if line.lower().startswith("cpu mhz"):
                try:
                    mhz_vals.append(float(line.split(":")[1]))
                except Exception:
                    pass
        if mhz_vals:
            base_mhz = f"{sum(mhz_vals)/len(mhz_vals):.0f}"  # current avg, not true base
    if base_khz:
        try: base_mhz = f"{float(base_khz)/1000.0:.0f}"
        except Exception: pass
    if max_khz:
        try: max_mhz = f"{float(max_khz)/1000.0:.0f}"
        except Exception: pass

    # Boost state (AMD/Intel, best effort)
    boost = None
    # Generic cpufreq boost
    p = "/sys/devices/system/cpu/cpufreq/boost"
    if os.path.exists(p):
        v = read_text(p)
        if v in ("0","1"): boost = "enabled" if v=="1" else "disabled"
    # Intel pstate no_turbo (0 means turbo enabled)
    p2 = "/sys/devices/system/cpu/intel_pstate/no_turbo"
    if os.path.exists(p2):
        nv = read_text(p2)
        if nv in ("0","1"):
            boost = "enabled" if nv=="0" else "disabled"
    return {
        "base_freq_mhz": base_mhz,
        "max_freq_mhz": max_mhz,
        "governor": governor,
        "driver": driver.strip() if driver else None,
        "boost": boost,
    }

def cache_info():
    if IS_DARWIN:
        caches = []
        for pl in (0, 1):
            name = run(["sysctl", "-n", f"hw.perflevel{pl}.name"])
            prefix = f"hw.perflevel{pl}"
            l1d = run(["sysctl", "-n", f"{prefix}.l1dcachesize"])
            l1i = run(["sysctl", "-n", f"{prefix}.l1icachesize"])
            l2 = run(["sysctl", "-n", f"{prefix}.l2cachesize"])
            tag = name or f"perflevel{pl}"
            if l1d.isdigit():
                caches.append({"level": "1", "type": f"{tag} Data",
                               "size": human_bytes(int(l1d)), "associativity": None})
            if l1i.isdigit():
                caches.append({"level": "1", "type": f"{tag} Instruction",
                               "size": human_bytes(int(l1i)), "associativity": None})
            if l2.isdigit():
                caches.append({"level": "2", "type": f"{tag} Unified",
                               "size": human_bytes(int(l2)), "associativity": None})
        l3 = run(["sysctl", "-n", "hw.l3cachesize"])
        if l3.isdigit():
            caches.append({"level": "3", "type": "Unified",
                           "size": human_bytes(int(l3)), "associativity": None})
        return caches
    # Inspect cpu0 cache levels
    base = "/sys/devices/system/cpu/cpu0/cache"
    caches = []
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            p = os.path.join(base, entry)
            if not os.path.isdir(p): continue
            level = read_text(os.path.join(p,"level"))
            ctype = read_text(os.path.join(p,"type"))
            size = read_text(os.path.join(p,"size"))
            ways = read_text(os.path.join(p,"ways_of_associativity"))
            if level and size:
                caches.append({"level": level, "type": ctype, "size": size, "associativity": ways})
    return caches

def numa_info():
    if IS_DARWIN:
        return []
    nodes = []
    nb = "/sys/devices/system/node"
    if not os.path.isdir(nb): return nodes
    for dn in sorted(os.listdir(nb)):
        if not dn.startswith("node"): continue
        node_id = dn[4:]
        cpulist = read_text(os.path.join(nb, dn, "cpulist"))
        mem_kB = read_text(os.path.join(nb, dn, "meminfo"))
        mem_total_kB = None
        if mem_kB:
            m = re.search(r"MemTotal:\s+(\d+)\s+kB", mem_kB)
            if m: mem_total_kB = int(m.group(1))
        nodes.append({"node": int(node_id), "cpulist": cpulist, "mem_total": human_bytes(mem_total_kB*1024) if mem_total_kB else None})
    return nodes

def mem_info():
    if IS_DARWIN:
        data = {}
        total = run(["sysctl", "-n", "hw.memsize"])
        if total.isdigit():
            data["total"] = int(total)
        vm = run(["vm_stat"])
        page_size = 4096
        m = re.search(r"page size of (\d+) bytes", vm)
        if m:
            page_size = int(m.group(1))
        free = inactive = 0
        for line in vm.splitlines():
            m = re.match(r"Pages\s+free:\s+(\d+)", line)
            if m: free = int(m.group(1))
            m = re.match(r"Pages\s+inactive:\s+(\d+)", line)
            if m: inactive = int(m.group(1))
        data["available"] = (free + inactive) * page_size if (free or inactive) else None
        swap = run(["sysctl", "-n", "vm.swapusage"])
        m = re.search(r"total = ([0-9.]+)M\s+used = ([0-9.]+)M\s+free = ([0-9.]+)M", swap)
        if m:
            data["swap_total"] = int(float(m.group(1)) * 1024 * 1024)
            data["swap_free"] = int(float(m.group(3)) * 1024 * 1024)
        data["hugepages_total"] = None
        data["hugepage_size"] = None
        return data
    data = {}
    txt = read_text("/proc/meminfo")
    for line in txt.splitlines():
        if ":" in line:
            k,v = line.split(":",1)
            data[k.strip()] = v.strip()
    def get_bytes(key):
        v = data.get(key)
        if not v: return None
        # Usually "NNN kB"
        m = re.match(r"(\d+)\s*kB", v)
        return int(m.group(1))*1024 if m else None
    huge_total = data.get("HugePages_Total")
    huge_size_kB = data.get("Hugepagesize")
    def parse_huge(s):
        m = re.match(r"(\d+)\s*kB", s) if s else None
        return int(m.group(1))*1024 if m else None

    return {
        "total": get_bytes("MemTotal"),
        "available": get_bytes("MemAvailable"),
        "free": get_bytes("MemFree"),
        "swap_total": get_bytes("SwapTotal"),
        "swap_free": get_bytes("SwapFree"),
        "hugepages_total": int(huge_total) if huge_total and huge_total.isdigit() else None,
        "hugepage_size": parse_huge(huge_size_kB),
    }

def dmidecode_memory():
    # Requires root; returns list of speed strings per DIMM
    if not which("dmidecode"): return []
    txt = run(["dmidecode","-t","memory"])
    speeds = []
    cur = {}
    for line in txt.splitlines():
        if not line.strip():
            if cur:
                if "Configured Memory Speed" in cur and cur.get("Size","") != "No Module Installed":
                    speeds.append(cur["Configured Memory Speed"])
                elif "Speed" in cur and cur.get("Size","") != "No Module Installed":
                    speeds.append(cur["Speed"])
                cur = {}
            continue
        if ":" in line:
            k,v = [x.strip() for x in line.split(":",1)]
            cur[k] = v
    if cur:
        if "Configured Memory Speed" in cur and cur.get("Size","") != "No Module Installed":
            speeds.append(cur["Configured Memory Speed"])
        elif "Speed" in cur and cur.get("Size","") != "No Module Installed":
            speeds.append(cur["Speed"])
    # Normalize "NNNN MT/s" or "Unknown"
    return [s for s in speeds if s]

def gpu_info():
    if IS_DARWIN:
        out = run(["system_profiler", "SPDisplaysDataType"])
        gpus = []
        current = {}
        for line in out.splitlines():
            line = line.rstrip()
            if not line:
                continue
            stripped = line.strip()
            if not line.startswith(" ") and line.endswith(":") and current:
                gpus.append(current)
                current = {}
            if ":" in stripped:
                k, v = stripped.split(":", 1)
                current[k.strip()] = v.strip()
        if current:
            gpus.append(current)
        result = []
        for g in gpus:
            name = g.get("Chipset Model")
            vram = g.get("VRAM (Total)") or g.get("VRAM")
            if name or vram:
                result.append({"vendor": "Apple", "name": name, "vram": vram})
        return result
    gpus = []
    if which("nvidia-smi"):
        q = run(["nvidia-smi","--query-gpu=name,driver_version,memory.total,pstate,clocks.gr,clocks.mem","--format=csv,noheader"])
        for line in q.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpus.append({
                    "vendor": "NVIDIA",
                    "name": parts[0],
                    "driver": parts[1],
                    "vram": parts[2] + " MiB",
                    "pstate": parts[3],
                    "clock_graphics": parts[4] + " MHz" if parts[4].isdigit() else parts[4],
                })
    elif which("rocm-smi"):
        q = run(["rocm-smi","--showproductname","--showdriverversion","--showvbios"])
        if q:
            gpus.append({"vendor":"AMD","raw": q})
    elif which("glxinfo"):
        # generic renderer
        b = run(["glxinfo","-B"])
        name = None
        for line in b.splitlines():
            if "OpenGL renderer string" in line:
                name = line.split(":",1)[1].strip()
        if name:
            gpus.append({"vendor":"OpenGL","name": name})
    return gpus

def storage_info():
    devs = []
    if which("lsblk"):
        # -d: no partitions ; -e7 exclude loop; -o fields
        out = run(["lsblk","-d","-e7","-o","NAME,TYPE,ROTA,SIZE,MODEL,SERIAL,STATE"])
        for i, line in enumerate(out.splitlines()):
            if i==0: continue
            parts = line.split()
            if not parts: continue
            # Reconstruct MODEL (may contain spaces) by aligning from right
            # Columns: NAME TYPE ROTA SIZE MODEL... SERIAL STATE
            # We’ll parse ROTA, SIZE from known positions and join the middle for MODEL.
            name = parts[0]
            dtype = parts[1] if len(parts)>1 else ""
            rota = parts[2] if len(parts)>2 else ""
            size = parts[3] if len(parts)>3 else ""
            # MODEL could be multiple tokens; SERIAL and STATE likely last 1-2 tokens
            serial = state = ""
            model_tokens = []
            if len(parts) >= 6:
                # Heuristic: STATE often last; SERIAL usually before STATE; both single tokens
                state = parts[-1]
                serial = parts[-2]
                model_tokens = parts[4:-2]
            elif len(parts) == 5:
                model_tokens = [parts[4]]
            model = " ".join(model_tokens).strip()
            devs.append({
                "name": name,
                "type": dtype,
                "size": size,
                "model": model or None,
                "serial": serial or None,
                "is_rotational": (rota == "1"),
                "state": state or None,
            })
    return devs

def gcc_version():
    if not which("gcc"): return None
    first = run(["gcc","--version"]).splitlines()
    return first[0] if first else None

def parse_flags(flags):
    key = {"avx512f":"AVX-512F","avx512vl":"AVX-512VL","avx512dq":"AVX-512DQ","avx512bw":"AVX-512BW","avx512cd":"AVX-512CD",
           "avx2":"AVX2","avx":"AVX","sse4_2":"SSE4.2","sse4_1":"SSE4.1","fma":"FMA","neon":"NEON","asimd":"ASIMD"}
    present = [name for flg,name in key.items() if flg in flags]
    return present

def build_report(args):
    color = not args.no_color
    osrel = parse_os_release()
    uname = uname_info()
    lscpu = parse_lscpu()
    pinfo = proc_cpuinfo()
    freq = cpufreq_info()
    caches = cache_info()
    numa = numa_info()
    mem = mem_info()
    memspeeds = dmidecode_memory()
    gpus = gpu_info()
    disks = storage_info()
    gcc = gcc_version()

    # CPU summary
    model = lscpu.get("Model name") or pinfo.get("model_name") or "Unknown CPU"
    sockets = lscpu.get("Socket(s)") or (str(pinfo["sockets"]) if pinfo.get("sockets") else None)
    cores_per_socket = lscpu.get("Core(s) per socket") or (str(pinfo["cores_per_socket"]) if pinfo.get("cores_per_socket") else None)
    threads_per_core = lscpu.get("Thread(s) per core")
    cpus = lscpu.get("CPU(s)")
    arch = lscpu.get("Architecture") or uname.get("machine")

    # Frequencies
    base_ghz = mhz_to_ghz(freq["base_freq_mhz"]) if freq.get("base_freq_mhz") else (lscpu.get("CPU MHz") and mhz_to_ghz(lscpu["CPU MHz"]))
    max_ghz  = mhz_to_ghz(freq["max_freq_mhz"]) if freq.get("max_freq_mhz") else (lscpu.get("CPU max MHz") and mhz_to_ghz(lscpu["CPU max MHz"]))

    # Caches summary
    l3 = lscpu.get("L3 cache")
    l2 = lscpu.get("L2 cache")
    l1d = lscpu.get("L1d cache")
    l1i = lscpu.get("L1i cache")

    simd = parse_flags(pinfo.get("flags", []))

    perf_cores = lscpu.get("Performance cores")
    eff_cores = lscpu.get("Efficiency cores")

    # Memory
    total_ram = human_bytes(mem["total"]) if mem.get("total") else None
    avail_ram = human_bytes(mem["available"]) if mem.get("available") else None
    swap_total = human_bytes(mem["swap_total"]) if mem.get("swap_total") else None

    # Build top summary lines
    summary = []
    summary.append(f"{colorize('CPU', 'cyan', True, color)}: {model}")
    line2 = []
    if sockets: line2.append(f"sockets {sockets}")
    if cores_per_socket: line2.append(f"cores/socket {cores_per_socket}")
    if threads_per_core: line2.append(f"threads/core {threads_per_core}")
    if cpus: line2.append(f"logical {cpus}")
    summary.append("  " + ", ".join(line2))
    if perf_cores or eff_cores:
        summary.append(f"  core types: {perf_cores or '?'} perf, {eff_cores or '?'} eff")
    clocks = []
    if base_ghz: clocks.append(f"base {base_ghz}")
    if max_ghz: clocks.append(f"max {max_ghz}")
    if freq.get("boost"): clocks.append(f"boost {freq['boost']}")
    if clocks:
        summary.append("  " + ", ".join(clocks))
    if l3: summary.append(f"  L3: {l3}")
    if simd: summary.append(f"  SIMD: {', '.join(simd)}")

    summary.append(f"{colorize('Memory', 'cyan', True, color)}: {total_ram or 'Unknown'}"
                   + (f" (available {avail_ram})" if avail_ram else ""))
    if memspeeds:
        speeds = ", ".join(sorted(set(memspeeds)))
        summary.append(f"  DIMM speeds: {speeds}")

    if gpus:
        gsum = "; ".join([f"{g.get('vendor','GPU')} {g.get('name','')}".strip() for g in gpus])
        if False:
          summary.append(f"{colorize('GPU', 'cyan', True, color)}: {gsum}")

    if disks:
        kinds = defaultdict(int)
        for d in disks:
            kinds["SSD" if not d["is_rotational"] else "HDD"] += 1
        ksum = ", ".join([f"{n} {k}" for k,n in kinds.items()])
        if False:
          summary.append(f"{colorize('Storage', 'cyan', True, color)}: {ksum or 'Unknown'}")

    summary.append(f"{colorize('OS/Kernel', 'cyan', True, color)}: {osrel.get('distro') or 'Linux'}, {uname['kernel']} ({arch})")

    # Exit early if --short
    if args.short:
        return "\n".join(summary), {
            "cpu": {"model": model, "sockets": sockets, "cores_per_socket": cores_per_socket,
                    "threads_per_core": threads_per_core, "logical_cpus": cpus,
                    "performance_cores": perf_cores, "efficiency_cores": eff_cores,
                    "base_freq": base_ghz, "max_freq": max_ghz, "boost": freq.get("boost"),
                    "l3_cache": l3, "simd": simd},
            "memory": {"total": mem.get("total"), "available": mem.get("available"), "swap_total": mem.get("swap_total"), "dimm_speeds": memspeeds},
            "gpu": gpus,
            "storage_summary": dict(kinds) if False and disks else {},
            "os": {"distro": osrel.get("distro"), "kernel": uname["kernel"], "arch": arch},
        }

    # Full sections
    lines = []
    lines.extend(summary)
    lines.append("")

    # Detailed CPU
    lines.append(colorize("== CPU Details ==", "yellow", True, color))
    lines.append(f"Architecture : {arch}")
    lines.append(f"Model name   : {model}")
    if sockets or cores_per_socket or threads_per_core or cpus:
        lines.append(f"Topology     : sockets={sockets or '?'}, cores/socket={cores_per_socket or '?'}, threads/core={threads_per_core or '?'}, logical={cpus or '?'}")
    if perf_cores or eff_cores:
        lines.append(f"Core types   : perf={perf_cores or '?'} eff={eff_cores or '?'}")
    lines.append(f"cpufreq      : driver={freq.get('driver') or 'unknown'}, governor={freq.get('governor') or 'unknown'}, boost={freq.get('boost') or 'unknown'}")
    lines.append(f"Clocks       : base={base_ghz or 'unknown'}, max={max_ghz or 'unknown'}")
    if l1d or l1i or l2 or l3:
        lines.append(f"Caches       : L1d={l1d or '-'}, L1i={l1i or '-'}, L2={l2 or '-'}, L3={l3 or '-'}")
    if caches and not (l1d and l1i and l2 and l3):
        for c in caches:
            lines.append(f"  L{c['level']} {c['type']}: {c['size']} (assoc {c['associativity']})")
    if simd:
        lines.append("SIMD/Features: " + ", ".join(simd))
    else:
        # fallback to short lscpu Flags line
        if "Flags" in parse_lscpu():
            flags = parse_lscpu()["Flags"]
            lines.append("Flags        : " + flags)

    # NUMA
    if numa:
        lines.append("")
        lines.append(colorize("== NUMA Topology ==", "yellow", True, color))
        for n in numa:
            lines.append(f"Node {n['node']}: cpus={n['cpulist'] or '-'}; mem={n['mem_total'] or 'unknown'}")

    # Memory
    lines.append("")
    lines.append(colorize("== Memory ==", "yellow", True, color))
    lines.append(f"Total        : {total_ram or 'unknown'}")
    if avail_ram: lines.append(f"Available    : {avail_ram}")
    if swap_total: lines.append(f"Swap         : {swap_total} (free {human_bytes(mem['swap_free']) if mem.get('swap_free') else 'unknown'})")
    if mem.get("hugepages_total") is not None:
        lines.append(f"HugePages    : total={mem['hugepages_total']}, size={human_bytes(mem['hugepage_size']) if mem.get('hugepage_size') else 'unknown'}")
    if memspeeds:
        lines.append(f"DIMM speeds  : {', '.join(sorted(set(memspeeds)))}")
    elif which("dmidecode") and os.geteuid() != 0:
        lines.append("DIMM speeds  : (run as root to read via dmidecode)")

    # GPU
    lines.append("")
    if False:
      lines.append(colorize("== GPU(s) ==", "yellow", True, color))
    if gpus:
        for i,g in enumerate(gpus):
            base = f"[{i}] {g.get('vendor','GPU')}"
            if g.get("name"): base += f" {g['name']}"
            if False:
              lines.append(base)
              if g.get("driver"): lines.append(f"      driver: {g['driver']}")
              if g.get("vram"):   lines.append(f"      vram  : {g['vram']}")
              if g.get("pstate"): lines.append(f"      pstate: {g['pstate']}")
              if g.get("clock_graphics"): lines.append(f"      clk   : {g['clock_graphics']}")
              if g.get("raw"):    lines.append("      info  : " + g["raw"].replace("\n","\n              "))
    else:
        lines.append("No GPU info found (try installing nvidia-smi, rocm-smi, or glxinfo).")

    # Storage
    lines.append("")
    if False:
      lines.append(colorize("== Storage Devices ==", "yellow", True, color))
    if disks:
        for d in disks:
            kind = "SSD" if not d["is_rotational"] else "HDD"
            if False:
              lines.append(f"{d['name']}: {kind}, {d['size']}, model={d.get('model') or 'unknown'}"
                         + (f", state={d['state']}" if d.get("state") else "")
                         + (f", serial={d['serial']}" if d.get("serial") else ""))
    else:
        lines.append("No disk info (lsblk not available).")

    # OS/Kernel & Tooling
    lines.append("")
    lines.append(colorize("== OS / Kernel / Tooling ==", "yellow", True, color))
    lines.append(f"Distro       : {osrel.get('distro') or 'Linux'}")
    lines.append(f"Kernel       : {uname['kernel']} ({uname['machine']})")
    if gcc: lines.append(f"GCC          : {gcc}")
    py = f"Python       : {sys.version.split()[0]}"
    lines.append(py)

    report_text = "\n".join(lines)
    report_json = {
        "summary": {
            "cpu": {
                "model": model,
                "sockets": sockets,
                "cores_per_socket": cores_per_socket,
                "threads_per_core": threads_per_core,
                "logical_cpus": cpus,
                "performance_cores": perf_cores,
                "efficiency_cores": eff_cores,
                "base_freq": base_ghz,
                "max_freq": max_ghz,
                "boost": freq.get("boost"),
                "l3_cache": l3,
                "simd": simd,
            },
            "memory": {
                "total_bytes": mem.get("total"),
                "available_bytes": mem.get("available"),
                "swap_total_bytes": mem.get("swap_total"),
                "dimm_speeds": memspeeds,
            },
            "os": {
                "distro": osrel.get("distro"),
                "kernel": uname.get("kernel"),
                "arch": arch,
            }
        },
        "details": {
            "lscpu": lscpu,
            "cpufreq": freq,
            "caches": caches,
            "numa": numa,
            "meminfo": mem,
            "gcc": gcc,
        }
    }
    return report_text, report_json

def parse_args():
    import argparse
    ap = argparse.ArgumentParser(description="Generate a human-readable benchmark system report (Linux).")
    ap.add_argument("--short", action="store_true", help="Print only the top summary.")
    ap.add_argument("--json", action="store_true", help="Also print JSON after the human-readable report.")
    ap.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    return ap.parse_args()

def main():
    args = parse_args()
    text, js = build_report(args)
    print(text)
    if args.json:
        print()
        print(json.dumps(js, indent=2, sort_keys=False))

if __name__ == "__main__":
    main()