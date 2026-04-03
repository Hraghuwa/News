# Legacy shim — analysis is now handled by the multi-agent pipeline in agents/
# This file is kept for backward compatibility only.

def analyze_business_implications(articles):
    raise NotImplementedError(
        "Single-agent analysis has been replaced by the 4-agent pipeline. "
        "Use main.py to run the full pipeline."
    )
