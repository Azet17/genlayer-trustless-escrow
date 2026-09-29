# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json
import typing

"""
GenLayer Standard: TrustlessEscrow
=================================
A reusable delivery-adjudication contract for agentic commerce.

Flow:
1. buyer deploys the contract with seller + requirement
2. seller posts a public evidence URL
3. anyone calls resolve(); validators independently inspect the URL
   and ask an LLM whether the requirement was met
4. validator consensus determines RELEASED or REFUNDED state

This implementation focuses on the adjudication layer. Payment/funding can be
composed around it using GenLayer value-transfer primitives.
"""


class TrustlessEscrow(gl.Contract):
    buyer: Address
    seller: Address
    requirement: str
    evidence_url: str
    state: str          # OPEN -> DELIVERED -> RELEASED | REFUNDED
    verdict_reason: str

    def __init__(self, seller: str, requirement: str):
        self.buyer = gl.message.sender_address
        self.seller = Address(seller)
        self.requirement = requirement
        self.state = "OPEN"
        self.evidence_url = ""
        self.verdict_reason = ""

    @gl.public.view
    def get_status(self) -> str:
        return json.dumps({
            "state": self.state,
            "buyer": str(self.buyer),
            "seller": str(self.seller),
            "requirement": self.requirement,
            "evidence_url": self.evidence_url,
            "verdict_reason": self.verdict_reason,
        })

    @gl.public.write
    def deliver(self, evidence_url: str) -> None:
        assert gl.message.sender_address == self.seller, "only seller can deliver"
        assert self.state == "OPEN", "escrow not open"
        assert evidence_url.strip() != "", "evidence URL required"
        self.evidence_url = evidence_url
        self.state = "DELIVERED"

    @gl.public.write
    def resolve(self) -> None:
        assert self.state == "DELIVERED", "nothing delivered yet"

        def judge_delivery() -> typing.Any:
            page = gl.nondet.web.render(self.evidence_url, mode="text")
            prompt = (
                "You are an impartial judge of a delivery dispute.\n"
                "REQUIREMENT (verbatim): " + self.requirement + "\n"
                "EVIDENCE PAGE CONTENT:\n" + page[:12000] + "\n"
                "Return JSON with exactly these keys: "
                '{"met": true|false, "reason": "one concise sentence"}'\n'
                "Judge only from the supplied evidence and requirement."
            )
            result = gl.nondet.exec_prompt(prompt, response_format="json")
            if not isinstance(result, dict):
                raise gl.UserError("LLM did not return a JSON object")
            met = result.get("met")
            if not isinstance(met, bool):
                raise gl.vm.UserError("LLM JSON missing boolean 'met'")
            return {
                "met": met,
                "reason": str(result.get("reason", ""))[:500],
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            validator_data = judge_delivery()
            leader_data = leader_result.calldata
            if not isinstance(leader_data, dict):
                return False
            return leader_data.get("met") == validator_data.get("met")

        verdict = gl.vm.run_nondet_unsafe(judge_delivery, validator_fn)
        self.verdict_reason = verdict["reason"]

        if verdict["met"]:
            self.state = "RELEASED"
        else:
            self.state = "REFUNDED"
