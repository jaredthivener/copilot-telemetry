#!/usr/bin/env python3
"""
Pretty-print Copilot telemetry JSONL files.
Usage: telemetry_view.py <signal> <file>
  signal: traces | logs | metrics
"""
import sys, json, datetime, shutil, re, unicodedata, textwrap
from collections import defaultdict

W    = min(shutil.get_terminal_size((100, 40)).columns, 160)
RST  = "\033[0m";  BOLD = "\033[1m";  DIM  = "\033[2m"
RED  = "\033[31m"; GRN  = "\033[32m"; YLW  = "\033[33m"
BLU  = "\033[34m"; MAG  = "\033[35m"; CYN  = "\033[36m"
BBLK = "\033[90m"; BRED = "\033[91m"; BGRN = "\033[92m"
BYLW = "\033[93m"; BBLU = "\033[94m"; BMAG = "\033[95m"
BCYN = "\033[96m"; BWHT = "\033[97m"

ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def strip_ansi(s):
    return ANSI_RE.sub("", s)

def char_width(ch):
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1

def vis_width(s):
    return sum(char_width(ch) for ch in strip_ansi(s))

def ellipsize(s, width):
    if width <= 0:
        return ""
    if vis_width(s) <= width:
        return s
    out = []
    used = 0
    for ch in s:
        w = char_width(ch)
        if used + w >= width:
            break
        out.append(ch)
        used += w
    return "".join(out) + "…"

def pad_vis_right(s, width):
    pad = width - vis_width(s)
    return s + (" " * max(0, pad))

def minibar(val, maxv, w=14, full="█", empty="░"):
    if maxv <= 0: return ""
    n = round(min(val / maxv, 1.0) * w)
    return (full * n + empty * (w - n))[:w]

def attr_map(lst):
    m = {}
    for a in lst:
        v = a.get("value", {})
        k = a["key"]
        if   "stringValue" in v: m[k] = v["stringValue"]
        elif "intValue"    in v: m[k] = v["intValue"]
        elif "doubleValue" in v: m[k] = v["doubleValue"]
        elif "boolValue"   in v: m[k] = v["boolValue"]
        elif "arrayValue"  in v:
            vals = [list(x.values())[0] for x in v["arrayValue"].get("values", []) if x]
            m[k] = ", ".join(str(x) for x in vals)
    return m

# ══════════════════════════════════════════════════════════════════════════════
#  TRACES
# ══════════════════════════════════════════════════════════════════════════════

SPAN_STYLE = [
    ("invoke_agent", "◈", BMAG),
    ("chat",         "◆", BCYN),
    ("execute_tool", "⚙", BYLW),
    ("execute_hook", "⚡", BBLK),
    ("embeddings",   "◈", BBLU),
]

def span_fmt(name):
    for prefix, icon, color in SPAN_STYLE:
        if name.startswith(prefix): return icon, color
    return "·", BBLK

def ns_ms(v):
    try: return int(v) / 1_000_000
    except: return 0.0

def fmt_dur(ms):
    if ms <= 0: return "     —"
    if ms < 1000:  return f"{ms:>5.0f}ms"
    if ms < 60000: return f"{ms/1000:>5.2f}s "
    m = int(ms / 60000); s = (ms % 60000) / 1000
    return (f"{m}m {s:.0f}s").rjust(7)

def dur_color(ms):
    if ms < 200:   return BGRN
    if ms < 2000:  return BYLW
    if ms < 15000: return YLW
    return BRED

def fmt_time(ns):
    try: return datetime.datetime.fromtimestamp(int(ns) / 1e9).strftime("%H:%M:%S")
    except: return "??"

def _collect_text_parts(value, out):
    if isinstance(value, str):
        s = value.strip()
        if s:
            out.append(s)
        return
    if isinstance(value, list):
        for item in value:
            _collect_text_parts(item, out)
        return
    if isinstance(value, dict):
        # Prefer semantic text-like keys when present.
        for k in ("content", "text", "prompt", "message"):
            if k in value:
                _collect_text_parts(value[k], out)
        for v in value.values():
            _collect_text_parts(v, out)

