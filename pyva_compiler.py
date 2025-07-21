import re
import sys

functions = {}
global_vars = {}

class ReturnException(Exception):
    """Custom exception to handle return statements"""
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    """Custom exception to handle break statements"""
    pass

class ContinueException(Exception):
    """Custom exception to handle continue statements"""
    pass

def parse_type(type_str):
    """Convert type annotations to Python types"""
    type_map = {
        'String': str,
        'int': int,
        'float': float,
        'bool': bool
    }
    return type_map.get(type_str, str)

def evaluate_expression(expr, local_vars):
    """Enhanced expression evaluator with fixed comparison operators and ignored gaps within expressions"""
    expr = expr.strip()
    if not expr:
        return None
    if expr.startswith('"') and expr.endswith('"') and len(expr) >= 2:
        return expr[1:-1]
    expr_no_space = expr.replace(' ', '')
    if expr_no_space.lstrip('-').replace('.', '').isdigit():
        return float(expr_no_space) if '.' in expr_no_space else int(expr_no_space)
    expr_lower = expr.lower().replace(' ', '')
    if expr_lower in ['true', 'false']:
        return expr_lower == 'true'
    builtin_funcs = ['int', 'float', 'str', 'bool']
    for func in builtin_funcs:
        pattern = f'{func}\\s*\\((.*)\\)$'
        match = re.match(pattern, expr)
        if match:
            inner_expr = match.group(1).strip()
            inner_value = evaluate_expression(inner_expr, local_vars)
            try:
                if func == 'int':
                    if isinstance(inner_value, str):
                        inner_value = inner_value.strip()
                        if inner_value.lstrip('-').replace('.', '').isdigit():
                            return int(float(inner_value))
                        else:
                            return 0
                    return int(inner_value)
                elif func == 'float':
                    return float(inner_value)
                elif func == 'str':
                    return str(inner_value)
                elif func == 'bool':
                    if isinstance(inner_value, str):
                        return inner_value.lower() in ['true', '1', 'yes', 'y']
                    return bool(inner_value)
            except:
                return 0
    input_pattern = r'input\s*\((.*)\)$'
    match_input = re.match(input_pattern, expr)
    if match_input:
        prompt_expr = match_input.group(1).strip()
        prompt = evaluate_expression(prompt_expr, local_vars) if prompt_expr else ""
        user_input = input(str(prompt))
        return user_input
    if expr in local_vars:
        return local_vars[expr]
    elif expr in global_vars:
        return global_vars[expr]
    if ('(' in expr and ')' in expr and 
        not any(op in expr for op in ['+', '-', '*', '/', '%', '<=', '>=', '==', '!=', '<', '>', ' and ', ' or '])):
        try:
            fname, args = parse_function_call_enhanced(expr, local_vars)
            if fname in functions:
                return execute_function(fname, args)
        except Exception:
            pass
    if expr.startswith('(') and expr.endswith(')') and is_balanced_parentheses(expr):
        return evaluate_expression(expr[1:-1], local_vars)
    if ' or ' in expr:
        parts = split_expression_safe(expr, ' or ')
        if len(parts) > 1:
            return any(evaluate_expression(part.strip(), local_vars) for part in parts)
    if ' and ' in expr:
        parts = split_expression_safe(expr, ' and ')
        if len(parts) > 1:
            return all(evaluate_expression(part.strip(), local_vars) for part in parts)
    comparison_ops = ['<=', '>=', '==', '!=', '<', '>']
    for op in comparison_ops:
        parts = split_expression_safe(expr, op)
        if len(parts) == 2:
            left_val = evaluate_expression(parts[0].strip(), local_vars)
            right_val = evaluate_expression(parts[1].strip(), local_vars)
            left_val = convert_for_comparison(left_val)
            right_val = convert_for_comparison(right_val)
            try:
                if op == '==':
                    return left_val == right_val
                elif op == '!=':
                    return left_val != right_val
                elif op == '<=':
                    return left_val <= right_val
                elif op == '>=':
                    return left_val >= right_val
                elif op == '<':
                    return left_val < right_val
                elif op == '>':
                    return left_val > right_val
            except TypeError:
                if op == '==':
                    return str(left_val) == str(right_val)
                elif op == '!=':
                    return str(left_val) != str(right_val)
                else:
                    return False
    for op in ['+', '-']:
        parts = split_expression_safe(expr, op)
        if len(parts) > 1:
            result = evaluate_expression(parts[0].strip(), local_vars)
            for i in range(1, len(parts)):
                right = evaluate_expression(parts[i].strip(), local_vars)
                try:
                    if op == '+':
                        result = result + right
                    elif op == '-':
                        result = result - right
                except TypeError:
                    if op == '+':
                        result = str(result) + str(right)
                    else:
                        result = 0
            return result
    for op in ['*', '/', '%']:
        parts = split_expression_safe(expr, op)
        if len(parts) > 1:
            result = evaluate_expression(parts[0].strip(), local_vars)
            for i in range(1, len(parts)):
                right = evaluate_expression(parts[i].strip(), local_vars)
                try:
                    if op == '*':
                        result = result * right
                    elif op == '/':
                        result = result / right if right != 0 else 0
                    elif op == '%':
                        result = result % right if right != 0 else 0
                except:
                    result = 0
            return result
    if expr.isidentifier():
        return expr
    return expr

