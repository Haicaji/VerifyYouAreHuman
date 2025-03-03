from flask import Flask, jsonify, request, make_response, send_from_directory, render_template
import uuid
import os
import datetime
import random
import re

# 设置全局FLAG变量
FLAG = r"flag{NISACTF_2025}"

app = Flask(__name__)

# 配置静态文件目录
WWW_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'www')

# 存储用户Cookie的字典
verified_cookies = {}

# 生成乘法题目的函数
def generate_math_question():
    num1 = random.randint(100, 999)  # 3位数
    num2 = random.randint(100, 999)  # 3位数
    answer = num1 * num2
    print(answer)
    question = f"{num1} x {num2} = ?"  # 使用普通字符 'x' 替代特殊的乘法符号 '×'
    return question, answer

# 检测是否为脚本请求的函数
def is_script_request():
    """
    通过多种方式检测请求是否来自脚本而非浏览器
    返回(is_script, reason)元组，is_script为布尔值，reason为原因
    """
    # 1. 检查User-Agent
    print(request.headers)
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent:
        return True, "缺少User-Agent"
    
    # 检测常见的脚本/工具User-Agent
    script_patterns = [
        r'python', r'curl', r'wget', r'bot', r'http', r'request', 
        r'scrapy', r'phantomjs', r'selenium', r'axios'
    ]
    for pattern in script_patterns:
        if re.search(pattern, user_agent.lower()):
            return True, f"User-Agent包含脚本特征: {pattern}"
    
    # 2. 检查请求头一致性
    # 主流浏览器通常会发送这些头
    essential_headers = ['Accept', 'Accept-Language', 'Accept-Encoding']
    for header in essential_headers:
        if header not in request.headers:
            return True, f"缺少浏览器通常发送的请求头: {header}"
    
    # 3. 检查Referer（POST请求通常应该有Referer）
    if request.method == 'POST' and 'Referer' not in request.headers:
        if request.path.startswith('/api/'):
            return True, "API请求缺少Referer"
    
    # 4. 检查请求间隔（防止频繁请求）
    # 这需要在具体应用场景中实现，依赖于存储的用户会话信息
    verification_id = request.cookies.get('complex_verified')
    if verification_id and verification_id in verified_cookies:
        last_request = verified_cookies[verification_id].get('last_request_time')
        if last_request:
            time_since_last = (datetime.datetime.now() - last_request).total_seconds()
            if time_since_last < 0.5:  # 如果请求间隔小于0.5秒
                return True, f"请求频率过高: {time_since_last}秒"
        
        # 更新最后请求时间
        verified_cookies[verification_id]['last_request_time'] = datetime.datetime.now()
    
    # 5. 检查Cookie一致性
    if verification_id and verification_id in verified_cookies:
        math_question_cookie = request.cookies.get('math_question')
        stored_question = verified_cookies[verification_id].get('question')
        if not math_question_cookie or math_question_cookie != stored_question:
            return True, "Cookie不一致，可能是绕过脚本"
    
    return False, "正常请求"

# 路由：提供前端HTML页面
@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory(WWW_FOLDER, 'index.html')

# 路由：简单验证页面
@app.route('/easy-verify.html')
def easy_verify():
    return send_from_directory(WWW_FOLDER, 'easy-verify.html')

# 路由：复杂验证页面
@app.route('/complex-verify.html')
def complex_verify():
    # 生成唯一的验证标识符
    verification_id = uuid.uuid4().hex
    
    # 生成乘法题目
    question, answer = generate_math_question()
    
    # 记录题目、答案和发放时间
    verified_cookies[verification_id] = {
        "question": question,
        "answer": answer,
        "startTime": datetime.datetime.now()
    }
    
    # 创建响应对象
    response = make_response(send_from_directory(WWW_FOLDER, 'complex-verify.html'))
    
    # 设置cookie，过期时间为30分钟
    expires = datetime.datetime.now() + datetime.timedelta(minutes=30)
    
    # 设置验证cookie
    response.set_cookie(
        'complex_verified', 
        verification_id,
        expires=expires,
        httponly=True,  # 提高安全性，JavaScript无法读取
        path='/'
    )
    
    # 设置题目cookie (非httponly，允许JavaScript读取)
    response.set_cookie(
        'math_question', 
        question,
        expires=expires,
        httponly=False,
        path='/'
    )
    
    return response

