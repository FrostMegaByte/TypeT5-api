from .utils import *
from spot.type_env import AnnotInfo, collect_user_annotations
from .type_check import MypyFeedback, PythonType, parse_type_str
from .type_env import apply_annotations, collect_user_annotations


@dataclass
class TokenizedSrc:
    """A src file with certain type annotations masked out."""

    file: Path
    repo: Path
    types: list[PythonType]
    types_pos: list[int]  # the position of the types in tokenized_code.
    types_str: list[str]
    types_tks: list[list[int]]
    types_info: list[AnnotInfo]
    main_code: str
    tokenized_code: list[int]  # with certain types masked out
    preamble_code: str
    tokenized_preamble: list[int]
    prev_types: dict[int, PythonType] | None = None  # previously predicted types
    inlined_spans: dict[int, slice] | None = None  # the spans of inlined previous types
    feedbacks: list[MypyFeedback] | None = None

    @staticmethod
    def parse(
        code: str,
        file: Path,
        repo: Path,
        args: "PreprocessArgs | None" = None,
    ) -> "TokenizedSrc":
        if args is None:
            args = PreprocessArgs()
        d = preprocess_code(code, args)
        d["file"] = file
        d["repo"] = repo
        d["is_label"] = None
        return dict_to_tokenized_src(d)

    def __str__(self):
        segs = [
            "========TokenizedSrc========",
            f"file:{self.file}",
            f"repo:{self.repo}",
            "--------Preamble--------",
            self.preamble_code,
            "--------Main Code--------",
            self.main_code,
            "========End of TokenizedSrc========",
        ]
        return "\n".join(segs)

    def inline_prev_predictions(
        self, as_comment: bool, prev_types: dict[int, PythonType] | None = None
    ) -> "TokenizedSrc":
        "Inine the previous predictions into the code, either directly or as comments."
        if prev_types is None:
            prev_types = self.prev_types
        assert isinstance(prev_types, dict), f"prev_types has type: {type(prev_types)}"
        assert len(prev_types) > 0

        types_pos = list[int]()
        tokenized_code = list[int]()
        tokenizer = DefaultTokenizer
        mask_id = tokenizer.mask_token_id
        comment_start = tokenizer.encode("/* ", add_special_tokens=False)
        comment_end = tokenizer.encode(" */", add_special_tokens=False)

        inlined_spans = dict[int, slice]()

        i_types = 0
        for tk in self.tokenized_code:
            tokenized_code.append(tk)
            if tk == mask_id:
                span_start = len(tokenized_code)
                types_pos.append(span_start - 1)

                if i_types in prev_types:
                    to_insert = tokenizer.encode(
                        str(prev_types[i_types]), add_special_tokens=False
                    )
                    if as_comment:
                        to_insert = comment_start + to_insert + comment_end
                    tokenized_code.extend(to_insert)
                    span_end = len(tokenized_code)
                    inlined_spans[i_types] = slice(span_start, span_end)
                    assert_eq(tokenized_code[span_start:span_end], to_insert)
                i_types += 1
        assert_eq(i_types, len(self.types))
        assert prev_types.keys() == inlined_spans.keys()

        return TokenizedSrc(
            file=self.file,
            repo=self.repo,
            types=self.types,
            types_pos=types_pos,
            types_str=self.types_str,
            types_tks=self.types_tks,
            types_info=self.types_info,
            main_code=self.main_code,
            tokenized_code=tokenized_code,
            preamble_code=self.preamble_code,
            tokenized_preamble=self.tokenized_preamble,
            prev_types=prev_types,
            inlined_spans=inlined_spans,
            feedbacks=self.feedbacks,
        )

    def print_code(self, max_lines: int = 50):
        "Print out the (decoded) token sequence"
        code = decode_tokens(self.tokenized_code)
        print_limited(code, max_lines)

    @staticmethod
    def inline_predictions(
        src: "TokenizedSrc",
        as_comment: bool,
        prev_types: dict[int, PythonType] | None = None,
    ):
        return src.inline_prev_predictions(as_comment=as_comment, prev_types=prev_types)


