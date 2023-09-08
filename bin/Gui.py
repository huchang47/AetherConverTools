import PySimpleGUI as sg

custom_font = ('宋体', 9) 
print(sg.theme_list())
sg.theme('TealMono')  
sg.set_options(font=custom_font)  

layout=[
    [sg.Text('欢迎使用以太AI视频转绘工具')],
    [sg.Text('视频工程目录：'),sg.InputText('本机任意文件夹地址',enable_events=True),sg.FolderBrowse('浏览')],
    [sg.Text('视频文件地址：'),sg.InputText('本机地址，不可使用网络地址',enable_events=True),sg.FileBrowse('浏览',file_types=('视频文件','.mp4'))],
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