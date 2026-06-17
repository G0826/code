@echo off
cd /d "%~dp0"
echo.
echo  居民出行轨迹动画 - 本地服务器
echo  ================================
echo  浏览器打开: http://localhost:8080/travel_animation.html
echo  按 Ctrl+C 停止
echo.
python -m http.server 8080
