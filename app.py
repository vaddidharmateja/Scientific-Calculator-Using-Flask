from flask import Flask, render_template, request, jsonify
import math
import cmath

app = Flask(__name__)

# Initialize calculator state
calculator_state = {
    'display': '0',
    'memory': 0,
    'history': [],
    'angle_mode': 'DEG'
}


@app.route('/')
def index():
    # Reset all calculator state on page load
    calculator_state.update({
        'display': '0',
        'memory': 0,
        'history': [],
        'angle_mode': 'DEG'
    })
    return render_template('calculator.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    action = data.get('action')
    value = data.get('value')
    
    response = {
        'display': calculator_state['display'],
        'angle_mode': calculator_state['angle_mode']
    }
    
    try:
        if action == 'insert':
            calculator_state['display'] = insert_text(value, calculator_state['display'])
        elif action == 'operator':
            calculator_state['display'] = insert_operator(value, calculator_state['display'])
        elif action == 'clear':
            calculator_state['display'] = '0'
        elif action == 'backspace':
            calculator_state['display'] = backspace(calculator_state['display'])
        elif action == 'negate':
            calculator_state['display'] = negate(calculator_state['display'])
        elif action == 'square':
            result, history_entry = perform_operation(
                calculator_state['display'],
                lambda x: x ** 2,
                '²'
            )
            update_state(result, history_entry)
        elif action == 'calculate':
            expression = data.get('expression', calculator_state['display'])
            result = perform_calculation(expression)
            if result != 'Error':
                history_entry = f"{expression} = {result}"
                calculator_state['history'].append(history_entry)
                if len(calculator_state['history']) > 50:
                    calculator_state['history'].pop(0)
                calculator_state['display'] = result
            else:
                calculator_state['display'] = result
        elif action == 'math_function':
            func_map = {
                'sqrt': (lambda x: math.sqrt(abs(x)), '√'),
                'log': (math.log10, 'log'),
                'ln': (math.log, 'ln'),
                'exp': (math.exp, 'exp'),
                '10power': (lambda x: 10 ** x, '10^'),
                'factorial': (lambda x: math.factorial(int(x)) if x >= 0 and x == int(x) else None, '!'),
                'abs': (abs, 'abs'),
                'reciprocal': (lambda x: 1 / x if x != 0 else None, '1/')
            }
            func, symbol = func_map[value]
            result, history_entry = perform_operation(
                calculator_state['display'],
                func,
                symbol
            )
            update_state(result, history_entry)
        elif action == 'trig_function':
            func_map = {
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan
            }
            func = func_map[value]
            symbol = value
            result, history_entry = perform_trig_operation(
                calculator_state['display'],
                func,
                symbol,
                calculator_state['angle_mode']
            )
            update_state(result, history_entry)
        elif action == 'constant':
            calculator_state['display'] = insert_constant(value, calculator_state['display'])
        elif action == 'toggle_angle':
            calculator_state['angle_mode'] = 'RAD' if calculator_state['angle_mode'] == 'DEG' else 'DEG'
            response['angle_mode'] = calculator_state['angle_mode']
        elif action == 'memory_clear':
            calculator_state['memory'] = 0
        elif action == 'memory_recall':
            calculator_state['display'] = str(calculator_state['memory'])
        elif action == 'memory_add':
            calculator_state['memory'] += float(calculator_state['display'])
        elif action == 'memory_subtract':
            calculator_state['memory'] -= float(calculator_state['display'])
        elif action == 'memory_store':
            calculator_state['memory'] = float(calculator_state['display'])
        elif action == 'get_history':
            response['history'] = calculator_state['history']
            return jsonify(response)
        elif action == 'clear_history':
            calculator_state['history'] = []
            return jsonify(response)
            
        response['display'] = calculator_state['display']
        return jsonify(response)
        
    except Exception as e:
        calculator_state['display'] = 'Error'
        response['display'] = 'Error'
        return jsonify(response)


def update_state(result, history_entry=None):
    if result != 'Error':
        calculator_state['display'] = result
        if history_entry:
            calculator_state['history'].append(history_entry)
            if len(calculator_state['history']) > 50:
                calculator_state['history'].pop(0)


def perform_operation(current, operation, symbol):
    try:
        if current == "Error" or current == "0":
            return current, None
        
        value = float(current)
        result = operation(value)
        
        if result is None:
            return "Error", None
        
        formatted_result = str(int(result)) if result == int(result) else f"{result:.10g}"

        # Format history entry based on operation type
        if symbol == '√':
            history_entry = f"√{current} = {formatted_result}"
        elif symbol == 'log':
            history_entry = f"log({current}) = {formatted_result}"
        elif symbol == 'ln':
            history_entry = f"ln({current}) = {formatted_result}"
        elif symbol == 'exp':
            history_entry = f"exp({current}) = {formatted_result}"
        elif symbol == '10^':
            history_entry = f"10^{current} = {formatted_result}"
        elif symbol == '!':
            history_entry = f"{current}! = {formatted_result}"
        elif symbol == 'abs':
            history_entry = f"|{current}| = {formatted_result}"
        elif symbol == '1/':
            history_entry = f"1/({current}) = {formatted_result}"
        else:
            history_entry = f"{current}{symbol} = {formatted_result}"
        
        return formatted_result, history_entry
                    
    except Exception as e:
        return "Error", None


def perform_trig_operation(current, operation, symbol, angle_mode):
    try:
        if current == "Error" or current == "0":
            return current, None
        
        value = float(current)
        
        # Convert to radians if in degree mode for direct trig functions
        if angle_mode == "DEG" and symbol in ['sin', 'cos', 'tan']:
            value = math.radians(value)
        
        result = operation(value)
        
        # Convert back to degrees for inverse trig functions if in degree mode
        if angle_mode == "DEG" and symbol in ['asin', 'acos', 'atan']:
            result = math.degrees(result)
        
        formatted_result = str(int(result)) if result == int(result) else f"{result:.10g}"
        history_entry = f"{symbol}({current}) = {formatted_result} ({angle_mode})"
        
        return formatted_result, history_entry
            
    except Exception as e:
        return "Error", None


def insert_text(text, current):
    if current == "0" or current == "Error":
        return text
    else:
        return current + text


def insert_operator(op, current):
    if current == "Error":
        return current
    if current and current[-1] not in "+-*/^%":
        return insert_text(op, current)
    return current


def backspace(current):
    if len(current) > 1:
        return current[:-1]
    else:
        return "0"


def negate(current):
    try:
        if current.startswith('-'):
            return current[1:]
        else:
            return '-' + current
    except:
        return current


def perform_calculation(expression):
    try:
        if expression == "Error" or not expression:
            return expression
        
        # Replace display symbols with evaluable expressions
        expr = expression.replace('×', '*').replace('÷', '/')
        
        # π and e are already their actual values from frontend
        import re
        
        # Replace trigonometric functions
        angle_mode = calculator_state.get('angle_mode', 'DEG')
        
        def replace_trig(match):
            func = match.group(1)
            arg_expr = match.group(2)
            try:
                # Recursively evaluate the argument
                arg_val = eval(arg_expr)
                val = float(arg_val)
                
                if angle_mode == 'DEG' and func in ['sin', 'cos', 'tan']:
                    val = math.radians(val)
                
                result = getattr(math, func)(val)
                
                if angle_mode == 'DEG' and func in ['asin', 'acos', 'atan']:
                    result = math.degrees(result)
                    
                return str(result)
            except Exception as e:
                return "0"
        
        # Replace trig functions
        expr = re.sub(r'(sin|cos|tan|asin|acos|atan)\(([^)]+)\)', replace_trig, expr)
        
        # Replace math functions
        def replace_math_func(match):
            func = match.group(1)
            arg_expr = match.group(2)
            try:
                arg_val = eval(arg_expr)
                val = float(arg_val)
                
                if func == 'log':
                    return str(math.log10(val))
                elif func == 'ln':
                    return str(math.log(val))
                elif func == 'exp':
                    return str(math.exp(val))
                elif func == 'abs':
                    return str(abs(val))
                return str(val)
            except Exception as e:
                return "0"
        
        expr = re.sub(r'(log|ln|exp|abs)\(([^)]+)\)', replace_math_func, expr)
        
        # Replace square root
        def replace_sqrt(match):
            try:
                arg_val = eval(match.group(1))
                return str(math.sqrt(float(arg_val)))
            except:
                return "0"
        
        expr = re.sub(r'√\(([^)]+)\)', replace_sqrt, expr)
        
        # Replace reciprocal 1/(x)
        def replace_reciprocal(match):
            try:
                arg_val = eval(match.group(1))
                return str(1/float(arg_val))
            except:
                return "0"
        
        expr = re.sub(r'1/\(([^)]+)\)', replace_reciprocal, expr)
        
        # Replace 10^(x)
        def replace_10power(match):
            try:
                arg_val = eval(match.group(1))
                return str(10**float(arg_val))
            except:
                return "0"
        
        expr = re.sub(r'10\^\(([^)]+)\)', replace_10power, expr)
        
        # Handle factorial
        def replace_factorial(match):
            try:
                return str(math.factorial(int(float(match.group(1)))))
            except:
                return "0"
        
        expr = re.sub(r'([0-9.]+)!', replace_factorial, expr)
        
        # Handle power operator
        expr = expr.replace('^', '**')
        
        # Evaluate the final expression
        result = eval(expr)
        
        # Format result
        if isinstance(result, complex):
            if result.imag == 0:
                result = result.real
            else:
                return f"{result.real}+{result.imag}j"
        
        if isinstance(result, float):
            if result == int(result):
                return str(int(result))
            else:
                return f"{result:.10g}"
        else:
            return str(result)
                
    except Exception as e:
        return "Error"


def insert_constant(constant, current):
    if constant == 'pi':
        value = str(math.pi)
    elif constant == 'e':
        value = str(math.e)
    
    # If display is "0" or "Error", just show the constant
    if current == "0" or current == "Error":
        return value
    
    # If last character is an operator, perform the operation
    if current[-1] in "+-*/^%":
        try:
            # Evaluate the expression with the constant
            expr = current + value
            expr = expr.replace('×', '*').replace('÷', '/')
            result = eval(expr)
            
            # Format the result
            if isinstance(result, complex):
                if result.imag == 0:
                    formatted_result = str(result.real)
                else:
                    formatted_result = f"{result.real}+{result.imag}j"
            else:
                formatted_result = str(int(result)) if result == int(result) else f"{result:.10g}"
            
            # Add to history
            history_entry = f"{current}{value} = {formatted_result}"
            calculator_state['history'].append(history_entry)
            if len(calculator_state['history']) > 50:
                calculator_state['history'].pop(0)
            
            return formatted_result
        except:
            return "Error"
    
    # If last character is '(', just insert the constant
    if current[-1] == '(':
        return current + value

    # Otherwise append the constant
    return current + value
   

if __name__ == '__main__':
    app.run(debug=True)