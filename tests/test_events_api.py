import unittest

from newslynx.client import API


class TestEventsAPI(unittest.TestCase):
    org = 1
    api = API(org=1)

    def test_create_recipe_event_not_approved(self):
        e = {
            'source_id': '09ac-11e5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'body': 'foo bar',
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'tag_ids': [1, 2, 3],
            'recipe_id': 1,
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        event = self.api.events.create(**e)
        assert(event['source_id'] != e['source_id'])
        assert(not event['source_id'].startswith('manual'))
        assert(e['tag_ids'] == event['tag_ids'])
        assert(event['provenance'] == 'recipe')
        assert(event['status'] != 'approved')

    def test_create_recipe_event_pending(self):
        e = {
            'source_id': '09ac-11fdasfde5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'body': 'foo bar',
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'recipe_id': 1,
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        event = self.api.events.create(**e)
        assert(event['source_id'] != e['source_id'])
        assert(not event['source_id'].startswith('manual'))
        assert(len(event['tag_ids']) == 0)
        assert(event['provenance'] == 'recipe')
        assert(event['status'] == 'pending')

    def test_create_manual_event_not_approved(self):
        e = {
            'source_id': '09ac-11fdasfsafasdfasde5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'body': 'foo bar',
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'tag_ids': [1, 2, 3],
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        event = self.api.events.create(**e)
        assert(event['source_id'] != e['source_id'])
        assert(event['source_id'].startswith('manual'))
        assert(len(event['tag_ids']) == 3)
        assert(event['provenance'] == 'manual')
        assert(event['status'] != 'approved')

    def test_create_manual_event_pending(self):
        e = {
            'source_id': '09ac-11fdasffsafddsfsafasdfasdefdsaf5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'body': 'foo bar',
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        event = self.api.events.create(**e)
        assert(event['source_id'] != e['source_id'])
        assert(event['source_id'].startswith('manual'))
        assert(len(event['tag_ids']) == 0)
        assert(event['provenance'] == 'manual')
        assert(event['status'] == 'pending')

    # def test_create_event_with_content_string(self):
    #     t = self.api.content.get(1)
    #     e = {
    #         'source_id': '09ac-11fdasfsafasdfasdfdsafdfefdsaf5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'body': 'foo bar {}'.format(t['url']),
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(len(event['content_items']))

    # def test_create_event_with_content_html(self):
    #     t = self.api.content.get(1)
    #     e = {
    #         'source_id': '09ac-11fdasfsafasdfasdfdsafdfefdsaf5-8e2a-6c4008aeb606',
    #         'description': 'eos aliquid mollitia dicta',
    #         'body': 'foo bar <a href="{}"></a>'.format(t['url']),
    #         'created': '2015-05-15 09:54:46+00:00',
    #         'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
    #         'authors': ['Stanford Feeney'],
    #         'title': 'laboriosam facilis q',
    #         'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
    #     }
    #     event = self.api.events.create(**e)
    #     assert(len(event['content_items']))

    def test_search_and_delete_events(self):
        s = 'this is a unique string'
        e = {
            'source_id': '09ac-11fdasfsafasdfdasfddsafasdfdsafdfefdsaf5-8e2a-6c4008aeb606',
            'description': 'eos aliquid mollitia dicta',
            'body': s,
            'created': '2015-05-15 09:54:46+00:00',
            'url': 'http://example.com/a81857dc-09ac-11e5-8e2a-6c4008aeb606/',
            'authors': ['Stanford Feeney'],
            'title': 'laboriosam facilis q',
            'img_url': 'http://example.com/a818591c-09ac-11e5-8e9f-6c4008aeb606.jpg',
        }
        self.api.events.create(**e)
        results = self.api.events.search(q=s, incl_body=True)
        for r in results['events']:
            assert(s in r['body'])
            self.api.events.delete(r['id'], force=True)

    def test_error_on_create_deleted_events(self):
        event = self.api.events.search(status='deleted', provenance='recipe')
        e = event['events'][0]
        e.pop('status', None)
        e['source_id'] = e['source_id'].split(':')[1]
        try:
            self.api.events.create(**e)
        except Exception as e:
            assert(e.status_code == 422)
        else:
            assert False

    def test_null_on_create_event_with_no_content_items(self):
        r = self.api.events.search(status='pending', incl_body=True)
        e = r['events'][0]
        e.pop('id')
        e['must_link'] = True
        resp = self.api.events.create(**e)
        assert(resp is None)

    def test_event_update(self):
        res = self.api.events.search(
            status='pending', provenance='recipe', incl_body=True)
        event = res['events'][0]
        event['content_item_ids'] = [1, 2]
        event['tag_ids'] = [1, 2]
        event['status'] = 'approved'
        event = self.api.events.update(event['id'], **event)
        assert(len(event['content_items']))
        assert(len(event['tag_ids']))
        assert(event['status'] == 'approved')

    def test_event_delete_no_force(self):
        res = self.api.events.search(status='pending')
        event = res['events'][0]
        resp = self.api.events.delete(event['id'])
        assert(resp)
        resp = self.api.events.get(event['id'])
        assert(resp['id'] == event['id'])
        assert(resp['status'] == 'deleted')

    def test_event_delete_force(self):
        res = self.api.events.search(status='pending')
        event = res['events'][0]
        resp = self.api.events.delete(event['id'], force=True)
        assert(resp)
        try:
            self.api.events.update(event['id'], **event)
        except Exception as e:
            assert(e.status_code == 404)
        else:
            assert False

    def test_event_add_delete_tag(self):
        res = self.api.events.search(status='approved', per_page=1)
        event = res['events'][0]
        event = self.api.events.add_tag(event['id'], 1)
        assert(1 in event['tag_ids'])
        event = self.api.events.remove_tag(event['id'], 1)
        assert(1 not in event['tag_ids'])

    def test_event_add_delete_content_item(self):
        res = self.api.events.search(status='approved', per_page=1)
        event = res['events'][0]
        event = self.api.events.add_content_item(event['id'], 1)
        assert(1 in [t['id'] for t in event['content_items']])
        event = self.api.events.remove_content_item(event['id'], 1)
        assert(1 not in [t['id'] for t in event['content_items']])

    def test_event_facet_by_provenance(self):
        res = self.api.events.search(status='approved', per_page=1, facets='provenances')
        assert(res['total'] == sum([f['count'] for f in res['facets']['provenances']]))

    def test_event_facet_by_status(self):
        res = self.api.events.search(status='approved', per_page=1, facets='statuses')
        assert(res['total'] == sum([f['count'] for f in res['facets']['statuses']]))


if __name__ == '__main__':
    unittest.main()
