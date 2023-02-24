import module_lib_test

print("module_main_test.py __name__ = %s" %__name__)

if __name__ == "__main__":
    print("Hola")
    module_lib_test.function()
    try:
        print("Global", module_lib_test.local_variable)
    except Exception as e:
        print("Error: %s" %e)
    
    # now try inventing a new global, which might be bad practice but who cares
    module_lib_test.local_variable = 3
    module_lib_test.function()
    print("Global", module_lib_test.local_variable)

    print(vars(module_lib_test.function.__code__))
