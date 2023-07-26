import requests
import json
# 定义本机的SD网址
url = "http://127.0.0.1:7860"

def ListModel():
    ex_list_model_url = url + "/sdapi/v1/sd-models"
    resp = requests.get(url=ex_list_model_url).json()
    print(resp)
    return resp

data = ListModel()
for i in data:
    print(i['model_name'])
    
def ListCN():
    cn_url = url + "/controlnet/control_types"
    CN_list = requests.get(url=cn_url).json()
    print(CN_list)
    return CN_list
data = ListCN()
print(data)