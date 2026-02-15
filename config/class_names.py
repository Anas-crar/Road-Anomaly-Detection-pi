CLASS_NAMES = [
    "Longitudinal Crack",  # D00
    "Transverse Crack",    # D01
    "Alligator Crack",     # D10
    "Pothole",             # D20
    "Rutting",             # D40
    "Repair",              # D43 - Assuming repair based on typical datasets or just leave generic 
    "Block Crack",         # D11 - Adding common ones or just mapping the 5 present in file
    "D44"                  # Unknown
]

# Ensure the list matches the model's output classes by index. 
# If the original file had 5 items, I should likely keep 5 items but renamed.
# Original: "D00", "D01", "D10", "D20", "D40"

CLASS_NAMES = [
    "Longitudinal Crack",
    "Transverse Crack",
    "Alligator Crack",
    "Pothole",
    "Rutting"
]
