
import requests
print('posting')
requests.request('POST', 'localhost:8080/remember', data={'a': '1'})