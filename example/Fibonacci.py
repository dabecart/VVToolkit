import sys

# Function for nth fibonacci number 
def fibonacci(n):
    a = 0
    b = 1
     
    # Check is n is less than 0
    if n < 0:
        print("Incorrect input")
         
    # Check is n is equal to 0
    elif n == 0:
        return 0
       
    # Check if n is equal to 1
    elif n == 1:
        return b
    else:
        for _ in range(1, n):
            c = a + b
            a = b
            b = c
        return b
    
if __name__ == "__main__":
   print(fibonacci(int(sys.argv[1])))