# we will use ruff and radon/lizard + vulture her to get findings


from concurrent.futures import ThreadPoolExecutor
import subprocess

def run_ruff(file_path : str) -> str:
    result = subprocess.run(["ruff","check",file_path],capture_output = True , text = True)
    return result.stdout

result = run_ruff("app.py")
print(result)

# cc , mi , raw , hal

def run_radon(task : str , file_path : str) -> str:
    result = subprocess.run(["radon" , task , file_path],
    capture_output = True , text = True)

    return result.stdout



radon_tasks = [ "cc" , "mi" , "raw" , "hal" ]

with ThreadPoolExecutor(max_workers = 4) as executor:
        results = list(executor.map(run_radon , radon_tasks , ["app.py"] * 4))


print(results)