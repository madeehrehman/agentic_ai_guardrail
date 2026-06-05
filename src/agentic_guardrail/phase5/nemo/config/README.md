# NeMo Guardrails config (optional)

When you install NeMo for production topical/dialog control:

```powershell
pip install nemoguardrails
```

1. Copy NVIDIA’s sample `config/` (Colang flows + `config.yml`) into this directory.
2. Define topical boundaries for the regulatory assistant (e.g. block creative writing, steer to policy Q&A).
3. Set environment variables:

```powershell
$env:GUARDRAIL_TOPICAL_BACKEND = "nemo"
$env:GUARDRAIL_NEMO_CONFIG_PATH = "src/agentic_guardrail/phase5/nemo/config"
```

4. Extend `phase5/nemo/adapter.py` to call `RunnableRails(config).invoke(...)` and map NeMo block flags to `TopicalVerdict`.

Until then, `GUARDRAIL_TOPICAL_BACKEND=stub` (default) exercises the same graph node with in-repo rules.
