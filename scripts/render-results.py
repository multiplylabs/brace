"""Export the website's individual comparisons from the existing paper values."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    "ours": ("BRACE", "#C9521C", "o", "-"),
    "sonic": ("SONIC", "#227E83", "s", "-"),
    "heft": ("HEFT", "#3D4A53", "^", "-"),
    "twist2": ("TWIST2", "#8A959C", "D", "--"),
    "any2track": ("Any2Track", "#B4BEC4", "v", ":"),
}
COMPENSATION = [("tracking", 0), ("comp_10", 2), ("comp_25", 5),
                ("comp_50", 10), ("comp_75", 15), ("comp_100", 20)]
EXERTION = [(f"exert_{str(float(x)).replace('.', 'p')}", x) for x in (3, 4.5, 6, 7, 8, 9)]
METRICS = {
    "tracking": {"column": "mpjpe_g", "title": "Global tracking error", "unit": "mm",
                 "ylabel": "Global tracking error (mm)", "direction": "Lower is better.",
                 "limits": (0, 900), "ticks": (0, 300, 600, 900), "scale": 1},
    "success": {"column": "success", "title": "Success rate", "unit": "%",
                "ylabel": "Success rate (%)", "direction": "Higher is better.",
                "limits": (0, 100), "ticks": (0, 25, 50, 75, 100), "scale": 100},
    "force": {"column": "force_bias_N", "title": "Hand-force error", "unit": "N",
              "ylabel": "Hand-force error (N)", "direction": "Lower is better.",
              "limits": (0, 12), "ticks": (0, 4, 8, 12), "scale": 1},
}


def display_value(value, unit):
    digits = 0 if unit == "mm" else 1 if unit == "%" else 2
    return f"{value:.{digits}f}{'' if unit == '%' else ' '}{unit}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values", type=Path, default=ROOT / "data/results-values.csv")
    parser.add_argument("--font", type=Path, required=True, help="Barlow Medium TTF")
    args = parser.parse_args()
    rows = list(csv.DictReader(args.values.open()))
    lookup = {(r["dataset"], r["condition"], r["method"]): r for r in rows}
    assert len(lookup) == len(rows) == 240
    font_manager.fontManager.addfont(str(args.font))
    plt.rcParams.update({"font.family": font_manager.FontProperties(fname=args.font).get_name(),
                         "font.size": 14, "svg.fonttype": "path", "svg.hashsalt": "brace-results",
                         "axes.labelcolor": "#30415C", "text.color": "#30415C",
                         "xtick.color": "#53657E", "ytick.color": "#53657E"})
    image_dir = ROOT / "assets/img/results"
    image_dir.mkdir(parents=True, exist_ok=True)
    output = {"source_sha256": hashlib.sha256(args.values.read_bytes()).hexdigest(), "settings": {}}
    for mode in ("compensation", "exertion"):
        conditions = COMPENSATION if mode == "compensation" else EXERTION
        xs = [x for _, x in conditions]
        xlabel = "External load per hand (N)" if mode == "compensation" else "Commanded force per hand (N)"
        for ground in ("flat", "terrain"):
            setting = f"{mode}-{ground}"
            terrain = "Flat ground" if ground == "flat" else "Slopes of 4.6°–17.7°"
            title = f"Force {mode} · {'flat ground' if ground == 'flat' else 'sloped terrain'}"
            force = "0–20 N external load per hand" if mode == "compensation" else "3–9 N commanded force per hand"
            point = f"At {xs[-1]:g} N {'load' if mode == 'compensation' else 'command'} per hand"
            metrics = {}
            for name, metric in METRICS.items():
                if name == "force" and mode == "compensation":
                    continue
                curves = {}
                for method in METHODS:
                    curves[method] = []
                    for condition, _ in conditions:
                        values = [lookup[f"{dataset}_{ground}", condition, method][metric["column"]]
                                  for dataset in ("phuma", "bones")]
                        # Match the paper renderer's mean over available dataset values.
                        curves[method].append(mean(float(v) for v in values if v) * metric["scale"])
                assert all(metric["limits"][0] <= y <= metric["limits"][1]
                           for curve in curves.values() for y in curve)
                fig, ax = plt.subplots(figsize=(6, 4.7))
                fig.subplots_adjust(left=.15, right=.97, bottom=.18, top=.77)
                for method in reversed(METHODS):
                    label, color, marker, style = METHODS[method]
                    ax.plot(xs, curves[method], label=label, color=color, marker=marker,
                            linestyle=style, linewidth=2.6 if method == "ours" else 1.8,
                            markersize=6, markeredgewidth=.6, markeredgecolor="white")
                ax.set(xlabel=xlabel, ylabel=metric["ylabel"], ylim=metric["limits"],
                       xlim=(xs[0]-.025*(xs[-1]-xs[0]), xs[-1]+.025*(xs[-1]-xs[0])),
                       xticks=(0, 5, 10, 15, 20) if mode == "compensation" else (3, 4.5, 6, 7.5, 9),
                       yticks=metric["ticks"])
                ax.set_axisbelow(True)
                ax.grid(axis="y", color="#E5E8EB", linewidth=.8)
                ax.spines[["top", "right"]].set_visible(False)
                for side in ("left", "bottom"):
                    ax.spines[side].set_color("#CCD6E3")
                ax.tick_params(length=3)
                handles, labels = ax.get_legend_handles_labels()
                legend = fig.legend(handles[::-1], labels[::-1], loc="upper center", ncol=3,
                                    frameon=False, fontsize=13, columnspacing=1.2, handlelength=1.7)
                image = f"assets/img/results/{setting}-{name}.svg"
                metadata = {"Date": None, "Creator": "BRACE", "Title": f"{title}: {metric['title']}"}
                fig.savefig(ROOT / image, metadata=metadata)
                # A narrower canvas keeps the axis and legend text readable on phones.
                mobile_image = image.replace(".svg", "-mobile.svg")
                fig.set_size_inches(4.2, 4.4)
                fig.subplots_adjust(left=.19, right=.97, bottom=.18, top=.69)
                legend.remove()
                fig.legend(handles[::-1], labels[::-1], loc="upper center", ncol=2,
                           frameon=False, fontsize=13, columnspacing=1, handlelength=1.5)
                fig.savefig(ROOT / mobile_image, metadata=metadata)
                plt.close(fig)
                baselines = [m for m in METHODS if m != "ours"]
                choose = max if name == "success" else min
                best = choose(baselines, key=lambda m: curves[m][-1])
                metrics[name] = {"title": metric["title"], "direction": metric["direction"],
                                 "image": image, "mobile_image": mobile_image,
                                 "ours": display_value(curves["ours"][-1], metric["unit"]),
                                 "baseline": METHODS[best][0],
                                 "baseline_value": display_value(curves[best][-1], metric["unit"]),
                                 "alt": f"{metric['title']} for {title.lower()}, comparing BRACE, SONIC, HEFT, TWIST2 and Any2Track."}
            output["settings"][setting] = {"title": title, "condition": f"{terrain}; {force}.",
                                           "point": point, "metrics": metrics}
    target = ROOT / "assets/data/results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"Exported {sum(len(s['metrics']) for s in output['settings'].values())} individual comparisons.")


if __name__ == "__main__":
    main()
