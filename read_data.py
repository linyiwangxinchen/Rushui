import numpy as np
import re


def read_data(filename, parameter_name):
    # Open the file
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except FileNotFoundError:
        prmt = 'inexistence'
        return prmt

    # 识别不同参数，在list中分开保存
    found = False
    line_num = 0
    params = []
    param1 = []
    temp_prmtname2 = None
    for line in lines:
        line_num += 1
        if line.startswith('%'):  # 读取起始百分号
            temp_prmtname1 = line.strip('% \t\n')
            temp_prmtname2 = temp_prmtname1.split()
            if temp_prmtname2[0] == 'end':
                params.append(param1)
                param1 = []
            else:
                param1.append(temp_prmtname2)
        else:
            if len(temp_prmtname2) >= 3:
                if temp_prmtname2[2] == 'STR':
                    param1.append(line.strip(' \t\n'))
                else:
                    param1.append(line.strip(' \t\n').split())
    # 分类处理加工数据
    for i in range(len(params)):
        line_num_i=-1
        for liness in params[i]:
            line_num_i+=1
            word_num_i=-1
            for words in liness:
                word_num_i+=1
                if words=="null":
                    params[i][line_num_i][word_num_i]=None
        if matches_prefix(params[i][0][1], parameter_name):  # 查找参数
            if params[i][0][0] == 'single':  # 区分数据结构
                if params[i][0][2] == 'FLT':  # 区分数据类型
                    parameter = float(params[i][1][0])
                elif params[i][0][2] == 'INT':
                    parameter = int(params[i][1][0])
                else:
                    parameter = params[i][1]
                return parameter, [1], params[i][0][1]
            elif params[i][0][0] == 'enum':  # 区分数据结构
                if params[i][0][2] == 'FLT':  # 区分数据类型
                    parameter = float(params[i][1][0])
                elif params[i][0][2] == 'INT':
                    parameter = int(params[i][1][0])
                else:
                    parameter = params[i][1]
                return parameter, [1], params[i][0][1]
            elif params[i][0][0] == 'ComArray':
                if params[i][0][2] == 'FLT':
                    parameter = np.array(params[i][2:], dtype=float)
                elif params[i][0][2] == 'INT':
                    parameter = np.array(params[i][2:], dtype=int)
                else:
                    parameter = np.array(params[i][2:])
                return parameter, list(map(int, [params[i][0][3], params[i][0][4]])), params[i][1], params[i][0][1]
            elif params[i][0][0] == 'array1':
                # parameter = list(map(float, np.array(params[i][1])))
                if params[i][0][2] == 'FLT':
                    parameter = np.array(params[i][1], dtype=float)
                elif params[i][0][2] == 'INT':
                    parameter = np.array(params[i][1], dtype=int)
                else:
                    parameter = np.array(params[i][1])
                return parameter, [int(params[i][0][3])], params[i][0][1]
            elif params[i][0][0] == 'array2':
                if params[i][0][2] == 'FLT':
                    parameter = np.array(params[i][1:], dtype=float)
                elif params[i][0][2] == 'INT':
                    parameter = np.array(params[i][1:], dtype=int)
                else:
                    parameter = np.array(params[i][1:])
                return parameter, list(map(int, [params[i][0][3], params[i][0][4]])), params[i][0][1]

def matches_prefix(s, target):
    # 如果完全相等，直接返回 True
    if s == target:
        return True
    return extract_param_name(s) == target

def extract_param_name(s: str) -> str:
    def strip_last_bracket_block(s, open_b, close_b):
        depth = 0
        end = len(s)
        for i in range(len(s) - 1, -1, -1):
            if s[i] == close_b:
                depth += 1
            elif s[i] == open_b:
                depth -= 1
                if depth == 0:
                    return s[:i].rstrip()
        return s  # 没有匹配成功，返回原始字符串

    # 反复剥除最后一个匹配的 () / [] / {} 块
    while True:
        original = s
        for open_b, close_b in [('<', '>'), ('(', ')'), ('[', ']'), ('{', '}')]:
            if s.endswith(close_b):
                s = strip_last_bracket_block(s, open_b, close_b)
        if s == original:
            break  # 没有进一步剥除，结束
    return s

if __name__ == "__main__":
    filename = 'input.txt'
    parameter_name = '文件'
    result = read_data(filename, parameter_name)
    print(result)
