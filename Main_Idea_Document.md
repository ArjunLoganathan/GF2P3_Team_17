### Main Ideas

## Parser

# Device definitions 

1. Have an "include" keyword to allow various devices (such as 2 bit adder, SR nor latch etc) to be read at compile time
1.1. This allows definitions to be "packaged" and stored as .txt files to be saved and stored later
1.2. Will allow for compound devices, such as RAM or higher bit adders to be created.


## GUI Ideas

# Display

1. Have interactable visual drag and drop to potentially generate a new definition file to both display previously written files visually and edit them to easily. May make it easier to debug intended behaviours - probably complex
2. Have a device definer GUI to create devices with the devices you already have, package them into a module and be able to drag and drop this new module into new circuits
2.1. Example - package 2 bit adder and draw a new symbol for it to be used in subsequent "modules" 
2.2. This process must be efficient to ensure compounded circuit definitions aren't redefined and reread too many times in memeory
2.3. Will allow for complex structures to be created such as 2^n bit adders, multipliers etc. 
2.4. Could also package current state of a "module" to be able to store things in "memory" such as a storage module to save various data structures
2.5. Potentially add a 7 segment display
