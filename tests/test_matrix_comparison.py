#!/usr/bin/env python3
"""Exercise the shared renderer with non-product alternatives and hostile text."""

from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/matrix-comparison'
spec = importlib.util.spec_from_file_location('matrix_render', SKILL / 'scripts/render.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def fixture():
    return {
        'title': 'Decision processes', 'scope': 'Illustrative team choices',
        'observed_at': 'Illustrative data', 'name_label': 'Approach',
        'columns': [
            {'key': 'verdict', 'label': 'Recommendation'},
            {'key': 'hours', 'label': 'Meeting hours', 'kind': 'number'},
            {'key': 'async', 'label': 'Asynchronous', 'kind': 'feature'},
            {'key': 'record', 'label': 'Decision record', 'kind': 'feature'},
        ],
        'rows': [
            {'id': 'written', 'name': 'Written proposal', 'cells': {
                'verdict': {'text': 'Best for considered decisions', 'status': 'good'},
                'hours': {'text': '0 hours', 'value': 0},
                'async': {'text': 'Yes', 'status': 'good', 'present': True},
                'record': {'text': 'Yes, but requires care', 'status': 'caution', 'present': True},
            }, 'details': [{'label': 'Basis', 'text': 'Illustrative, not research'}]},
            {'id': 'meeting', 'name': 'Live discussion', 'cells': {
                'hours': {'text': '1 hour', 'value': 1},
                'async': {'text': 'No', 'status': 'poor', 'present': False},
                'record': {'text': 'Not verified', 'status': 'unknown'},
            }},
            {'id': 'unknown', 'name': 'Unassessed approach', 'category': 'excluded', 'cells': {}},
        ],
        'numeric_filters': [{'key': 'hours', 'label': 'Meeting time', 'options': [
            {'label': 'Under 1 hour', 'max': 1, 'exclusive': True},
            {'label': '1 hour or less', 'max': 1}]}],
        'facets': [{'id': 'capabilities', 'title': 'Capabilities', 'columns': [
            {'key': 'async', 'label': 'Asynchronous', 'kind': 'feature'}]}],
    }


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.row_ids = []
        self.remote_assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'tr' and 'data-id' in attrs:
            self.row_ids.append(attrs['data-id'])
        if tag in {'script', 'img', 'link'} and (attrs.get('src') or attrs.get('href')):
            self.remote_assets.append(attrs)


class TestMatrixComparison(unittest.TestCase):
    def test_non_product_rows_facets_links_and_offline_output(self):
        text = renderer.render(fixture())
        doc = Document()
        doc.feed(text)
        self.assertEqual(doc.row_ids, ['written', 'meeting', 'unknown'] * 2)
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        for link in doc.links:
            if link.startswith('#'):
                self.assertIn(link[1:], doc.ids)
        self.assertEqual(doc.remote_assets, [])
        self.assertNotIn('{{TITLE}}', text)
        self.assertIn('Match all selected requirements', text)
        config = json.loads(re.search(r'type="application/json">(.*?)</script>', text, re.S)[1])
        self.assertEqual(config['rows'][0]['features'], ['async', 'record'])
        self.assertEqual(config['rows'][1]['features'], [])
        self.assertIsNone(config['rows'][2]['values']['hours'])

    def test_text_and_script_endings_are_escaped(self):
        data = fixture()
        data['rows'][0]['name'] = '<img src=x onerror=alert(1)>'
        data['rows'][0]['cells']['verdict']['text'] = '</script><script>alert(2)</script>'
        text = renderer.render(data)
        self.assertNotIn('<img src=x', text)
        self.assertNotIn('</script><script>alert', text)
        self.assertIn('&lt;img', text)
        self.assertIn('\\u003c/script', text)

    def test_bad_links_and_ambiguous_filter_values_fail(self):
        for change in ['bad_url', 'bad_source', 'string_flag', 'boolean_number', 'duplicate_id']:
            with self.subTest(change=change):
                data = fixture()
                if change == 'bad_url':
                    data['rows'][0]['url'] = 'javascript:alert(1)'
                elif change == 'bad_source':
                    data['rows'][0]['cells']['verdict']['sources'] = [{'label': 'Source', 'url': 'file:///secret'}]
                elif change == 'string_flag':
                    data['rows'][0]['cells']['async']['present'] = 'true'
                elif change == 'boolean_number':
                    data['rows'][0]['cells']['hours']['value'] = True
                else:
                    data['rows'][1]['id'] = data['rows'][0]['id']
                with self.assertRaises(ValueError):
                    renderer.render(data)

    def test_conflicting_facet_definitions_fail(self):
        data = fixture()
        data['facets'][0]['columns'][0]['kind'] = 'text'
        with self.assertRaises(ValueError):
            renderer.render(data)

    def test_section_id_collisions_fail(self):
        data = fixture()
        data['table_id'] = 'candidate-written'
        with self.assertRaises(ValueError):
            renderer.render(data)

    def test_empty_inputs_fail_before_creating_a_report(self):
        data = fixture()
        data['rows'] = []
        with self.assertRaises(ValueError):
            renderer.render(data)


if __name__ == '__main__':
    unittest.main()
