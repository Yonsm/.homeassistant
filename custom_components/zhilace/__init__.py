#!/usr/bin/env python3
import sys
import json
import logging
from remote_hass import RemoteHass

_LOGGER = logging.getLogger(__name__)

sensor_units = ['°C', '%', 'μg/m³', 'ppm', 'mg/m³', 'lm']
#sensor_classes = ['temperature', 'humidity', 'pm25', 'co2', 'hcho', 'illuminance']
binary_sensor_classes = ['opening', 'motion', 'window', 'illuminance']
card_types = ['weather-forecast', 'glance', 'entities', 'entity', 'media-control', 'thermostat', 'picture-entity']
zone_names = [['客厅', '室内'], ['餐厅', '入户', '玄关', '厨房'], ['过道', '洗手间'], ['主卧', '浴室'], ['次卧'], ['儿童房'], ['书房'], ['阳台', '天气', '日照', '太阳', '室外'], ['其它']]
domain_names = ['', '天气', '日照', '太阳', '传感器', '二元传感器', '人员',  '设备', '灯光', '开关', '风扇', '净化器', '新风机', '扫地机', '卷帘', '空调', '地暖', '视听', '摄像头', '输入', '遥控', '智能', '隐藏', '其它']
domain_types = ['weather', 'sun', 'sensor', 'binary_sensor', 'person', 'device_tracker', 'light', 'switch', 'fan', 'remote', 'vacuum', 'cover', 'climate', 'media_player', 'camera', 'input_text', 'automation']


def make_lovelace(hass):
    status_cards = []
    toggle_cards = []
    thermostat_cards = []
    guard_cards = []
    guard_badges = []
    automation_cards = []
    other_cards = []
    sorts = domain_names[:-1] + [zone for z in zone_names for zone in z]

    def get_zone(name):
        for z in zone_names:
            for zone in z:
                if name.startswith(zone):
                    return z[0]
        return '其它'

    def get_sort_index(title):
        i = len(sorts) - 1
        while i >= 0 and title != sorts[i]:  # title not in zone_names[i]:
            i -= 1
        return i

    def add_to_sorted(items, item, func, func2=None):
        n1 = func(item)
        z1 = func2(n1) if func2 else n1
        i = len(items)-1
        while i >= 0:
            n2 = func(items[i])
            z2 = func2(n2) if func2 else n2
            j = get_sort_index(z2)
            k = get_sort_index(z1)
            if k > j or (j == k and n1 > n2):
                break
            i -= 1
        items.insert(i + 1, item)

    entity_names = {}

    def add_to_entities(entities, entity_id):
        add_to_sorted(entities, entity_id, lambda x: entity_names[x], lambda x: get_zone(x))

    def add_to_entities_card(cards, card):
        add_to_sorted(cards, card, lambda x: entity_names[x['entity']], lambda x: get_zone(x))

    def add_to_entities_card(entity_id, cards, title, key='title', type='entities'):
        card = next((i for i in cards if i.get(key) == title), None)
        if card is None:
            card = {'type': type, key: title, 'entities': [entity_id]}
            add_to_sorted(cards, card, lambda x: x[key])
        else:
            add_to_entities(card['entities'], entity_id)
        return card

    # title = '智家'
    entities = hass.states.async_all()
    for i in entities:
        entity_id = i.entity_id
        attributes = i.attributes
        name = attributes['friendly_name']
        entity_names[entity_id] = name
        domain = entity_id[:entity_id.find('.')]
        if entity_id == 'zone.home':
            title = name
        elif 'hidden' in attributes:
            add_to_entities_card(entity_id, other_cards, '隐藏')
        elif domain == 'weather':
            card = {'type': 'weather-forecast', 'name': name, 'entity': entity_id}
            if 'attribution' in attributes:
                card['secondary_info_attribute'] = 'attribution'
            status_cards.insert(0, card)
        elif domain == 'sun' or domain == 'sensor':
            zone = '阳台' if domain == 'sun' else get_zone(name)
            add_to_entities_card(entity_id, status_cards, zone, 'name', 'glance')
        elif domain == 'light':
            add_to_entities_card(entity_id, toggle_cards, '灯光')
        elif domain == 'media_player':
            add_to_entities_card(entity_id, toggle_cards, '视听')
        elif domain == 'cover' or domain == 'fan' or domain == 'switch' or domain == 'vacuum':
            name_domain_names = {'净化': '净化器',  '新风': '新风机', '扇': '风扇', '音箱': '视听', '存储': '视听', '幕布': '视听', '帘': '卷帘'}
            add_to_entities_card(entity_id, toggle_cards, next((v for k, v in name_domain_names.items() if k in name), '其它'))
        elif domain == 'climate':
            card = {'type': 'thermostat', 'entity': entity_id}
            add_to_entities_card(thermostat_cards, card)
        elif domain == 'binary_sensor':
            add_to_entities(guard_badges, entity_id)
        elif domain == 'camera':
            card = {'type': 'picture-entity', 'entity': entity_id}
            add_to_entities_card(guard_cards, card)
        elif domain == 'automation':
            add_to_entities_card(entity_id, automation_cards, get_zone(name))
        else:
            domain_names = {'device_tracker': '设备', 'input_text': '输入', 'person': '人员'}
            add_to_entities_card(entity_id, other_cards, domain_names.get(domain, '其它'))

    for cards in [status_cards, toggle_cards, thermostat_cards, guard_cards, automation_cards, other_cards]:
        for card in cards:
            card_type = card['type']
            if card_type == 'entities':
                card_key = 'title'
            elif card_type == 'glance':
                card_key = 'name'
            else:
                continue
            if card[card_key] != '其它':
                entities = card['entities']
                if len(entities) == 1:
                    add_to_entities_card(entities[0], cards, '其它', card_key, card_type)
                    cards.remove(card)

    result = {
        'title': title,
        'views': [
            {
                'title': '状态',
                'path': 'status',
                'cards': status_cards
            },
            {
                'title': '调控',
                'path': 'toggle',
                'cards': toggle_cards
            },
            {
                'title': '空调',
                'path': 'thermostat',
                'cards': thermostat_cards
            },
            {
                'title': '安防',
                'path': 'guard',
                'badges': guard_badges,
                'cards': guard_cards
            },
            {
                'title': '智能',
                'path': 'automation',
                'cards': automation_cards
            },
            {
                'title': '其它',
                'path': 'other',
                'cards': other_cards
            },
        ]
    }
    return result


