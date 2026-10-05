"""T009/T011: CLI belépés — tidy | train | eval | predict | run.

Gate-parancs: `python -m triage eval --min-accuracy 0.90` (exit 0/1).
A `run` a tidy→train→eval teljes lánc, időbélyeg-naplóval (US2, SC-003).
"""
import argparse
import json
import sys
import time
from pathlib import Path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="triage", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("tidy", help="nyers CSV -> tidy Parquet + recipe jsonl")
    s.add_argument("--raw", default="data/raw")
    s.add_argument("--tidy", default="data/tidy")
    s.add_argument("--tasks", default="data/tasks")
    s.add_argument("--seed", type=int, default=0)

    s = sub.add_parser("train", help="finomhangolás a tidy adaton")
    s.add_argument("--tidy", default="data/tidy")
    s.add_argument("--run", required=True, help="run-mappa, pl. runs/baseline-s0")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--epochs", type=int, default=None)

    s = sub.add_parser("eval", help="értékelés a fagyott teszthalmazon (gate)")
    s.add_argument("--run", required=True)
    s.add_argument("--tidy", default="data/tidy")
    s.add_argument("--min-accuracy", type=float, default=0.90)

    s = sub.add_parser("label", help="LLM-tanár címkézés (lm15, mentett login)")
    s.add_argument("--out", default="data/labels/teacher.jsonl")
    s.add_argument("--model", default=None, help="lm15 modell-id (alap: kimi-code)")
    s.add_argument("--start", type=int, default=4, help="kezdő párhuzamosság")
    s.add_argument("--limit", type=int, default=None, help="próba: csak N sor")

    s = sub.add_parser("generate", help="szintetikus ticketek gyártása (gyenge kategóriák)")
    s.add_argument("--out", default="data/labels/generated_v2.jsonl")
    s.add_argument("--handchecked", default="data/labels/handchecked_test.jsonl")
    s.add_argument("--per-subtopic", type=int, default=5)
    s.add_argument("--n-per-call", type=int, default=5)
    s.add_argument("--seed", type=int, default=0)

    s = sub.add_parser("confusion", help="konfúziós riport a fagyott teszten")
    s.add_argument("--run", required=True)
    s.add_argument("--out", default="runs/003-confusion")

    s = sub.add_parser("testconflicts", help="teszthalmaz duplikátum-konfliktusai")
    s.add_argument("--test", default="data/labels/handchecked_test.jsonl")
    s.add_argument("--out", default="runs/004-conflicts")
    s.add_argument("--decisions", default="data/labels/testset_decisions.csv")
    s.add_argument("--exit-code", action="store_true",
                   help="0 ha nincs konfliktus, 1 ha van (SC-001 gate)")

    s = sub.add_parser("predict", help="egy ticket osztályozása")
    s.add_argument("--run", required=True)
    s.add_argument("text")

    s = sub.add_parser("run", help="teljes lánc: tidy -> train -> eval (US2)")
    s.add_argument("--name", default="run")
    s.add_argument("--seed", type=int, default=0)

    args = p.parse_args(argv)

    import polars as pl

    if args.cmd == "tidy":
        from triage.data import tidy_and_split
        train, test = tidy_and_split(args.raw, args.tidy, args.tasks, seed=args.seed)
        print(f"tidy kész: {len(train)} train / {len(test)} test -> {args.tidy}")
        return 0

    if args.cmd == "train":
        from triage.train import train_run
        train_df = pl.read_parquet(Path(args.tidy) / "train.parquet")
        test_df = pl.read_parquet(Path(args.tidy) / "test.parquet")
        config = train_run(train_df, test_df, args.run, seed=args.seed,
                           epochs_override=args.epochs)
        print(f"train kész: {config['epochs']} epoch, {config['train_seconds']} s")
        return 0

    if args.cmd == "eval":
        from triage.evaluate import check_threshold, evaluate_run
        test_df = pl.read_parquet(Path(args.tidy) / "test.parquet")
        m = evaluate_run(args.run, test_df, min_accuracy=args.min_accuracy)
        print(f"accuracy: {m['accuracy']:.1%} (n={m['n_test']})")
        for label, c in sorted(m["per_category"].items()):
            print(f"  {label:22s} {c['accuracy']:.1%} (n={c['n']})")
        return check_threshold(m, args.min_accuracy)

    if args.cmd == "label":
        import asyncio
        import polars as pl
        from triage.label import DEFAULT_MODEL, label_all
        texts_path = Path("data/tidy/texts.parquet")
        if not texts_path.exists():
            from triage.data import build_texts
            texts_path.parent.mkdir(parents=True, exist_ok=True)
            build_texts("data/raw").write_parquet(texts_path)
        df = pl.read_parquet(texts_path)
        rows = df.select("id", "text").to_dicts()
        if args.limit:
            rows = rows[: args.limit]
        stats = asyncio.run(label_all(rows, args.out,
                                      model=args.model or DEFAULT_MODEL,
                                      start=args.start))
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        ok = stats["valid_rate"] is not None and stats["valid_rate"] >= 0.99
        print(f"SC-005 (>=99% érvényes): {'TELJESÜL' if ok else 'NEM TELJESÜL'}")
        return 0 if ok else 1

    if args.cmd == "generate":
        import asyncio
        from triage.generate import generate_all
        stats = asyncio.run(generate_all(args.out, args.handchecked,
                                         per_subtopic=args.per_subtopic,
                                         n_per_call=args.n_per_call,
                                         seed=args.seed))
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "confusion":
        import polars as pl
        from triage.confusion import confusion_report, top_confusions
        from triage.evaluate import predict_texts
        test_df = pl.read_parquet("data/tidy/test.parquet")
        labels = sorted(test_df["label"].unique().to_list())
        y_pred = predict_texts(Path(args.run) / "model", test_df["text"].to_list())
        rep = confusion_report(test_df["id"].to_list(), test_df["text"].to_list(),
                               test_df["label"].to_list(), y_pred, labels,
                               out_dir=args.out)
        print(f"accuracy: {rep['accuracy']:.1%} (n={rep['n_test']}), "
              f"tévesztve: {len(rep['misclassified'])}")
        for c in top_confusions(rep):
            print(f"  {c['true']} -> {c['pred']}: {c['n']} sor")
        return 0

    if args.cmd == "testconflicts":
        from triage.testset import find_conflicts, write_decisions_template
        groups = find_conflicts(args.test)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "report.json").write_text(
            json.dumps({"test_file": args.test, "n_conflicts": len(groups),
                        "conflicts": groups}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        if groups:
            write_decisions_template(groups, args.decisions)
        print(f"konfliktusos csoportok: {len(groups)} -> {args.out}/report.json")
        for g in groups:
            print(f"  {g['count']}x | {g['labels']} | {g['texts'][0][:70]}")
        return (1 if groups else 0) if args.exit_code else 0

    if args.cmd == "predict":
        from triage.predict import predict_one
        r = predict_one(Path(args.run) / "model", args.text)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["ok"] else 2

    if args.cmd == "run":
        from triage.data import tidy_and_split
        from triage.evaluate import evaluate_run
        from triage.train import train_run
        t0 = time.monotonic()
        run_dir = Path("runs") / f"{args.name}-s{args.seed}"
        train_df, test_df = tidy_and_split("data/raw", "data/tidy", "data/tasks",
                                           seed=0)  # a split seed mindig 0 (FR-002)
        train_run(train_df, test_df, run_dir, seed=args.seed)
        m = evaluate_run(run_dir, test_df)
        total = time.monotonic() - t0
        summary = {"run": str(run_dir), "seed": args.seed,
                   "accuracy": m["accuracy"], "total_seconds": round(total, 1)}
        (run_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
