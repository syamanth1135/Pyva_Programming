from flask import Flask, request, jsonify, render_template
import io
import contextlib
import pyva_compiler

app = Flask(__name__)

def execute_pyva_code(code, inputs):
    try:
        output = io.StringIO()
        inputs = inputs.split('\n')
        input_index = 0
        def mock_input(prompt=''):
            nonlocal input_index
            if input_index < len(inputs):
                result = inputs[input_index]
                input_index += 1
                return result
            else:
                return ''
        import builtins
        old_input = builtins.input
        builtins.input = mock_input
        with contextlib.redirect_stdout(output):
            pyva_compiler.run_program(code)
        builtins.input = old_input
        return output.getvalue().strip()
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_code():
    code = request.json['code']
    inputs = request.json.get('inputs', '')
    output = execute_pyva_code(code, inputs)
    return jsonify({'output': output})

if __name__ == '__main__':
    app.run(debug=True)