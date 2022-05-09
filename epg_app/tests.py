from django.test import TestCase
from django.urls import reverse
#
# from .models import Channel, ChannelCategory
#
#
# class TestChannelModel(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.channel_data_1 = {
#             'name': 'BBC World News',
#             'resolution': 'SD',
#             'desc': 'BBC World News is an international English-language pay television network',
#         }
#
#         cls.channel_data_2 = {
#             'name': 'Discovery',
#             'resolution': 'SD',
#             'desc': 'Discovery Channel is an American cable channel owned by Warner Bros',
#         }
#
#     def setUp(self):
#         super().setUpClass()
#         channel_1 = Channel.objects.create(name="FOX Sport", resolution='SD')
#         channel_2 = Channel.objects.create(name=self.channel_data_2['name'],
#                                            resolution=self.channel_data_2['resolution'],
#                                            desc=self.channel_data_2['desc'])
#         channel_3 = Channel.objects.create(name="Comedy Central", resolution='HD')
#         category_1 = ChannelCategory.objects.create(name="sport")
#         category_1.channel.add(channel_1)
#         category_2 = ChannelCategory.objects.create(name="movies")
#         category_2.channel.add(channel_2)
#         category_2.channel.add(channel_3)
#         category_3 = ChannelCategory.objects.create(name="entertaining")
#         category_3.channel.add(channel_1)
#         category_3.channel.add(channel_3)
#
#     def tearDown(self):
#         Channel.objects.all().delete()
#
#     def test_channel_update(self):
#         channel = Channel.objects.get(name=self.channel_data_2["name"])
#         new_name = 'Discovery Channel HD'
#         new_resolution = 'HD'
#
#         response = self.client.post(
#             reverse('channel_update', kwargs={'pk': channel.id}),
#             {'name': new_name,
#              'resolution': new_resolution})
#
#         self.assertEqual(response.status_code, 302)
#
#         new_channel = Channel.objects.get(id=channel.id)
#
#         self.assertEqual(new_name,
#                          new_channel.name)
#
#         self.assertEqual(new_resolution,
#                          new_channel.resolution)
#
#     def test_channel_update_without_resolution(self):
#         channel = Channel.objects.get(name=self.channel_data_2["name"])
#
#         response = self.client.post(
#             reverse('channel_update', kwargs={'pk': channel.id}),
#             {'name': 'Discovery Channel HD'})
#
#         self.assertEqual(response.status_code, 200)
#
#     def test_channel_get(self):
#         channel_1 = Channel.objects.get(name="FOX Sport")
#         channel_2 = Channel.objects.get(name="Discovery")
#         self.assertNotEqual(channel_1, channel_2)
#
#     def test_channel_print(self):
#         channel_1 = Channel.objects.get(name="Discovery")
#         channel_2 = Channel.objects.get(name="Comedy Central")
#         self.assertEqual(str(channel_1), 'Discovery (movies)')
#         self.assertEqual(str(channel_2), 'Comedy Central (movies, entertaining)')
#
#     def test_channel_get_items(self):
#         channel_1 = Channel.objects.get(name="FOX Sport")
#         channel_2 = Channel.objects.get(name="Comedy Central")
#         channels = ChannelCategory.objects.get(name="entertaining").channel.all()
#         self.assertEqual(list(channels), [channel_1, channel_2])
#
#     def test_channel_add(self):
#         response = self.client.post(
#             '/channel/create/',
#             data=self.channel_data_1
#         )
#
#         self.assertEqual(302, response.status_code)
#
#         new_channel = Channel.objects.get(
#             name=self.channel_data_1['name']
#         )
#
#         self.assertEqual(self.channel_data_1['desc'],
#                          new_channel.desc)
#
#     def test_channel_add_duplicate(self):
#         response = self.client.post(
#             '/channel/create/',
#             data=self.channel_data_2
#         )
#         self.assertEqual(200, response.status_code)
