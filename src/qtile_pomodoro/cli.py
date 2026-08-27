from __future__ import annotations

import argparse
import asyncio
import json
import sys
from .core import serve, socket_path

async def request(command: str) -> dict:
    reader, writer = await asyncio.open_unix_connection(socket_path())
    writer.write(json.dumps({"command": command}).encode() + b"\n"); await writer.drain()
    response = json.loads((await reader.readline()).decode())
    writer.close(); await writer.wait_closed()
    if not response["ok"]: raise RuntimeError(response["error"])
    return response["result"]

def main() -> None:
    parser = argparse.ArgumentParser(prog="qtile-pomodoro")
    parser.add_argument("command", choices=["daemon", "status", "start", "pause", "reset", "skip", "reload", "stats"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "daemon": asyncio.run(serve()); return
    try: result = asyncio.run(request(args.command))
    except (OSError, RuntimeError) as error: parser.error(f"Timer Service unavailable: {error}")
    if args.json: print(json.dumps(result))
    elif args.command == "stats":
        print(f"Today: {result['today_minutes']} minutes\nThis ISO week: {result['week_minutes']} minutes")
        for row in result["history"]: print(f"{row['completed_at']}  {row['minutes']} minutes")
    else: print(f"{result['phase']} {result['status']} {result['remaining']}s ({result['completed_in_cycle']}/{result['long_break_after']})")

if __name__ == "__main__": main()
