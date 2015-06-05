import unittest
from faker import Faker

from newslynx.client import API
from newslynx import settings

fake = Faker()


class TestEventsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    # def test_create_recipe_event_approved(self):
    #     e = {
    #         'source_id': '09ac-11e5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'content': 'foo bar',
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'tag_ids': [1, 2, 3],
    #         'recipe_id': 1,
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(event['source_id'] != e['source_id'])
    #     assert(not event['source_id'].startswith('manual'))
    #     assert(e['tag_ids'] == event['tag_ids'])
    #     assert(event['provenance'] == 'recipe')
    #     assert(event['status'] == 'approved')

    # def test_create_recipe_event_pending(self):
    #     e = {
    #         'source_id': '09ac-11fdasfde5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'content': 'foo bar',
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'recipe_id': 1,
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(event['source_id'] != e['source_id'])
    #     assert(not event['source_id'].startswith('manual'))
    #     assert(len(event['tag_ids']) == 0)
    #     assert(event['provenance'] == 'recipe')
    #     assert(event['status'] == 'pending')

    # def test_create_manual_event_approved(self):
    #     e = {
    #         'source_id': '09ac-11fdasfsafasdfasde5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'content': 'foo bar',
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'tag_ids': [1, 2, 3],
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(event['source_id'] != e['source_id'])
    #     assert(event['source_id'].startswith('manual'))
    #     assert(len(event['tag_ids']) == 3)
    #     assert(event['provenance'] == 'manual')
    #     assert(event['status'] == 'approved')

    # def test_create_manual_event_pending(self):
    #     e = {
    #         'source_id': '09ac-11fdasffsafddsfsafasdfasdefdsaf5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'content': 'foo bar',
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(event['source_id'] != e['source_id'])
    #     assert(event['source_id'].startswith('manual'))
    #     assert(len(event['tag_ids']) == 0)
    #     assert(event['provenance'] == 'manual')
    #     assert(event['status'] == 'pending')

    # def test_create_event_with_thing_string(self):
    #     t = self.api.things.get(1)
    #     e = {
    #         'source_id': '09ac-11fdasfsafasdfasdfdsafdfefdsaf5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'content': 'foo bar {}'.format(t.url),
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(len(event['things']))

    def test_create_event_with_thing_short_url(self):
        t = self.api.things.get(1)
        e = {
            'source_id': '09ac-11fdasfsafasdfasdefdsafsadfdfasf5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'content': 'foo bar nwsln.cz/1KcLvR0',
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        event = self.api.events.create(**e)
        assert(len(event['things']))

if __name__ == '__main__':
    unittest.main()