def extract_prompt_from_trace(sps):
    candidates = []

    def add_candidate(raw):
        if not raw:
            return
        s = str(raw).strip()
        if not s:
            return
        # If the raw payload includes <userRequest>, keep that focused text.
        m = re.search(r"<userRequest>\s*(.*?)\s*</userRequest>", s, flags=re.S)
        if m:
            s = m.group(1).strip()
        candidates.append(s)

    for sp in sps:
        a = attr_map(sp.get("attributes", []))
        for k in ("gen_ai.input.messages", "copilot_chat.user_request", "gen_ai.prompt", "prompt"):
            if k in a:
                add_candidate(a.get(k))

    if not candidates:
        return ""

    extracted = []
    for raw in candidates:
        text_bits = []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                # Prefer user-role messages for context.
                user_msgs = [x for x in parsed if isinstance(x, dict) and x.get("role") == "user"]
                src = user_msgs[-1] if user_msgs else parsed[-1]
                _collect_text_parts(src, text_bits)
            else:
                _collect_text_parts(parsed, text_bits)
        except Exception:
            text_bits = [raw]

        if not text_bits:
            continue

        line = " ".join(text_bits).replace("\\n", " ").replace("\\t", " ")
        line = re.sub(r"\s+", " ", line).strip()
        m = re.search(r"<userRequest>\s*(.*?)\s*</userRequest>", line, flags=re.S)
        if m:
            line = m.group(1).strip()
        line = re.sub(r"^(<[^>]+>)+", "", line).strip()
        if line:
            extracted.append(line)

    if not extracted:
        return ""

    def score(s):
        bad_markers = (
            "the tool simplified the command",
            "the following files were successfully edited",
            "tool_call_response",
            "genai inference",
        )
        ls = s.lower()
        val = 0
        if any(b in ls for b in bad_markers):
            val -= 5
        if "<userrequest>" in ls:
            val += 4
        if "{" in s and "}" in s:
            val -= 2
        if 8 <= len(s) <= 220:
            val += 2
        if "?" in s:
            val += 1
        return val

    extracted.sort(key=lambda s: (score(s), -len(s)))
    return extracted[-1]