@dataclass
class PreprocessArgs:
    imports_in_preamble: bool = True
    drop_comments: bool = True


def preprocess_code(code: str, args: PreprocessArgs) -> dict:
    """Preprocess the Python code to carve out all the type annotations. The original
    code is split into sequences at the type annotations."""
    m = cst.parse_module(code)
    preamble_segs = list[str]()

    if args.drop_comments:
        m = remove_comments(m)
    if args.imports_in_preamble:
        m, imports = remove_imports(m)
        imports_part = cst.Module([cst.SimpleStatementLine([s]) for s in imports])
        preamble_segs.append(imports_part.code)

    cst_code = m.code
    annots_info, types = collect_user_annotations(m)
    types_str = [
        m.code_for_node(not_none(info.annot).annotation) for info in annots_info
    ]
    mask_annot = cst.Annotation(cst.Name(SpecialNames.TypeMask))
    replaces = dict()
    for info in annots_info:
        replaces[info.path] = mask_annot
    new_code = apply_annotations(m, replaces).code
    code_segs = new_code.split(SpecialNames.TypeMask)

    assert (
        len(code_segs) == len(types) + 1
    ), f"{len(code_segs)} != {len(types) + 1}. replaces: {replaces}\ncode: {new_code}"
    return {
        "preamble": "".join(preamble_segs),
        "code_segs": code_segs,
        "types": types,
        "types_str": types_str,
        "annots_info": annots_info,
        "cst_code": cst_code,
        "prev_types": None,
    }


def dict_to_tokenized_src(d: dict) -> TokenizedSrc:
    tkn = DefaultTokenizer

    r = TokenizedSrc(
        file=d["file"],
        repo=d["repo"],
        main_code=d["cst_code"],
        tokenized_code=list[int](),
        preamble_code=d["preamble"],
        tokenized_preamble=tkn.encode(d["preamble"], add_special_tokens=False),
        types=list[PythonType](),
        types_pos=list[int](),
        types_str=list[str](),
        types_info=list[AnnotInfo](),
        types_tks=list[list[int]](),
        prev_types=d["prev_types"],
    )

    match d:
        case {
            "code_segs": segs,
            "types": types,
            "types_str": types_str,
            "annots_info": annots_info,
            "is_label": is_label,
        }:
            assert len(segs) == len(types) + 1
        case _:
            raise ValueError(f"Invalid dict with keys: {d.keys()}")

    bos_id = not_none(tkn.bos_token_id)
    eos_id = not_none(tkn.eos_token_id)
    mask_id = not_none(tkn.mask_token_id)
    all_tks = r.tokenized_code
    all_tks.append(bos_id)
    for i in range(len(types)):
        all_tks.extend(tkn.encode(segs[i], add_special_tokens=False))
        if is_label is None or is_label[i]:
            r.types_pos.append(len(all_tks))
            r.types.append(types[i])
            r.types_tks.append(tkn.encode(str(types[i]), add_special_tokens=False))
            r.types_str.append(types_str[i])
            r.types_info.append(annots_info[i])
            all_tks.append(mask_id)
        else:
            all_tks.extend(tkn.encode(types_str[i], add_special_tokens=False))
    all_tks.extend(tkn.encode(segs[-1], add_special_tokens=False))
    all_tks.append(eos_id)

    return r