def convert_for_comparison(value):
    if isinstance(value, str):
        if value.lstrip('-').replace('.', '').isdigit():
            return float(value) if '.' in value else int(value)
    return value

def is_balanced_parentheses(expr):
    count = 0
    in_string = False
    for char in expr:
        if char == '"':
            in_string = not in_string
        elif not in_string:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
                if count < 0:
                    return False
    return count == 0

def split_expression_safe(expr, operator):
    parts = []
    current_part = ""
    paren_depth = 0
    quote_depth = 0
    i = 0
    op_len = len(operator)
    while i < len(expr):
        if expr[i] == '"' and paren_depth == 0:
            quote_depth = 1 - quote_depth
            current_part += expr[i]
        elif expr[i] == '(' and quote_depth == 0:
            paren_depth += 1
            current_part += expr[i]
        elif expr[i] == ')' and quote_depth == 0:
            paren_depth -= 1
            current_part += expr[i]
        elif (paren_depth == 0 and quote_depth == 0 and 
              i + op_len <= len(expr) and 
              expr[i:i+op_len].lower() == operator):
            before_ok = (i == 0 or expr[i-1] not in '=!<>')
            after_ok = (i + op_len >= len(expr) or (i + op_len < len(expr) and expr[i + op_len] not in '=!<>'))
            if before_ok and after_ok:
                parts.append(current_part.strip())
                current_part = ""
                i += op_len - 1
            else:
                current_part += expr[i]
        else:
            current_part += expr[i]
        i += 1
    if current_part:
        parts.append(current_part.strip())
    return parts

def parse_function_call_enhanced(expr, local_vars):
    paren_index = expr.find('(')
    if paren_index == -1:
        raise ValueError("Invalid function call syntax")
    fname = expr[:paren_index].strip()
    args_start = paren_index + 1
    paren_count = 1
    i = args_start
    while i < len(expr) and paren_count > 0:
        if expr[i] == '(':
            paren_count += 1
        elif expr[i] == ')':
            paren_count -= 1
        i += 1
    if paren_count != 0:
        raise ValueError("Mismatched parentheses in function call")
    args_str = expr[args_start:i-1].strip()
    args = []
    if args_str:
        args = parse_arguments(args_str, local_vars)
    return fname, args

def parse_arguments(args_str, local_vars):
    args = []
    current_arg = ""
    paren_depth = 0
    quote_depth = 0
    for char in args_str + ',':
        if char == '"' and paren_depth == 0:
            quote_depth = 1 - quote_depth
            current_arg += char
        elif char == '(' and quote_depth == 0:
            paren_depth += 1
            current_arg += char
        elif char == ')' and quote_depth == 0:
            paren_depth -= 1
            current_arg += char
        elif char == ',' and paren_depth == 0 and quote_depth == 0:
            if current_arg.strip():
                arg_value = evaluate_expression(current_arg.strip(), local_vars)
                args.append(arg_value)
            current_arg = ""
        else:
            current_arg += char
    return args

