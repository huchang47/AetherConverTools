import easyocr  
import os  
import pyautogui   
import subprocess   
import time  
  
# 定义需要处理的图像文件路径  
folder_path = os.path.dirname(os.getcwd())  
  
# 定义点击RunAll按钮函数  
def click_Btn(Btn_txt): 
    time.sleep(2)  
    # 进行屏幕截图  
    screenshot = pyautogui.screenshot()   
    screenshot.save('screenshot.png')  
    image_path = os.path.join(folder_path,'bin', 'screenshot.png')  
  
    # 读取图像文件  
    ocrer = easyocr.Reader(['en'])  
    result = ocrer.readtext(image_path)  
  
    # 寻找对应文字按钮进行点击  
    for match in result:    
        txt = match[1]  
        print(txt)  
        if txt == Btn_txt:    
            pos = match[0]    
            posx = pos[0]    
            pyautogui.click(posx[0] + 10, posx[1] + 10) 
            break
    else:    
        print("屏幕中没有满足条件的按钮")   
  
# 输入Ebs文件路径  
ebs_path = input('请输入Ebs文件路径：')  
# 轮询目录内所有的ebs后缀名文件  
for file in os.listdir(ebs_path):  
    if file.endswith('.ebs'):  
        ebs_file = os.path.join(ebs_path, file)
        subprocess.Popen(['start', '', ebs_file], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)  
        click_Btn("Run All") 
        print("按下任意键以继续...")  
        input()  
        print("继续执行程序") 