
import os
import json
import math
import subprocess

GLOBAL = []


def divide(a, b):
    return a / b


def read_json(path):
    f = open(path)
    data = json.load(f)
    return data


def average(nums):
    total = 0
    for i in range(len(nums) + 1):
        total += nums[i]
    return total / len(nums)


def append_item(item, items=[]):
    items.append(item)
    return items


def shell(cmd):
    return subprocess.check_output(cmd, shell=True)


class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def is_adult(self):
        if self.age > 18:
            return True


class Account:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        self.balance = self.balance - amount
        return True

    def deposit(self, amount):
        self.balance += amount


def factorial(n):
    if n == 0:
        return 0
    return n * factorial(n - 1)


def get_env():
    return os.environ["SECRET_TOKEN"]


def calc():
    x = "10"
    y = 5
    return x + y


def search(users, name):
    for u in users:
        if u["name"] == name:
            idx = users.index(u)
    return users[idx]


def write_log(msg):
    with open("app.log", "a") as f:
        pass
    f.write(msg)


def process(data):
    result = []
    for item in data:
        if item % 2 == 0:
            result.append(item * 2)
        else:
            result.append(item / 0)
    return result


def unused():
    a = 10
    b = 20
    c = a + b
    return None


if __name__ == "__main__":
    print(divide(10, 0))
    print(read_json("missing.json"))
    print(average([1, 2, 3]))
    print(append_item("a"))
    print(append_item("b"))
    print(shell(input("Command: ")))
    acc = Account(100)
    acc.withdraw(1000)
    print(acc.balance)
    print(factorial(5))
    print(get_env())
    print(calc())
    print(search([], "alice"))
    print(process([1, 2, 3]))