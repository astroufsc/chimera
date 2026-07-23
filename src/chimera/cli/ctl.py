#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2026-present Paulo Henrique Silva <ph.silva@gmail.com>

import json
import optparse
import sys
from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table

from chimera.core.version import chimera_version

from .cli import ChimeraCLI, ParameterType, action


def _fmt_age(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m{int(seconds % 60):02d}s"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h{int((seconds % 3600) // 60):02d}m"
    return f"{int(seconds // 86400)}d{int((seconds % 86400) // 3600):02d}h"


def _table(title: str, *columns: str) -> Table:
    table = Table(
        title=title,
        title_justify="left",
        title_style="bold",
        box=box.SIMPLE,
        pad_edge=False,
    )
    for column in columns:
        table.add_column(column)
    return table


class ChimeraCtl(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(
            self, "chimera-ctl", "System debug and control", chimera_version
        )

        self._console = Console()
        self._config_target: str | None = None

        self.add_help_group("CTL", "System inspection")
        self.add_controller(
            name="manager",
            cls="Manager",
            required=True,
            help="Manager to inspect",
            help_group="CTL",
        )
        self.add_parameters(
            dict(
                name="json",
                long="json",
                type=ParameterType.BOOLEAN,
                default=False,
                help="Dump the raw status as JSON",
                help_group="CTL",
            )
        )

    def run(self, cmdline_args: list[str]):
        args = list(cmdline_args)

        # subcommand-style front end over the flag-based framework:
        #   chimera-ctl [status]
        #   chimera-ctl config [object]
        if len(args) > 1 and not args[1].startswith("-"):
            subcommand = args.pop(1)
            match subcommand:
                case "status":
                    args.insert(1, "--status")
                case "config":
                    if len(args) > 1 and not args[1].startswith("-"):
                        self._config_target = args.pop(1)
                    args.insert(1, "--show-config")
                case _:
                    self.exit(f"Unknown command: {subcommand}")

        super().run(args)

    def _get_selected_actions(self, options: optparse.Values) -> list[Any]:
        selected = super()._get_selected_actions(options)
        if not selected:
            # no action given: default to --status
            selected = [self._actions["status"]]
        return selected

    @action(help="Print the current state of the whole system", help_group="CTL")
    def status(self, options: optparse.Values):
        status = self.manager.get_status()

        if options.json:
            self.out(json.dumps(status, indent=2))
            return

        self._print_status(status)

    @action(
        name="show_config",
        long="show-config",
        help="Print objects with their current config (chimera-ctl config [object])",
        help_group="CTL",
    )
    def show_config(self, options: optparse.Values):
        objects = self.manager.get_status()["objects"]

        target = self._config_target
        if target:
            matches = [obj for obj in objects if target in obj["path"]]
            if not matches:
                available = ", ".join(obj["path"] for obj in objects)
                self.exit(f"No object matching '{target}'. Available: {available}")
            objects = matches

        if options.json:
            payload = [
                {"path": obj["path"], "class": obj["class"], "config": obj["config"]}
                for obj in objects
            ]
            self.out(json.dumps(payload, indent=2))
            return

        for obj in objects:
            self._console.print(
                f"[bold]{obj['path']}[/bold] [dim]({obj['class']})[/dim]"
            )
            table = _table("", "key", "value", "type")
            table.title = None
            for key, value in obj["config"].items():
                table.add_row(key, str(value), f"[dim]{type(value).__name__}[/dim]")
            self._print_table(table, "no config")

    def _print_status(self, status: dict[str, Any]) -> None:
        console = self._console
        system = status["system"]
        bus = status["bus"]

        console.rule("[bold]System[/bold]")
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim")
        grid.add_column()
        grid.add_row("version", str(system["version"]))
        grid.add_row("pid", str(system["pid"]))
        grid.add_row("python", system["python"])
        console.print(grid)

        console.rule("[bold]Bus[/bold]")
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="dim")
        grid.add_column()
        grid.add_row("url", bus["url"])
        grid.add_row("inbox url", f"{bus['inbox_url']} [dim](how peers see us)[/dim]")
        grid.add_row(
            "running",
            "[green]yes[/green]" if bus["running"] else "[red]no[/red]",
        )
        grid.add_row("inbox", f"{bus['inbox_size']} queued")
        console.print(grid)
        console.print()

        self._print_pool("Bus pool", bus["pool"])

        # our own ephemeral bus shows up as a peer of the manager: mark it
        us = self.bus.url.bus
        peers = _table(f"Peers ({len(bus['peers'])})", "bus")
        for peer in bus["peers"]:
            marker = " [dim](us)[/dim]" if peer == us else ""
            peers.add_row(f"{peer}{marker}")
        self._print_table(peers, "no connected peers")

        mailboxes = bus["mailboxes"]
        pending = _table(
            f"Pending requests ({len(mailboxes)})", "id", "destination", "age"
        )
        for entry in sorted(mailboxes, key=lambda entry: -entry["age"]):
            pending.add_row(str(entry["id"]), entry["dst_bus"], _fmt_age(entry["age"]))
        self._print_table(pending, "no pending requests")

        publishing = _table(
            f"Events, publisher side ({len(bus['subscribers'])})",
            "publisher",
            "event",
            "subscribers",
        )
        for entry in bus["subscribers"]:
            publishing.add_row(
                entry["publisher"], entry["event"], str(entry["subscribers"])
            )
        self._print_table(publishing, "no subscribed events")

        subscribed = _table(
            f"Events, subscriber side ({len(bus['callbacks'])})",
            "publisher",
            "event",
            "callbacks",
        )
        for entry in bus["callbacks"]:
            subscribed.add_row(
                entry["publisher"], entry["event"], str(entry["callbacks"])
            )
        self._print_table(subscribed, "no event callbacks")

        console.rule("[bold]Objects[/bold]")
        objects = _table(
            f"Objects ({len(status['objects'])})",
            "location",
            "class",
            "state",
            "loop",
            "loop id",
            "age",
        )
        for obj in status["objects"]:
            state = obj["state"] or "-"
            if state == "RUNNING":
                state = f"[green]{state}[/green]"
            elif state == "STOPPED":
                state = f"[yellow]{state}[/yellow]"

            objects.add_row(
                obj["path"],
                obj["class"],
                state,
                obj["loop"],
                str(obj["loop_id"] or "-"),
                _fmt_age(obj["age"]),
            )
        self._print_table(objects, "no objects")

        loops_pool = status["pool"]
        console.print(
            f"[dim]control loops pool:[/dim] "
            f"{len(loops_pool['threads'])}/{loops_pool['max_workers']} workers, "
            f"{loops_pool['queued']} queued"
        )
        console.print()

    def _print_pool(self, name: str, pool: dict[str, Any]) -> None:
        threads = pool["threads"]
        title = (
            f"{name} ({len(threads)}/{pool['max_workers']} workers, "
            f"{pool['queued']} queued)"
        )
        table = _table(title, "id", "name", "state")
        for thread in threads:
            state = "[green]alive[/green]" if thread["alive"] else "[red]dead[/red]"
            table.add_row(str(thread["id"]), thread["name"], state)
        self._print_table(table, "no threads")

    def _print_table(self, table: Table, empty_message: str) -> None:
        if table.row_count:
            self._console.print(table)
        else:
            if table.title:
                self._console.print(f"[bold]{table.title}[/bold]")
            self._console.print(f"[dim]{empty_message}[/dim]")
        self._console.print()


def main():
    cli = ChimeraCtl()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