def show_traces(path, prompt_full=False):
    spans = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except: continue
            for rs in obj.get("resourceSpans", []):
                for ss in rs.get("scopeSpans", []):
                    for sp in ss.get("spans", []):
                        spans.append(sp)

    if not spans:
        print(f"  {DIM}no spans recorded yet{RST}"); return

    traces = defaultdict(list)
    for sp in spans:
        traces[sp["traceId"]].append(sp)

    models     = sorted({attr_map(s.get("attributes", [])).get("gen_ai.request.model", "") for s in spans} - {""})
    model_pill = "  ".join(f"{BCYN}{m}{RST}" for m in models)

    print(f"\n{BOLD}{BCYN}{'━' * W}{RST}")
    print(f"{BOLD} ◈  TRACES{RST}  {DIM}{len(traces)} traces  ·  {len(spans)} spans{RST}  {model_pill}")
    print(f"{BOLD}{BCYN}{'━' * W}{RST}")

    def render_span(sp, ids, kids, max_ms, depth=0, is_last=True, anc_lasts=None):
        if anc_lasts is None: anc_lasts = []
        name       = sp.get("name", "?")
        icon, col  = span_fmt(name)
        t          = fmt_time(sp.get("startTimeUnixNano", "0"))
        ms         = ns_ms(sp.get("endTimeUnixNano","0")) - ns_ms(sp.get("startTimeUnixNano","0"))
        dc         = dur_color(ms)
        a          = attr_map(sp.get("attributes", []))

        pre = ""
        for anc_last in anc_lasts:
            pre += "   " if anc_last else "│  "
        if depth > 0:
            pre += "└─ " if is_last else "├─ "

        ex    = []
        model = a.get("gen_ai.request.model", "")
        tool  = a.get("gen_ai.tool.name", "")
        if model: ex.append(model)
        if tool:  ex.append(tool)

        tree_txt = ellipsize(f"{pre}{icon} {name}", 52)
        ext_txt  = ellipsize(" | ".join(ex), 44)

        tree_col = pad_vis_right(tree_txt, 52)
        ext_col  = pad_vis_right(ext_txt, 44)

        print(
            f" {DIM}│{RST}  {BBLK}{t}{RST}  "
            f"{col}{tree_col}{RST}  "
            f"{dc}{fmt_dur(ms):>7}{RST}  "
            f"{DIM}{ext_col}{RST}"
        )

        ck = sorted(kids.get(sp["spanId"], []), key=lambda s: int(s.get("startTimeUnixNano","0")))
        for i, c in enumerate(ck):
            render_span(c, ids, kids, max_ms, depth + 1, i == len(ck) - 1, anc_lasts + [is_last])

    for tid, sps in sorted(traces.items(), key=lambda x: min(int(s.get("startTimeUnixNano","0")) for s in x[1])):
        sps     = sorted(sps, key=lambda s: int(s.get("startTimeUnixNano","0")))
        ids     = {s["spanId"] for s in sps}
        kids    = defaultdict(list)
        for s in sps:
            p = s.get("parentSpanId", "")
            if p and p in ids: kids[p].append(s)
        roots   = [s for s in sps if not s.get("parentSpanId") or s.get("parentSpanId") not in ids]
        max_ms  = max(ns_ms(s.get("endTimeUnixNano","0")) - ns_ms(s.get("startTimeUnixNano","0")) for s in sps)
        t_start = int(sps[0].get("startTimeUnixNano","0"))
        t_end   = max(int(s.get("endTimeUnixNano","0")) for s in sps)
        t_dur   = (t_end - t_start) / 1_000_000
        dc      = dur_color(t_dur)
        prompt  = extract_prompt_from_trace(sps)

        print(f"\n {DIM}┌─{RST} {BOLD}{BLU}{tid[:8]}{RST}  {BBLK}{fmt_time(t_start)}{RST}  {DIM}{len(sps)} spans{RST}  {dc}{BOLD}{fmt_dur(t_dur)}{RST}")
        if prompt:
            if prompt_full:
                label = f" {DIM}│{RST}  {DIM}prompt:{RST} "
                wrapped = textwrap.wrap(prompt, width=108) or [prompt]
                first = wrapped[0]
                print(f"{label}{BCYN}{first}{RST}")
                cont_prefix = f" {DIM}│{RST}          "
                for line in wrapped[1:]:
                    print(f"{cont_prefix}{BCYN}{line}{RST}")
            else:
                p = ellipsize(prompt, 118)
                print(f" {DIM}│{RST}  {DIM}prompt:{RST} {BCYN}{p}{RST}")
        else:
            print(f" {DIM}│{RST}  {DIM}prompt:{RST} {BBLK}(not captured in this trace){RST}")
        print(f" {DIM}│{RST}  {DIM}{'time':<8}  {'span':<52}  {'dur':>7}  {'details':<44}{RST}")
        print(f" {DIM}│{RST}  {DIM}{'·' * 8}  {'·' * 52}  {'·' * 7}  {'·' * 44}{RST}")
        for i, r in enumerate(roots):
            render_span(r, ids, kids, max_ms, 0, i == len(roots) - 1, [])
        print(f" {DIM}└{'─' * (W - 2)}{RST}")

    print()

# ══════════════════════════════════════════════════════════════════════════════
#  LOGS
# ══════════════════════════════════════════════════════════════════════════════

EVENT_STYLE = {
    "copilot_chat.session.start":                ("▶", BGRN, "session.start"),
    "copilot_chat.tool.call":                    ("⚙", BYLW, "tool.call    "),
    "copilot_chat.agent.turn":                   ("↺", BCYN, "agent.turn   "),
    "gen_ai.client.inference.operation.details": ("◆", BMAG, "inference    "),
    "copilot_chat.edit.hunk.action":             ("✎", BBLU, "edit.action  "),
}

