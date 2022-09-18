def foo(x:int):
    try:
        assert x > 10\
            , "hello world"
    except AssertionError:
        raise AssertionError
    return x

x = None
print (1 in x)

