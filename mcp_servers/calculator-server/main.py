import math
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Calculator MCP Server", version="1.0.0")

class ToolRequest(BaseModel):
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    content: str
    success: bool = True

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "server": "calculator-mcp"}

@app.get("/tools")
async def get_tools():
    """Get available tools"""
    return {
        "tools": [
            {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "advanced_math",
                "description": "Perform advanced mathematical operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "Operation to perform",
                            "enum": ["sqrt", "sin", "cos", "tan", "log", "ln", "exp", "factorial", "power"]
                        },
                        "value": {
                            "type": "number",
                            "description": "Input value"
                        },
                        "base": {
                            "type": "number",
                            "description": "Base for power or log operations",
                            "default": 10
                        }
                    },
                    "required": ["operation", "value"]
                }
            },
            {
                "name": "statistics",
                "description": "Calculate statistical measures for a list of numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "List of numbers"
                        },
                        "measures": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["mean", "median", "mode", "std", "var", "min", "max", "sum", "count"]
                            },
                            "description": "Statistical measures to calculate",
                            "default": ["mean", "median", "std"]
                        }
                    },
                    "required": ["numbers"]
                }
            },
            {
                "name": "unit_conversion",
                "description": "Convert between different units",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Value to convert"
                        },
                        "from_unit": {
                            "type": "string",
                            "description": "Source unit"
                        },
                        "to_unit": {
                            "type": "string", 
                            "description": "Target unit"
                        },
                        "category": {
                            "type": "string",
                            "description": "Unit category",
                            "enum": ["length", "weight", "temperature", "area", "volume"],
                            "default": "length"
                        }
                    },
                    "required": ["value", "from_unit", "to_unit"]
                }
            }
        ]
    }

@app.get("/resources")
async def get_resources():
    """Get available resources"""
    return {
        "resources": [
            {
                "uri": "calculator://constants",
                "name": "Mathematical Constants",
                "description": "List of mathematical constants"
            },
            {
                "uri": "calculator://functions",
                "name": "Available Functions",
                "description": "List of available mathematical functions"
            }
        ]
    }

def safe_eval(expression: str) -> float:
    """Safely evaluate a mathematical expression"""
    # Define allowed names for eval
    allowed_names = {
        "__builtins__": {},
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }
    
    # Remove any potentially dangerous characters/functions
    dangerous = ["import", "exec", "eval", "__", "open", "file", "input", "raw_input"]
    for danger in dangerous:
        if danger in expression.lower():
            raise ValueError(f"Dangerous operation detected: {danger}")
    
    try:
        result = eval(expression, allowed_names)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")

@app.post("/tools/calculate")
async def calculate(request: ToolRequest) -> ToolResponse:
    """Perform basic mathematical calculations"""
    try:
        expression = request.arguments.get("expression", "").strip()
        
        if not expression:
            raise HTTPException(status_code=400, detail="Expression is required")
        
        result = safe_eval(expression)
        
        response_text = f"Expression: {expression}\nResult: {result}"
        
        logger.info(f"Calculated: {expression} = {result}")
        return ToolResponse(content=response_text)
        
    except Exception as e:
        logger.error(f"Error calculating: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/advanced_math")
async def advanced_math(request: ToolRequest) -> ToolResponse:
    """Perform advanced mathematical operations"""
    try:
        operation = request.arguments.get("operation")
        value = request.arguments.get("value")
        base = request.arguments.get("base", 10)
        
        if not operation or value is None:
            raise HTTPException(status_code=400, detail="Operation and value are required")
        
        result = None
        
        if operation == "sqrt":
            if value < 0:
                raise ValueError("Cannot calculate square root of negative number")
            result = math.sqrt(value)
        elif operation == "sin":
            result = math.sin(math.radians(value))
        elif operation == "cos":
            result = math.cos(math.radians(value))
        elif operation == "tan":
            result = math.tan(math.radians(value))
        elif operation == "log":
            if value <= 0:
                raise ValueError("Cannot calculate logarithm of non-positive number")
            result = math.log(value, base)
        elif operation == "ln":
            if value <= 0:
                raise ValueError("Cannot calculate natural logarithm of non-positive number")
            result = math.log(value)
        elif operation == "exp":
            result = math.exp(value)
        elif operation == "factorial":
            if value < 0 or value != int(value):
                raise ValueError("Factorial requires non-negative integer")
            result = math.factorial(int(value))
        elif operation == "power":
            result = math.pow(value, base)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        response_text = f"Operation: {operation}({value}" + (f", {base}" if operation in ["log", "power"] else "") + f")\nResult: {result}"
        
        logger.info(f"Advanced math: {operation}({value}) = {result}")
        return ToolResponse(content=response_text)
        
    except Exception as e:
        logger.error(f"Error in advanced math: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/statistics")
