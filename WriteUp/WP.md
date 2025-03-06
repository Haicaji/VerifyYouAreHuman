# VerifyYouAreHuman 题解

## 题目分析

这道题主要是考察常见的请求头反爬虫手段的绕过

打开网站后，我们看到两个可选的验证路径：

1. **一键验证**（easy-verify.html）
2. **答题验证**（complex-verify.html）

通过分析网站代码，我们需要找出获取flag的正确方法。

## 解题思路

### 方法一：一键验证（陷阱路径）

首先尝试"一键验证"路径，页面显示一个类似reCAPTCHA的验证框。点击"我不是机器人"后，它会提示我们：

1. 按下Windows+R组合键
2. 按Ctrl+V粘贴内容
3. 按回车键

查看源代码，发现这是一个recaptcha人机验证的钓鱼网页。点击验证按钮后，会向剪贴板写入一个外部链接（微信公众号URL）。这并不是获取flag的正确路径。

### 方法二：答题验证（正确路径）

查看"答题验证"页面，系统会出一道三位数乘以三位数的算术题，并要求在5秒内计算出正确结果。

分析后端代码发现：

1. 服务器会通过多种方法检测请求是否来自真实浏览器：
   - 检查User-Agent
   - 验证必要的请求头（Accept, Accept-Language等）
   - 检查Referer头
   - 验证请求间隔时间
   - 检查Cookie一致性

2. 只有当满足以下条件时才会返回flag：
   - 答案计算正确
   - 回答时间不超过5秒

## 解题方案

我们需要编写一个脚本，不仅能快速计算出答案，还能绕过服务器的反爬虫检测。

### Python脚本实现

```python
import requests
import re
import time
import random

# 目标URL
TARGET_URL = "http://题目IP地址"  # 实际使用时替换为题目服务器地址

def extract_numbers(question):
    """从题目中提取两个数字"""
    match = re.search(r"(\d+)\s*x\s*(\d+)", question)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError(f"无法从题目中提取数字: {question}")

def main():
    # 创建会话以保持cookie
    session = requests.Session()
    
    # 模拟浏览器请求头
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    session.headers.update(browser_headers)
    
    # 先访问主页增加真实性
    session.get(f"{TARGET_URL}/")
    time.sleep(random.uniform(0.8, 1.5))  # 模拟人类浏览间隔
    
    # 访问验证页面获取题目
    verify_url = f"{TARGET_URL}/complex-verify.html"
    response = session.get(verify_url)
    
    # 添加Referer请求头
    session.headers.update({'Referer': verify_url})
    
    # 从cookie中获取题目
    math_question = session.cookies.get('math_question')
    print(f"获取到的题目: {math_question}")
    
    # 解析题目并计算答案
    num1, num2 = extract_numbers(math_question)
    answer = num1 * num2
    print(f"计算答案: {num1} × {num2} = {answer}")
    
    # 模拟人类计算时间（但不要太长，需要在5秒内提交）
    time.sleep(random.uniform(0.5, 1.0))
    
    # 提交答案
    json_headers = {'Content-Type': 'application/json'}
    session.headers.update(json_headers)
    
    response = session.post(
        f"{TARGET_URL}/api/verify", 
        json={"answer": answer}
    )
    
    # 解析结果
    result = response.json()
    print(f"服务器响应: {result}")
    
    if 'flag' in result:
        print(f"成功获取flag: {result['flag']}")

if __name__ == "__main__":
    main()