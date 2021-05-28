from requests import get


def my_ip():
    ip = get('https://api.my-ip.io/ip').text
    return ip


def my_coord():
    ip = my_ip()
    url_lib = f'http://ipwhois.app/json/{ip}'
    response = get(url_lib)
    data = response.json()

    param = [float(data['latitude']), float(data['longitude'])]
    return param


if __name__ == '__main__':
    print(my_coord())
