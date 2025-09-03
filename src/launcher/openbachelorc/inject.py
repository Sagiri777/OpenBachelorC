import os
import time
import subprocess
import json
import signal
import sys

import frida
import requests

from .const import PACKAGE_NAME
from .config import config
from .adb import start_gadget

SCRIPT_DIRPATH = "rel/"

JAVA_SCRIPT_FILEPATH = os.path.join(SCRIPT_DIRPATH, "java.js")
NATIVE_SCRIPT_FILEPATH = os.path.join(SCRIPT_DIRPATH, "native.js")
EXTRA_SCRIPT_FILEPATH = os.path.join(SCRIPT_DIRPATH, "extra.js")
TRAINER_SCRIPT_FILEPATH = os.path.join(SCRIPT_DIRPATH, "trainer.js")

# Frida server配置
FRIDA_SERVER_PATH = "/data/local/tmp/florida-17.2.15"
FRIDA_SERVER_NAME = "florida-17.2.15"
FRIDA_PORT = "27042"  # 使用frida-server实际监听的端口
ENABLE_PORT_FORWARDING = True


def run_adb_command(command, capture_output=True):
    """执行adb命令"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(command, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        print(f"执行命令失败: {command}, 错误: {e}")
        return False, "", str(e)


def check_frida_server_status():
    """检查frida-server状态"""
    success, pid_output, _ = run_adb_command(f"adb shell pidof {FRIDA_SERVER_NAME}")
    
    if success and pid_output:
        print(f"✓ 检测到已运行的frida-server，PID: {pid_output}")
        
        # 检查端口
        success, port_info, _ = run_adb_command(f"adb shell netstat -tulnp | grep {pid_output}")
        if success and port_info:
            print(f"✓ frida-server监听端口信息: {port_info}")
            
            # 检查是否在正确端口监听
            if "27042" in port_info:
                print("✓ frida-server正在正确的端口27042上监听")
                return True, "27042"
            else:
                # 尝试从端口信息中提取端口号
                import re
                port_match = re.search(r':(\d+)', port_info)
                if port_match:
                    actual_port = port_match.group(1)
                    print(f"✓ frida-server在端口{actual_port}上监听")
                    return True, actual_port
        
        print("? 无法确定frida-server监听端口")
        return True, "27042"  # 默认使用27042
    
    return False, None


def setup_frida_server():
    """设置并启动frida-server"""
    # 首先检查是否已有frida-server运行
    is_running, port = check_frida_server_status()
    
    if is_running:
        print("frida-server已在运行，跳过启动步骤")
        global FRIDA_PORT
        FRIDA_PORT = port
        return setup_port_forwarding()
    
    print("启动 frida-server...")
    
    # 授予执行权限
    success, _, _ = run_adb_command(f"adb shell chmod 755 {FRIDA_SERVER_PATH}")
    if not success:
        print("授予frida-server执行权限失败")
        return False
    
    # 杀掉可能已存在的frida-server进程
    print("清理可能存在的旧进程...")
    run_adb_command(f"adb shell pkill -f {FRIDA_SERVER_NAME}")
    
    # 启动frida-server
    print("正在启动 frida-server...")
    success, _, _ = run_adb_command(f'adb shell "nohup {FRIDA_SERVER_PATH} > /dev/null 2>&1 &"', capture_output=False)
    
    # 等待服务器启动
    time.sleep(2)
    
    # 检查frida-server是否在运行
    print("检查 frida-server 是否运行...")
    is_running, port = check_frida_server_status()
    
    if is_running:
        FRIDA_PORT = port
        # 设置端口转发
        if ENABLE_PORT_FORWARDING:
            return setup_port_forwarding()
        else:
            print("端口转发已禁用")
            return True
    else:
        print("✗ frida-server 启动失败")
        return False


def setup_port_forwarding():
    """设置端口转发"""
    print(f"设置端口转发: 本地端口{FRIDA_PORT} -> 设备端口{FRIDA_PORT}")
    success, _, _ = run_adb_command(f"adb forward tcp:{FRIDA_PORT} tcp:{FRIDA_PORT}")
    
    if not success:
        print("✗ 端口转发设置失败")
        return False
    
    # 测试端口转发连接
    print("测试端口转发连接...")
    
    # 检查frida-ps命令是否可用
    try:
        result = subprocess.run(["frida-ps", "-U"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ 端口转发设置成功，可以正常访问设备上的frida-server")
            return True
        else:
            print("✗ 端口转发设置失败，无法通过转发访问frida-server")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # 如果没有frida-ps命令，使用adb forward --list检查端口转发状态
        success, forward_status, _ = run_adb_command(f"adb forward --list | grep tcp:{FRIDA_PORT}")
        if success and forward_status:
            print(f"✓ 端口转发已设置: {forward_status}")
            print("提示: 可以使用frida-ps -U等命令测试连接")
            return True
        else:
            print("✗ 端口转发设置可能失败")
            return False


def start_target_app():
    """启动目标应用"""
    print(f"启动{PACKAGE_NAME}应用...")
    
    # 启动应用
    success, _, _ = run_adb_command(
        f"adb shell am start -n {PACKAGE_NAME}/com.u8.sdk.U8UnityContext "
        f"-a android.intent.action.MAIN -c android.intent.category.LAUNCHER"
    )
    
    if not success:
        print(f"✗ 启动{PACKAGE_NAME}失败")
        return None
    
    # 等待应用启动
    time.sleep(5)
    
    # 获取应用PID
    success, pid_output, _ = run_adb_command(f"adb shell pidof {PACKAGE_NAME}")
    
    if success and pid_output:
        print(f"✓ {PACKAGE_NAME} 已启动，PID: {pid_output}")
        return int(pid_output)
    else:
        print(f"✗ 未能获取{PACKAGE_NAME}的PID，应用可能启动失败")
        return None


def test_remote_port():
    try:
        requests.get(
            "http://127.0.0.1:27042",
            proxies={"http": "", "https": ""},
            timeout=5,
        )

        return True
    except Exception:
        return False


def handle_script_message(script_filepath, message, data):
    print(f"message [{os.path.basename(script_filepath)}]:", message)


def load_script(device, pid, script_filepath, script_config, is_emulated_realm=False):
    if is_emulated_realm:
        session = device.attach(pid, realm="emulated")
    else:
        session = device.attach(pid)

    with open(script_filepath, encoding="utf-8") as f:
        script_str = f.read()
    script = session.create_script(script_str)
    script.on(
        "message",
        lambda message, data: handle_script_message(script_filepath, message, data),
    )
    script.load()

    for k, v in script_config.items():
        script.post({"type": "conf", "k": k, "v": v})

    return script


class Game:
    def __init__(
        self, device, pid, java_script, native_script, extra_script, trainer_script
    ):
        self.device = device
        self.pid = pid
        self.java_script = java_script
        self.native_script = native_script
        self.extra_script = extra_script
        self.trainer_script = trainer_script

    def exec_trainer_command(self, trainer_command_name):
        if self.trainer_script is not None:
            self.trainer_script.post(
                {"type": "conf", "k": "invoke", "v": trainer_command_name}
            )
        else:
            print("err: trainer is disabled")


def start_game(emulator_id):
    """启动游戏并注入脚本"""
    
    # 检查并设置frida-server（如果需要的话）
    if not setup_frida_server():
        print("frida-server设置失败，尝试直接连接...")
    
    print("frida-server 检查完成")
    
    try:
        # 连接到远程设备
        device = frida.get_remote_device()
        print("✓ 成功连接到frida设备")
    except Exception as e:
        print(f"✗ 连接frida设备失败: {e}")
        # 尝试使用USB连接
        try:
            device = frida.get_usb_device()
            print("✓ 使用USB连接到frida设备")
        except Exception as e2:
            print(f"✗ USB连接也失败: {e2}")
            return None

    pid = None
    
    if config["use_gadget"]:
        pid = "Gadget"
        start_gadget(emulator_id)

        print("等待gadget连接...")
        for i in range(100):
            if test_remote_port():
                print("✓ Gadget连接成功")
                break
            else:
                time.sleep(0.1)
        else:
            print("✗ Gadget连接超时")
            return None
    else:
        # 首先尝试attach到已运行的应用
        try:
            existing_pid = None
            success, pid_output, _ = run_adb_command(f"adb shell pidof {PACKAGE_NAME}")
            if success and pid_output:
                existing_pid = int(pid_output)
                print(f"检测到已运行的{PACKAGE_NAME}，PID: {existing_pid}")
                pid = existing_pid
            else:
                # 启动目标应用
                app_pid = start_target_app()
                if app_pid is None:
                    print("启动目标应用失败，尝试spawn方式")
                    try:
                        pid = device.spawn(PACKAGE_NAME)
                        print(f"✓ 使用spawn启动应用，PID: {pid}")
                    except Exception as e:
                        print(f"✗ spawn启动应用失败: {e}")
                        return None
                else:
                    pid = app_pid
        except Exception as e:
            print(f"获取应用PID失败: {e}")
            return None

    host = config["host"]
    port = config["port"]
    proxy_url = f"http://{host}:{port}"

    is_emulated_realm = config["use_emulated_realm"]

    try:
        print("加载Java脚本...")
        java_script = load_script(
            device,
            pid,
            JAVA_SCRIPT_FILEPATH,
            {"proxy_url": proxy_url, "no_proxy": config["no_proxy"]},
        )
        print("✓ Java脚本加载成功")

        print("加载Native脚本...")
        native_script = load_script(
            device,
            pid,
            NATIVE_SCRIPT_FILEPATH,
            {"proxy_url": proxy_url, "no_proxy": config["no_proxy"]},
            is_emulated_realm=is_emulated_realm,
        )
        print("✓ Native脚本加载成功")

        extra_script = None
        if config["enable_extra"]:
            print("加载Extra脚本...")
            extra_script = load_script(
                device,
                pid,
                EXTRA_SCRIPT_FILEPATH,
                config["extra_config"],
                is_emulated_realm=is_emulated_realm,
            )
            print("✓ Extra脚本加载成功")

        trainer_script = None
        if config["enable_trainer"]:
            print("加载Trainer脚本...")
            trainer_script = load_script(
                device,
                pid,
                TRAINER_SCRIPT_FILEPATH,
                config["trainer_config"],
                is_emulated_realm=is_emulated_realm,
            )
            print("✓ Trainer脚本加载成功")

        # 如果是spawn方式启动，需要resume进程
        if not config["use_gadget"] and isinstance(pid, int) and pid not in [p for p in device.enumerate_processes() if p.name == PACKAGE_NAME]:
            try:
                device.resume(pid)
                print("✓ 进程已恢复运行")
            except Exception as e:
                print(f"恢复进程失败，可能进程已在运行: {e}")

        game = Game(device, pid, java_script, native_script, extra_script, trainer_script)
        print("✓ 游戏注入完成")
        
        return game
        
    except Exception as e:
        print(f"✗ 脚本加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def cleanup():
    """清理资源"""
    print("清理端口转发...")
    run_adb_command(f"adb forward --remove tcp:{FRIDA_PORT}")


# 注册清理函数
def signal_handler(sig, frame):
    print("\n收到中断信号，正在清理...")
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)