def parse_function(lines):
    header = lines[0].strip()
    match = re.match(r'def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*(\w+))?:', header)
    if not match:
        raise SyntaxError("Invalid function definition")
    fname = match.group(1)
    params_str = match.group(2)
    return_type = match.group(3) or 'void'
    params = []
    if params_str.strip():
        for param in params_str.split(','):
            param = param.strip()
            if ':' in param:
                name, ptype = param.split(':', 1)
                params.append((name.strip(), parse_type(ptype.strip())))
            else:
                params.append((param, str))
    body = lines[1:]
    functions[fname] = (params, body, return_type)

def execute_statement(line, local_vars):
    line = line.strip()
    if not line:
        return
    try:
        if '(' in line and ')' in line and '=' not in line:
            try:
                fname, args = parse_function_call_enhanced(line, local_vars)
                if fname in functions:
                    return execute_function(fname, args)
                elif fname == 'print':
                    if args:
                        print(*args)
                    else:
                        print()
                    return
                elif fname == 'input':
                    prompt = args[0] if args else ""
                    return input(str(prompt))
            except Exception as e:
                raise SyntaxError(f"Error in function call '{line}': {e}")
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            parts = line.split('=', 1)
            var_name = parts[0].strip()
            expr = parts[1].strip()
            value = evaluate_expression(expr, local_vars)
            local_vars[var_name] = value
            return
        if line.startswith("print(") and line.endswith(")"):
            expr = line[6:-1]
            value = evaluate_expression(expr, local_vars)
            print(value if value is not None else "")
            return
        if line.startswith("return"):
            if len(line) > 6:
                expr = line[6:].strip()
                value = evaluate_expression(expr, local_vars)
            else:
                value = None
            raise ReturnException(value)
        if line == "break":
            raise BreakException()
        if line == "continue":
            raise ContinueException()
        try:
            result = evaluate_expression(line, local_vars)
            return result
        except Exception as e:
            raise SyntaxError(f"Error evaluating expression '{line}': {e}")
    except Exception as e:
        print(f"Error: {e}")

def execute_if_block(lines, start_idx, local_vars):
    i = start_idx
    n = len(lines)
    line = lines[i].strip()
    if_match = re.match(r'if\s+(.+):', line)
    if not if_match:
        raise SyntaxError("Invalid if statement")
    conditions_blocks = []
    cond = if_match.group(1).strip()
    current_block = []
    i += 1
    while i < n:
        current_line = lines[i]
        stripped_line = current_line.strip()
        if stripped_line.startswith('if ') or stripped_line.startswith('elif ') or stripped_line.startswith('else:'):
            conditions_blocks.append((cond, current_block))
            current_block = []
            if stripped_line.startswith('elif '):
                elif_match = re.match(r'elif\s+(.+):', stripped_line)
                if not elif_match:
                    raise SyntaxError("Invalid elif statement")
                cond = elif_match.group(1).strip()
            elif stripped_line == 'else:':
                cond = None
            else:
                break
            i += 1
            continue
        if stripped_line and not current_line.startswith('    ') and not current_line.startswith('\t'):
            break
        if stripped_line or current_line.strip() == "":
            current_block.append(stripped_line)
        i += 1
    conditions_blocks.append((cond, current_block))
    for cond, block in conditions_blocks:
        if cond is None:
            execute_block(block, local_vars)
            break
        else:
            cond_result = evaluate_expression(cond, local_vars)
            if isinstance(cond_result, bool):
                cond_bool = cond_result
            elif isinstance(cond_result, (int, float)):
                cond_bool = cond_result != 0
            elif isinstance(cond_result, str):
                cond_bool = cond_result.lower() in ['true', '1', 'yes', 'y'] and cond_result != ""
            else:
                cond_bool = bool(cond_result)
            if cond_bool:
                execute_block(block, local_vars)
                break
    return i - 1

