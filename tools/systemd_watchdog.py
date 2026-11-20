"""P00 Linux systemd readiness/watchdog adapter for the READ-ONLY observer.

No service installation, GitHub write, model execution or shell invocation.
Operator must install the separately reviewed systemd unit. READY and
WATCHDOG are emitted only *after* a successfully authenticated observation
was durably stored under the live worker lease.
"""
from __future__ import annotations

import os
import re
import socket
import sys
from typing import Callable, Mapping


class SystemdWatchdogDenied(RuntimeError):
    """Invalid service authority or failed notification; no host secrets echoed."""


def _send_notification(address: str, message: bytes) -> None:
    """Use standard systemd AF_UNIX datagrams without a third-party library."""
    dest = ("\0" + address[1:]) if address.startswith("@") else address
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as channel:
            channel.settimeout(2)
            sent = channel.sendto(message, dest)
            if sent != len(message):
                raise SystemdWatchdogDenied("incomplete watchdog datagram")
    except OSError:
        raise SystemdWatchdogDenied("systemd notification unavailable") from None


class SystemdWatchdog:
    """Optional fail-closed notify adapter, never an independent host attestation."""

    def __init__(self, address: str, watchdog_usec: int, *,
                 sender: Callable[[str, bytes], None] = _send_notification):
        self.address = address
        self.watchdog_usec = watchdog_usec
        self.sender = sender
        self.ready_sent = False

    @classmethod
    def from_environment(
        cls, environ: Mapping[str, str] | None = None, *,
        platform: str | None = None, pid: int | None = None,
        sender: Callable[[str, bytes], None] = _send_notification,
    ) -> "SystemdWatchdog":
        # Explicit operator opt-in is enforced by phase_worker CLI; this method
        # refuses incomplete/mismatched systemd-supplied service environment.
        system = sys.platform if platform is None else platform
        values = os.environ if environ is None else environ
        process_id = os.getpid() if pid is None else pid
        if system != "linux":
            raise SystemdWatchdogDenied("systemd notification is Linux-only")
        addr = values.get("NOTIFY_SOCKET")
        usec_text = values.get("WATCHDOG_USEC")
        expected_pid = values.get("WATCHDOG_PID")
        if (
            not isinstance(addr, str)
            or not 1 < len(addr) <= 200
            or addr[0] not in ("/", "@")
            or (addr[0] == "@" and len(addr) < 3)
            or any(ord(c) < 33 or ord(c) > 126 for c in addr)
            or "\\" in addr
            or not isinstance(usec_text, str)
            or re.fullmatch(r"[1-9][0-9]{0,11}", usec_text) is None
            or (expected_pid is not None and expected_pid != str(process_id))
        ):
            raise SystemdWatchdogDenied("systemd watchdog environment missing or invalid")
        watchdog_usec = int(usec_text)
        # Deliberately bounded. Too-small deadlines can cause misleading
        # watchdog behavior on slow GitHub API paths; the unit uses 300 s.
        if not 180_000_000 <= watchdog_usec <= 600_000_000:
            raise SystemdWatchdogDenied("unapproved systemd watchdog interval")
        return cls(addr, watchdog_usec, sender=sender)

    def on_successful_observation(self) -> None:
        """Main process only: called AFTER authenticated observation and DB commit.

        No watchdog packets on transient API failure, corrupt state, stale
        lease, or unsafe host environment. This is NOT a coding-agent heartbeat.
        """
        marker = b"READY=1\nWATCHDOG=1" if not self.ready_sent else b"WATCHDOG=1"
        try:
            self.sender(self.address, marker)
        except SystemdWatchdogDenied:
            raise
        except (OSError, ValueError, TypeError):
            raise SystemdWatchdogDenied("systemd watchdog signal failed") from None
        self.ready_sent = True
