import os
import subprocess
import json
from langchain_core.tools import tool


@tool('calculator', description='Tool para fazer calculos. Usa isto para qualquer problema matemático')
def calculator(expression : str):
    """Avalia expressões matemáticas"""
    return str(eval(expression))