def execute_while_loop(lines, start_idx, local_vars):
    i = start_idx
    line = lines[i].strip()
    while_match = re.match(r'while\s+(.+):', line)
    if not while_match:
        raise SyntaxError("Invalid while statement")
    condition = while_match.group(1).strip()
    i += 1
    loop_body = []
    while i < len(lines):
        current_line = lines[i]
        stripped_line = current_line.strip()
        if stripped_line and not current_line.startswith("    ") and not current_line.startswith("\t"):
            break
        if stripped_line:
            loop_body.append(stripped_line)
        elif current_line.strip() == "":
            loop_body.append("")
        i += 1
    loop_iterations = 0
    max_iterations = 100000
    while loop_iterations < max_iterations:
        condition_result = evaluate_expression(condition, local_vars)
        if isinstance(condition_result, bool):
            condition_bool = condition_result
        elif isinstance(condition_result, (int, float)):
            condition_bool = condition_result != 0
        elif isinstance(condition_result, str):
            condition_bool = (condition_result.lower() in ['true', '1', 'yes', 'y'] and 
                            condition_result.strip() != "")
        elif condition_result is None:
            condition_bool = False
        else:
            condition_bool = bool(condition_result)
        if not condition_bool:
            break
        try:
            execute_block(loop_body, local_vars)
        except ReturnException:
            raise
        except BreakException:
            break
        except ContinueException:
            pass
        loop_iterations += 1
    if loop_iterations >= max_iterations:
        print(f"Warning: While loop exceeded {max_iterations} iterations, stopping")
    return i - 1

def execute_do_while_loop(lines, start_idx, local_vars):
    i = start_idx
    line = lines[i].strip()
    if line != "do:":
        raise SyntaxError("Invalid do-while statement - expected 'do:'")
    i += 1
    loop_body = []
    while i < len(lines):
        current_line = lines[i]
        stripped_line = current_line.strip()
        if stripped_line.startswith("while ") and stripped_line.endswith(":"):
            while_match = re.match(r'while\s+(.+):', stripped_line)
            if not while_match:
                raise SyntaxError("Invalid while condition in do-while loop")
            condition = while_match.group(1).strip()
            break
        if stripped_line and not current_line.startswith("    ") and not current_line.startswith("\t"):
            raise SyntaxError("do-while loop missing 'while' condition")
        if stripped_line:
            loop_body.append(stripped_line)
        elif current_line.strip() == "":
            loop_body.append("")
        i += 1
    if i >= len(lines):
        raise SyntaxError("do-while loop missing 'while' condition")
    loop_iterations = 0
    max_iterations = 100000
    while True:
        loop_iterations += 1
        if loop_iterations > max_iterations:
            print(f"Warning: Do-while loop exceeded {max_iterations} iterations, stopping")
            break
        try:
            execute_block(loop_body, local_vars)
        except ReturnException:
            raise
        except BreakException:
            break
        except ContinueException:
            pass
        condition_result = evaluate_expression(condition, local_vars)
        if isinstance(condition_result, bool):
            condition_bool = condition_result
        elif isinstance(condition_result, (int, float)):
            condition_bool = condition_result != 0
        elif isinstance(condition_result, str):
            condition_bool = (condition_result.lower() in ['true', '1', 'yes', 'y'] and 
                            condition_result.strip() != "")
        elif condition_result is None:
            condition_bool = False
        else:
            condition_bool = bool(condition_result)
        if not condition_bool:
            break
    return i

