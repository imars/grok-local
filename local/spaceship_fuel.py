# spaceship_fuel.py
def calculate_fuel(distance, fuel_rate=0.5):
    """Calculate fuel needed for a distance at a given rate (fuel per unit distance)."""
    fuel_needed = distance * fuel_rate
    return fuel_needed

def main():
    print("Spaceship Fuel Simulator")
    distance = float(input("Enter travel distance (light-years): "))
    fuel = calculate_fuel(distance)
    print(f"Fuel required: {fuel:.2f} units")

if __name__ == "__main__":
    main()