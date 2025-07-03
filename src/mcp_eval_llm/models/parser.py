import ast
import json
import re
from collections import Counter
import base64
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
import numpy as np

def stringify(data):
    '''
    Handle some data types that can not be json dumped.
    '''
    if isinstance(data, (str, int, float, bool, type(None))):
        return str(data)
    elif isinstance(data, (list, tuple, set)):
        return '[' + ', '.join(stringify(item) for item in data) + ']'
    elif isinstance(data, dict):
        items = (stringify(key) + ': ' + stringify(value) for key, value in data.items())
        return '{' + ', '.join(items) + '}'
    else:
        return str(data)
        
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                            np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return self.default(obj.tolist())  # Recursively apply conversion
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        
        # Handle additional types
        elif isinstance(obj, (Decimal)):
            return float(obj)
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, (bytes, bytearray)):
            return base64.b64encode(obj).decode('utf-8')
        elif isinstance(obj, Enum):
            return obj.value
        
        elif isinstance(obj, (set,)):
            return self.default(list(obj))  # Convert set to list then process recursively
        elif isinstance(obj, (list, tuple)):
            return [self.default(item) for item in obj]  # Recursively apply to each item
        elif isinstance(obj, dict):
            # Convert keys that are not str, int, float, bool or None to a string
            processed_dict = {}
            for key, value in obj.items():
                if not isinstance(key, (str, int, float, bool, type(None))):
                    key = str(key)  # Convert tuple keys and other non-standard types to string
                processed_dict[self.default(key)] = self.default(value)
            return processed_dict
        elif isinstance(obj, complex):
            return str(obj)  # Convert complex numbers to string
        return str(obj)  # Fallback to string for any other unhandled types

    
