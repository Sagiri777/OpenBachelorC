#!/bin/bash

# 设置frida-server路径
FRIDA_SERVER_PATH="/data/local/tmp/florida-17.2.15"
FRIDA_SERVER_NAME="florida-17.2.15"

# 添加自定义frida端口变量
FRIDA_PORT="9443"

# 添加端口转发控制变量，设置为true时启用端口转发
ENABLE_PORT_FORWARDING=true

echo "启动 frida-server..."

# 授予执行权限
adb shell chmod 755 $FRIDA_SERVER_PATH

# 杀掉可能已存在的frida-server进程
echo "清理可能存在的旧进程..."
adb shell pkill -f $FRIDA_SERVER_NAME

# 启动frida-server
echo "正在启动 frida-server..."
adb shell "nohup $FRIDA_SERVER_PATH > /dev/null 2>&1 &"

# 等待服务器启动
sleep 2

# 检查frida-server是否在运行
echo "检查 frida-server 是否运行..."
FRIDA_PID=$(adb shell pidof $FRIDA_SERVER_NAME)

if [ -n "$FRIDA_PID" ]; then
    echo "✓ frida-server 已成功启动，PID: $FRIDA_PID"
    
    # 检查监听的端口
    echo "检查 frida-server 监听的端口..."
    PORT_INFO=$(adb shell netstat -tulnp | grep $FRIDA_PID)
    
    if [ -n "$PORT_INFO" ]; then
        echo "✓ frida-server 正在监听以下端口:"
        echo "$PORT_INFO"
    else
        # 如果通过PID查不到端口信息，尝试查找frida相关端口
        PORT_INFO=$(adb shell netstat -tulnp | grep frida)
        if [ -n "$PORT_INFO" ]; then
            echo "✓ 检测到 frida 相关端口:"
            echo "$PORT_INFO"
        else
            echo "? 未检测到明确的端口监听信息"
        fi
    fi
    
    # 根据变量控制是否进行端口转发
    if [ "$ENABLE_PORT_FORWARDING" = true ]; then
        echo "设置端口转发: 本地端口$FRIDA_PORT -> 设备端口$FRIDA_PORT"
        adb forward tcp:$FRIDA_PORT tcp:$FRIDA_PORT
        
        # 运行一个小命令检测是否可以通过转发访问设备上的fridaserver
        echo "测试端口转发连接..."
        # 使用frida-ps命令测试连接，-U表示通过USB连接（经过端口转发）
        if command -v frida-ps > /dev/null; then
            if frida-ps -U > /dev/null 2>&1; then
                echo "✓ 端口转发设置成功，可以正常访问设备上的frida-server"
            else
                echo "✗ 端口转发设置失败，无法通过转发访问frida-server"
            fi
        else
            # 如果没有frida-ps命令，使用adb forward --list检查端口转发状态
            FORWARD_STATUS=$(adb forward --list | grep tcp:$FRIDA_PORT)
            if [ -n "$FORWARD_STATUS" ]; then
                echo "✓ 端口转发已设置: $FORWARD_STATUS"
                echo "提示: 可以使用frida-ps -U等命令测试连接"
            else
                echo "✗ 端口转发设置可能失败"
            fi
        fi
        
        # 测试阶段：启动com.hypergryph.arknights并获取pid
        echo "测试阶段：启动com.hypergryph.arknights应用..."
        adb shell am start -n com.hypergryph.arknights/com.u8.sdk.U8UnityContext -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
        
        # 等待应用启动
        sleep 5
        
        # 获取应用PID
        ARKNIGHTS_PID=$(adb shell pidof com.hypergryph.arknights)
        if [ -n "$ARKNIGHTS_PID" ]; then
            echo "✓ com.hypergryph.arknights 已启动，PID: $ARKNIGHTS_PID"
        else
            echo "✗ 未能获取com.hypergryph.arknights的PID，应用可能启动失败"
        fi
    else
        echo "端口转发已禁用"
    fi
else
    echo "✗ frida-server 启动失败"
    exit 1
fi

echo "frida-server 启动检查完成"