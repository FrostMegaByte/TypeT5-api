import html
import re
from typing import Sequence

import ipywidgets as widgets

from spot.data import ChunkedDataset, CtxArgs, PythonType
from spot.utils import *


def visualize_batch(
    dataset: ChunkedDataset,
    i: int,
    preds: list[list[PythonType]],
    tokenizer: TokenizerSPOT,
    ctx_args: CtxArgs,
) -> str:
    pred_types = preds[i]
    typpes_enc = [
        tokenizer.encode(str(t), add_special_tokens=False) for t in pred_types
    ]

    label_types = dataset.chunks_info[i].types
    code_tks = inline_predictions(dataset.data["input_ids"][i], typpes_enc, tokenizer)
    sep_1 = tokenizer.encode(
        "\n---------⬆context⬆---------\n", add_special_tokens=False
    )
    sep_2 = tokenizer.encode(
        "\n---------⬇context⬇---------\n", add_special_tokens=False
    )
    margin_left, _, margin_right = ctx_args.as_tuple()
    code_tks = (
        code_tks[:margin_left]
        + sep_1
        + code_tks[margin_left:-margin_right]
        + sep_2
        + code_tks[-margin_right:]
    )
    code_dec = tokenizer.decode(code_tks, skip_special_tokens=False)
    code_dec = code_inline_extra_ids(code_dec, label_types)
    src_ids = sorted(list(set(dataset.chunks_info[i].src_ids)))
    files = [dataset.files[i] for i in src_ids]
    return "".join(
        [
            "labels: ",
            str(label_types),
            "\n",
            "preds: ",
            str(pred_types),
            "\n",
            "files: ",
            str(files),
            "\n",
            "========================== Code =======================\n",
            code_dec,
            "\n",
        ]
    )


def inline_predictions(
    input_tks: Sequence[int],
    predictions: Sequence[Sequence[int]],
    tokenizer: TokenizerSPOT,
) -> list[int]:
    """Inline the model predictions into the input code and then decode"""
    out_tks = list[int]()
    extra_id = 0
    next_special = tokenizer.additional_special_tokens_ids[99 - extra_id]
    for tk in input_tks:
        out_tks.append(tk)
        if tk == next_special:
            out_tks.extend(predictions[extra_id])
            extra_id += 1
            next_special = tokenizer.additional_special_tokens_ids[99 - extra_id]
    assert extra_id == len(predictions), f"{extra_id} != {len(predictions)}"
    return out_tks


# def visualize_texts(contents: Sequence[str]):
#     assert len(contents) > 0

#     slider = widgets.IntSlider(min=0, max=len(contents) - 1, value=0)
#     panel = widgets.Output()

#     def update_panel(i: int):
#         panel.clear_output(wait=True)
#         with panel:
#             print(contents[i])

#     slider.observe(names="value", handler=lambda x: update_panel(x["new"]))
#     update_panel(0)

#     box_layout = widgets.Layout(overflow="scroll")
#     return widgets.VBox([slider, widgets.Box([panel], layout=box_layout)])


def visualize_sequence(contents: Sequence[str | widgets.Widget], max_height="500px"):
    assert len(contents) > 0

    slider = widgets.IntSlider(min=0, max=len(contents) - 1, value=0)
    slider_label = widgets.Label(value=f"({len(contents)} total)")

    def select(i: int):
        el = contents[i]
        if isinstance(el, str):
            print(el)
        else:
            display(el)

    out = widgets.interactive_output(select, {"i": slider})
    out.layout.height = max_height
    box_layout = widgets.Layout(overflow="scroll")
    return widgets.VBox(
        [
            widgets.HBox([slider, slider_label]),
            widgets.Box([out], layout=box_layout),
        ]
    )


def visualize_code_sequence(contents: Sequence[str]):
    els = [
        widgets.HTML(
            "<pre style='line-height: 1.2; padding: 10px; color: rgb(212,212,212); background-color: rgb(30,30,30); }'>"
            + colorize_code_html(html.escape(contents[i]))
            + "</pre>"
        )
        for i in range(len(contents))
    ]

    return visualize_sequence(els)


def colorize_code_html(code: str) -> str:
    "Highligh the special comments in the type checker-augmented python code."
    output = list[str]()
    in_comment = False
    for i in range(len(code)):
        c = code[i]
        prev = code[i - 1] if i > 0 else None
        next = code[i + 1] if i < len(code) - 1 else None
        if not in_comment and c == "/" and next == "*":
            output.append("<span style='color: rgb(106, 153, 85)'>")
            in_comment = True
        output.append(c)
        if in_comment and prev == "*" and c == "/":
            output.append("</span>")
            in_comment = False
    new_code = "".join(output)

    def replace(m: re.Match[str]):
        ml = re.match(r"&lt;label;([^;]+);label&gt;", m[0])
        assert ml is not None
        l = ml.group(1)
        return f"<span style='color: rgb(78, 201, 176)'>({l})</span>"

    return re.sub(r"(&lt;label;[^;]+;label&gt;)", replace, new_code)


def code_inline_extra_ids(code: str, preds: list):
    def replace(m: re.Match[str]):
        mi = re.match(r"<extra_id_(\d+)>", m[0])
        assert mi is not None
        id = int(mi.group(1))
        label = str(preds[id])
        return f"<label;{label};label>"

    return re.sub(r"(<extra_id_\d+>)", replace, code)
