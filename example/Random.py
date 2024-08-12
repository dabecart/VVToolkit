import sys
import random
    
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Error: two integer arguments are needed!")
        exit(-1)

    val = random.randint(int(sys.argv[1]), int(sys.argv[2]))
    print(val)