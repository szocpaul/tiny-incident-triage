"""T006: Ettin-17M full fine-tune CPU-n — pontosan a tiny-classifiers receptje.

Referencia: MaximeRivest/tiny-classifiers recipe/train.py és a tutorial Section 4.
Fix lépésszám: epochs = max(6, round(6 * 9493 / tanítósorok)).
"""
import json
import math
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

MODEL_ID = "jhu-clsp/ettin-encoder-17m"
RECIPE = dict(batch=32, lr=1e-4, weight_decay=0.01, warmup_frac=0.05,
              clip=1.0, maxlen=128, reference_steps_of=9493, min_epochs=6)


def recipe_epochs(n_texts: int) -> int:
    return max(RECIPE["min_epochs"], round(6 * RECIPE["reference_steps_of"] / n_texts))


def train_run(train_df, test_df, run_dir, seed=0, epochs_override=None, batch=None):
    """Teljes finomhangolás; minden paraméter a run config.json-jába (FR-008)."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    batch = batch or RECIPE["batch"]
    labels = sorted(train_df["label"].unique().to_list())
    epochs = epochs_override or recipe_epochs(len(train_df))

    config = dict(RECIPE, model=MODEL_ID, seed=seed, epochs=epochs, labels=labels,
                  n_train=len(train_df), n_test=len(test_df), batch=batch)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    torch.manual_seed(seed)
    rng = random.Random(seed)
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    texts = train_df["text"].to_list()
    targets = train_df["label"].to_list()
    ids = [tok(t, truncation=True, max_length=RECIPE["maxlen"])["input_ids"] for t in texts]
    y = torch.tensor([labels.index(t) for t in targets])

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID, num_labels=len(labels), id2label=dict(enumerate(labels)),
        label2id={l: i for i, l in enumerate(labels)})
    opt = torch.optim.AdamW(model.parameters(), lr=RECIPE["lr"],
                            weight_decay=RECIPE["weight_decay"])
    steps = epochs * math.ceil(len(ids) / batch)
    warm = max(1, int(RECIPE["warmup_frac"] * steps))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: (s + 1) / warm if s < warm
        else 0.5 * (1 + math.cos(math.pi * (s - warm) / (steps - warm))))

    model.train()
    t0 = time.monotonic()
    step = 0
    for epoch in range(epochs):
        order = list(range(len(ids)))
        rng.shuffle(order)
        for i in range(0, len(order), batch):
            b = order[i:i + batch]
            enc = tok.pad({"input_ids": [ids[j] for j in b]}, return_tensors="pt")
            logits = model(**enc).logits.float()
            loss = F.cross_entropy(logits, y[b])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), RECIPE["clip"])
            opt.step()
            sched.step()
            step += 1
        print(f"epoch {epoch + 1}/{epochs} | step {step}/{steps} | loss {loss.item():.4f} | "
              f"{time.monotonic() - t0:.0f}s", flush=True)
    train_seconds = time.monotonic() - t0

    model.eval()
    model.save_pretrained(run_dir / "model")
    tok.save_pretrained(run_dir / "model")

    config["train_seconds"] = round(train_seconds, 1)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config
