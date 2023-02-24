# calling one member from another function in another function
def dummy_function():
    print("dummy_function")
    a = 1

def dummy_function2():
    print("dummy_function2")
    dummy_function()
    print("a?", a)

dummy_function2()

exit()

import http.client

conn = http.client.HTTPSConnection('store.steampowered.com')
conn.request('GET', '/api/appdetails?appids=1973710')
res = conn.getresponse()

data = res.read()
print(res.status, res.reason)
print(data.decode('utf-8'))
print(res.getheaders())