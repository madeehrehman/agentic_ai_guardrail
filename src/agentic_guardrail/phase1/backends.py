"""Mock GRC and mail backends for stale-state validation demos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FindingRecord:
    finding_id: str
    entity_id: str
    status: str  # open | closed
    version: int
    title: str


@dataclass
class WorldState:
    """In-memory 'source of truth' outside the LLM — re-checked after HITL resume."""

    findings: dict[str, FindingRecord] = field(default_factory=dict)
    sent_messages: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def demo(cls) -> WorldState:
        return cls(
            findings={
                "FIN-2024-017": FindingRecord(
                    finding_id="FIN-2024-017",
                    entity_id="entity-uk-bank-01",
                    status="open",
                    version=3,
                    title="BCBS239 data aggregation gap",
                ),
            }
        )

    def get_finding(self, finding_id: str) -> FindingRecord | None:
        return self.findings.get(finding_id)

    def close_finding(self, finding_id: str, comment: str) -> str:
        rec = self.findings[finding_id]
        if rec.status != "open":
            raise ValueError(f"finding {finding_id} is not open")
        rec.status = "closed"
        rec.version += 1
        return f"closed {finding_id} v{rec.version}: {comment}"

    def simulate_external_close(self, finding_id: str) -> None:
        """Another user closed the finding while human was reviewing — stale path."""
        rec = self.findings[finding_id]
        rec.status = "closed"
        rec.version += 1

    def send_email(self, to: list[str], subject: str, body: str) -> str:
        allowed_domains = ("@bank.internal", "@legal.bank.internal")
        for addr in to:
            if not any(addr.endswith(d) for d in allowed_domains):
                raise ValueError(f"recipient not on allowlist: {addr}")
        msg_id = f"msg-{len(self.sent_messages) + 1}"
        self.sent_messages.append(
            {"id": msg_id, "to": ",".join(to), "subject": subject, "body": body}
        )
        return msg_id


# Process-wide demo store; tests inject their own instance via context if needed.
WORLD = WorldState.demo()
