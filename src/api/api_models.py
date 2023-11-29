from typing import List


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