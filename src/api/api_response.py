import json
import re
from typing import List
import libcst as cst

from typet5.static_analysis import FunctionSignature


class Function:
    def __init__(self, name, q_name, params_p, ret_type_p):
        self.name = name
        self.q_name = q_name
        self.params_p = params_p
        self.ret_type_p = ret_type_p
        
    def to_dict(self):
        return {
            'name': self.name,
            'q_name': self.q_name,
            'params_p': self.params_p,
            'ret_type_p': self.ret_type_p,
        }

class Class:
    def __init__(self, name, q_name, funcs: List[Function]):
        self.name = name
        self.q_name = q_name
        self.funcs = funcs
        
    def to_dict(self):
        return {
            'name': self.name,
            'q_name': self.q_name,
            'funcs': [func.to_dict() for func in self.funcs],
        }

class APIResponse:
    def __init__(self, file_path, classes: List[Class], funcs: List[Function]):
        self.file_path = file_path
        self.response = {
            'classes': [cls.to_dict() for cls in classes],
            'funcs': [func.to_dict() for func in funcs]
        }
        
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'response': self.response,
        }
        
class API:
    def __init__(self, responses: List[APIResponse]):
        self.responses = responses
        
    def to_dict(self):
        return {
            'responses': [response.to_dict() for response in self.responses],
        }
        
def group_predictions_by_file(final_sigmap):
    file_predictions = {}
    for location, type_prediction in final_sigmap.items():
        if location.module in file_predictions:
            file_predictions[location.module][location] = type_prediction
        else:
            file_predictions[location.module] = { location: type_prediction }
    return file_predictions
        
        
def create_api_response(predictions_by_file, project_directory):
    api_responses = []
    for file in predictions_by_file:
        file_path = str(project_directory / (file.replace(".", "/") + ".py"))
        classes = {}
        funcs = []
        for location, type_prediction in predictions_by_file[file].items():
            if isinstance(type_prediction, FunctionSignature):
                params_p, ret_type_p = parse_function_signature(type_prediction)
                function = Function(location.path.split(".")[-1], location.path, params_p, ret_type_p)
                
                if type_prediction.in_class:
                    class_name = location.path.split(".")[-2]
                    full_class_name = location.path.rsplit('.', 1)[0]
                    if full_class_name in classes:
                        classes[full_class_name].funcs.append(function)
                    else:
                        classes[full_class_name] = Class(class_name, full_class_name, [function])
                else:
                    funcs.append(function)
        
        if len(classes) > 0 or len(funcs) > 0:
            api_responses.append(APIResponse(file_path, list(classes.values()), funcs))
    api = API(api_responses).to_dict()
    return json.dumps(api)

def node_to_code(node: cst.CSTNode):
    node_string = cst.Module([]).code_for_node(node)
    node_string = node_string.replace("\n", "")
    node_string = re.sub(r"\[\s+", "[", node_string)
    node_string = re.sub(r"\s+\]", "]", node_string)
    return node_string
            
def parse_function_signature(type_prediction):
    params_p = {}
    ret_type_p = []
    for param, annotation in type_prediction.params.items():
        params_p[param] = [[node_to_code(annotation.annotation), 1.0]]
    ret_type_p.append([node_to_code(type_prediction.returns.annotation), 1.])
    return params_p, ret_type_p