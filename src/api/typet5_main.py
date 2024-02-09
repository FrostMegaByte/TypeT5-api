import os
from typing import *
import pickle

import torch
from api.api_response import create_api_response, group_predictions_by_file

from typet5.model import ModelWrapper
from typet5.train import PreprocessArgs
from typet5.utils import *
from typet5.function_decoding import (
    RolloutCtx,
    PreprocessArgs,
    DecodingOrders
)
from typet5.static_analysis import PythonProject

os.chdir(proj_root())

class TypeT5Model:
  def __init__(self):
    wrapper = ModelWrapper.load_from_hub("MrVPlusOne/TypeT5-v7")
    device = torch.device(f"cuda" if torch.cuda.is_available() else "cpu")
    wrapper.to(device)
    print("Model loaded")
    print("Running on device:", device)
    
    self.rctx = RolloutCtx(model=wrapper)
    self.pre_args = PreprocessArgs()
    self.decode_order = DecodingOrders.DoubleTraversal()
  
  async def run_model(self):
    project = PythonProject.parse_from_root(proj_root() / "data/code")
    rollout_cache_file = Path(__file__).parent / "cache/rollout_prediction.pkl"
    
    if os.path.exists(rollout_cache_file):
      with open(rollout_cache_file, 'rb') as f:
        rollout = pickle.load(f)
    else:
      rollout = await self.rctx.run_on_project(project, self.pre_args, self.decode_order)
      os.makedirs(Path(__file__).parent / "cache", exist_ok=True)
      with open(rollout_cache_file, 'wb+') as f:
        pickle.dump(rollout, f)
    
    predictions_by_file = group_predictions_by_file(rollout.final_sigmap)
    response = create_api_response(predictions_by_file)
    return response