def try_fix_json(json_str, max_depth=5):
    """
    Attempts to correct common JSON formatting errors in a given string to make it valid.
    
    The function recursively tries to fix errors detected by the json.loads method by
    addressing known error patterns such as extra data, missing commas, unterminated strings,
    invalid control characters, and missing brackets. It stops if the maximum recursion depth
    (max_depth) is exceeded to prevent infinite loops.
    
    Parameters:
    - json_str (str): The JSON string that potentially contains formatting errors.
    - max_depth (int): The maximum depth of recursive calls to prevent infinite recursion.
                       Default is 10.
    
    Returns:
    - tuple: 
        - A string that is either the corrected JSON or the best attempt at correction.
        - A boolean indicating whether the correction was successful (True) or not (False).
        - A list of strings describing each correction attempt made.
    
    Raises:
    - RecursionError: If the recursion depth exceeds the maximum depth allowed.
    
    Example Usage:
    --------------
    input_str = '{"key1": "value1" "key2": "value2"}'  # Missing comma between items
    fixed_json, success, fix_history = try_fix_json(input_str)
    
    if success:
        print("Fixed JSON:", fixed_json)
        print("Fixing History:")
        for msg in fix_history:
            print("- " + msg)
    else:
        print("Failed to fix JSON. Invalid format.")
    
    Note:
    - This function can handle a variety of common JSON format issues but is not guaranteed
      to fix all possible errors. It is recommended to manually review the corrections made,
      especially in critical applications.
    """
    fix_history = []

    def _try_fix_json(json_str, depth=0):
        if depth > max_depth:
            return json_str, False, fix_history + [
                "Max depth exceeded. Stopping to prevent infinite loop."
            ]

        try:
            parsed = json.loads(json_str)
            return json.dumps(parsed), True, fix_history
        except json.JSONDecodeError as e:
            error_msg = str(e)

            # a special case that the model outputs contents more than specified
            # extract the string between ```{xxx}```

            # Pattern to match content within triple backticks, optionally starting with 'json'
            json_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
            json_match = json_pattern.search(json_str)
            if not json_match:
                # Try matching without the 'json' keyword if the first attempt fails
                json_pattern = re.compile(r'```(.*?)```', re.DOTALL)
                json_match = json_pattern.search(json_str)
            if json_match:
                json_str = json_match.group(1).strip()
                # fix_history.append(f"Removed extra data (``` symbols) to extract json")

            # Handle invalid escape sequences
            if "Invalid \escape" in error_msg:
                # Replace invalid escape sequences (\x where x is not a valid escape character)
                json_str = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_str)
                fix_history.append("Corrected invalid escape sequences")
                return _try_fix_json(json_str, depth + 1)

            if "Extra data" in error_msg:
                extra_data_pos = int(
                    re.findall(r'\(char (\d+)\)', error_msg)[0])
                fix_history.append(
                    f"Removed extra data at position {extra_data_pos}")
                return _try_fix_json(json_str[:extra_data_pos], depth + 1)

            elif "Expecting ',' delimiter" in error_msg or "Expecting property name enclosed in double quotes" in error_msg:
                expecting_pos = int(
                    re.findall(r'\(char (\d+)\)', error_msg)[0])
                if expecting_pos < len(json_str):
                    if json_str[expecting_pos] == '"':
                        fix_history.append(
                            f"Added missing ',' delimiter before position {expecting_pos}"
                        )
                        return _try_fix_json(
                            json_str[:expecting_pos] + ',' +
                            json_str[expecting_pos:], depth + 1)
                    elif json_str[expecting_pos] in ['}', ']']:
                        fix_history.append(
                            f"Added missing ',' delimiter at position {expecting_pos}"
                        )
                        return _try_fix_json(
                            json_str[:expecting_pos] + ',' +
                            json_str[expecting_pos:], depth + 1)
                fix_history.append(f"Added missing ',' delimiter at the end")
                return _try_fix_json(json_str + ',', depth + 1)

            elif "Expecting value" in error_msg:
                expecting_pos = int(
                    re.findall(r'\(char (\d+)\)', error_msg)[0])
                if expecting_pos < len(
                        json_str) and json_str[expecting_pos] in [
                            ',', '}', ']'
                        ]:
                    fix_history.append(
                        f"Added missing value 'null-jianguo' at position {expecting_pos}"
                    )
                    return _try_fix_json(
                        json_str[:expecting_pos] + 'null-jianguo' +
                        json_str[expecting_pos:], depth + 1)
                fix_history.append(f"Added missing value 'null-jianguo' at the end")
                return _try_fix_json(json_str + 'null-jianguo', depth + 1)

            elif "Unterminated string starting at" in error_msg:
                unterminated_pos = int(
                    re.findall(r'\(char (\d+)\)', error_msg)[0])
                fix_history.append(
                    f"Terminated unterminated string at position {unterminated_pos}"
                )
                return _try_fix_json(
                    json_str[:unterminated_pos] + '"' +
                    json_str[unterminated_pos:], depth + 1)

            elif "Invalid control character at" in error_msg:
                invalid_pos = int(re.findall(r'\(char (\d+)\)', error_msg)[0])
                fix_history.append(
                    f"Removed invalid control character at position {invalid_pos}"
                )
                return _try_fix_json(
                    json_str[:invalid_pos] + json_str[invalid_pos + 1:],
                    depth + 1)

            elif "Expecting '}'" in error_msg or "Expecting ']'" in error_msg:
                fix_history.append(f"Added missing closing bracket at the end")
                return _try_fix_json(
                    json_str + ('}' if "Expecting '}'" in error_msg else ']'),
                    depth + 1)

        return json_str, False, fix_history

    return _try_fix_json(json_str)


def get_fixed_tool_calls_or_text_output(json_str, max_depth=5):
    text_output = try_fix_json(json_str, max_depth)
    if text_output[1] is True:
        parsed_text_out = text_output[0]
        return json.loads(parsed_text_out), "api_tool_calls"
    else:
        parsed_text_out = text_output[0].split("null-jianguo", 1)[0].strip()
        return parsed_text_out, "api_text_output"
    
    
def convert_json_string_to_dict(input_str):
    """
    Convert the input JSON string to a dictionary with tool_call names as keys
    and their arguments as values. This function will also handle minor format issues.

    Parameters:
    - input_str: A JSON-formatted string containing 'tool_calls' with 'name' and 'arguments'.

    Returns:
    - A dictionary with tool_call names as keys and their arguments as dictionary values.
    """
    # Parse the JSON string to a Python dictionary
    # print("=" * 20)

    # print(input_str)
    input_str, success, fix_history = try_fix_json(input_str, max_depth=3)
    if success:
        data = json.loads(input_str)
    else:
        return {}, success, fix_history
    
    result_list = []

    if isinstance(data, list):
        tool_calls = data
    elif isinstance(data, dict):
        tool_calls = data.get('tool_calls', [])
    else:
        tool_calls = []
    # print("tool_calls: ")
    # Iterate through each tool_call in the input data
    for tool_call in tool_calls:
        # Initialize an empty dictionary to hold the conversion result
        result_dict = {}
        # print(tool_call)
        # Extract the name and arguments of the tool_call
        if isinstance(tool_call, dict):
            name = tool_call.get('name', "")
            arguments = tool_call.get('arguments', {})
            # Add them to the result dictionary
            result_dict[name] = arguments
        else:
            print(tool_call)
            
        result_list.append(result_dict)
        
    return result_list, success, fix_history

