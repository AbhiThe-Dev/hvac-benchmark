"""Self-supervised pretraining of a "what does a plausible HVAC connection
look like" representation from the unlabeled real-building Brick corpus.

Requires the optional `pretrain` extra (`uv sync --extra pretrain`), which
installs PyTorch. `data` is torch-free; `model`/`train`/`evaluate` need it.
"""