def execute_for_loop(lines, start_idx, local_vars):
    i = start_idx
    line = lines[i].strip()
    for_range_match = re.match(r'for\s+(\w+)\s+in\s+range\s*\((.+)\):', line)
    for_list_match = re.match(r'for\s+(\w+)\s+in\s*\[(.+)\]:', line)
    for_var_match = re.match(r'for\s+(\w+)\s+in\s+(\w+):', line)
    if for_range_match:
        var_name = for_range_match.group(1)
        range_expr = for_range_match.group(2)
        loop_type = "range"
    elif for_list_match:
        var_name = for_list_match.group(1)
        list_expr = for_list_match.group(2)
        loop_type = "list"
    elif for_var_match:
        var_name = for_var_match.group(1)
        iterable_var = for_var_match.group(2)
        loop_type = "variable"
    else:
        raise SyntaxError("Invalid for statement")
    i += 1
    loop_body = []
    while i < len(lines):
        current_line = lines[i]
        stripped_line = current_line.strip()
        if stripped_line and not current_line.startswith("    ") and not current_line.startswith("\t"):
            break
        if stripped_line:
            loop_body.append(stripped_line)
        elif current_line.strip() == "":
            loop_body.append("")
        i += 1
    try:
        if loop_type == "range":
            parts_raw = [p.strip() for p in split_range_args(range_expr)]
            if len(parts_raw) == 1:
                start_val = 0
                end_val = int(evaluate_expression(parts_raw[0], local_vars))
                step_val = 1
            elif len(parts_raw) == 2:
                start_val = int(evaluate_expression(parts_raw[0], local_vars))
                end_val = int(evaluate_expression(parts_raw[1], local_vars))
                step_val = 1
            elif len(parts_raw) == 3:
                start_val = int(evaluate_expression(parts_raw[0], local_vars))
                end_val = int(evaluate_expression(parts_raw[1], local_vars))
                step_val = int(evaluate_expression(parts_raw[2], local_vars))
            else:
                raise ValueError("Range function accepts 1, 2, or 3 arguments")
            for value in range(start_val, end_val, step_val):
                local_vars[var_name] = value
                try:
                    execute_block(loop_body, local_vars)
                except ReturnException:
                    raise
                except BreakException:
                    break
                except ContinueException:
                    continue
        elif loop_type == "list":
            list_items = []
            if list_expr.strip():
                items = split_list_items(list_expr)
                for item in items:
                    item_value = evaluate_expression(item.strip(), local_vars)
                    list_items.append(item_value)
            for value in list_items:
                local_vars[var_name] = value
                try:
                    execute_block(loop_body, local_vars)
                except ReturnException:
                    raise
                except BreakException:
                    break
                except ContinueException:
                    continue
        elif loop_type == "variable":
            if iterable_var in local_vars:
                iterable = local_vars[iterable_var]
            elif iterable_var in global_vars:
                iterable = global_vars[iterable_var]
            else:
                raise NameError(f"Variable '{iterable_var}' not defined")
            if isinstance(iterable, (list, tuple)):
                iteration_values = iterable
            elif isinstance(iterable, str):
                iteration_values = list(iterable)
            elif isinstance(iterable, range):
                iteration_values = list(iterable)
            else:
                try:
                    iteration_values = list(iterable)
                except TypeError:
                    raise TypeError(f"'{type(iterable).__name__}' object is not iterable")
            for value in iteration_values:
                local_vars[var_name] = value
                try:
                    execute_block(loop_body, local_vars)
                except ReturnException:
                    raise
                except BreakException:
                    break
                except ContinueException:
                    continue
    except (ValueError, TypeError) as e:
        raise SyntaxError(f"Error in for loop: {e}")
    return i - 1

def split_range_args(range_expr):
    args = []
    current = ''
    depth = 0
    for c in range_expr:
        if c == '(':
            depth += 1
            current += c
        elif c == ')':
            depth -= 1
            current += c
        elif c == ',' and depth == 0:
            args.append(current.strip())
            current = ''
        else:
            current += c
    if current.strip():
        args.append(current.strip())
    return args

def split_list_items(list_expr):
    items = []
    current = ''
    depth = 0
    in_string = False
    i = 0
    while i < len(list_expr):
        c = list_expr[i]
        if c == '"':
            in_string = not in_string
            current += c
        elif c == '[' and not in_string:
            depth += 1
            current += c
        elif c == ']' and not in_string:
            depth -= 1
            current += c
        elif c == ',' and depth == 0 and not in_string:
            items.append(current.strip())
            current = ''
        else:
            current += c
        i += 1
    if current.strip():
        items.append(current.strip())
    return items

def execute_block(lines, local_vars):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("if "):
            i = execute_if_block(lines, i, local_vars)
        elif line.startswith("while "):
            i = execute_while_loop(lines, i, local_vars)
        elif line.startswith("for "):
            i = execute_for_loop(lines, i, local_vars)
        elif line == "do:":
            i = execute_do_while_loop(lines, i, local_vars)
        else:
            execute_statement(line, local_vars)
        i += 1