def evt_style(ev, body):
    combined = ev + body
    for key, (icon, color, label) in EVENT_STYLE.items():
        if key in combined: return icon, color, label
    return "·", BBLK, (ev[:13].ljust(13) if ev else "event        ")

def tok_bar(n, maxn, w=12):
    if maxn <= 0: return "░" * w
    filled = round(min(n / maxn, 1.0) * w)
    return "█" * filled + "░" * (w - filled)

def show_logs(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except: continue
            for rl in obj.get("resourceLogs", []):
                for sl in rl.get("scopeLogs", []):
                    for lr in sl.get("logRecords", []):
                        records.append(lr)

    if not records:
        print(f"  {DIM}no log records yet{RST}"); return

    records = sorted(records, key=lambda r: int(r.get("timeUnixNano","0")))

    sessions, cur = [], []
    for r in records:
        a  = attr_map(r.get("attributes", []))
        ev = a.get("event.name", r.get("body", {}).get("stringValue", ""))
        if "session.start" in ev and cur:
            sessions.append(cur); cur = []
        cur.append(r)
    if cur: sessions.append(cur)

    max_in  = max((int(attr_map(r.get("attributes",[])).get("gen_ai.usage.input_tokens",  0)) for r in records), default=1)
    max_out = max((int(attr_map(r.get("attributes",[])).get("gen_ai.usage.output_tokens", 0)) for r in records), default=1)

    print(f"\n{BOLD}{BGRN}{'━' * W}{RST}")
    print(f"{BOLD} ◆  LOGS / EVENTS{RST}  {DIM}{len(records)} records  ·  {len(sessions)} sessions{RST}")
    print(f"{BOLD}{BGRN}{'━' * W}{RST}")

    for sess_idx, sess in enumerate(sessions):
        sess_model = ""
        for r in sess:
            a = attr_map(r.get("attributes", []))
            m = a.get("gen_ai.request.model", a.get("gen_ai.response.model", ""))
            if m: sess_model = m; break
        t0        = fmt_time(sess[0].get("timeUnixNano","0"))
        model_tag = f"  {BCYN}{sess_model}{RST}" if sess_model else ""
        fill      = "─" * max(W - 26 - len(sess_model), 2)
        print(f"\n {BGRN}▶{RST}  {BOLD}Session {sess_idx + 1}{RST}  {BBLK}{t0}{RST}{model_tag}  {DIM}{fill}{RST}")

        for r in sess:
            t    = fmt_time(r.get("timeUnixNano","0"))
            body = r.get("body", {}).get("stringValue", "")
            a    = attr_map(r.get("attributes", []))
            ev   = a.get("event.name", body)
            icon, color, label = evt_style(ev, body)

            in_tok  = int(a.get("gen_ai.usage.input_tokens",  0))
            out_tok = int(a.get("gen_ai.usage.output_tokens", 0))
            model   = a.get("gen_ai.request.model", a.get("gen_ai.response.model", ""))
            tool    = a.get("gen_ai.tool.name", "")

            if in_tok or out_tok:
                ib     = tok_bar(in_tok,  max_in)
                ob     = tok_bar(out_tok, max_out)
                detail = (f"  {DIM}in{RST} {BCYN}{ib}{RST} {BYLW}{in_tok:>7,}{RST}"
                          f"  {DIM}out{RST} {BGRN}{ob}{RST} {BYLW}{out_tok:>5,}{RST}")
            elif tool:
                detail = f"  {BYLW}{tool}{RST}"
            elif model and "session.start" in ev:
                detail = f"  {BCYN}{model}{RST}"
            else:
                detail = ""

            disp = body
            if body.startswith("GenAI inference:"):
                disp = body[len("GenAI inference: "):]
            elif "copilot_chat." in body and ": " in body:
                disp = body.split(": ", 1)[-1]

            print(f"  {BBLK}{t}{RST}  {color}{icon}{RST}  {DIM}{label}{RST}  {BOLD}{disp:<32}{RST}{detail}")

    print()

# ══════════════════════════════════════════════════════════════════════════════
#  METRICS
# ══════════════════════════════════════════════════════════════════════════════

NS_COLOR   = {"copilot_chat": BCYN, "gen_ai": BMAG, "otelcol": BBLU}
PREF_LABEL = (
    "gen_ai.tool.name", "gen_ai.request.model", "gen_ai.response.model",
    "gen_ai.agent.name", "copilot_chat.language_id", "outcome", "type",
)

def primary_label(all_keys):
    for k in PREF_LABEL:
        if k in all_keys: return k
    return None

def fmt_val(v):
    if isinstance(v, float): return f"{v:,.2f}" if v != int(v) else f"{int(v):,}"
    if isinstance(v, int):   return f"{v:,}"
    return str(v)

def show_metrics(path):
    latest = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except: continue
            for rm in obj.get("resourceMetrics", []):
                for sm in rm.get("scopeMetrics", []):
                    for m in sm.get("metrics", []):
                        name = m.get("name","?"); unit = m.get("unit","")
                        for kind in ("sum","gauge"):
                            if kind not in m: continue
                            for dp in m[kind].get("dataPoints",[]):
                                labels = attr_map(dp.get("attributes",[]))
                                val    = dp.get("asDouble", dp.get("asInt", 0))
                                ts     = int(dp.get("timeUnixNano","0"))
                                key    = (name, frozenset(labels.items()))
                                if key not in latest or ts > latest[key][0]:
                                    latest[key] = (ts, val, unit, labels)
                        if "histogram" in m:
                            for dp in m["histogram"].get("dataPoints",[]):
                                labels = attr_map(dp.get("attributes",[]))
                                ts     = int(dp.get("timeUnixNano","0"))
                                count  = int(dp.get("count",0))
                                s      = float(dp.get("sum",0.0))
                                avg    = s / count if count else 0.0
                                key    = (name + " ⊞", frozenset(labels.items()))
                                if key not in latest or ts > latest[key][0]:
                                    latest[key] = (ts, {"count": count, "sum": s, "avg": avg}, unit, labels)

    if not latest:
        print(f"  {DIM}no metrics recorded yet{RST}"); return

    by_ns = defaultdict(lambda: defaultdict(list))
    for (name, _), (ts, val, unit, labels) in latest.items():
        if   name.startswith("copilot_chat"): ns="copilot_chat"; short=name[len("copilot_chat."):]
        elif name.startswith("gen_ai"):       ns="gen_ai";        short=name[len("gen_ai."):]
        elif name.startswith("otelcol"):      ns="otelcol";       short=name[len("otelcol_"):]
        else:                                  ns="other";         short=name
        by_ns[ns][short].append((val, unit, labels))

    total = sum(len(v) for d in by_ns.values() for v in d.values())

    print(f"\n{BOLD}{BYLW}{'━' * W}{RST}")
    print(f"{BOLD} ⬡  METRICS{RST}  {DIM}{total} series  ·  {len(by_ns)} namespaces{RST}")
    print(f"{BOLD}{BYLW}{'━' * W}{RST}")

    def box_hdr(ns):
        nc   = NS_COLOR.get(ns, BBLK)
        lbl  = f" {nc}{BOLD}{ns}{RST} "
        fill = max(W - len(ns) - 6, 2)
        print(f"\n {DIM}┌─{RST}{lbl}{DIM}{'─' * fill}─┐{RST}")

    def box_row(content):
        raw = len(strip_ansi(content)) + 3          # 2 for " │" prefix + 1 for trailing "│"
        pad = max(W - raw, 0)
        print(f" {DIM}│{RST} {content}{' ' * pad}{DIM}│{RST}")

    def box_sep():
        print(f" {DIM}│{'╌' * (W - 2)}│{RST}")

    def box_ftr():
        print(f" {DIM}└{'─' * (W - 2)}┘{RST}")

    def render_metric(short_name, series):
        is_hist   = short_name.endswith(" ⊞")
        disp_name = short_name.rstrip(" ⊞")
        all_keys  = set(k for _, _, l in series for k in l)
        prim      = primary_label(all_keys)

        COL_NAME = 38

        if is_hist:
            avgs    = [v["avg"] for v, _, _ in series if isinstance(v, dict)]
            max_avg = max(avgs) if avgs else 1
            # Suppress noisy time-delay survival variants — keep t=0 only
            if "copilot_chat.time_delay_ms" in all_keys:
                series = [s for s in series if str(s[2].get("copilot_chat.time_delay_ms","")) in ("0","")]
                if not series: return
            series_s = sorted(series, key=lambda x: x[0].get("avg",0) if isinstance(x[0], dict) else 0, reverse=True)
            for i, (v, u, l) in enumerate(series_s[:8]):
                count  = v["count"]; avg = v["avg"]
                bar    = minibar(avg, max_avg)
                avg_s  = (f"{avg/1000:.2f}s " if u in ("ms","milliseconds") and avg >= 1000
                          else f"{avg:.0f}ms " if u in ("ms","milliseconds") else f"{avg:.3f}")
                lv     = f"{BCYN}{str(l.get(prim,'')):<26}{RST}" if prim and l.get(prim) else ""
                pfx    = f"{BYLW}{disp_name:<{COL_NAME}}{RST}" if i == 0 else " " * COL_NAME
                box_row(f"{pfx}  n={BBLK}{count:<4}{RST} avg={BYLW}{avg_s:<8}{RST} {DIM}{bar}{RST}  {lv}")
            if len(series_s) > 8:
                box_row(f"{' ' * COL_NAME}  {DIM}… {len(series_s) - 8} more series{RST}")
        else:
            nums   = [(float(v) if isinstance(v, (int, float)) else 0, u, l) for v, u, l in series]
            max_v  = max(x[0] for x in nums) if nums else 1
            nums_s = sorted(nums, key=lambda x: -x[0])
            for i, (val, u, l) in enumerate(nums_s[:10]):
                bar      = minibar(val, max_v)
                lv       = str(l.get(prim,"")) if prim else ""
                success  = l.get("success","")
                vc       = BGRN if str(success)=="True" else (BRED if str(success)=="False" else BYLW)
                extra    = "  ".join(f"{k}={v2}" for k, v2 in sorted(l.items())
                                     if k != prim and str(v2) not in ("True","False","true","false"))
                pfx      = f"{BYLW}{disp_name:<{COL_NAME}}{RST}" if i == 0 else " " * COL_NAME
                if prim and lv:
                    lv_d = f"{BCYN}{lv:<28}{RST}"
                    box_row(f"{pfx}  {lv_d}  {vc}{fmt_val(val):<8}{RST} {DIM}{bar}{RST}")
                else:
                    tail = f"  {DIM}{extra[:34]}{RST}" if extra else ""
                    box_row(f"{pfx}  {vc}{fmt_val(val):<8}{RST} {DIM}{bar}{RST}{tail}")
            if len(nums_s) > 10:
                box_row(f"{' ' * COL_NAME}  {DIM}… {len(nums_s) - 10} more series{RST}")

    for ns in ("copilot_chat","gen_ai","otelcol","other"):
        if ns not in by_ns: continue
        box_hdr(ns)
        for j, (short_name, series) in enumerate(sorted(by_ns[ns].items())):
            if j > 0: box_sep()
            render_metric(short_name, series)
        box_ftr()

    print()

# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} traces|logs|metrics <file> [--prompt-full]", file=sys.stderr)
        sys.exit(1)
    signal, path = sys.argv[1], sys.argv[2]
    flags = set(sys.argv[3:])
    prompt_full = "--prompt-full" in flags
    if   signal == "traces":  show_traces(path, prompt_full=prompt_full)
    elif signal == "logs":    show_logs(path)
    elif signal == "metrics": show_metrics(path)
    else:
        print(f"Unknown signal: {signal}", file=sys.stderr); sys.exit(1)
