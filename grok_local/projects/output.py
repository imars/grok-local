import sys

input_line = sys.stdin.read().strip()

parts = input_line.split()
if len(parts) != 2:
    print("Error: Invalid input")
    sys.exit(1)

number1 = int(parts[0])
number2 = int(parts[1])

sum_numbers = number1 + number2
print(f"The sum of {number1} and {number2} is {sum_numbers}")