def feedbacks_to_tokenized_src(
    src: TokenizedSrc,
    current_code: str,
    feedbacks: list[MypyFeedback],
    patch_predictions: bool = False,
) -> TokenizedSrc:
    try:
        m = cst.parse_module(current_code)
    except Exception as e:
        raise RuntimeError(
            f"Failed to parse file: '{src.file}' with content:\n{current_code}"
        ) from e
    m_code = m.code
    assert (
        m_code.rstrip() == current_code.rstrip()
    ), f"String diffferences: {show_string_diff(current_code, m_code)}"
    current_annots, _ = collect_user_annotations(m)
    preds_map = dict[CodeRange, str]()
    types = list[PythonType]()
    prev_types = dict[int, PythonType]()
    types_str = list[str]()
    annots_info = list[AnnotInfo]()
    path2label_id = {info.path: i for i, info in enumerate(src.types_info)}

    for a in current_annots:
        if a.path in path2label_id:
            assert (r := a.annot_range) is not None
            assert (annot := a.annot) is not None
            prev_type = preds_map[r] = m.code_for_node(annot.annotation)
            li = path2label_id[a.path]
            prev_types[li] = parse_type_str(prev_type)
            types.append(src.types[li])
            types_str.append(src.types_str[li])
            annots_info.append(a)
    pos_to_msg = {f.position: f.message for f in feedbacks}
    new_code = patch_code_with_extra(
        current_code, preds_map, pos_to_msg, patch_predictions
    )
    code_segs = new_code.split(SpecialNames.TypeMask)
    assert (
        len(code_segs) == len(types) + 1
    ), f"{len(code_segs)} != {len(types)} + 1.\nNew Code:\n{new_code}"

    d = {
        "file": src.file,
        "repo": src.repo,
        "cst_code": new_code,
        "code_segs": code_segs,
        "types": types,
        "types_str": types_str,
        "annots_info": annots_info,
        "prev_types": prev_types,
        "is_label": None,
    }
    new_src = dict_to_tokenized_src(d)
    new_src.feedbacks = feedbacks
    return new_src


def patch_code_with_extra(
    code: str,
    predictions: dict[CodeRange, str],
    errors: dict[CodePosition, str],
    patch_predictions: bool,
) -> str:
    replaces = []
    # When the ranges overlap, we want to use the order: new_prediction -> prev_prediction -> errors
    for r, t in predictions.items():
        replaces.append((r, 1, SpecialNames.TypeMask))
        if patch_predictions:
            replaces.append((CodeRange(r.start, r.start), 2, f"/* {t} */"))

    for p, e in errors.items():
        replaces.append((CodeRange(p, p), 3, f"/* error: {e} */"))

    return replace_strs_by_pos(code, replaces)


def remove_comments(m: cst.Module) -> cst.Module:
    """Removes all comments and docstrings."""
    return m.visit(CommentRemover())


class CommentRemover(cst.CSTTransformer):
    """Removes comments and docstrings."""

    def leave_IndentedBlock(
        self, node: cst.IndentedBlock, updated: cst.IndentedBlock
    ) -> cst.IndentedBlock:
        new_body = type(updated.body)(  # type: ignore
            filter(lambda n: not CommentRemover.is_doc_string(n), updated.body)
        )
        if len(new_body) != len(updated.body):
            return updated.with_changes(body=new_body)
        else:
            return updated

    def leave_Module(self, node, updated):
        return self.leave_IndentedBlock(node, updated)

    def leave_EmptyLine(self, node: cst.EmptyLine, updated: cst.EmptyLine):
        if updated.comment is not None:
            return cst.RemoveFromParent()
        else:
            return updated

    def leave_TrailingWhitespace(self, node, updated: cst.TrailingWhitespace):
        if updated.comment is not None:
            return updated.with_changes(comment=None)
        else:
            return updated

    @staticmethod
    def is_doc_string(node: cst.BaseStatement) -> bool:
        match node:
            case cst.SimpleStatementLine(body=[cst.Expr(value=cst.SimpleString())]):
                return True
            case _:
                return False


def remove_imports(
    m: cst.Module,
) -> tuple[cst.Module, list[cst.Import | cst.ImportFrom]]:
    """Removes all top-level import statements and collect them into a list."""
    remover = ImportsRemover()
    m = m.visit(remover)
    return m, list(remover.import_stmts)


class ImportsRemover(cst.CSTTransformer):
    """Removes all top-level import statements and collect them into `self.import_stmts`."""

    def __init__(self):
        self.import_stmts = set[cst.Import | cst.ImportFrom]()

    def leave_Import(self, node: cst.Import, updated: cst.Import):
        self.import_stmts.add(updated)
        return cst.RemoveFromParent()

    def leave_ImportFrom(self, node: cst.ImportFrom, updated: cst.ImportFrom):
        self.import_stmts.add(updated)
        return cst.RemoveFromParent()

    def visit_FunctionDef(self, node):
        # stops traversal at inner levels.
        return False