def get_zone(name, default=None):
    for i in zone_names:
        for zone in i:
            if name.startswith(zone):
                return i[0]
    return None


def get_zone_index(name):
    for i in range(len(zone_names)):
        for zone in zone_names[i]:
            if name.startswith(zone):
                return i
    return -1


def get_entity_zone(attributes, default=None):
    for key in ['genie_zone', 'genie_name', 'friendly_name']:
        if key in attributes:
            zone = get_zone(attributes[key])
            if zone is not None:
                return zone
    return default


def get_entity_zone_index(attributes):
    for key in ['genie_zone', 'genie_name', 'friendly_name']:
        if key in attributes:
            index = get_zone_index(attributes[key])
            if index != -1:
                return index
    return -1


def add_to_sorted(item, items, compare):
    i = len(items) - 1
    while i >= 0 and compare(item, items[i]) < 0:
        i -= 1
    items.insert(i + 1, item)


def compare_item(items, item1, item2):
    try:
        index1 = items.index(item1)
    except:
        index1 = -1
    try:
        index2 = items.index(item2)
    except:
        index2 = -1
    return index1 - index2


def compare_string(string1, string2):
    if string1 < string2:
        return -1
    elif string1 > string2:
        return 1
    return 0


def compare_title(title1, title2):
    ret = get_zone_index(title1) - get_zone_index(title2)
    if ret == 0:
        ret = compare_item(domain_names, title1, title2)
        if ret == 0:
            ret = compare_string(title1, title2)
    return ret


def compare_view(view1, view2):
    return compare_title(view1['title'], view2['title'])


entity_attributes = {}