async def statistics(request: ToolRequest) -> ToolResponse:
    """Calculate statistical measures"""
    try:
        numbers = request.arguments.get("numbers", [])
        measures = request.arguments.get("measures", ["mean", "median", "std"])
        
        if not numbers:
            raise HTTPException(status_code=400, detail="Numbers list is required")
        
        if not isinstance(numbers, list) or not all(isinstance(x, (int, float)) for x in numbers):
            raise HTTPException(status_code=400, detail="Numbers must be a list of numeric values")
        
        results = {}
        
        if "mean" in measures:
            results["mean"] = sum(numbers) / len(numbers)
        
        if "median" in measures:
            sorted_nums = sorted(numbers)
            n = len(sorted_nums)
            if n % 2 == 0:
                results["median"] = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
            else:
                results["median"] = sorted_nums[n//2]
        
        if "mode" in measures:
            from collections import Counter
            counts = Counter(numbers)
            max_count = max(counts.values())
            modes = [k for k, v in counts.items() if v == max_count]
            results["mode"] = modes[0] if len(modes) == 1 else modes
        
        if "std" in measures:
            mean = sum(numbers) / len(numbers)
            variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
            results["std"] = math.sqrt(variance)
        
        if "var" in measures:
            mean = sum(numbers) / len(numbers)
            results["var"] = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        
        if "min" in measures:
            results["min"] = min(numbers)
        
        if "max" in measures:
            results["max"] = max(numbers)
        
        if "sum" in measures:
            results["sum"] = sum(numbers)
        
        if "count" in measures:
            results["count"] = len(numbers)
        
        response_lines = [f"Statistics for {len(numbers)} numbers:"]
        for measure, value in results.items():
            response_lines.append(f"{measure}: {value}")
        
        response_text = "\n".join(response_lines)
        
        logger.info(f"Statistics calculated for {len(numbers)} numbers")
        return ToolResponse(content=response_text)
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Unit conversion factors (to base unit)
CONVERSION_FACTORS = {
    "length": {
        "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
        "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.34
    },
    "weight": {
        "mg": 0.001, "g": 1.0, "kg": 1000.0, "t": 1000000.0,
        "oz": 28.3495, "lb": 453.592, "st": 6350.29
    },
    "temperature": {
        # Special handling required
    },
    "area": {
        "mm2": 0.000001, "cm2": 0.0001, "m2": 1.0, "km2": 1000000.0,
        "in2": 0.00064516, "ft2": 0.092903, "yd2": 0.836127, "acre": 4046.86
    },
    "volume": {
        "ml": 0.001, "l": 1.0, "m3": 1000.0,
        "fl_oz": 0.0295735, "cup": 0.236588, "pt": 0.473176, "qt": 0.946353, "gal": 3.78541
    }
}

@app.post("/tools/unit_conversion")
async def unit_conversion(request: ToolRequest) -> ToolResponse:
    """Convert between different units"""
    try:
        value = request.arguments.get("value")
        from_unit = request.arguments.get("from_unit", "").lower()
        to_unit = request.arguments.get("to_unit", "").lower()
        category = request.arguments.get("category", "length").lower()
        
        if value is None or not from_unit or not to_unit:
            raise HTTPException(status_code=400, detail="Value, from_unit, and to_unit are required")
        
        if category == "temperature":
            # Special handling for temperature
            result = convert_temperature(value, from_unit, to_unit)
        else:
            if category not in CONVERSION_FACTORS:
                raise ValueError(f"Unknown category: {category}")
            
            factors = CONVERSION_FACTORS[category]
            
            if from_unit not in factors:
                raise ValueError(f"Unknown unit '{from_unit}' for category '{category}'")
            if to_unit not in factors:
                raise ValueError(f"Unknown unit '{to_unit}' for category '{category}'")
            
            # Convert to base unit, then to target unit
            base_value = value * factors[from_unit]
            result = base_value / factors[to_unit]
        
        response_text = f"Conversion: {value} {from_unit} = {result} {to_unit}"
        
        logger.info(f"Unit conversion: {value} {from_unit} -> {result} {to_unit}")
        return ToolResponse(content=response_text)
        
    except Exception as e:
        logger.error(f"Error in unit conversion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert temperature between different units"""
    # Convert to Celsius first
    if from_unit == "f" or from_unit == "fahrenheit":
        celsius = (value - 32) * 5/9
    elif from_unit == "k" or from_unit == "kelvin":
        celsius = value - 273.15
    elif from_unit == "c" or from_unit == "celsius":
        celsius = value
    else:
        raise ValueError(f"Unknown temperature unit: {from_unit}")
    
    # Convert from Celsius to target
    if to_unit == "f" or to_unit == "fahrenheit":
        return celsius * 9/5 + 32
    elif to_unit == "k" or to_unit == "kelvin":
        return celsius + 273.15
    elif to_unit == "c" or to_unit == "celsius":
        return celsius
    else:
        raise ValueError(f"Unknown temperature unit: {to_unit}")

@app.get("/resources/calculator://constants")
async def get_constants():
    """Get mathematical constants"""
    constants = {
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "golden_ratio": (1 + math.sqrt(5)) / 2,
        "euler_gamma": 0.5772156649015329
    }
    
    content_lines = ["Mathematical Constants:"]
    for name, value in constants.items():
        content_lines.append(f"{name}: {value}")
    
    return {
        "content": "\n".join(content_lines),
        "mimeType": "text/plain"
    }

@app.get("/resources/calculator://functions")
async def get_functions():
    """Get available mathematical functions"""
    functions = [
        "Basic: +, -, *, /, %, ** (power)",
        "Trigonometric: sin, cos, tan (in degrees)",
        "Logarithmic: log (base 10), ln (natural log)",
        "Exponential: exp, sqrt",
        "Statistical: mean, median, mode, std, var, min, max, sum, count",
        "Unit conversion: length, weight, temperature, area, volume"
    ]
    
    return {
        "content": "Available Mathematical Functions:\n" + "\n".join(f"- {func}" for func in functions),
        "mimeType": "text/plain"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