def python_to_flatten_json_tool_calls(python_format, openai_format=False):
    """
    Converts a list of function calls in Python format to flatten JSON format.
    This version handles multiple levels of attributes using recursion to accommodate nested structures.
    
    Parameters:
    python_format (list): A list of strings, where each string is a function call in Python format.
    
    Returns:
    json_format (list): A list of dictionaries representing the function calls in flattened JSON format.
    info (list): A list of meta information during format conversion.
    """

    if not isinstance(python_format, list):
        python_format = [python_format]

    def get_full_function_name(node):
        """
        Recursively builds the full function name from nested attribute calls.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return get_full_function_name(node.value) + '.' + node.attr
        else:
            return ""

    info = []

    json_format = []
    for call in python_format:
        call = call.strip()  # Remove leading/trailing whitespaces
        try:
            tree = ast.parse(call, mode='eval')
        except SyntaxError as e:
            info.append(f"Error parsing {call}: {e}")
            continue
        
        if isinstance(tree.body, ast.Call):
            func_call = tree.body
            full_func_name = get_full_function_name(func_call.func)
            args_dict = {}
            
            for keyword in func_call.keywords:
                # Attempt to use literal_eval to evaluate the argument value safely
                try:
                    value = ast.literal_eval(keyword.value)
                except (ValueError, SyntaxError):
                    # If literal_eval fails, fall back to using the string representation
                    value = ast.unparse(keyword.value).strip()
                args_dict[keyword.arg] = value

            # openai doesn't support function call type xxx.yyy, so convert it to xxx_yyy
            if openai_format:
                full_func_name = re.sub(r"\.", "_", full_func_name)

            json_format.append({full_func_name: args_dict})
    
    return json_format, info


def flatten_json_to_python_tool_calls(json_format):
    """
    Converts a list of function calls in flatten JSON format to Python format.
    
    Parameters:
    json_format (list): A list of dictionaries, where each dictionary represents a function call in flatten JSON format.
    
    Returns:
    python_format (list): A list of strings, where each string is a function call in Python format.
    """
    if not isinstance(json_format, list):
        json_format = [json_format]
    python_format = []
    for call in json_format:
        for func_name, args in call.items():
            # Constructing argument strings, ensuring correct formatting for nested structures
            args_str = ', '.join([f"{key}={repr(value)}" for key, value in args.items()])
            python_format.append(f"{func_name}({args_str})")
    return python_format

def python_to_api_json_tool_calls(python_format, openai_format=False):
    """
    Converts a list of function calls in Python format to API/OpenAI JSON format.
    This version handles multiple levels of attributes using recursion to accommodate nested structures.
    
    Parameters:
    python_format (list): A list of strings, where each string is a function call in Python format.
    
    Returns:
    json_format (list): A list of dictionaries representing the function calls in API/OpenAI JSON format.
    info (list): A list of meta information during format conversion.
    """
    flatten_json_list, info = python_to_flatten_json_tool_calls(python_format, openai_format)
    api_json = []
    for flatten_json in flatten_json_list:
        for func_name, args in flatten_json.items():
            api_json.append(
                {
                    "name": func_name,
                    "arguments": args
                }
            )
    return api_json, info


def api_json_to_python_tool_calls(tool_calls):
    """
    Converts a list of function calls in API JSON format to Python format.
    
    Parameters:
    json_format (list): A list of dictionaries, where each dictionary represents a function call in API JSON format.
    
    Returns:
    python_format (list): A list of strings, where each string is a function call in Python format.
    """
    if not isinstance(tool_calls, list):
        tool_calls = [tool_calls]

    tool_calls_flatten = []
    for tool_call in tool_calls:
        # Initialize an empty dictionary to hold the conversion result
        result_dict = {}
        # print(tool_call)
        # Extract the name and arguments of the tool_call
        if isinstance(tool_call, dict):
            name = tool_call.get('name', "")
            arguments = tool_call.get('arguments', {})
            # Add them to the result dictionary
            result_dict[name] = arguments
        else:
            print(tool_call)
            
        tool_calls_flatten.append(result_dict)
    return flatten_json_to_python_tool_calls(tool_calls_flatten)

def compute_json_match(converted, groundtruth):
    """
    Computes whether the converted JSON format matches the groundtruth JSON data, handling special cases for argument matching.
    
    Parameters:
    converted (list): A list of dictionaries representing the function calls in converted JSON format.
    groundtruth (list): A list of dictionaries representing the function calls in groundtruth JSON format.
    
    Returns:
    match (bool): True if the converted and groundtruth JSON formats match exactly, False otherwise.
    match_score (float): The percentage of functions and arguments that match with the groundtruth, considering special cases.
    """
    def normalize_value(value):
        """
        Normalize boolean and numeric values for comparison.
        Converts strings that represent boolean values to boolean, and attempts to convert numeric strings to numbers.
        """
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            try:
                # Attempt to convert string to integer, then to float if unsuccessful
                return float(value)
            except ValueError:
                try:
                    return int(value)
                except ValueError:
                    return value.lower()
        else:
            return value
    
    def compare_values(value1, value2):
        """
        Compares two values after normalization.
        """
        return normalize_value(value1) == normalize_value(value2)

    converted = converted if isinstance(converted, list) else [converted]
    groundtruth = groundtruth if isinstance(groundtruth, list) else [groundtruth]
    total_functions = len(groundtruth)
    match_functions = 0
    total_arguments = 0
    match_arguments = 0
    
    for i, gt_call in enumerate(groundtruth):
        if i < len(converted) and gt_call.keys() == converted[i].keys():
            # Function name matches
            match_functions += 1
            func_name = list(gt_call.keys())[0]
            gt_args = gt_call[func_name]
            conv_args = converted[i][func_name]
            total_arguments += len(gt_args)
            match_arguments += sum(1 for arg in gt_args if arg in conv_args and compare_values(gt_args[arg], conv_args[arg]))
            
    match_score = ((match_functions + match_arguments) / (total_functions + total_arguments)) if (total_functions + total_arguments) > 0 else 0
    match = match_score == 1
    return match, match_score


def compute_python_match(converted, groundtruth):
    """
    Computes whether the converted Python format matches the groundtruth Python data.
    
    Parameters:
    converted (str): A string representing the function calls in converted Python format.
    groundtruth (str): A string representing the function calls in groundtruth Python format.
    
    Returns:
    match (bool): True if the converted and groundtruth Python formats match exactly, False otherwise.
    match_score (float): The percentage of functions and arguments that match with the groundtruth.
    """
    
    converted = ''.join(converted) if isinstance(converted, list) else converted
    groundtruth = ''.join(groundtruth) if isinstance(groundtruth, list) else groundtruth

    # Handle special cases:
    # Normalize double to single quotes
    converted = converted.replace('"', "'")
    groundtruth = groundtruth.replace('"', "'")
    
    # Normalize boolean values
    converted = converted.replace("true", "True").replace("false", "False")
    groundtruth = groundtruth.replace("true", "True").replace("false", "False")
    
    # Additional normalization could include:
    # - Removing or standardizing whitespace
    converted = ''.join(converted.split())
    groundtruth = ''.join(groundtruth.split())

    match = (converted == groundtruth)
    
    counter1 = Counter(converted)
    counter2 = Counter(groundtruth)
    
    # Intersection of both Counters gives common elements and their minimum counts
    common = counter1 & counter2
    total_common = sum(common.values())
    
    # The total possible is the sum of the counts in both strings
    total_possible = len(converted) + len(groundtruth)
    
    # The similarity score is twice the count of common elements divided by the total possible count
    # This is because each common element is counted twice, once in each string
    similarity_score = (2 * total_common) / total_possible if total_possible > 0 else 0
    
    return match, similarity_score

def convert_to_python_function_code(functions):
    """
    Converts a list of API function metadata into Python function definitions.

    This function processes each API function's metadata to generate a Python function definition with
    parameters, type annotations, and a docstring describing its purpose and parameters.

    Args:
        functions (list of dict): A list of dictionaries, each containing metadata about a function. Expected keys:
                                  - 'name' (str): Function name.
                                  - 'description' (str): Description of the function.
                                  - 'parameters' (dict): Dictionary of parameter names to their details, which
                                                         include 'type' (str), 'description' (str), 'example_value'
                                                         (optional), and 'required' (bool).

    Returns:
        str: A string containing the generated Python function definitions with detailed docstrings.
    """
    code_output = ""
    for function in functions:
        func_name = function['name']
        func_desc = function['description']
        params = function['parameters']
        
        param_str = []
        docstring = f'"""{func_desc}\n\nArgs:\n'
        for param_name, param_details in params.items():
            param_type = param_details['type']
            param_desc = param_details['description']
            example_value = param_details.get('example_value', None)
            required = param_details.get('required', True)
            
            # Pythonic default handling
            default_value = f' = {example_value!r}' if not required else ''
            param_str.append(f"{param_name}: {param_type}{default_value}")
            
            # Docstring details
            docstring += f"\t{param_name} ({param_type}): {param_desc}"
            if example_value:
                docstring += f" Example: {example_value}"
            docstring += "\n"
        
        docstring += '"""'
        
        # Join all parameters with commas and add type annotations
        param_str = ', '.join(param_str)
        function_def = f"def {func_name}({param_str}):\n{docstring}\n    pass\n\n"
        code_output += function_def
        
    return code_output

