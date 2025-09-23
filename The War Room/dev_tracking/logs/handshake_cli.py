#!/usr/bin/env python3
"""
Handshake CLI

Streamlines creating Request / ACK / Confirm / Debrief handshakes and appends
links to the daily handoffs file for quick visibility.

Usage examples:
  python dev_tracking/handshake_cli.py request --from POWER --to NETWORK \
      --subject "Dependency Install" --summary "Install required deps" \
      --tasks "pip install -r requirements.txt; rerun smoke" --due "2025-09-16"

  python dev_tracking/handshake_cli.py ack --acker POWER --requester NETWORK \
      --subject "Dependency Install" --due "2025-09-16"

  python dev_tracking/handshake_cli.py confirm --confirmer NETWORK --counterpart POWER \
      --subject "Dependency Install" --due "2025-09-16"

  python dev_tracking/handshake_cli.py debrief --from POWER --to DEESCALATION \
      --summary "Section 6 fixed; all sections pass smoke" \
      --artifacts "dev_tracking/SMOKE_RUN_RESULTS_EXTENDED.json; DKI_Repository/exports/*.pdf"
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re

ROOT = Path.cwd()
DEV = ROOT / "dev_tracking"
H_DIR = DEV / "Handshakes"
T_DIR = DEV / "templates" / "handshakes"
S_TPL = DEV / "templates" / "session_log.md"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", text.strip())
    s = re.sub(r"_+", "_", s)
    return s.strip("_") or "HANDOFF"


def ensure_dirs():
    H_DIR.mkdir(parents=True, exist_ok=True)


def read_template(name: str) -> str:
    p = T_DIR / f"{name}.md"
    if not p.exists():
        raise SystemExit(f"Missing template: {p}")
    return p.read_text(encoding="utf-8")


def write_and_link(filename: str, content: str) -> Path:
    ensure_dirs()
    path = H_DIR / filename
    path.write_text(content, encoding="utf-8")
    # Append a bullet to today's DAILY_HANDOFFS file for visibility
    handoffs = DEV / f"DAILY_HANDOFFS_{today()}.md"
    line = f"- Handshake: {path.name}\n"
    if handoffs.exists():
        with handoffs.open("a", encoding="utf-8") as f:
            f.write(line)
    else:
        with handoffs.open("w", encoding="utf-8") as f:
            f.write(f"# DAILY HANDOFFS — {today()}\n\n")
            f.write(line)
    return path


def write_session_log(agent: str, content: str) -> Path:
    agent_map = {
        'POWER': DEV / 'agent_1_POWER_CODING',
        'NETWORK': DEV / 'agent_2_NETWORK_CODING',
        'DEESCALATION': DEV / 'agent_3_DEESCALATION_CODING',
    }
    folder = agent_map.get(agent.upper())
    if not folder:
        raise SystemExit(f"Unknown agent: {agent}. Expected POWER|NETWORK|DEESCALATION")
    folder.mkdir(parents=True, exist_ok=True)
    fname = folder / f"SESSION_LOG_{today()}.md"
    if fname.exists():
        # Append another session block
        with fname.open('a', encoding='utf-8') as f:
            f.write("\n\n---\n\n")
            f.write(content)
    else:
        fname.write_text(content, encoding='utf-8')

    # Link in daily handoffs
    handoffs = DEV / f"DAILY_HANDOFFS_{today()}.md"
    line = f"- Session Log ({agent}): {fname.name}\n"
    if handoffs.exists():
        with handoffs.open("a", encoding="utf-8") as f:
            f.write(line)
    else:
        with handoffs.open("w", encoding="utf-8") as f:
            f.write(f"# DAILY HANDOFFS — {today()}\n\n")
            f.write(line)
    return fname


def fill(template: str, mapping: dict) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace(f"{{{{{k}}}}}", str(v or ""))
    return out


def cmd_request(args):
    tmpl = read_template("request")
    subj_slug = slugify(args.subject)
    fname = f"HANDSHAKE_{today()}_{args.from_agent}_to_{args.to_agent}_{subj_slug}.md"
    mapping = {
        "DATE": today(),
        "FROM": args.from_agent,
        "TO": args.to_agent,
        "SUBJECT": args.subject,
        "SUMMARY": args.summary or "",
        "TASKS": bulletize(args.tasks),
        "DUE": args.due or "",
        "SUCCESS": bulletize(args.success),
        "NOTES": args.notes or "",
        "SUMMARY_PATH": args.summary_path or "",
    }
    content = fill(tmpl, mapping)
    path = write_and_link(fname, content)
    print(str(path))


def cmd_ack(args):
    tmpl = read_template("ack")
    subj_slug = slugify(args.subject)
    fname = f"HANDSHAKE_{today()}_{args.acker}_ACK_{args.requester}_{subj_slug}.md"
    mapping = {
        "DATE": today(),
        "ACKER": args.acker,
        "REQUESTER": args.requester,
        "SUBJECT": args.subject,
        "SUMMARY": args.summary or "",
        "TASKS_SUMMARY": args.tasks or "",
        "NEXT_STEPS": bulletize(args.next_steps),
        "DUE": args.due or "",
    }
    content = fill(tmpl, mapping)
    path = write_and_link(fname, content)
    print(str(path))


def cmd_confirm(args):
    tmpl = read_template("confirm")
    subj_slug = slugify(args.subject)
    fname = f"HANDSHAKE_{today()}_{args.confirmer}_CONFIRM_{args.counterpart}_{subj_slug}.md"
    mapping = {
        "DATE": today(),
        "CONFIRMER": args.confirmer,
        "COUNTERPART": args.counterpart,
        "SUBJECT": args.subject,
        "SCOPE": args.scope or "",
        "DUE": args.due or "",
        "ACTIONS": bulletize(args.actions),
        "SUCCESS": bulletize(args.success),
    }
    content = fill(tmpl, mapping)
    path = write_and_link(fname, content)
    print(str(path))


def cmd_debrief(args):
    tmpl = read_template("debrief")
    fname = f"HANDSHAKE_{today()}_{args.from_agent}_DEBRIEF_to_{args.to_agent}.md"
    mapping = {
        "DATE": today(),
        "FROM": args.from_agent,
        "TO": args.to_agent,
        "SUMMARY": args.summary or "",
        "ARTIFACTS": bulletize(args.artifacts),
        "NOTES": args.notes or "",
        "REQUESTS": bulletize(args.requests),
    }
    content = fill(tmpl, mapping)
    path = write_and_link(fname, content)
    print(str(path))


def cmd_session(args):
    if not S_TPL.exists():
        raise SystemExit(f"Missing template: {S_TPL}")
    tmpl = S_TPL.read_text(encoding='utf-8')
    mapping = {
        'DATE': today(),
        'AGENT': args.agent,
        'SUMMARY': args.summary or '',
        'WORK': bulletize(args.work),
        'ARTIFACTS': bulletize(args.artifacts),
        'ISSUES': bulletize(args.issues),
        'NEXT': bulletize(args.next_steps),
    }
    for k, v in mapping.items():
        tmpl = tmpl.replace(f"{{{{{k}}}}}", str(v or ''))
    path = write_session_log(args.agent, tmpl)
    print(str(path))


def bulletize(text: str | None) -> str:
    if not text:
        return ""
    # Accept semicolons or newlines as separators
    parts = [p.strip() for p in re.split(r"[\n;]", text) if p.strip()]
    return "\n".join(f"- {p}" for p in parts)


def main():
    p = argparse.ArgumentParser(description="Handshake generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("request", help="Create a REQUEST handshake")
    pr.add_argument("--from", dest="from_agent", required=True)
    pr.add_argument("--to", dest="to_agent", required=True)
    pr.add_argument("--subject", required=True)
    pr.add_argument("--summary")
    pr.add_argument("--tasks")
    pr.add_argument("--due")
    pr.add_argument("--success")
    pr.add_argument("--notes")
    pr.add_argument("--summary-path", dest="summary_path", required=True)
    pr.set_defaults(func=cmd_request)

    pa = sub.add_parser("ack", help="Create an ACK handshake")
    pa.add_argument("--acker", required=True)
    pa.add_argument("--requester", required=True)
    pa.add_argument("--subject", required=True)
    pa.add_argument("--summary")
    pa.add_argument("--tasks")
    pa.add_argument("--next-steps", dest="next_steps")
    pa.add_argument("--due")
    pa.set_defaults(func=cmd_ack)

    pc = sub.add_parser("confirm", help="Create a CONFIRM handshake")
    pc.add_argument("--confirmer", required=True)
    pc.add_argument("--counterpart", required=True)
    pc.add_argument("--subject", required=True)
    pc.add_argument("--scope")
    pc.add_argument("--actions")
    pc.add_argument("--success")
    pc.add_argument("--due")
    pc.set_defaults(func=cmd_confirm)

    pd = sub.add_parser("debrief", help="Create a DEBRIEF handshake")
    pd.add_argument("--from", dest="from_agent", required=True)
    pd.add_argument("--to", dest="to_agent", required=True)
    pd.add_argument("--summary")
    pd.add_argument("--artifacts")
    pd.add_argument("--notes")
    pd.add_argument("--requests")
    pd.set_defaults(func=cmd_debrief)

    ps = sub.add_parser("session", help="Create/append an agent SESSION_LOG for today")
    ps.add_argument("--agent", required=True, choices=["POWER", "NETWORK", "DEESCALATION"])
    ps.add_argument("--summary")
    ps.add_argument("--work")
    ps.add_argument("--artifacts")
    ps.add_argument("--issues")
    ps.add_argument("--next-steps", dest="next_steps")
    ps.set_defaults(func=cmd_session)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