def compare_entity_id(entity_id1, entity_id2):
    domain1 = entity_id1[:entity_id1.find('.')]
    domain2 = entity_id2[:entity_id2.find('.')]
    ret = compare_item(domain_types, domain1, domain2)
    if ret == 0:
        attrs1 = entity_attributes[entity_id1]
        attrs2 = entity_attributes[entity_id2]
        ret = get_entity_zone_index(attrs1) - get_entity_zone_index(attrs2)
        if ret == 0:
            if domain1 == 'sensor':
                ret = compare_item(sensor_units, attrs1.get('unit_of_measurement'), attrs2.get('unit_of_measurement'))
            elif domain1 == 'binary_sensor':
                ret = compare_item(binary_sensor_classes, attrs1.get('device_class'), attrs2.get('device_class'))
            if ret == 0:
                ret = compare_string(attrs1['friendly_name'], attrs2['friendly_name'])
    return ret


def compare_card(card1, card2):
    ret = compare_item(card_types, card1['type'], card2['type'])
    if ret == 0:
        title1 = card1.get('title') or card1.get('name', '')
        title2 = card2.get('title') or card2.get('name', '')
        ret = compare_title(title1, title2)
        if ret == 0:
            entity_id1 = card1.get('entity')
            entity_id2 = card2.get('entity')
            if entity_id1:
                if entity_id2:
                    return compare_entity_id(entity_id1, entity_id2)
                else:
                    return -1
            elif entity_id2:
                return 1
    return ret

def add_to_entities_card(entity_id, cards, title='', key='title', type='entities'):
    card = next((i for i in cards if i.get(key) == title), None)
    if card is None:
        card = {'type': type, key: title, 'entities': [entity_id]}
        add_to_sorted(card, cards, compare_card)
    else:
        add_to_sorted(entity_id, card['entities'], compare_entity_id)


def make_lovelace2(hass):
    views = []

    # title = '智家'
    entities = hass.states.async_all()
    for i in entities:
        entity_id = i.entity_id
        attributes = i.attributes
        name = attributes['friendly_name']
        if entity_id == 'zone.home':
            title = name
            continue
        entity_attributes[entity_id] = attributes
        domain = entity_id[:entity_id.find('.')]
        zone = '其它' if 'hidden' in attributes else get_entity_zone(attributes, '其它')
        view = next((i for i in views if i.get('title') == zone), None)
        if view is None:
            view = {'title': zone, 'badges': [], 'cards': []}
            add_to_sorted(view, views, compare_view)
        if domain == 'sun' or domain == 'sensor' or domain == 'binary_sensor' or domain == 'person' or domain == 'device_tracker':
            add_to_sorted(entity_id, view['badges'], compare_entity_id)
            continue
        cards = view['cards']
        if 'hidden' in attributes:
            add_to_entities_card(entity_id, cards, '隐藏')
            continue
        elif domain == 'weather':
            card = {'type': 'weather-forecast', 'name': name, 'entity': entity_id}
        elif domain == 'media_player':
            card = {'type': 'media-control', 'entity': entity_id}
        elif domain == 'climate':
            card = {'type': 'thermostat', 'entity': entity_id}
        elif domain == 'camera':
            card = {'type': 'picture-entity', 'entity': entity_id}
        elif domain == 'automation':
            add_to_entities_card(entity_id, cards, '智能')
            continue
        else:
            add_to_entities_card(entity_id, cards, '')
            continue
        add_to_sorted(card, cards, compare_card)

    return {'title': title, 'views': views}


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) < 3:
        print(f'Usage: {argv[0]} <https://192.168.1.x:8123> <token> [[-]<1|2|3|4>] [deviceId]')
        exit(0)
    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    hass = RemoteHass(argv[1], argv[2])
    result = make_lovelace(hass) if len(argv) > 3 and argv[3] == '2' else make_lovelace2(hass)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    ret1 = compare_item(sensor_classes, 'temperature', 'humidity')
    ret2 = compare_string('A', 'B')
    ret3 = compare_title('客厅', '餐厅')
    ret4 = compare_title('灯光', '智能')
    ret5 = compare_entity_id('sensor.can_ting_wen_du', 'sensor.can_ting_ke_li_wu')
    print('x')