@echo off  
chcp 65001 > nul  
call "./Aethervenv/Scripts/activate"
echo "以太虚拟环境启用成功"
cd bin
python Continue.py
pause