# API接口：验证乘法题答案
@app.route('/api/verify', methods=['POST'])
def verify_answer():
    # 检测脚本请求
    is_script, reason = is_script_request()
    if is_script:
        print(f"检测到脚本请求: {reason}")
        return jsonify({
            'status': 'error',
            'message': '不是?你真是机器人啊?'
        }), 403
    
    # 获取用户答案
    data = request.get_json()
    user_answer = data.get('answer', '')
    
    # 获取用户验证ID
    verification_id = request.cookies.get('complex_verified')
    
    if not verification_id or verification_id not in verified_cookies:
        return jsonify({
            'status': 'error',
            'message': '验证会话无效，请重新获取验证题目'
        }), 400
    
    # 获取用户题目信息
    user_data = verified_cookies[verification_id]
    correct_answer = user_data.get('answer')
    start_time = user_data.get('startTime')
    
    # 计算答题用时
    time_used = (datetime.datetime.now() - start_time).total_seconds()
    
    # 验证答案
    try:
        user_answer = int(user_answer)
        
        if user_answer == correct_answer:
            # 验证成功，更新Cookie状态
            verified_cookies[verification_id]['verified'] = True
            verified_cookies[verification_id]['time_used'] = time_used
            
            # 检查是否在5秒内回答
            if time_used <= 5:
                # 在5秒内回答正确，返回flag
                return jsonify({
                    'status': 'success',
                    'message': '认证成功!',
                    'flag': FLAG,
                    'time': f'{time_used:.2f}秒'
                })
            else:
                # 回答正确但超过5秒
                return jsonify({
                    'status': 'success',
                    'message': f'花这么久才回答正确，flag不给你！',
                    'time': f'{time_used:.2f}秒'
                })
        else:
            # 答案错误，生成新题目
            new_question, new_answer = generate_math_question()
            
            # 更新用户题目信息
            verified_cookies[verification_id]['question'] = new_question
            verified_cookies[verification_id]['answer'] = new_answer
            verified_cookies[verification_id]['startTime'] = datetime.datetime.now()
            
            # 创建响应
            response = jsonify({
                'status': 'error',
                'message': '这都答不对？再给你一次机会！',
                'new_question': new_question
            })
            
            # 更新题目cookie
            expires = datetime.datetime.now() + datetime.timedelta(minutes=30)
            response.set_cookie(
                'math_question', 
                new_question,
                expires=expires,
                httponly=False,
                path='/'
            )
            
            return response, 400
    
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': '请输入有效的数字答案'
        }), 400

# 新增API接口：获取新的乘法题目（添加更多错误处理和日志）
@app.route('/api/get-new-question', methods=['GET'])
def get_new_question():
    # 检测脚本请求
    is_script, reason = is_script_request()
    if is_script:
        print(f"检测到脚本请求: {reason}")
        return jsonify({
            'status': 'error',
            'message': '检测到自动化工具，请使用浏览器进行人工验证'
        }), 403
        
    # 获取用户验证ID
    verification_id = request.cookies.get('complex_verified')
    
    print(f"获取新题目请求: verification_id={verification_id}")
    
    if not verification_id:
        print("验证ID不存在")
        return jsonify({
            'status': 'error',
            'message': '验证会话无效，请重新获取验证题目'
        }), 400
    
    if verification_id not in verified_cookies:
        print(f"验证ID无效: {verification_id}")
        return jsonify({
            'status': 'error',
            'message': '验证会话已过期，请刷新页面'
        }), 400
    
    try:
        # 生成新题目
        new_question, new_answer = generate_math_question()
        
        # 更新用户题目信息
        verified_cookies[verification_id]['question'] = new_question
        verified_cookies[verification_id]['answer'] = new_answer
        verified_cookies[verification_id]['startTime'] = datetime.datetime.now()
        
        print(f"新题目生成成功: question={new_question}, answer={new_answer}")
        
        # 创建响应
        response = jsonify({
            'status': 'success',
            'message': '已生成新题目',
            'new_question': new_question
        })
        
        # 更新题目cookie
        expires = datetime.datetime.now() + datetime.timedelta(minutes=30)
        response.set_cookie(
            'math_question', 
            new_question,
            expires=expires,
            httponly=False,
            path='/'
        )
        
        return response
    
    except Exception as e:
        print(f"生成新题目时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'生成题目时发生错误: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
