from onvif import ONVIFCamera
from config import *
from time import sleep

mycam = ONVIFCamera(ONVIF_1_HOST, 8000, ONVIF_1_USER, ONVIF_1_PASS)
media = mycam.create_media_service()
token = media.GetProfiles()[0].token
ptz = mycam.create_ptz_service()


ptz.Stop({'ProfileToken': token})

# # Start continuous move
# ptz.ContinuousMove({
#     'ProfileToken': token,
#     'Velocity': {
#         'PanTilt': {
#             'x': .3,
#             'y': .4
#         },
#         'Zoom': {
#             'x': 0
#         }
#     }
# })
#
# # Wait a certain time
# sleep(1)
#
# # Stop continuous move
# ptz.Stop({'ProfileToken': token})
#
# req = ptz.create_type('GotoHomePosition')
# print(req)
# req.ProfileToken = token
# print(req)
# ptz.GotoHomePosition(req)

print(ptz.GotoPreset({'ProfileToken': token, 'PresetToken': ptz.GetPresets({'ProfileToken': token})[0].token}))
