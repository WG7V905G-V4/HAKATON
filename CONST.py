import geocoder

def get_my_location():
    g = geocoder.ip('me')  # определяет по IP адресу
    return g.lat, g.lng

MY_LOCATION = get_my_location()

MY_USERNAME = 