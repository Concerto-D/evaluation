import os
import yaml


errors = []


def check_log(output, name, file_name, up="start", down="end"):
    if any(name in k for k in output.keys()):
        if not (f"{up}_{name}" in output.keys() and f"{down}_{name}" in output.keys()):
            print(f"{name} ERROR, ONLY ONE")
            errors.append((name, file_name))
            for k, v in output.items():
                print(k, v)
            return 0
        else:
            return output[f"{down}_{name}"] - output[f"{up}_{name}"]
    return 0

for file_name in os.listdir("/tmp"):
    if "dep" in file_name or "server" in file_name:
        with open(f"/tmp/{file_name}") as f:
            output = yaml.safe_load(f)
            print(f"---- {file_name} ----")
            uptime = 0
            ls = 0
            d = 0
            u = 0
            ss = 0
            uptime += check_log(output, "time", file_name, up="up", down="sleep")
            ls += check_log(output, "loading_state", file_name)
            d += check_log(output, "deploy", file_name)
            u += check_log(output, "update", file_name)
            ss += check_log(output, "saving_state", file_name)
            print(f"uptime: {uptime}")
            print(f"ls: {ls}")
            print(f"d: {d}")
            print(f"u: {u}")
            print(f"ss: {ss}")
            print("-----------------------")


if not errors:
    print("no errors")
else:
    print("errors:")
    for e in errors:
        print(e)