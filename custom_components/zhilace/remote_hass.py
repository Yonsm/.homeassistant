#!/usr/bin/env python3
import json
import requests
import logging

_LOGGER = logging.getLogger(__name__)


class RemoteHass:

    def __init__(self, url, token):
        self.url = url + '/api/'
        self.token = token
        self.states = self
        self.services = self
        requests.packages.urllib3.disable_warnings()

    def rest(self, cmd, data=None):
        url = self.url + cmd
        method = 'POST' if data else 'GET'
        _LOGGER.debug('REST %s %s %s', method, url, data or '')
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Content-Type': 'application/json'} if self.token else None
        text = requests.request(method, url, json=data, headers=headers, verify=False).text
        # _LOGGER.info('REST RESPONSE: %s', text)
        return json.loads(text)

    def async_all(self):
        from collections import namedtuple
        states = []
        for d in self.rest('states') or []:
            states.append(namedtuple('EntityState', d.keys())(*d.values()))
        return states

    def get(self, entity_id):
        from collections import namedtuple
        d = self.rest('states/' + entity_id) or {}
        return namedtuple('EntityState', d.keys())(*d.values())

    def call(self, domain, service, data, blocking=False):
        return self.rest('services/' + domain + '/' + service, data) or []

    async def async_call(self, domain, service, data, blocking=False):
        return self.call(self, domain, service, data, blocking)