def convert_python_code_to_api_json(python_functions: list):
    """
    Converts a list of Python function definitions into a JSON format that includes function metadata
    such as name, description, parameters with their types, default values, and descriptions.

    Args:
        python_functions (list): A list containing Python function codes as strings.

    Returns:
        A list of JSON dictionary or a string of error message if the conversion is failed.
    """

    def _get_type_annotation(arg):
        """
        Extracts type annotation from an AST node, supporting basic types and generics.
        """
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                return arg.annotation.id
            elif isinstance(arg.annotation, ast.Subscript):  # For generics
                return ast.unparse(arg.annotation)
            else:
                return "ComplexType"
        return "Unknown"

    def _extract_param_type(docstring, param_name):
        """
        Extracts the parameter type from the function's docstring.
        """
        if docstring:
            pattern = re.escape(param_name) + r"\s*\((.*?)\):"
            match = re.search(pattern, docstring)
            if match:
                return match.group(1).strip()
        return "Unknown"

    def _get_default_value(arg, args):
        """
        Safely extract default values, handling complex expressions.
        """
        defaults_index = len(args.args) - len(args.defaults) + args.args.index(arg)
        if len(args.defaults) > defaults_index - len(args.args):
            default = args.defaults[defaults_index - len(args.args)]
            try:
                return ast.literal_eval(default)
            except ValueError:
                return ast.unparse(default)  # Fallback to unparsing the AST node
        return None

    def _extract_param_description(docstring, param_name):
        """
        Extracts the parameter description from the function's docstring.
        """
        if docstring:
            pattern = re.escape(param_name) + r"\s*\(.*?\):\s*(.*?)(?:\n|$)"
            match = re.search(pattern, docstring, re.DOTALL)
            if match:
                return match.group(1).strip()
        return "No description provided."
    
    def _extract_function_details(func_def):
        """
        Extracts details from a function definition node.

        Args:
            func_def (ast.FunctionDef): The function definition node from the AST.

        Returns:
            dict: A dictionary containing the function's name, description, and parameters with details.
        """
        name = func_def.name
        args = func_def.args
        docstring = ast.get_docstring(func_def)
        description = docstring.split('\n')[0] if docstring else 'No description provided.'

        params = {}
        for arg in args.args:
            param_name = arg.arg
            # Attempt to extract type from docstring or use ast or fall back to 'Unknown'
            param_type = _extract_param_type(docstring, param_name)
            if param_type == "Unknown":
                param_type = _get_type_annotation(arg)

            default_value = _get_default_value(arg, args)

            params[param_name] = {'description': _extract_param_description(docstring, param_name)}
            if param_type != "Unknown":
                params[param_name]['type'] = param_type
            if default_value:
                params[param_name]['default'] = default_value

        return {
            'name': name,
            'description': description,
            'parameters': params
        }
    
    if not isinstance(python_functions, list):
        python_functions = [python_functions]

    try:
        functions_details = [_extract_function_details(ast.parse(func_code).body[0]) for func_code in python_functions]
        # try whether it it is serializable
        test_string = json.dumps(functions_details)
        return functions_details
    except Exception as e:
        return e