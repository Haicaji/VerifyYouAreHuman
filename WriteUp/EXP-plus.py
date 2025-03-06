# 增加绕过检测
import requests
import re
import time
import random

# 目标URL
TARGET_URL = "http://127.0.0.1"

def extract_numbers(question):
    """从题目中提取两个数字"""
    match = re.search(r"(\d+)\s*x\s*(\d+)", question)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError(f"无法从题目中提取数字: {question}")

def main():
    print("[+] 开始利用自动计算获取flag（绕过反爬版本）...")
    
    # 创建会话以保持cookie
    session = requests.Session()
    
    # 设置浏览器like的请求头
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    session.headers.update(browser_headers)
    
    # 步骤1: 首先访问主页，增加真实性
    print("[+] 访问主页增加真实性...")
    index_response = session.get(f"{TARGET_URL}/")
    time.sleep(random.uniform(0.8, 1.5))  # 模拟真实用户的浏览间隔
    
    # 步骤2: 访问验证页面，获取题目
    print("[+] 访问验证页面...")
    verify_url = f"{TARGET_URL}/complex-verify.html"
    response = session.get(verify_url)
    
    # 增加额外请求头（包括Referer）
    session.headers.update({
        'Referer': verify_url,
    })
    
    # 随机延时，模拟人类用户思考时间
    time.sleep(random.uniform(0.8, 1.2))
    
    # 步骤3: 从cookie中获取题目
    math_question = session.cookies.get('math_question')
    if not math_question:
        print("[-] 无法获取题目，可能是服务器拒绝了请求")
        return
    
    print(f"[+] 获取到的题目: {math_question}")
    
    # 步骤4: 解析题目并计算答案
    try:
        num1, num2 = extract_numbers(math_question)
        answer = num1 * num2
        print(f"[+] 解析题目: {math_question}")
        print(f"[+] 计算答案: {num1} × {num2} = {answer}")
    except ValueError as e:
        print(f"[-] 题目解析失败: {e}")
        return
    
    # 模拟人类计算时间（不会太快，保证通过反爬的请求间隔检测）
    calculation_time = random.uniform(1.5, 3.0)
    print(f"[+] 模拟计算时间: {calculation_time:.2f}秒...")
    time.sleep(calculation_time)
    
    # 步骤5: 提交答案（带上正确的Content-Type和Referer等请求头）
    print("[+] 提交答案...")
    
    # 对于JSON请求额外设置Content-Type
    json_headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',  # 模拟AJAX请求
    }
    session.headers.update(json_headers)
    
    start_time = time.time()
    response = session.post(
        f"{TARGET_URL}/api/verify", 
        json={"answer": answer}
    )
    
    elapsed = time.time() - start_time
    print(f"[+] 响应时间: {elapsed:.2f}秒")
    
    # 步骤6: 解析响应获取flag
    try:
        result = response.json()
        print(f"[+] 服务器响应状态码: {response.status_code}")
        print(f"[+] 服务器响应: {result}")
        
        if response.status_code == 200 and 'flag' in result:
            print(f"\n[+] 成功获取flag: {result['flag']}")
        else:
            print(f"[-] 未能获取flag: {result.get('message', '未知错误')}")
            
            # 如果服务器提示答案错误，可能需要尝试获取新题目
            if '再给你一次机会' in result.get('message', ''):
                print("[+] 服务器生成了新题目，正在重试...")
                new_question = result.get('new_question')
                if new_question:
                    print(f"[+] 新题目: {new_question}")
                    # 这里可以递归调用main或者写循环来处理新题目
        
    except Exception as e:
        print(f"[-] 解析响应失败: {e}")
        print(f"[-] 原始响应内容: {response.text}")

if __name__ == "__main__":
    main()
