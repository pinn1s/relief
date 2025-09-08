# relief interpreter

#!/usr/bin/env python3
import sys
import re
import time

env = {}

# custom exception to stop execution
class StopExe(Exception):
    pass

def eval_expr(expr: str):
    """evaluate math/variables or return string in relief code"""
    expr = expr.strip()
    try:
        # handle string assignment
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # replace variable names with values from env
        for var, val in env.items():
            # whole word replacement
            expr = re.sub(rf'\b{var}\b', str(val), expr)

        return eval(expr)
    except Exception as e:
        print(f"ERROR: {e} from '{expr}'")
        return None

def run_relief(code: str):
    match = re.search(r"when project start\s*{([\s\S]*)}", code)
    if not match:
        print("ERROR: entry point not found")
        return

    body = match.group(1).strip().splitlines()
    i = 0
    while i < len(body):
        line = body[i].strip()

        if not line:
            i += 1
            continue

        # stop()
        if line.startswith("stop()"):
            raise StopExe()

        # wait.time()
        elif line.startswith("wait."):
            m = re.match(r"wait\.(\w+)\((\d+)\)", line)
            if m:
                unit, value = m.groups()
                value = int(value)
                if unit == "milsec":
                    time.sleep(value / 1000.0)
                elif unit == "sec":
                    time.sleep(value)
                elif unit == "min":
                    time.sleep(value * 60)
                elif unit == "hrs":
                    time.sleep(value * 3600)
                else:
                    print(f"ERROR: unknown '{unit}'")

        # var = expr
        elif "=" in line and not line.startswith("if"):
            var, val = line.split("=", 1)
            var = var.strip()
            val = eval_expr(val)
            env[var] = val

        # out
        elif line.startswith("out"):
            m = re.match(r"out\s*\(\s*(.*)\s*\)", line)
            if m:
                content = m.group(1)
                result = eval_expr(content)
                if result is not None:
                    print(result)

        # rep
        elif line.startswith("rep"):
            times = re.search(r"rep\s+(\d+)\s*{", line)
            if times:
                count = int(times.group(1))
                block = []
                i += 1
                while i < len(body) and "}" not in body[i]:
                    block.append(body[i])
                    i += 1
                for _ in range(count):
                    run_relief("when project start { " + "\n".join(block) + " }")
            else:
                print(f"ERROR: invalid rep syntax in line {line}")

        # if
        elif line.startswith("if"):
            m = re.search(r"if\s*\((.*)\)\s*{", line)
            if m:
                cond = m.group(1)
                condition_result = eval_expr(cond)
                block = []
                i += 1
                while i < len(body) and "}" not in body[i]:
                    block.append(body[i])
                    i += 1
                if condition_result:
                    run_relief("when project start { " + "\n".join(block) + " }")
            else:
                print(f"ERROR: invalid if syntax in line: {line}")

        i += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: python interpreter.py YOUR_PROJECT_HERE.relief")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r") as f:
        code = f.read()
    try:
        run_relief(code)
    except StopExe:
        print("STOPPED: execution stopped by stop()")