def execute_function(fname, args):
    if fname not in functions:
        raise NameError(f"Function '{fname}' not defined")
    params, body, return_type = functions[fname]
    if len(params) != len(args):
        raise ValueError(f"Function '{fname}' expects {len(params)} arguments, got {len(args)}")
    local_vars = {}
    for i, (param_name, param_type) in enumerate(params):
        try:
            if param_type == int:
                if isinstance(args[i], str) and args[i].lstrip('-').replace('.', '').isdigit():
                    local_vars[param_name] = int(float(args[i]))
                else:
                    local_vars[param_name] = int(args[i])
            elif param_type == float:
                local_vars[param_name] = float(args[i])
            elif param_type == bool:
                if isinstance(args[i], str):
                    local_vars[param_name] = args[i].lower() in ['true', '1', 'yes', 'y']
                else:
                    local_vars[param_name] = bool(args[i])
            else:
                local_vars[param_name] = str(args[i])
        except (ValueError, TypeError):
            local_vars[param_name] = args[i]
    try:
        execute_block(body, local_vars)
        return None
    except ReturnException as e:
        return e.value

def run_program(source_code):
    global functions, global_vars
    functions.clear()
    global_vars.clear()
    lines = source_code.strip().split('\n')
    lines = [line.rstrip() for line in lines]

    # Parse function definitions
    i = 0
    main_block_lines = []
    in_main_block = False
    main_block_indent = None

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("def "):
            j = i + 1
            while j < len(lines) and (lines[j].startswith("    ") or lines[j].startswith("\t") or lines[j].strip() == ""):
                j += 1
            func_lines = lines[i:j]
            parse_function(func_lines)
            i = j
        elif line.startswith("main"):
            # Detect main block start: e.g. main { or main{
            m = re.match(r'main\s*\{', line)
            if m:
                in_main_block = True
                main_block_lines = []
                i += 1
                # collect main block lines until matching closing '}'
                brace_count = 1
                while i < len(lines) and brace_count > 0:
                    cur_line = lines[i]
                    # count braces to find block end
                    brace_count += cur_line.count('{')
                    brace_count -= cur_line.count('}')
                    if brace_count > 0:
                        main_block_lines.append(cur_line.strip())
                    i += 1
                continue
            else:
                i += 1
        else:
            i += 1

    # Execute main block
    if main_block_lines:
        try:
            execute_block(main_block_lines, global_vars)
        except ReturnException as e:
            return e.value

    return None

def interpret_file(filename):
    try:
        with open(filename, 'r') as file:
            source_code = file.read()
        result = run_program(source_code)
        if result is not None:
            print(f"Program returned: {result}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except Exception as e:
        print(f"Error: {e}")

def interactive_mode():
    print("Enhanced Compiler Interactive Mode")
    print("Type 'exit' to quit, 'help' for commands")
    print("Enter multi-line code, end with 'END' on a new line")
    while True:
        try:
            command = input(">>> ").strip()
            if command.lower() == 'exit':
                break
            elif command.lower() == 'help':
                print("Commands:")
                print("  exit - Exit the interpreter")
                print("  help - Show this help")
                print("  clear - Clear all functions and variables")
                print("  vars - Show current variables")
                print("  funcs - Show defined functions")
                print("  Enter code and end with 'END' to execute multi-line code")
                continue
            elif command.lower() == 'clear':
                functions.clear()
                global_vars.clear()
                print("Cleared all functions and variables")
                continue
            elif command.lower() == 'vars':
                print("Global variables:", global_vars)
                continue
            elif command.lower() == 'funcs':
                print("Defined functions:", list(functions.keys()))
                continue
            lines = [command]
            while True:
                line = input("... ")
                if line.strip() == 'END':
                    break
                lines.append(line)
            source_code = '\n'.join(lines)
            result = run_program(source_code)
            if result is not None:
                print(f"Result: {result}")
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Place for test calls if any
            pass
        elif sys.argv[1] == "--interactive":
            interactive_mode()
        else:
            interpret_file(sys.argv[1])
    else:
        print("Enhanced Compiler Usage:")
        print("  python pyva_compiler.py <filename>     - Run a program file")
        print("  python pyva_compiler.py --interactive   - Interactive mode")
        print("\nSupported Features:")
        print("  - Functions with type annotations")
        print("  - While loops")
        print("  - Do-while loops")
        print("  - For loops (range, list, variable)")
        print("  - If-elif-else statements")
        print("  - Break and continue statements")
        print("  - Nested loops and functions")
        print("  - Variable assignments and expressions")
        print("  - Built-in functions: print, input, int, float, str, bool")

