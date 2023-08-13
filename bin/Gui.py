import PySimpleGUI as sg

layout=[
    [sg.Text('欢迎使用以太AI视频转绘工具')],
    [sg.Text('视频工程目录：'),sg.InputText('本机任意文件夹地址',enable_events=True),sg.FolderBrowse('选择')],
    [sg.Text('视频文件地址：'),sg.InputText('本机地址，不可使用网络地址',enable_events=True),sg.FileBrowse('选择')],
    [sg.Checkbox('自定义项目步骤目录')],
]

windows = sg.Window('以太转绘工作流',layout)
while True:
    event,values=windows.read()
    if event==None:
        break
    if event in ['本机任意文件夹地址','本机地址，不可使用网络地址']:
        sg.Popup('牛逼')


windows.close