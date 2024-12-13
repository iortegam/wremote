import weather
#from weather import Unit
#from weather import Weather as we, Unit

weather = weather.Weather(unit=Unit.CELSIUS)
location = weather.lookup_by_location('boulder')
condition = location.condition
print(condition.text)