# GenLayer Standard: TrustlessEscrow

A reusable Intelligent Contract for delivery adjudication in agentic commerce.
The contract records an agreed requirement, accepts a public evidence URL from the
seller, and lets GenLayer validators independently inspect the evidence and judge
whether the requirement was met.

## Why this is a Standard

The reusable primitive is the **delivery-decision layer**: applications can compose
this contract's final `RELEASED` / `REFUNDED` decision with their own GEN payment or
escrow funding flow.

- **Reusable** — deploy with two constructor arguments: seller address + requirement text.
- **Educational** — demonstrates `gl.nondet.web.render` for real-world evidence,
  `gl.nondet.exec_prompt(..., response_format="json")` for structured LLM judgment,
  and `gl.vm.run_nondet_unsafe` for independent validator verification.
- **Consensus-aware** — validators do not blindly accept the leader's LLM output;
  they re-run the same evidence-grounded judgment and require the `met` decision to match.
- **Composable** — the adjudication result can be paired with GenLayer's value-transfer
  primitives for applications that also need on-chain funding and payout.

## The flow

```text
buyer deploys contract
        |
        v
seller posts public evidence URL
        |
        v
anyone calls resolve()
        |
        +--> leader fetches page + LLM judges requirement
        |
        +--> validators independently repeat the judgment
        |
        v
RELEASED (requirement met) / REFUNDED (requirement not met)
```

## Requirement format

Use free text, but make it objectively checkable. Example:

> A public web page containing a written article of at least 800 words about the
> 2050 tokenization economy, with the buyer's handle @azet mentioned once.

The LLM receives the requirement and the rendered page content and returns a
structured `met` decision plus a short reason. The leader's decision is accepted
only when validators independently reproduce the same decision.

## Contract methods

- `get_status()` — read the current state and evidence URL.
- `deliver(evidence_url)` — seller submits public delivery evidence.
- `resolve()` — anyone triggers validator-backed adjudication.

## Deploy

Paste `TrustlessEscrow.py` into GenLayer Studio. Constructor arguments:
`seller` and `requirement`. The deployer becomes `buyer`.

For production settlement, pair the adjudication result with GenLayer's native
GEN value-transfer primitives rather than treating this demo as a custody contract.

## Notes and limitations

- Evidence pages should be public and stable enough for independent validator reads.
- The contract intentionally separates adjudication from payment custody so it can be
  reused with different funding and payout modules.
- The verdict reason is capped at 500 characters.
