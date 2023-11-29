import os
from typing import *

import torch

from typet5.model import ModelWrapper
from typet5.train import PreprocessArgs
from typet5.utils import *
from typet5.function_decoding import (
    RolloutCtx,
    PreprocessArgs,
    DecodingOrders
)
from typet5.static_analysis import FunctionSignature, PythonProject

os.chdir(proj_root())

class TypeT5Model:
  def __init__(self):
    wrapper = ModelWrapper.load_from_hub("MrVPlusOne/TypeT5-v7")
    device = torch.device(f"cuda" if torch.cuda.is_available() else "cpu")
    wrapper.to(device)
    print("Model loaded")
    
    self.rctx = RolloutCtx(model=wrapper)
    self.pre_args = PreprocessArgs()
    self.decode_order = DecodingOrders.DoubleTraversal()

  async def run_model(self) -> str:
    project = PythonProject.parse_from_root(proj_root() / "data/ex_repo")
    # rollout = await rctx.run_on_project(project, pre_args, decode_order)
    json = await self.rctx.run_on_project(project, self.pre_args, self.decode_order)
    return json