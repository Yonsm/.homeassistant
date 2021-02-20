#/user/bin/env python3

from braviarc.braviarc import BraviaRC
braviarc = BraviaRC('x9400e')

#connect to the instance (or register)
pin = '8404'
braviarc.connect(pin, 'HomeAssistant', 'Home Assistant')

#check connection
if braviarc.is_connected():

  #get power status
  power_status = braviarc.get_power_status()
  print (power_status)

  #get playing info
  playing_content = braviarc.get_playing_info()

  #print current playing channel
  print (playing_content.get('title'))

  #get volume info
  volume_info = braviarc.get_volume_info()

  #print current volume
  print (volume_info.get('volume'))

  #change channel
  braviarc.play_content('https://www.sample-videos.com/video123/mp4/720/big_buck_bunny_720p_20mb.mp4')

  #get app list
  app_info = braviarc.load_app_list()
  print (app_info)

  #start a given app
  braviarc.start_app("Kodi")

  #turn off the TV
  #braviarc.turn_off()
